from fastapi.testclient import TestClient
import pytest

import main


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_state(tmp_path, monkeypatch):
    with main._history_lock:
        main._history_store.clear()
    profile_file = tmp_path / "server_profile.json"
    profile_file.write_text('{"custom_roles": []}\n', encoding="utf-8")
    monkeypatch.setattr(main, "SERVER_PROFILE_FILE", profile_file)
    client.cookies.clear()
    yield
    with main._history_lock:
        main._history_store.clear()
    client.cookies.clear()


def test_engineer_role_passes_engineer_master_prompt(monkeypatch):
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3"])
    captured: dict[str, str | None] = {"role_prompt": None}

    def fake_rag_query(question, model, top_k, role_prompt=None):
        captured["role_prompt"] = role_prompt
        return "Role answer", "ctx"

    monkeypatch.setattr(main, "rag_query", fake_rag_query)

    resp = client.post(
        "/api/ask",
        data={
            "question": "How to do it?",
            "model": "llama3",
            "topk": "8",
            "role": "engineer",
            "role_style": "detailed",
        },
    )
    assert resp.status_code == 200
    expected_prompt = main.build_role_prompt("en", "engineer", "detailed")
    assert captured["role_prompt"] == expected_prompt

    history = client.get("/api/history")
    assert history.status_code == 200
    assert "Engineer" in history.text
    assert "Detailed" in history.text


def test_unknown_role_falls_back_to_analyst_prompt(monkeypatch):
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3"])
    captured: dict[str, str | None] = {"role_prompt": None}

    def fake_rag_query(question, model, top_k, role_prompt=None):
        captured["role_prompt"] = role_prompt
        return "Fallback answer", "ctx"

    monkeypatch.setattr(main, "rag_query", fake_rag_query)

    resp = client.post(
        "/api/ask",
        data={
            "question": "Fallback role?",
            "model": "llama3",
            "topk": "8",
            "role": "not-a-role",
        },
    )
    assert resp.status_code == 200
    expected_prompt = main.build_role_prompt("en", "analyst", "balanced")
    assert captured["role_prompt"] == expected_prompt

    history = client.get("/api/history")
    assert history.status_code == 200
    assert "Analyst" in history.text


def test_russian_prompt_uses_russian_role_and_language_rules():
    prompt = main.build_role_prompt("ru", "engineer", "balanced")

    assert "Отвечай только на русском языке" in prompt
    assert "Роль: Инженер." in prompt
    assert "Стиль: сбалансированно." in prompt


def test_role_image_catalog_contains_defaults():
    labels = lambda key: key  # noqa: E731
    catalog = main.get_role_image_catalog(labels)

    assert catalog["analyst"]["default"] == "analyst"
    assert catalog["engineer"]["default"] == "engineer"
    assert catalog["archivist"]["default"] == "archivist"
    assert len(catalog["analyst"]["options"]) == 16
    assert any(option["value"] == "strategist" for option in catalog["analyst"]["options"])
    assert any(option["value"] == "blacksmith" for option in catalog["engineer"]["options"])
    assert any(option["value"] == "scribe" for option in catalog["archivist"]["options"])
    assert "/static/roles/analyst.png" in catalog["analyst"]["default_src"]
    assert "?v=" in catalog["analyst"]["default_src"]
    assert all(".svg" not in option["src"] for option in catalog["analyst"]["options"])


def test_custom_role_prompt_override_is_passed_to_rag_query(monkeypatch):
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3"])
    captured: dict[str, str | None] = {"role_prompt": None}

    def fake_rag_query(question, model, top_k, role_prompt=None):
        captured["role_prompt"] = role_prompt
        return "Custom answer", "ctx"

    monkeypatch.setattr(main, "rag_query", fake_rag_query)

    resp = client.post(
        "/api/ask",
        data={
            "question": "Use custom role prompt",
            "model": "llama3",
            "topk": "8",
            "role": "engineer",
            "role_style": "balanced",
            "custom_role_prompt": "Custom engineer prompt.\nReturn only implementation notes.",
        },
    )
    assert resp.status_code == 200
    assert captured["role_prompt"] is not None
    assert "Custom engineer prompt." in captured["role_prompt"]
    assert "Role: Engineer." not in captured["role_prompt"]


def test_answer_language_override_uses_selected_language_prompt(monkeypatch):
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3"])
    captured: dict[str, str | None] = {"role_prompt": None}

    def fake_rag_query(question, model, top_k, role_prompt=None):
        captured["role_prompt"] = role_prompt
        return "Answer in Russian", "ctx"

    monkeypatch.setattr(main, "rag_query", fake_rag_query)

    resp = client.post(
        "/api/ask",
        data={
            "question": "Where did he go?",
            "model": "llama3",
            "topk": "8",
            "role": "engineer",
            "role_style": "balanced",
            "answer_language": "ru",
        },
    )
    assert resp.status_code == 200
    assert captured["role_prompt"] == main.build_role_prompt("ru", "engineer", "balanced")
    assert "Роль: Инженер." in captured["role_prompt"]


def test_debug_mode_adds_debug_block(monkeypatch):
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3"])
    monkeypatch.setattr(
        main,
        "rag_query",
        lambda question, model, top_k, role_prompt=None: ("Debug answer", "ctx"),
    )

    resp = client.post(
        "/api/ask",
        data={
            "question": "Need debug",
            "model": "llama3",
            "topk": "8",
            "role": "analyst",
            "role_style": "concise",
            "debug_mode": "1",
        },
    )
    assert resp.status_code == 200
    assert "Debug metadata" in resp.text
    assert "Latency (ms)" in resp.text


def test_debug_mode_shows_retrieval_rows(monkeypatch):
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3"])
    monkeypatch.setattr(
        main,
        "rag_query",
        lambda question, model, top_k, role_prompt=None: ("Debug answer", "ctx"),
    )
    monkeypatch.setattr(
        main,
        "get_retrieval_debug_snapshot",
        lambda question, top_k: [
            {
                "rank": 1,
                "source_label": "[C:\\Temp\\PDF\\Айболит.txt | lines 10-18]",
                "score": 27.5,
                "vector_bonus": 0.7,
                "source_overlap": 2,
                "source_focus_overlap": 1,
                "content_overlap": 3,
                "quality": 0.81,
                "exact_source_title_match": True,
                "all_terms_present": True,
            }
        ],
    )

    resp = client.post(
        "/api/ask",
        data={
            "question": "Need retrieval debug",
            "model": "llama3",
            "topk": "8",
            "role": "analyst",
            "role_style": "concise",
            "debug_mode": "1",
        },
    )

    assert resp.status_code == 200
    assert "Retrieved chunks" in resp.text
    assert "Title match" in resp.text
    assert "All terms" in resp.text
    assert "Айболит.txt" in resp.text


def test_custom_role_id_and_label_are_preserved_in_history(monkeypatch):
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3"])
    captured: dict[str, str | None] = {"role_prompt": None}

    def fake_rag_query(question, model, top_k, role_prompt=None):
        captured["role_prompt"] = role_prompt
        return "Strategist answer", "ctx"

    monkeypatch.setattr(main, "rag_query", fake_rag_query)

    resp = client.post(
        "/api/ask",
        data={
            "question": "What is the strategy?",
            "model": "llama3",
            "topk": "8",
            "role": "custom-strategist",
            "role_label": "Strategist",
            "role_style": "balanced",
            "custom_role_prompt": "Role: Strategist.\nAnswer like a tactical planner.",
        },
    )

    assert resp.status_code == 200
    assert captured["role_prompt"] is not None
    assert "Role: Strategist." in captured["role_prompt"]

    history = client.get("/api/history")
    assert history.status_code == 200
    assert "Strategist" in history.text
    assert "Analyst" not in history.text


def test_custom_roles_profile_api_roundtrip():
    payload = {
        "custom_roles": [
            {
                "id": "custom-strategist",
                "name": "Strategist",
                "description": "Plans next moves.",
                "prompt": "Role: Strategist.\nReturn a tactical plan.",
                "image": "strategist",
                "answer_language": "ru",
                "default_model": "llama3",
                "default_style": "detailed",
            }
        ]
    }

    save_resp = client.post("/api/profile/custom-roles", json=payload)

    assert save_resp.status_code == 200
    saved = save_resp.json()
    assert saved["ok"] is True
    assert saved["custom_roles"][0]["id"] == "custom-strategist"
    assert saved["custom_roles"][0]["default_style"] == "detailed"
    assert saved["custom_roles"][0]["answer_language"] == "ru"

    get_resp = client.get("/api/profile/custom-roles")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["custom_roles"][0]["name"] == "Strategist"
    assert fetched["custom_roles"][0]["default_model"] == "llama3"


def test_custom_roles_export_endpoint():
    main.set_server_custom_roles(
        [
            {
                "id": "custom-strategist",
                "name": "Strategist",
                "description": "Plans next moves.",
                "prompt": "Role: Strategist.\nReturn a tactical plan.",
                "image": "strategist",
                "answer_language": "ru",
                "default_model": "llama3",
                "default_style": "detailed",
            }
        ]
    )

    resp = client.get("/api/profile/custom-roles/export")

    assert resp.status_code == 200
    assert "localrag-custom-roles.json" in resp.headers["content-disposition"]
    payload = resp.json()
    assert payload["ok"] is True
    assert payload["profile"]["custom_roles"][0]["id"] == "custom-strategist"
    assert payload["custom_roles"][0]["default_style"] == "detailed"


def test_custom_role_server_profile_controls_prompt_language_style_and_model(monkeypatch):
    main.set_server_custom_roles(
        [
            {
                "id": "custom-strategist",
                "name": "Strategist",
                "description": "Plans next moves.",
                "prompt": "Role: Strategist.\nReturn a tactical plan.",
                "image": "strategist",
                "answer_language": "ru",
                "default_model": "phi3:mini",
                "default_style": "detailed",
            }
        ]
    )
    monkeypatch.setattr(main, "get_ollama_models", lambda: ["llama3", "phi3:mini"])
    captured: dict[str, str | None] = {"role_prompt": None, "model": None}

    def fake_rag_query(question, model, top_k, role_prompt=None):
        captured["model"] = model
        captured["role_prompt"] = role_prompt
        return "Strategist answer", "ctx"

    monkeypatch.setattr(main, "rag_query", fake_rag_query)

    resp = client.post(
        "/api/ask",
        data={
            "question": "What is the strategy?",
            "topk": "8",
            "role": "custom-strategist",
        },
    )

    assert resp.status_code == 200
    assert captured["model"] == "phi3:mini"
    assert captured["role_prompt"] == main.build_role_prompt(
        "ru",
        "analyst",
        "detailed",
        custom_role_prompt="Role: Strategist.\nReturn a tactical plan.",
    )

    history = client.get("/api/history")
    assert history.status_code == 200
    assert "Strategist" in history.text
