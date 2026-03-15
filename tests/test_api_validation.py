import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_ask_empty_question():
    resp = client.post("/api/ask", data={"question": "", "model": "llama3", "topk": 8})
    assert resp.status_code == 200
    assert "Please enter a question before submitting." in resp.text


def test_ask_invalid_topk():
    resp = client.post(
        "/api/ask", data={"question": "Test?", "model": "llama3", "topk": 999}
    )
    assert resp.status_code == 200
    assert "Invalid top_k value" in resp.text


def test_ask_invalid_model():
    resp = client.post(
        "/api/ask", data={"question": "Test?", "model": "notamodel", "topk": 8}
    )
    assert resp.status_code == 200
    assert "Models unavailable" in resp.text
