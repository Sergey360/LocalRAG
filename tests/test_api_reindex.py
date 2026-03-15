import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_reindex_background():
    resp = client.post("/api/reindex")
    assert resp.status_code == 200
    assert resp.json().get("status") == "reindex started"


def test_status_polling():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    assert "Current documents folder" in resp.text
