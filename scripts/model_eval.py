from __future__ import annotations

import argparse
import html
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import requests
from fastapi.testclient import TestClient


ANSWER_RE = re.compile(
    r'<textarea id="answer"[^>]*>(?P<value>.*?)</textarea>',
    re.IGNORECASE | re.DOTALL,
)
PRE_RE = re.compile(r"<pre>(?P<value>.*?)</pre>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LocalRAG model eval against seed questions.")
    parser.add_argument(
        "--mode",
        choices=("http", "inprocess"),
        default="http",
        help="Evaluate against a running server or import the app in-process.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:7860",
        help="Running LocalRAG base URL.",
    )
    parser.add_argument(
        "--seed-file",
        default="eval/rag_eval_seed.json",
        help="Path to eval seed JSON file.",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="One or more Ollama model tags to evaluate.",
    )
    parser.add_argument(
        "--topk",
        type=int,
        default=6,
        help="top-k used for retrieval.",
    )
    parser.add_argument(
        "--role",
        default="archivist",
        help="Response role to use during eval.",
    )
    parser.add_argument(
        "--answer-language",
        default="ru",
        help="Preferred answer language.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=420,
        help="Per-question request timeout in seconds.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional output path. Defaults to temp/model_eval_<timestamp>.json",
    )
    parser.add_argument(
        "--startup-wait-timeout",
        type=int,
        default=900,
        help="Maximum time to wait for index readiness before evaluation.",
    )
    parser.add_argument(
        "--startup-poll-interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds while waiting for index readiness.",
    )
    parser.add_argument(
        "--min-documents",
        type=int,
        default=1,
        help="Minimum indexed documents required before eval starts.",
    )
    parser.add_argument(
        "--docs-path",
        default="",
        help="Optional docs path override for in-process mode.",
    )
    parser.add_argument(
        "--host-docs-path",
        default="",
        help="Optional host docs path display override for in-process mode.",
    )
    parser.add_argument(
        "--ollama-base-url",
        default="",
        help="Optional Ollama base URL override. In in-process mode defaults to http://127.0.0.1:11434.",
    )
    return parser.parse_args()


def load_seed(path: str) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def extract_answer(fragment: str) -> str:
    match = ANSWER_RE.search(fragment or "")
    if not match:
        return ""
    return html.unescape(match.group("value")).strip()


def extract_context_blocks(fragment: str) -> list[str]:
    blocks = []
    for match in PRE_RE.finditer(fragment or ""):
        value = TAG_RE.sub("", match.group("value"))
        text = html.unescape(value).strip()
        if text:
            blocks.append(text)
    return blocks


def normalize_text(value: str) -> str:
    normalized = str(value or "").casefold()
    normalized = re.sub(r"\b([a-zа-яё])\.\s*", r"\1.", normalized)
    return " ".join(normalized.split())


def evaluate_case(
    session: requests.Session,
    base_url: str,
    model: str,
    question_case: dict[str, Any],
    *,
    topk: int,
    role: str,
    answer_language: str,
    timeout: int,
) -> dict[str, Any]:
    payload = {
        "question": question_case["question"],
        "model": model,
        "topk": str(topk),
        "lang": answer_language,
        "answer_language": answer_language,
        "role": role,
        "response_role": role,
        "role_style": "balanced",
        "debug_mode": "1",
    }
    started = time.perf_counter()
    response = session.post(f"{base_url.rstrip('/')}/api/ask", data=payload, timeout=timeout)
    latency_ms = int((time.perf_counter() - started) * 1000)
    response.raise_for_status()

    answer = extract_answer(response.text)
    context_blocks = extract_context_blocks(response.text)
    context_text = "\n---\n".join(context_blocks)

    answer_normalized = normalize_text(answer)
    context_normalized = normalize_text(context_text)
    expected_contains = [str(item) for item in question_case.get("expected_contains", [])]
    expected_contains_hits = [
        item for item in expected_contains if normalize_text(item) in answer_normalized
    ]
    raw_expected_sources = question_case.get("expected_sources")
    if isinstance(raw_expected_sources, list) and raw_expected_sources:
        expected_sources = [str(item) for item in raw_expected_sources if str(item).strip()]
    else:
        expected_sources = [str(question_case.get("expected_source") or "")]
    expected_sources = [item for item in expected_sources if item]
    source_hit = any(normalize_text(item) in context_normalized for item in expected_sources)
    hit_ratio = (
        len(expected_contains_hits) / len(expected_contains)
        if expected_contains
        else 1.0
    )
    pass_loose = bool(expected_contains_hits) and source_hit
    pass_strict = len(expected_contains_hits) == len(expected_contains) and source_hit
    return {
        "id": question_case.get("id"),
        "question": question_case.get("question"),
        "expected_contains": expected_contains,
        "expected_source": expected_sources[0] if expected_sources else "",
        "expected_sources": expected_sources,
        "answer": answer,
        "context_excerpt": context_blocks[:3],
        "latency_ms": latency_ms,
        "answer_hits": expected_contains_hits,
        "answer_hit_ratio": round(hit_ratio, 3),
        "source_hit": source_hit,
        "pass_loose": pass_loose,
        "pass_strict": pass_strict,
        "notes": question_case.get("notes", ""),
    }


def summarize_model(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {
            "loose_pass_rate": 0.0,
            "strict_pass_rate": 0.0,
            "avg_latency_ms": 0,
            "avg_answer_hit_ratio": 0.0,
        }
    count = len(results)
    loose = sum(1 for row in results if row["pass_loose"])
    strict = sum(1 for row in results if row["pass_strict"])
    avg_latency = int(sum(int(row["latency_ms"]) for row in results) / count)
    avg_hit_ratio = round(sum(float(row["answer_hit_ratio"]) for row in results) / count, 3)
    return {
        "loose_pass_rate": round(loose / count, 3),
        "strict_pass_rate": round(strict / count, 3),
        "avg_latency_ms": avg_latency,
        "avg_answer_hit_ratio": avg_hit_ratio,
        "loose_passed": loose,
        "strict_passed": strict,
        "total": count,
    }


def default_output_path() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("temp") / f"model_eval_{stamp}.json"


class ResponseAdapter:
    def __init__(self, response):
        self._response = response
        self.text = response.text

    def raise_for_status(self) -> None:
        status = getattr(self._response, "status_code", 200)
        if status >= 400:
            raise requests.HTTPError(f"HTTP {status}: {self.text[:500]}")

    def json(self) -> Any:
        return self._response.json()


class TestClientSession:
    def __init__(self, client: TestClient):
        self._client = client

    def _path(self, url: str) -> str:
        parsed = urlsplit(url)
        return parsed.path or "/"

    def get(self, url: str, timeout: int | None = None) -> ResponseAdapter:
        _ = timeout
        return ResponseAdapter(self._client.get(self._path(url)))

    def post(self, url: str, data: dict[str, Any] | None = None, timeout: int | None = None) -> ResponseAdapter:
        _ = timeout
        return ResponseAdapter(self._client.post(self._path(url), data=data or {}))


def load_inprocess_session(args: argparse.Namespace) -> tuple[TestClientSession, dict[str, Any]]:
    root_dir = Path(__file__).resolve().parent.parent
    app_dir = root_dir / "app"
    main_path = root_dir / "main.py"

    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    os.environ["LOCALRAG_SKIP_STARTUP"] = "1"
    if args.docs_path:
        os.environ["DOCS_PATH"] = args.docs_path
    if args.host_docs_path:
        os.environ["HOST_DOCS_PATH"] = args.host_docs_path
    os.environ["OLLAMA_BASE_URL"] = (
        args.ollama_base_url.strip() or "http://127.0.0.1:11434"
    )

    spec = importlib.util.spec_from_file_location("localrag_eval_main", main_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load main module from {main_path}")
    main_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_mod)

    if not main_mod.load_persisted_index():
        main_mod.rebuild_index()
    status_code, status_params = main_mod.get_index_status_meta()
    indexed_documents = int(main_mod.get_indexed_file_count())
    health_payload = {
        "ok": status_code in {"ready_ask", "ready_loaded"},
        "mode": "inprocess",
        "index": {
            "ready": status_code in {"ready_ask", "ready_loaded"},
            "status": status_code,
            "documents": indexed_documents,
            "params": status_params,
        },
        "docs_path": main_mod.get_docs_path_display(),
    }
    if indexed_documents < max(1, int(args.min_documents or 1)):
        details = json.dumps(health_payload, ensure_ascii=False)
        raise RuntimeError(f"In-process LocalRAG index is not ready for eval. {details}")

    client = TestClient(main_mod.app)
    return TestClientSession(client), health_payload


def wait_until_ready(
    session: requests.Session,
    base_url: str,
    *,
    timeout: int,
    poll_interval: float,
    min_documents: int,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_payload: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        try:
            response = session.get(f"{base_url.rstrip('/')}/api/health", timeout=15)
            response.raise_for_status()
            last_payload = response.json()
        except requests.RequestException:
            time.sleep(poll_interval)
            continue

        index = last_payload.get("index") or {}
        status = str(index.get("status") or "")
        documents = int(index.get("documents") or 0)
        ready = bool(index.get("ready"))
        if ready and status in {"ready_ask", "ready_loaded"} and documents >= min_documents:
            return last_payload
        time.sleep(poll_interval)

    details = json.dumps(last_payload or {}, ensure_ascii=False)
    raise RuntimeError(
        "LocalRAG did not reach a ready index state before eval "
        f"(timeout={timeout}s, min_documents={min_documents}). Last payload: {details}"
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    seed = load_seed(args.seed_file)
    if args.mode == "inprocess":
        session, health_payload = load_inprocess_session(args)
    else:
        session = requests.Session()
        health_payload = wait_until_ready(
            session,
            args.base_url,
            timeout=args.startup_wait_timeout,
            poll_interval=args.startup_poll_interval,
            min_documents=args.min_documents,
        )
    report: dict[str, Any] = {
        "mode": args.mode,
        "base_url": args.base_url,
        "seed_file": args.seed_file,
        "health": health_payload,
        "models": {},
    }
    for model in args.models:
        rows = []
        print(f"\n=== {model} ===")
        for index, question_case in enumerate(seed, start=1):
            row = evaluate_case(
                session,
                args.base_url,
                model,
                question_case,
                topk=args.topk,
                role=args.role,
                answer_language=args.answer_language,
                timeout=args.timeout,
            )
            rows.append(row)
            status = "PASS" if row["pass_loose"] else "FAIL"
            print(
                f"[{status}] {index:02d}/{len(seed)} {row['id']} "
                f"lat={row['latency_ms']}ms hits={row['answer_hits']} source={row['source_hit']}"
            )
        report["models"][model] = {
            "summary": summarize_model(rows),
            "cases": rows,
        }

    output_path = Path(args.output) if args.output else default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== summary ===")
    for model, payload in report["models"].items():
        summary = payload["summary"]
        print(
            f"{model}: loose={summary['loose_passed']}/{summary['total']} "
            f"strict={summary['strict_passed']}/{summary['total']} "
            f"avg_hit_ratio={summary['avg_answer_hit_ratio']} "
            f"avg_latency={summary['avg_latency_ms']}ms"
        )
    print(f"\nSaved report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
