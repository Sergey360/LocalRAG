from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run retrieval-only embedding eval against LocalRAG seed questions."
    )
    parser.add_argument(
        "--seed-file",
        default="eval/rag_eval_extended.json",
        help="Path to eval seed JSON file.",
    )
    parser.add_argument(
        "--embedding-models",
        nargs="+",
        required=True,
        help="One or more embedding models or local paths to compare.",
    )
    parser.add_argument(
        "--topk",
        type=int,
        default=8,
        help="top-k retrieval depth used for source-hit checks.",
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
        "--output",
        default="",
        help="Optional output path. Defaults to temp/embed_eval_<timestamp>.json",
    )
    return parser.parse_args()


def default_output_path() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("temp") / f"embed_eval_{stamp}.json"


def load_seed(path: str) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    normalized = str(value or "").casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def extract_expected_sources(question_case: dict[str, Any]) -> list[str]:
    raw_expected_sources = question_case.get("expected_sources")
    if isinstance(raw_expected_sources, list) and raw_expected_sources:
        values = [str(item).strip() for item in raw_expected_sources if str(item).strip()]
    else:
        values = [str(question_case.get("expected_source") or "").strip()]
    return [value for value in values if value]


def source_label_hit(source_label: str, expected_sources: list[str]) -> bool:
    haystack = normalize_text(source_label)
    return any(normalize_text(expected) in haystack for expected in expected_sources)


def load_inprocess_main(args: argparse.Namespace):
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

    spec = importlib.util.spec_from_file_location("localrag_embed_eval_main", main_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load main module from {main_path}")
    main_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_mod)
    return main_mod


def evaluate_embedding_model(
    main_mod,
    seed: list[dict[str, Any]],
    embedding_model: str,
    *,
    topk: int,
) -> dict[str, Any]:
    started_rebuild = time.perf_counter()
    main_mod.set_embedding_model(embedding_model)
    rebuild_status = main_mod.rebuild_index()
    rebuild_ms = int((time.perf_counter() - started_rebuild) * 1000)
    status_code, status_params = main_mod.get_index_status_meta()
    if status_code not in {"ready_ask", "ready_loaded"}:
        raise RuntimeError(
            f"Embedding model '{embedding_model}' failed to build a ready index: "
            f"{status_code} {status_params}"
        )

    rows: list[dict[str, Any]] = []
    reciprocal_rank_total = 0.0

    for question_case in seed:
        expected_sources = extract_expected_sources(question_case)
        started_query = time.perf_counter()
        debug_rows = main_mod.get_retrieval_debug_snapshot(
            str(question_case.get("question") or ""),
            int(topk),
        )
        query_ms = int((time.perf_counter() - started_query) * 1000)
        hit_rank = 0
        matched_label = ""
        for index, row in enumerate(debug_rows, start=1):
            source_label = str(row.get("source_label") or "")
            if source_label_hit(source_label, expected_sources):
                hit_rank = index
                matched_label = source_label
                break
        if hit_rank:
            reciprocal_rank_total += 1.0 / hit_rank
        rows.append(
            {
                "id": question_case.get("id"),
                "question": question_case.get("question"),
                "expected_sources": expected_sources,
                "top1_hit": hit_rank == 1,
                "topk_hit": hit_rank > 0,
                "hit_rank": hit_rank,
                "matched_source_label": matched_label,
                "query_ms": query_ms,
                "retrieved": [
                    {
                        "rank": int(row.get("rank") or 0),
                        "source_label": str(row.get("source_label") or ""),
                        "score": row.get("score"),
                    }
                    for row in debug_rows
                ],
            }
        )

    total = len(rows) or 1
    top1_hits = sum(1 for row in rows if row["top1_hit"])
    topk_hits = sum(1 for row in rows if row["topk_hit"])
    avg_query_ms = int(sum(int(row["query_ms"]) for row in rows) / total)

    return {
        "embedding_model": embedding_model,
        "rebuild_status": rebuild_status,
        "rebuild_ms": rebuild_ms,
        "summary": {
            "top1_hit_rate": round(top1_hits / total, 3),
            "topk_hit_rate": round(topk_hits / total, 3),
            "mrr": round(reciprocal_rank_total / total, 3),
            "top1_hits": top1_hits,
            "topk_hits": topk_hits,
            "total": total,
            "avg_query_ms": avg_query_ms,
        },
        "rows": rows,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    seed = load_seed(args.seed_file)
    main_mod = load_inprocess_main(args)

    report = {
        "seed_file": args.seed_file,
        "topk": int(args.topk),
        "docs_path": args.docs_path or main_mod.get_docs_path_display(),
        "embedding_models": {},
    }

    for embedding_model in args.embedding_models:
        print(f"\n=== embedding: {embedding_model} ===")
        result = evaluate_embedding_model(
            main_mod,
            seed,
            embedding_model,
            topk=int(args.topk),
        )
        report["embedding_models"][embedding_model] = result
        summary = result["summary"]
        print(
            "top1={top1}/{total} topk={topk_hits}/{total} mrr={mrr} avg_query_ms={avg_query_ms} rebuild_ms={rebuild_ms}".format(
                top1=summary["top1_hits"],
                topk_hits=summary["topk_hits"],
                total=summary["total"],
                mrr=summary["mrr"],
                avg_query_ms=summary["avg_query_ms"],
                rebuild_ms=result["rebuild_ms"],
            )
        )

    output_path = Path(args.output) if args.output else default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nSaved report to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
