#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assert LocalRAG model eval quality thresholds.")
    parser.add_argument("--report", required=True, help="Path to model_eval JSON report.")
    parser.add_argument("--model", required=True, help="Model name inside the report.")
    parser.add_argument("--min-strict", type=float, default=1.0, help="Minimum strict pass rate.")
    parser.add_argument("--min-loose", type=float, default=1.0, help="Minimum loose pass rate.")
    parser.add_argument(
        "--min-hit-ratio",
        type=float,
        default=1.0,
        help="Minimum average answer hit ratio.",
    )
    parser.add_argument(
        "--max-latency-ms",
        type=int,
        default=0,
        help="Optional maximum average latency in milliseconds. Zero disables the check.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    if hasattr(sys.stderr, "buffer"):
        sys.stderr.buffer.write((message + "\n").encode("utf-8", errors="replace"))
    else:
        sys.stderr.write(message + "\n")
    return 1


def main() -> int:
    args = parse_args()
    report_path = Path(args.report)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    models = payload.get("models") or {}
    if args.model not in models:
        return fail(f"Model '{args.model}' not found in report {report_path}")

    summary = (models.get(args.model) or {}).get("summary") or {}
    strict_rate = float(summary.get("strict_pass_rate") or 0.0)
    loose_rate = float(summary.get("loose_pass_rate") or 0.0)
    avg_hit_ratio = float(summary.get("avg_answer_hit_ratio") or 0.0)
    avg_latency_ms = int(summary.get("avg_latency_ms") or 0)

    violations: list[str] = []
    if strict_rate < args.min_strict:
        violations.append(f"strict_pass_rate={strict_rate} < {args.min_strict}")
    if loose_rate < args.min_loose:
        violations.append(f"loose_pass_rate={loose_rate} < {args.min_loose}")
    if avg_hit_ratio < args.min_hit_ratio:
        violations.append(f"avg_answer_hit_ratio={avg_hit_ratio} < {args.min_hit_ratio}")
    if args.max_latency_ms > 0 and avg_latency_ms > args.max_latency_ms:
        violations.append(f"avg_latency_ms={avg_latency_ms} > {args.max_latency_ms}")

    summary_text = (
        f"model={args.model} strict={strict_rate} loose={loose_rate} "
        f"hit_ratio={avg_hit_ratio} latency_ms={avg_latency_ms}"
    )
    if violations:
        return fail(summary_text + " | gate failed: " + "; ".join(violations))

    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write((summary_text + " | gate passed\n").encode("utf-8", errors="replace"))
    else:
        sys.stdout.write(summary_text + " | gate passed\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
