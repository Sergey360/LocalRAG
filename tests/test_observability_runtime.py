import json

from fastapi.testclient import TestClient

import main
from main import app


client = TestClient(app)


def test_request_id_header_round_trips():
    request_id = "issue-14-test-request"

    resp = client.get("/api/health", headers={"X-Request-ID": request_id})

    assert resp.status_code == 200
    assert resp.headers["x-request-id"] == request_id
    assert resp.json()["ok"] is True


def test_request_id_header_is_generated_when_missing():
    resp = client.get("/api/meta")

    assert resp.status_code == 200
    assert resp.headers.get("x-request-id")


def test_metrics_endpoint_exposes_runtime_and_http_metrics():
    client.get("/api/health")

    resp = client.get("/metrics")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert "# HELP localrag_http_requests_total" in resp.text
    assert "localrag_http_requests_total" in resp.text
    assert 'route="/api/health"' in resp.text
    assert "localrag_index_status" in resp.text
    assert "localrag_indexed_file_count" in resp.text


def test_ask_validation_records_privacy_safe_rag_metric():
    private_question = "private question should not appear in telemetry"

    resp = client.post(
        "/api/ask",
        data={"question": private_question, "model": "llama3", "topk": 999},
    )
    metrics = client.get("/metrics").text

    assert resp.status_code == 200
    assert "Invalid top_k value" in resp.text
    assert "localrag_rag_queries_total" in metrics
    assert 'outcome="validation_error"' in metrics
    assert private_question not in metrics


def test_structured_log_payload_has_required_contract_fields():
    payload = main.build_structured_log_payload(
        event_name="test_event",
        event_domain="observability",
        event_outcome="success",
        severity="info",
        message="test event",
        correlation_id="issue-14-correlation",
        question_chars=42,
        client_ip_hash=main.hash_private_value("127.0.0.1"),
    )

    required_fields = {
        "service_name",
        "app_env",
        "app_release",
        "app_version",
        "app_instance_id",
        "correlation_id",
        "event_name",
        "event_domain",
        "event_outcome",
        "severity",
        "message",
        "timestamp_utc",
        "host",
    }
    assert required_fields.issubset(payload)
    assert payload["correlation_id"] == "issue-14-correlation"
    rendered = json.dumps(payload, ensure_ascii=False)
    assert "127.0.0.1" not in rendered
    assert "question_chars" in payload
