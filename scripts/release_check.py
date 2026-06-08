#!/usr/bin/env python3
"""Release smoke checks for a running LocalRAG instance."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


DEFAULT_BASE_URL = "http://localhost:7860"
DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_QUESTION = "Куда поехал Айболит?"
DEFAULT_EXPECTED_SNIPPET = "Айболит поехал в Африку"
ROOT_DIR = Path(__file__).resolve().parent.parent


def normalize_host_path(value: str | None) -> str:
    return str(value or "").strip().replace("\\", "/").rstrip("/").lower()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run release smoke checks against LocalRAG")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="App base URL")
    parser.add_argument("--expected-model", default=DEFAULT_MODEL, help="Expected default model")
    parser.add_argument(
        "--expected-docs-path",
        default=None,
        help="Expected documents path in /api/meta",
    )
    parser.add_argument("--question", default=DEFAULT_QUESTION, help="Smoke-test question")
    parser.add_argument(
        "--answer-substring",
        default=DEFAULT_EXPECTED_SNIPPET,
        help="Substring expected in the answer body",
    )
    parser.add_argument("--topk", type=int, default=8, help="Top-k value for ask request")
    return parser.parse_args()


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    payload: dict[str, Any] | None = None


def append_result(
    rows: list[CheckResult],
    name: str,
    ok: bool,
    detail: str,
    payload: dict[str, Any] | None = None,
) -> None:
    rows.append(CheckResult(name=name, ok=ok, detail=detail, payload=payload))


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    expected_docs_path = args.expected_docs_path or detect_expected_docs_path()
    rows: list[CheckResult] = []
    session = requests.Session()

    try:
        health_resp = session.get(f"{base_url}/api/health", timeout=30)
        health_resp.raise_for_status()
        health_payload = health_resp.json()
    except Exception as exc:  # noqa: BLE001
        append_result(rows, "health", False, f"Health request failed: {exc}")
        print_report(base_url, rows)
        return 1

    append_result(
        rows,
        "health",
        bool(health_payload.get("ok")),
        f"index.status={health_payload.get('index', {}).get('status')}",
        health_payload,
    )

    try:
        meta_resp = session.get(f"{base_url}/api/meta", timeout=30)
        meta_resp.raise_for_status()
        meta_payload = meta_resp.json()
    except Exception as exc:  # noqa: BLE001
        append_result(rows, "meta", False, f"Meta request failed: {exc}")
        print_report(base_url, rows)
        return 1

    meta_ok = (
        meta_payload.get("default_model") == args.expected_model
        and normalize_host_path(meta_payload.get("docs_path"))
        == normalize_host_path(expected_docs_path)
    )
    append_result(
        rows,
        "meta",
        meta_ok,
        (
            f"default_model={meta_payload.get('default_model')}, "
            f"docs_path={meta_payload.get('docs_path')}"
        ),
        meta_payload,
    )

    ask_payload = {
        "question": args.question,
        "model": args.expected_model,
        "topk": str(args.topk),
        "lang": "ru",
        "answer_language": "ru",
        "response_role": "analyst",
    }
    try:
        ask_resp = session.post(f"{base_url}/api/ask", data=ask_payload, timeout=240)
        ask_resp.raise_for_status()
        ask_text = ask_resp.text
    except Exception as exc:  # noqa: BLE001
        append_result(rows, "ask", False, f"Ask request failed: {exc}")
        print_report(base_url, rows)
        return 1

    ask_ok = args.answer_substring in ask_text
    append_result(
        rows,
        "ask",
        ask_ok,
        f"answer contains '{args.answer_substring}': {ask_ok}",
        {"response_excerpt": ask_text[:800]},
    )

    print_report(base_url, rows)
    return 0 if all(row.ok for row in rows) else 1


def print_report(base_url: str, rows: list[CheckResult]) -> None:
    report = {
        "base_url": base_url,
        "ok": all(row.ok for row in rows),
        "checks": [
            {
                "name": row.name,
                "ok": row.ok,
                "detail": row.detail,
                "payload": row.payload,
            }
            for row in rows
        ],
    }
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write(payload.encode("utf-8", errors="replace"))
    else:
        sys.stdout.write(payload)


def detect_expected_docs_path() -> str:
    for candidate in (ROOT_DIR / ".env", ROOT_DIR / ".env.example"):
        if not candidate.exists():
            continue
        values: dict[str, str] = {}
        for line in candidate.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            values[key.strip()] = value.strip()
        for preferred_key in ("HOST_DOCS_PATH", "DOCS_PATH"):
            preferred_value = values.get(preferred_key, "").strip()
            if preferred_value:
                return preferred_value
    return "./files"


if __name__ == "__main__":
    raise SystemExit(main())
