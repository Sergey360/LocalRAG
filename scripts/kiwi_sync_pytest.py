#!/usr/bin/env python3
"""Run pytest and sync test results to Kiwi TCMS executions."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


DEFAULT_ENDPOINT = "https://kiwi.it360.ru/json-rpc/"
DEFAULT_MAPPING = Path("tests/kiwi_sync_mapping.json")
DEFAULT_JUNIT_XML = Path("temp/kiwi_pytest_report.xml")
DEFAULT_NAS_HOST = "nas"
DEFAULT_NAS_CRED_PATH = "/vmstore/containers/kiwi-tcms/sergey360.credentials"


def normalize_endpoint(value: str) -> str:
    endpoint = value.strip().rstrip("/")
    if endpoint.endswith("/json-rpc"):
        return endpoint + "/"
    if "/json-rpc/" in endpoint:
        return endpoint + "/" if not endpoint.endswith("/") else endpoint
    return endpoint + "/json-rpc/"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run pytest and sync statuses to Kiwi test executions"
    )
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Kiwi JSON-RPC URL")
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=DEFAULT_MAPPING,
        help="JSON mapping file (junit key -> Kiwi case summary)",
    )
    parser.add_argument(
        "--run-id",
        type=int,
        default=None,
        help="Kiwi run id; overrides run_id from mapping file",
    )
    parser.add_argument(
        "--junit-xml",
        type=Path,
        default=DEFAULT_JUNIT_XML,
        help="Path for pytest junit xml report",
    )
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Do not run pytest, only parse existing junit xml and sync",
    )
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to pytest (default: -q)",
    )
    parser.add_argument(
        "--nas-host",
        default=DEFAULT_NAS_HOST,
        help="SSH host for NAS credentials fallback",
    )
    parser.add_argument(
        "--nas-cred-path",
        default=DEFAULT_NAS_CRED_PATH,
        help="Credential file on NAS for fallback auth",
    )
    parser.add_argument(
        "--disable-nas-fallback",
        action="store_true",
        help="Use only KIWI_USERNAME/KIWI_PASSWORD from environment",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not update Kiwi, only print intended changes",
    )
    parser.add_argument(
        "--report-file",
        type=Path,
        default=None,
        help="Path for sync JSON report (default: temp/kiwi_sync_report_<ts>.json)",
    )
    return parser.parse_args()


@dataclass
class MappingItem:
    junit_key: str
    summary: str
    category: str | None = None
    priority: str | None = None


def load_mapping(mapping_file: Path) -> tuple[int | None, list[MappingItem]]:
    data = json.loads(mapping_file.read_text(encoding="utf-8"))
    run_id = data.get("run_id")
    cases = data.get("cases", [])
    items: list[MappingItem] = []
    seen_keys: set[str] = set()
    seen_summaries: set[str] = set()
    for entry in cases:
        junit_key = str(entry["junit"]).strip()
        summary = str(entry["summary"]).strip()
        category = str(entry.get("category", "")).strip() or None
        priority = str(entry.get("priority", "")).strip() or None
        if not junit_key or not summary:
            raise ValueError(f"Invalid mapping entry in {mapping_file}: {entry}")
        if junit_key in seen_keys:
            raise ValueError(f"Duplicate junit key in mapping: {junit_key}")
        if summary in seen_summaries:
            raise ValueError(f"Duplicate summary in mapping: {summary}")
        seen_keys.add(junit_key)
        seen_summaries.add(summary)
        items.append(
            MappingItem(
                junit_key=junit_key,
                summary=summary,
                category=category,
                priority=priority,
            )
        )
    return run_id, items


def parse_credentials_text(text: str) -> tuple[str, str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    values: dict[str, str] = {}
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip().lower()] = value.strip()

    username = (
        values.get("username")
        or values.get("user")
        or values.get("login")
        or values.get("kiwi_username")
    )
    password = values.get("password") or values.get("pass") or values.get("kiwi_password")

    if (not username or not password) and len(lines) >= 2:
        if ":" in lines[0]:
            username, password = lines[0].split(":", 1)
        else:
            username, password = lines[0], lines[1]

    if not username or not password:
        raise ValueError("Could not parse Kiwi credentials")
    return username, password


def load_credentials(args: argparse.Namespace) -> tuple[str, str]:
    username = (os.environ.get("KIWI_USERNAME") or "").strip()
    password = (os.environ.get("KIWI_PASSWORD") or "").strip()
    if username and password:
        return username, password

    if args.disable_nas_fallback:
        raise RuntimeError(
            "KIWI_USERNAME and KIWI_PASSWORD are required when NAS fallback is disabled"
        )

    try:
        raw = subprocess.check_output(
            ["ssh", args.nas_host, f"cat {args.nas_cred_path}"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Failed to load NAS credentials: {exc.output}") from exc

    return parse_credentials_text(raw)


@dataclass
class KiwiClient:
    endpoint: str
    timeout_s: int = 90
    max_retries: int = 3

    def __post_init__(self) -> None:
        self._session = requests.Session()
        self._request_id = 1

    def call(self, method: str, params: list[Any]) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }
        self._request_id += 1
        last_error: requests.RequestException | None = None
        response = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._session.post(
                    self.endpoint,
                    json=payload,
                    timeout=self.timeout_s,
                    headers={"User-Agent": "LocalRAG-KiwiSync/1.0"},
                )
                response.raise_for_status()
                last_error = None
                break
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(attempt)
        if last_error is not None or response is None:
            raise RuntimeError(f"Network error calling {method}: {last_error}") from last_error

        data = response.json()
        if data.get("error"):
            raise RuntimeError(f"RPC error for {method}: {data['error']}")
        return data.get("result")

    def login(self, username: str, password: str) -> None:
        self.call("Auth.login", [username, password])


def run_pytest(args: argparse.Namespace) -> int:
    junit_xml = args.junit_xml
    junit_xml.parent.mkdir(parents=True, exist_ok=True)

    pytest_args = list(args.pytest_args or [])
    if not pytest_args:
        pytest_args = ["-q"]
    if not any(a.startswith("--junitxml") for a in pytest_args):
        pytest_args.append(f"--junitxml={junit_xml.as_posix()}")

    command = ["pytest", *pytest_args]
    print("Running:", " ".join(command), flush=True)
    return subprocess.run(command, check=False).returncode


def parse_junit_results(junit_xml: Path) -> dict[str, dict[str, str]]:
    if not junit_xml.exists():
        raise FileNotFoundError(f"junit xml not found: {junit_xml}")
    tree = ET.parse(junit_xml)
    root = tree.getroot()

    results: dict[str, dict[str, str]] = {}
    for testcase in root.iter("testcase"):
        classname = testcase.attrib.get("classname", "").strip()
        name = testcase.attrib.get("name", "").strip()
        if not classname or not name:
            continue
        key = f"{classname}::{name}"
        detail = ""
        outcome = "passed"
        for tag, normalized in (("failure", "failed"), ("error", "error"), ("skipped", "skipped")):
            node = testcase.find(tag)
            if node is not None:
                outcome = normalized
                message = (node.attrib.get("message") or "").strip()
                text = (node.text or "").strip()
                detail = message or text
                if text and message and message != text:
                    detail = f"{message}\n{text}"
                break
        results[key] = {"outcome": outcome, "detail": detail}
    return results


def get_git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:  # noqa: BLE001
        return None


def resolve_status_ids(client: KiwiClient) -> dict[str, int]:
    status_rows = client.call("TestExecutionStatus.filter", [{}])
    lookup: dict[str, int] = {}
    for row in status_rows:
        name = str(row.get("name", "")).upper().strip()
        if name:
            lookup[name] = int(row["id"])

    required = ("PASSED", "FAILED", "BLOCKED")
    missing = [name for name in required if name not in lookup]
    if missing:
        raise RuntimeError(f"Missing Kiwi execution statuses: {', '.join(missing)}")
    return lookup


def resolve_case_status_ids(client: KiwiClient) -> dict[str, int]:
    rows = client.call("TestCaseStatus.filter", [{}])
    lookup: dict[str, int] = {}
    for row in rows:
        name = str(row.get("name", "")).upper().strip()
        if name:
            lookup[name] = int(row["id"])
    if "CONFIRMED" not in lookup:
        raise RuntimeError("Missing Kiwi case status: CONFIRMED")
    return lookup


def resolve_priority_ids(client: KiwiClient) -> dict[str, int]:
    rows = client.call("Priority.filter", [{}])
    lookup: dict[str, int] = {}
    for row in rows:
        value = str(row.get("value", "")).upper().strip()
        if value:
            lookup[value] = int(row["id"])
    if "P1" not in lookup:
        raise RuntimeError("Missing Kiwi priority: P1")
    return lookup


def resolve_category_ids(client: KiwiClient, product_id: int) -> dict[str, int]:
    rows = client.call("Category.filter", [{"product": product_id}])
    if not rows:
        rows = client.call("Category.filter", [{}])
    lookup: dict[str, int] = {}
    for row in rows:
        try:
            row_product_id = int(row.get("product"))
        except Exception:  # noqa: BLE001
            continue
        if row_product_id != product_id:
            continue
        name = str(row.get("name", "")).strip()
        if name:
            lookup[name.lower()] = int(row["id"])
    if not lookup:
        raise RuntimeError(f"No Kiwi categories found for product {product_id}")
    return lookup


def resolve_user_id(client: KiwiClient, username: str) -> int | None:
    users = client.call("User.filter", [{"username": username}])
    if not users:
        return None
    return int(users[0]["id"])


def resolve_run_info(client: KiwiClient, run_id: int) -> dict[str, Any]:
    rows = client.call("TestRun.filter", [{"id": run_id}])
    if not rows:
        raise RuntimeError(f"Kiwi run not found: {run_id}")
    return dict(rows[0])


def execution_map_for_run(client: KiwiClient, run_id: int) -> dict[str, int]:
    run_cases = client.call("TestRun.get_cases", [run_id])
    by_summary: dict[str, int] = {}
    for row in run_cases:
        summary = str(row.get("summary", "")).strip()
        execution_id = int(row["execution_id"])
        if summary in by_summary:
            raise RuntimeError(f"Duplicate case summary in run {run_id}: {summary}")
        by_summary[summary] = execution_id
    return by_summary


def outcome_to_status_name(outcome: str) -> str:
    if outcome == "passed":
        return "PASSED"
    if outcome in {"failed", "error"}:
        return "FAILED"
    return "BLOCKED"


def infer_category_name(item: MappingItem) -> str:
    if item.category:
        return item.category.strip()
    summary = item.summary.lower()
    if " web:" in summary:
        return "Web"
    return "API"


def infer_priority_name(item: MappingItem) -> str:
    return (item.priority or "P1").strip().upper()


def build_case_text(item: MappingItem) -> str:
    return "\n".join(
        [
            "Steps:",
            f"1. Run automated pytest case `{item.junit_key}`.",
            "Expected:",
            "- Test completes without assertion failures.",
            f"- Assertions for '{item.summary}' pass.",
        ]
    )


def resolve_case_id_by_summary(client: KiwiClient, summary: str) -> int | None:
    rows = client.call("TestCase.filter", [{"summary": summary}])
    if not rows:
        return None
    if len(rows) > 1:
        raise RuntimeError(f"Multiple Kiwi cases matched summary: {summary}")
    return int(rows[0]["id"])


def create_test_case(
    client: KiwiClient,
    item: MappingItem,
    product_id: int,
    author_id: int | None,
    confirmed_case_status_id: int,
    category_ids: dict[str, int],
    priority_ids: dict[str, int],
) -> int:
    category_name = infer_category_name(item)
    category_id = category_ids.get(category_name.lower())
    if category_id is None:
        raise RuntimeError(
            f"Kiwi category '{category_name}' not found for product {product_id}"
        )
    priority_name = infer_priority_name(item)
    priority_id = priority_ids.get(priority_name)
    if priority_id is None:
        raise RuntimeError(f"Kiwi priority '{priority_name}' not found")

    values: dict[str, Any] = {
        "summary": item.summary,
        "product": product_id,
        "category": category_id,
        "priority": priority_id,
        "case_status": confirmed_case_status_id,
        "is_automated": True,
        "notes": f"Auto-created from LocalRAG mapping ({item.junit_key})",
        "text": build_case_text(item),
    }
    if author_id is not None:
        values["author"] = author_id

    created = client.call("TestCase.create", [values])
    if isinstance(created, dict):
        return int(created["id"])
    return int(created)


def add_case_to_run(client: KiwiClient, run_id: int, case_id: int) -> None:
    try:
        client.call("TestRun.add_case", [run_id, case_id])
        return
    except RuntimeError as first_error:
        try:
            client.call("TestRun.add_case", [run_id, [case_id]])
            return
        except RuntimeError as second_error:
            raise RuntimeError(
                f"Could not add case {case_id} to run {run_id}: "
                f"{first_error} | fallback failed: {second_error}"
            ) from second_error


def ensure_cases_in_run(
    client: KiwiClient,
    run_id: int,
    mapping_items: list[MappingItem],
    product_id: int,
    author_id: int | None,
    confirmed_case_status_id: int,
    category_ids: dict[str, int],
    priority_ids: dict[str, int],
    dry_run: bool = False,
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    by_summary = execution_map_for_run(client, run_id)
    actions: list[dict[str, Any]] = []

    for item in mapping_items:
        if item.summary in by_summary:
            continue

        case_id = resolve_case_id_by_summary(client, item.summary)
        if case_id is None:
            if dry_run:
                actions.append(
                    {
                        "summary": item.summary,
                        "junit": item.junit_key,
                        "action": "would_create_case",
                        "category": infer_category_name(item),
                        "priority": infer_priority_name(item),
                    }
                )
                continue
            case_id = create_test_case(
                client=client,
                item=item,
                product_id=product_id,
                author_id=author_id,
                confirmed_case_status_id=confirmed_case_status_id,
                category_ids=category_ids,
                priority_ids=priority_ids,
            )
            actions.append(
                {
                    "summary": item.summary,
                    "junit": item.junit_key,
                    "action": "created_case",
                    "case_id": case_id,
                }
            )
        else:
            actions.append(
                {
                    "summary": item.summary,
                    "junit": item.junit_key,
                    "action": "reused_case",
                    "case_id": case_id,
                }
            )

        if dry_run:
            actions.append(
                {
                    "summary": item.summary,
                    "junit": item.junit_key,
                    "action": "would_add_case_to_run",
                    "case_id": case_id,
                }
            )
            continue

        add_case_to_run(client, run_id, case_id)
        actions.append(
            {
                "summary": item.summary,
                "junit": item.junit_key,
                "action": "added_case_to_run",
                "case_id": case_id,
            }
        )

    if not dry_run:
        by_summary = execution_map_for_run(client, run_id)
    return by_summary, actions


def main() -> int:
    args = parse_args()
    endpoint = normalize_endpoint(args.endpoint)
    mapping_run_id, mapping_items = load_mapping(args.mapping_file)
    run_id = args.run_id if args.run_id is not None else mapping_run_id
    if run_id is None:
        raise SystemExit("Run id is not provided (use --run-id or mapping run_id)")
    if not mapping_items:
        raise SystemExit(f"No mapping items found in {args.mapping_file}")

    pytest_exit_code = 0
    if not args.skip_pytest:
        pytest_exit_code = run_pytest(args)

    junit_results = parse_junit_results(args.junit_xml)
    username, password = load_credentials(args)

    client = KiwiClient(endpoint=endpoint)
    client.login(username, password)
    run_info = resolve_run_info(client, run_id)
    product_id = int(run_info["build__version__product"])
    status_ids = resolve_status_ids(client)
    case_status_ids = resolve_case_status_ids(client)
    priority_ids = resolve_priority_ids(client)
    category_ids = resolve_category_ids(client, product_id)
    tested_by_id = resolve_user_id(client, username)
    by_summary, ensure_actions = ensure_cases_in_run(
        client=client,
        run_id=run_id,
        mapping_items=mapping_items,
        product_id=product_id,
        author_id=tested_by_id,
        confirmed_case_status_id=case_status_ids["CONFIRMED"],
        category_ids=category_ids,
        priority_ids=priority_ids,
        dry_run=args.dry_run,
    )

    timestamp = dt.datetime.now().isoformat(timespec="seconds")
    commit_sha = get_git_sha()
    report_rows: list[dict[str, Any]] = []
    sync_errors: list[str] = []

    for item in mapping_items:
        junit_entry = junit_results.get(item.junit_key)
        if junit_entry is None:
            outcome = "missing"
            detail = "Test result is missing in junit xml report"
        else:
            outcome = junit_entry["outcome"]
            detail = junit_entry["detail"]

        status_name = outcome_to_status_name(outcome)
        status_id = status_ids[status_name]
        execution_id = by_summary.get(item.summary)
        if execution_id is None:
            sync_errors.append(f"Case not found in run {run_id}: {item.summary}")
            report_rows.append(
                {
                    "summary": item.summary,
                    "junit": item.junit_key,
                    "outcome": outcome,
                    "status_name": status_name,
                    "execution_id": None,
                    "synced": False,
                    "error": "missing_execution",
                }
            )
            continue

        comment_lines = [
            "Automated sync from LocalRAG pytest",
            f"Test: {item.junit_key}",
            f"Outcome: {outcome.upper()}",
            f"Mapped status: {status_name}",
            f"Synced at: {timestamp}",
        ]
        if commit_sha:
            comment_lines.append(f"Commit: {commit_sha}")
        if detail:
            compact_detail = detail.strip()
            if len(compact_detail) > 1200:
                compact_detail = compact_detail[:1200] + "... [truncated]"
            comment_lines.append("")
            comment_lines.append("Details:")
            comment_lines.append(compact_detail)
        comment = "\n".join(comment_lines)

        if args.dry_run:
            report_rows.append(
                {
                    "summary": item.summary,
                    "junit": item.junit_key,
                    "outcome": outcome,
                    "status_name": status_name,
                    "execution_id": execution_id,
                    "synced": False,
                    "dry_run": True,
                }
            )
            continue

        try:
            values: dict[str, Any] = {"status": status_id}
            if tested_by_id is not None:
                values["tested_by"] = tested_by_id
            try:
                client.call("TestExecution.update", [execution_id, values])
            except RuntimeError:
                values.pop("tested_by", None)
                client.call("TestExecution.update", [execution_id, values])

            comment_added = True
            try:
                client.call("TestExecution.add_comment", [execution_id, comment])
            except RuntimeError:
                comment_added = False

            report_rows.append(
                {
                    "summary": item.summary,
                    "junit": item.junit_key,
                    "outcome": outcome,
                    "status_name": status_name,
                    "execution_id": execution_id,
                    "synced": True,
                    "comment_added": comment_added,
                }
            )
        except RuntimeError as exc:
            sync_errors.append(f"Execution {execution_id}: {exc}")
            report_rows.append(
                {
                    "summary": item.summary,
                    "junit": item.junit_key,
                    "outcome": outcome,
                    "status_name": status_name,
                    "execution_id": execution_id,
                    "synced": False,
                    "error": str(exc),
                }
            )

    report = {
        "run_id": run_id,
        "endpoint": endpoint,
        "mapping_file": str(args.mapping_file),
        "junit_xml": str(args.junit_xml),
        "pytest_exit_code": pytest_exit_code,
        "timestamp": timestamp,
        "ensure_actions": ensure_actions,
        "rows": report_rows,
        "sync_errors": sync_errors,
    }

    report_path = args.report_file
    if report_path is None:
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path("temp") / f"kiwi_sync_report_{ts}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    passed = sum(1 for row in report_rows if row.get("status_name") == "PASSED")
    failed = sum(1 for row in report_rows if row.get("status_name") == "FAILED")
    blocked = sum(1 for row in report_rows if row.get("status_name") == "BLOCKED")
    synced = sum(1 for row in report_rows if row.get("synced"))
    ensured = len(ensure_actions)

    print(f"Kiwi run: {run_id}")
    if ensured:
        print(f"Ensure actions: {ensured}")
    print(f"Rows total: {len(report_rows)} | synced: {synced}")
    print(f"Status counts -> PASSED: {passed}, FAILED: {failed}, BLOCKED: {blocked}")
    print(f"Report: {report_path}")

    if sync_errors:
        for item in sync_errors:
            print(f"SYNC_ERROR: {item}", file=sys.stderr)
        return 2

    if pytest_exit_code != 0:
        return pytest_exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
