import json
from pathlib import Path

import main
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_server_profile(tmp_path, monkeypatch):
    profile_file = tmp_path / "server_profile.json"
    profile_file.write_text('{"custom_roles": []}\n', encoding="utf-8")
    monkeypatch.setattr(main, "SERVER_PROFILE_FILE", profile_file)
    yield


def test_index_page():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "LocalRAG" in resp.text
    assert 'id="settings-open-btn"' in resp.text
    assert 'id="settings-modal"' in resp.text
    assert 'id="role-strip-card"' in resp.text
    assert 'id="settings-answer-language"' in resp.text
    assert 'id="answer-language-hidden"' in resp.text
    assert 'id="settings-role-prompt-analyst"' in resp.text
    assert 'id="role-image-catalog"' in resp.text
    assert 'id="settings-role-image-analyst"' in resp.text
    assert 'id="settings-role-image-engineer"' in resp.text
    assert 'id="settings-role-image-archivist"' in resp.text
    assert 'id="settings-role-image-preview-analyst"' in resp.text
    assert 'id="settings-role-image-preview-engineer"' in resp.text
    assert 'id="settings-role-image-preview-archivist"' in resp.text
    assert 'id="settings-docs-picker-btn"' in resp.text
    assert 'id="docs-browser-overlay"' in resp.text
    assert 'id="docs-browser-card"' in resp.text
    assert 'id="docs-browser-use-btn"' in resp.text
    assert 'id="docs-browser-close-btn"' in resp.text
    assert 'id="docs-browser-list"' in resp.text
    assert 'id="settings-embedding-card"' in resp.text
    assert 'id="settings-embedding-model-select"' in resp.text
    assert 'id="settings-embedding-model-custom"' in resp.text
    assert 'id="embedding-model-prepare-btn"' in resp.text
    assert 'id="embedding-models-pull-status"' in resp.text
    assert 'id="installed-embedding-models-list"' in resp.text
    assert 'id="recommended-embedding-models-list"' in resp.text
    assert 'data-settings-tab="general"' in resp.text
    assert 'data-settings-tab="models"' in resp.text
    assert 'data-settings-tab="roles"' in resp.text
    assert 'id="models-refresh-btn"' in resp.text
    assert 'id="installed-models-list"' in resp.text
    assert 'id="recommended-models-list"' in resp.text
    assert 'id="manual-model-name"' in resp.text
    assert 'id="custom-role-prompt-hidden"' in resp.text
    assert 'id="role-label-hidden"' in resp.text
    assert 'id="default-role-definitions"' in resp.text
    assert 'id="server-profile-data"' in resp.text
    assert 'id="settings-i18n"' in resp.text
    assert 'id="docs-browser-search"' in resp.text
    assert 'id="settings-custom-roles-card"' in resp.text
    assert 'id="settings-custom-roles-list"' in resp.text
    assert 'id="custom-roles-export-btn"' in resp.text
    assert 'id="custom-roles-import-btn"' in resp.text
    assert 'id="custom-roles-import-file"' in resp.text
    assert 'id="custom-roles-reset-btn"' in resp.text
    assert 'id="custom-role-name"' in resp.text
    assert 'id="custom-role-image"' in resp.text
    assert 'id="custom-role-answer-language"' in resp.text
    assert 'id="custom-role-default-model"' in resp.text
    assert 'id="custom-role-default-style"' in resp.text
    assert 'id="custom-role-prompt"' in resp.text
    assert 'class="app-footer"' in resp.text
    assert 'app-footer-runtime' in resp.text
    assert 'https://github.com/Sergey360' in resp.text
    assert 'https://github.com/Sergey360/LocalRAG' in resp.text
    assert 'hx-sync="this:replace"' in resp.text
    assert resp.text.index('id="settings-embedding-card"') < resp.text.index('id="settings-models-card"')
    assert resp.text.index('id="settings-models-card"') < resp.text.index('id="settings-role-images-card"')
    assert resp.text.index('id="settings-custom-roles-card"') < resp.text.index('id="settings-role-images-card"')
    assert resp.text.index('id="settings-role-images-card"') < resp.text.index('id="settings-role-prompts-card"')


def test_status_endpoint():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    assert "Current documents folder" in resp.text


def test_status_endpoint_renders_progress_bar(monkeypatch):
    monkeypatch.setattr(main, "get_index_status_meta", lambda: ("indexing", {"progress": 46}))
    monkeypatch.setattr(main, "get_indexed_file_count", lambda: 18)
    monkeypatch.setattr(main, "get_docs_path_display", lambda: r"C:\\Temp\\PDF")

    resp = client.get("/api/status")

    assert resp.status_code == 200
    assert 'data-status-code="indexing"' in resp.text
    assert "status-progress-bar" in resp.text
    assert "46%" in resp.text


def test_models_endpoint():
    resp = client.get("/api/models")
    assert resp.status_code == 200
    assert "<select" in resp.text


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["ok"] is True
    assert payload["app"]["name"] == "LocalRAG"
    assert payload["app"]["version"]
    assert "embedding_runtime" in payload["app"]
    assert "model_loaded" in payload["app"]["embedding_runtime"]
    assert "model_device" in payload["app"]["embedding_runtime"]
    assert "index" in payload


def test_meta_endpoint_matches_version_file():
    resp = client.get("/api/meta")
    assert resp.status_code == 200
    payload = resp.json()
    expected = Path("VERSION").read_text(encoding="utf-8").strip()
    assert payload["name"] == "LocalRAG"
    assert payload["version"] == expected
    assert payload["default_model"] == "qwen3.5:9b"
    assert payload["default_embedding_model"] == "intfloat/multilingual-e5-large"
    assert payload["embedding_model"]
    assert "embedding_runtime" in payload
    assert "device" in payload["embedding_runtime"]
    assert "model_loaded" in payload["embedding_runtime"]
    assert "model_device" in payload["embedding_runtime"]
    assert "default_docs_path" in payload
    assert payload["workspace_files_path"].endswith("files")


def test_lang_switch():
    resp = client.post("/api/lang_switch", json={"lang": "en"})
    assert resp.status_code == 200
    assert "LocalRAG" in resp.text


def test_localize_context_header_uses_translated_line_labels():
    translations = main.load_translations("ru")

    def t_local(key: str) -> str:
        return translations[key]

    localized = main.localize_context_header(
        r"[C:\Temp\PDF\Айболит.txt | page 3 | lines 91-109]",
        t_local,
    )

    assert "страница 3" in localized
    assert "строки 91-109" in localized
    assert "lines 91-109" not in localized


def test_embedding_translation_keys_are_not_placeholder_text():
    expected = {
        "ru": "Модель эмбеддингов",
        "zh": "嵌入模型",
        "he": "מודל ההטמעות",
    }
    for lang, value in expected.items():
        translations = main.load_translations(lang)
        assert translations["settings_embedding_model"] == value
        assert "?" not in translations["settings_tabs_label"]
        assert translations["footer_embedding_runtime"]


def test_docs_path_update_endpoint(monkeypatch):
    captured = {"docs_path": None, "rebuild_called": False}

    def fake_set_docs_path(value):
        captured["docs_path"] = value
        return value

    def fake_rebuild_index():
        captured["rebuild_called"] = True
        return "ok"

    monkeypatch.setattr(main, "set_docs_path", fake_set_docs_path)
    monkeypatch.setattr(main, "rebuild_index", fake_rebuild_index)

    resp = client.post("/api/docs-path", json={"docs_path": r"C:\\Temp\\PDF"})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["ok"] is True
    assert payload["docs_path"] == r"C:\\Temp\\PDF"
    assert captured["docs_path"] == r"C:\\Temp\\PDF"
    assert captured["rebuild_called"] is True


def test_embedding_model_update_endpoint(monkeypatch):
    captured = {"embedding_model": None, "rebuild_called": False}

    def fake_set_embedding_model(value):
        captured["embedding_model"] = value
        return value

    def fake_rebuild_index():
        captured["rebuild_called"] = True
        return "ok"

    monkeypatch.setattr(main, "set_embedding_model", fake_set_embedding_model)
    monkeypatch.setattr(main, "rebuild_index", fake_rebuild_index)

    resp = client.post("/api/embedding-model", json={"embedding_model": "BAAI/bge-m3"})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["ok"] is True
    assert payload["embedding_model"] == "BAAI/bge-m3"
    assert captured["embedding_model"] == "BAAI/bge-m3"
    assert captured["rebuild_called"] is True


def test_runtime_config_updates_docs_path_and_embedding_model(monkeypatch):
    captured = {"docs_path": None, "embedding_model": None, "rebuild_called": False}

    def fake_set_docs_path(value):
        captured["docs_path"] = value
        return value

    def fake_set_embedding_model(value):
        captured["embedding_model"] = value
        return value

    def fake_rebuild_index():
        captured["rebuild_called"] = True
        return "ok"

    monkeypatch.setattr(main, "set_docs_path", fake_set_docs_path)
    monkeypatch.setattr(main, "set_embedding_model", fake_set_embedding_model)
    monkeypatch.setattr(main, "rebuild_index", fake_rebuild_index)

    resp = client.post(
        "/api/runtime-config",
        json={
            "docs_path": r"C:\\Temp\\PDF",
            "embedding_model": "BAAI/bge-m3",
        },
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["ok"] is True
    assert payload["docs_path"] == r"C:\\Temp\\PDF"
    assert payload["embedding_model"] == "BAAI/bge-m3"
    assert captured["docs_path"] == r"C:\\Temp\\PDF"
    assert captured["embedding_model"] == "BAAI/bge-m3"
    assert captured["rebuild_called"] is True


def test_docs_browser_endpoint(monkeypatch):
    payload = {
        "root_path": r"C:\\",
        "requested_path": r"C:\\Temp",
        "path": r"C:\\Temp",
        "parent_path": r"C:\\",
        "directories": [
            {"name": "PDF", "path": r"C:\\Temp\\PDF"},
            {"name": "Books", "path": r"C:\\Temp\\Books"},
        ],
    }

    monkeypatch.setattr(main, "list_browsable_directories", lambda path=None: payload)

    resp = client.get("/api/fs/dirs", params={"path": r"C:\\Temp"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["path"] == r"C:\\Temp"
    assert body["directories"][0]["path"] == r"C:\\Temp\\PDF"


def test_load_translations_falls_back_from_placeholder_values(tmp_path, monkeypatch):
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()
    (locales_dir / "en.json").write_text(
        json.dumps(
            {
                "settings_model_manager": "Model manager",
                "models_installed": "Installed models",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (locales_dir / "ru.json").write_text(
        json.dumps(
            {
                "settings_model_manager": "???????? ???????",
                "models_installed": "????????????? ??????",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "LOCALES_DIR", locales_dir)

    payload = main.load_translations("ru")

    assert payload["settings_model_manager"] == "Model manager"
    assert payload["models_installed"] == "Installed models"


def test_locale_files_do_not_contain_placeholder_translations():
    locale_keys = ("ru", "zh", "he")

    for lang in locale_keys:
        payload = json.loads(Path(f"app/locales/{lang}.json").read_text(encoding="utf-8"))
        pattern = main.PLACEHOLDER_TRANSLATION_PATTERNS[lang]
        broken = [
            key
            for key, value in payload.items()
            if isinstance(value, str) and value.count("?") >= 3 and pattern.match(value.strip())
        ]
        assert broken == [], f"{lang} locale still contains placeholders: {broken}"


def test_zh_and_he_core_ui_labels_are_localized():
    english = json.loads(Path("app/locales/en.json").read_text(encoding="utf-8"))

    for lang in ("zh", "he"):
        payload = json.loads(Path(f"app/locales/{lang}.json").read_text(encoding="utf-8"))
        for key in (
            "open_settings",
            "history_title",
            "history_empty",
            "history_clear",
            "role_label",
            "settings_title",
            "settings_apply",
        ):
            assert payload[key] != english[key], f"{lang} locale still uses English for {key}"
