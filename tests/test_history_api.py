from fastapi.testclient import TestClient
import pytest

import main


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_history_store():
    with main._history_lock:
        main._history_store.clear()
    client.cookies.clear()
    yield
    with main._history_lock:
        main._history_store.clear()
    client.cookies.clear()


def test_history_empty_for_new_session():
    resp = client.get("/api/history")
    assert resp.status_code == 200
    assert "No questions asked yet." in resp.text
    assert "localrag_session_id" in resp.cookies


def test_history_records_successful_ask(monkeypatch):
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3"])
    monkeypatch.setattr(
        main,
        "rag_query",
        lambda question, model, top_k, role_prompt=None: ("Result answer", "ctx"),
    )

    ask_resp = client.post(
        "/api/ask",
        data={"question": "What is LocalRAG?", "model": "llama3", "topk": "8"},
    )
    assert ask_resp.status_code == 200
    assert "Result answer" in ask_resp.text

    history_resp = client.get("/api/history")
    assert history_resp.status_code == 200
    assert "What is LocalRAG?" in history_resp.text
    assert "Result answer" in history_resp.text
    assert "Success" in history_resp.text


def test_history_clear_removes_entries(monkeypatch):
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3"])
    monkeypatch.setattr(
        main,
        "rag_query",
        lambda question, model, top_k, role_prompt=None: ("Cleared answer", "ctx"),
    )

    client.post(
        "/api/ask",
        data={"question": "To be cleared", "model": "llama3", "topk": "5"},
    )
    precheck = client.get("/api/history")
    assert "To be cleared" in precheck.text

    clear_resp = client.post("/api/history/clear")
    assert clear_resp.status_code == 200
    assert "No questions asked yet." in clear_resp.text

    history_resp = client.get("/api/history")
    assert "To be cleared" not in history_resp.text


def test_history_limit_query_filters_visible_entries(monkeypatch):
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3"])
    monkeypatch.setattr(
        main,
        "rag_query",
        lambda question, model, top_k, role_prompt=None: ("Any answer", "ctx"),
    )

    client.post(
        "/api/ask",
        data={"question": "Older question", "model": "llama3", "topk": "5"},
    )
    client.post(
        "/api/ask",
        data={"question": "Latest question", "model": "llama3", "topk": "5"},
    )

    limited = client.get("/api/history?limit=1")
    assert limited.status_code == 200
    assert "Latest question" in limited.text
    assert "Older question" not in limited.text
