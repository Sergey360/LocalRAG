#!/usr/bin/env python3
"""Validate LocalRAG ops-observability setup artifacts.

The default mode is offline and non-mutating. With --check-gitlab-api the script
also verifies that the configured GitLab project can be resolved by the API.
It never creates, updates, pushes, or closes GitLab issues.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parent.parent
SETUP_DIR = ROOT_DIR / "artifacts" / "ops-observability" / "setup"
FIXTURES_DIR = SETUP_DIR / "fixtures"

UPTIME_FILE = SETUP_DIR / "2026-06-06-uptime-kuma-monitor-plan.json"
GRAYLOG_FILE = SETUP_DIR / "2026-06-06-graylog-event-definitions.json"
ROUTING_FILE = SETUP_DIR / "2026-06-06-mayalerts-gitlab-routing.json"
DRY_RUN_EVENT_FILE = FIXTURES_DIR / "2026-06-06-mayalerts-dry-run-event.json"
EXPECTED_GITLAB_FILE = FIXTURES_DIR / "2026-06-06-expected-gitlab-issue.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return payload


def release_major_minor(release: str) -> str:
    version = str(release).split("+", 1)[0].split("-", 1)[0]
    parts = version.split(".")
    if len(parts) >= 2 and all(part.isdigit() for part in parts[:2]):
        return f"{parts[0]}.{parts[1]}"
    return version or "unknown"


def render_fingerprint(event: dict[str, Any]) -> str:
    required = [
        "service_name",
        "app_env",
        "alert_name",
        "severity",
        "dedupe_resource",
        "app_release",
    ]
    missing = [field for field in required if not event.get(field)]
    if missing:
        raise AssertionError(f"dry-run event missing fingerprint fields: {', '.join(missing)}")
    return "|".join(
        [
            str(event["service_name"]),
            str(event["app_env"]),
            str(event["alert_name"]),
            str(event["severity"]),
            str(event["dedupe_resource"]),
            release_major_minor(str(event["app_release"])),
        ]
    )


def substitute_placeholders(values: list[str], event: dict[str, Any]) -> list[str]:
    rendered: list[str] = []
    for value in values:
        rendered.append(
            value.format(
                app_env=event["app_env"],
                severity=event["severity"],
                service_name=event["service_name"],
                summary=event.get("summary", event["alert_name"]),
            )
        )
    return rendered


def route_for_event(routing: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    routes = routing.get("gitlab_routes")
    if not isinstance(routes, dict):
        raise AssertionError("routing config must define gitlab_routes")
    app_env = str(event.get("app_env", ""))
    route = routes.get(app_env)
    if not isinstance(route, dict):
        raise AssertionError(f"routing config has no GitLab route for app_env={app_env!r}")
    return route


def render_title(route: dict[str, Any], event: dict[str, Any]) -> str:
    template = route.get("title_template")
    if not isinstance(template, str) or not template:
        raise AssertionError("route missing title_template")
    return template.format(
        app_env=event["app_env"],
        severity=event["severity"],
        service_name=event["service_name"],
        summary=event.get("summary", event["alert_name"]),
    )


def render_description(event: dict[str, Any], fingerprint: str) -> str:
    privacy = event.get("privacy_check", {})
    raw_question = "yes" if privacy.get("raw_question_text_included") else "no"
    raw_answer = "yes" if privacy.get("raw_answer_text_included") else "no"
    source_passages = "yes" if privacy.get("source_passages_included") else "no"
    raw_paths = "yes" if privacy.get("raw_filesystem_paths_included") else "no"
    claim_review = privacy.get("private_claim_or_security_claim_reviewed", "n/a")
    correlation_ids = ", ".join(str(item) for item in event.get("correlation_ids", [])) or "n/a"

    return "\n".join(
        [
            "## Alert",
            "",
            f"- Alert: `{event['alert_name']}`",
            f"- Severity: `{event['severity']}`",
            f"- Environment: `{event['app_env']}`",
            f"- Service: `{event['service_name']}`",
            f"- Release: `{event['app_release']}`",
            f"- Fingerprint: `{fingerprint}`",
            f"- First seen: `{event.get('first_seen_utc', event['timestamp_utc'])}`",
            f"- Last seen: `{event.get('last_seen_utc', event['timestamp_utc'])}`",
            f"- Occurrences: `{event.get('occurrences', 1)}`",
            "",
            "## Current Evidence",
            "",
            (
                f"- Condition: `{event.get('alert_value', 'n/a')}` vs threshold "
                f"`{event.get('alert_threshold', 'n/a')}` over "
                f"`{event.get('alert_window', 'n/a')}`"
            ),
            f"- Route/workflow/job: `{event.get('route_or_workflow', 'n/a')}`",
            f"- Correlation IDs: `{correlation_ids}`",
            f"- Instance: `{event.get('app_instance_id', 'n/a')}`",
            f"- Model: `{event.get('model_name', 'n/a')}`",
            f"- Embedding model: `{event.get('embedding_model', 'n/a')}`",
            f"- Index status: `{event.get('index_status', 'n/a')}`",
            f"- Indexed files: `{event.get('indexed_file_count', 'n/a')}`",
            "",
            "## Privacy Check",
            "",
            f"- Raw question text included: `{raw_question}`",
            f"- Raw answer text included: `{raw_answer}`",
            f"- Source passages included: `{source_passages}`",
            f"- Raw filesystem paths included: `{raw_paths}`",
            f"- Private claim/security claim reviewed: `{claim_review}`",
            "",
            "## Suggested Triage",
            "",
            "1. Check `/api/health` and `/api/meta` for this release.",
            "2. Review Graylog events by `alert_fingerprint` and `correlation_id`.",
            "3. Run or inspect the relevant release/synthetic check.",
            "4. Decide whether this is release-blocking, user-impacting, or hygiene.",
            "",
            "## Resolution Notes",
            "",
            "- Root cause:",
            "- Fix:",
            "- Verification:",
            "- Follow-up:",
        ]
    )


def build_gitlab_issue_payload(
    routing: dict[str, Any], event: dict[str, Any]
) -> dict[str, Any]:
    route = route_for_event(routing, event)
    fingerprint = render_fingerprint(event)
    labels = substitute_placeholders(route.get("labels", []), event)
    return {
        "project_path": routing["gitlab"]["project_path"],
        "api_url": routing["gitlab"]["api_url"],
        "issue_create_endpoint": routing["gitlab"]["issue_create_endpoint"],
        "method": "POST",
        "title": render_title(route, event),
        "confidential": bool(route.get("confidential")),
        "dedupe_fingerprint": fingerprint,
        "labels": labels,
        "description": render_description(event, fingerprint),
    }


def validate_uptime(payload: dict[str, Any]) -> None:
    monitors = payload.get("monitors")
    if not isinstance(monitors, list) or not monitors:
        raise AssertionError("Uptime plan must contain monitors")

    names = {monitor.get("name") for monitor in monitors}
    required_names = {
        "localrag-test-health",
        "localrag-test-meta",
        "localrag-test-release-smoke",
        "localrag-prod-health",
        "localrag-prod-meta",
        "localrag-prod-release-smoke",
    }
    missing = required_names - names
    if missing:
        raise AssertionError(f"Uptime plan missing monitors: {', '.join(sorted(missing))}")

    target_envs = {monitor.get("target_environment") for monitor in monitors}
    if not {"test", "prod"}.issubset(target_envs):
        raise AssertionError("Uptime plan must cover test and prod environments")

    monitor_kinds = {monitor.get("monitor_kind") for monitor in monitors}
    if not {"http", "push"}.issubset(monitor_kinds):
        raise AssertionError("Uptime plan must include both HTTP and push monitors")

    for monitor in monitors:
        for field in ("name", "mayalerts_alert_name", "mayalerts_severity", "dedupe_resource"):
            if not monitor.get(field):
                raise AssertionError(f"Uptime monitor {monitor.get('name')} missing {field}")


def validate_graylog(payload: dict[str, Any]) -> None:
    definitions = payload.get("event_definitions")
    if not isinstance(definitions, list) or not definitions:
        raise AssertionError("Graylog plan must contain event_definitions")

    alert_names = {definition.get("alert_name") for definition in definitions}
    required_alerts = {
        "localrag_service_error_5xx",
        "localrag_health_down",
        "localrag_index_build_failed",
        "localrag_ask_error_rate_high",
        "localrag_release_smoke_failed",
        "localrag_observability_contract_violation",
    }
    missing = required_alerts - alert_names
    if missing:
        raise AssertionError(f"Graylog plan missing alerts: {', '.join(sorted(missing))}")

    for definition in definitions:
        for field in ("alert_name", "title", "search_query", "window", "threshold"):
            if not definition.get(field):
                raise AssertionError(f"Graylog definition {definition.get('alert_name')} missing {field}")


def validate_routing(payload: dict[str, Any]) -> None:
    gitlab = payload.get("gitlab")
    if not isinstance(gitlab, dict):
        raise AssertionError("routing config missing gitlab block")
    if gitlab.get("project_path") != "myprojects/localrag":
        raise AssertionError("routing config must target myprojects/localrag")
    if gitlab.get("issue_create_endpoint") != "/projects/myprojects%2Flocalrag/issues":
        raise AssertionError("routing config has unexpected GitLab issue endpoint")

    sources = payload.get("mayalerts_sources")
    if not isinstance(sources, list) or len(sources) < 2:
        raise AssertionError("routing config must define Graylog and Uptime Kuma sources")
    source_names = {source.get("name") for source in sources}
    if {"localrag-graylog", "localrag-uptime-kuma"} - source_names:
        raise AssertionError("routing config missing required MayAlerts sources")

    n8n = payload.get("n8n_intake")
    if not isinstance(n8n, dict) or not n8n.get("webhook_path"):
        raise AssertionError("routing config missing n8n intake webhook")

    routes = payload.get("gitlab_routes")
    if not isinstance(routes, dict):
        raise AssertionError("routing config missing gitlab_routes")
    for app_env in ("dev", "staging", "prod"):
        route = routes.get(app_env)
        if not isinstance(route, dict):
            raise AssertionError(f"routing config missing route for {app_env}")
        if not route.get("labels"):
            raise AssertionError(f"routing route {app_env} missing labels")
    if not routes["prod"].get("confidential"):
        raise AssertionError("prod route must create confidential issues")
    if routes["staging"].get("confidential"):
        raise AssertionError("staging route should not be confidential by default")


def validate_expected_issue(
    routing: dict[str, Any], event: dict[str, Any], expected: dict[str, Any]
) -> None:
    payload = build_gitlab_issue_payload(routing, event)
    comparable_fields = [
        "project_path",
        "api_url",
        "issue_create_endpoint",
        "method",
        "title",
        "confidential",
        "dedupe_fingerprint",
        "labels",
    ]
    for field in comparable_fields:
        if payload.get(field) != expected.get(field):
            raise AssertionError(
                f"expected GitLab {field}={expected.get(field)!r}, got {payload.get(field)!r}"
            )

    description = payload["description"]
    missing_markers = [
        marker for marker in expected.get("description_required_markers", []) if marker not in description
    ]
    if missing_markers:
        raise AssertionError(
            "expected GitLab description missing markers: "
            + ", ".join(repr(marker) for marker in missing_markers)
        )


def check_gitlab_project(gitlab: dict[str, Any]) -> dict[str, Any]:
    api_url = os.environ.get("GITLAB_API_URL", gitlab.get("api_url", "")).rstrip("/")
    token = os.environ.get(str(gitlab.get("token_variable", "GITLAB_API_TOKEN")), "")
    project_path = str(gitlab.get("project_path", ""))
    if not api_url:
        raise AssertionError("GITLAB_API_URL is not configured")
    if not token:
        raise AssertionError("GITLAB_API_TOKEN is not configured")
    if not project_path:
        raise AssertionError("GitLab project_path is not configured")

    url = f"{api_url}/projects/{quote(project_path, safe='')}"
    request = Request(url, headers={"PRIVATE-TOKEN": token})
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body)
            return {
                "http_status": response.status,
                "project_id": payload.get("id"),
                "path_with_namespace": payload.get("path_with_namespace"),
                "web_url": payload.get("web_url"),
            }
    except HTTPError as exc:
        raise AssertionError(f"GitLab project lookup failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise AssertionError(f"GitLab project lookup failed: {exc.reason}") from exc


def add_check(
    checks: list[dict[str, Any]], name: str, ok: bool, detail: str, payload: dict[str, Any] | None = None
) -> None:
    row: dict[str, Any] = {"name": name, "ok": ok, "detail": detail}
    if payload is not None:
        row["payload"] = payload
    checks.append(row)


def validate_all(check_gitlab_api: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    try:
        uptime = load_json(UPTIME_FILE)
        validate_uptime(uptime)
        add_check(checks, "uptime-kuma-plan", True, "monitor plan covers test/prod HTTP and push jobs")
    except Exception as exc:  # noqa: BLE001
        add_check(checks, "uptime-kuma-plan", False, str(exc))

    try:
        graylog = load_json(GRAYLOG_FILE)
        validate_graylog(graylog)
        add_check(checks, "graylog-event-definitions", True, "event definitions cover service errors and critical workflows")
    except Exception as exc:  # noqa: BLE001
        add_check(checks, "graylog-event-definitions", False, str(exc))

    routing: dict[str, Any] | None = None
    try:
        routing = load_json(ROUTING_FILE)
        validate_routing(routing)
        add_check(checks, "mayalerts-gitlab-routing", True, "routing targets myprojects/localrag with non-prod and prod routes")
    except Exception as exc:  # noqa: BLE001
        add_check(checks, "mayalerts-gitlab-routing", False, str(exc))

    if routing is not None:
        try:
            event = load_json(DRY_RUN_EVENT_FILE)
            expected = load_json(EXPECTED_GITLAB_FILE)
            validate_expected_issue(routing, event, expected)
            add_check(
                checks,
                "alert-to-gitlab-dry-run",
                True,
                "dry-run MayAlerts event renders the expected GitLab issue payload",
                {
                    "title": expected["title"],
                    "fingerprint": expected["dedupe_fingerprint"],
                },
            )
        except Exception as exc:  # noqa: BLE001
            add_check(checks, "alert-to-gitlab-dry-run", False, str(exc))

        if check_gitlab_api:
            try:
                project_payload = check_gitlab_project(routing["gitlab"])
                add_check(
                    checks,
                    "gitlab-project-api",
                    True,
                    "non-mutating GitLab project lookup succeeded",
                    project_payload,
                )
            except Exception as exc:  # noqa: BLE001
                add_check(checks, "gitlab-project-api", False, str(exc))

    return {
        "ok": all(check["ok"] for check in checks),
        "artifact_dir": str(SETUP_DIR.relative_to(ROOT_DIR)),
        "checks": checks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-gitlab-api",
        action="store_true",
        help="Verify the configured GitLab project via a non-mutating API lookup.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate_all(check_gitlab_api=args.check_gitlab_api)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
