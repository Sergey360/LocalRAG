from pathlib import Path
import importlib.util
import sys


ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "app"
APP_MODULE_PATH = ROOT_DIR / "app" / "app.py"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
SPEC = importlib.util.spec_from_file_location("localrag_core", APP_MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
rag_core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rag_core)


def test_get_default_model_prefers_qwen_14b_when_available():
    model = rag_core.get_default_model(
        ["qwen2.5:7b-instruct", "qwen2.5:14b", "phi3:mini"]
    )
    assert model == "qwen2.5:14b"


def test_get_default_model_prefers_qwen3_when_available():
    model = rag_core.get_default_model(
        ["phi3:mini", "qwen2.5:14b", "qwen3:8b", "qwen3.5:9b"]
    )
    assert model == "qwen3.5:9b"


def test_build_ollama_generate_payload_disables_thinking_for_qwen3():
    payload = rag_core.build_ollama_generate_payload("qwen3:8b", "Prompt")
    assert payload["model"] == "qwen3:8b"
    assert payload["stream"] is False
    assert payload["think"] is False


def test_build_ollama_generate_payload_keeps_legacy_models_unchanged():
    payload = rag_core.build_ollama_generate_payload("phi3:mini", "Prompt")
    assert payload["model"] == "phi3:mini"
    assert payload["stream"] is False
    assert "think" not in payload


def test_build_answer_prompt_prioritizes_direct_answer_and_language():
    prompt = rag_core.build_answer_prompt(
        context="Айболит поехал в Африку лечить зверей.",
        question="Куда поехал Айболит?",
        answer_lang="ru",
        role_prompt="Отвечай только на русском языке.",
    )

    assert "If the context contains a direct answer, state that answer in the first sentence." in prompt
    assert "Keep the first sentence short and direct." in prompt
    assert "preserve the exact short designation from the context" in prompt
    assert "For list or place questions, keep the key items from the context" in prompt
    assert "copy the short label from the context verbatim when possible" in prompt
    assert "preserve the main items and repeated markers from the context" in prompt
    assert "Do not say that the context is insufficient when the answer is present in the context." in prompt
    assert "prefer the main destination unless the question explicitly asks for the narrower place." in prompt
    assert "Return the answer only in Russian." in prompt
    assert "Role instructions:\nОтвечай только на русском языке." in prompt
    assert "Question:\nКуда поехал Айболит?" in prompt


def test_repair_answer_language_uses_non_thinking_payload_for_qwen3(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "Исправленный ответ"}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(rag_core.requests, "post", fake_post)

    repaired = rag_core.repair_answer_language(
        context="Контекст",
        question="Вопрос",
        draft_answer="Черновой ответ",
        model_name="qwen3:8b",
        answer_lang="ru",
        role_prompt="Отвечай только на русском языке.",
    )

    assert repaired == "Исправленный ответ"
    assert captured["json"]["model"] == "qwen3:8b"
    assert captured["json"]["stream"] is False
    assert captured["json"]["think"] is False


def test_answer_needs_language_repair_flags_mixed_russian_output():
    mixed_answer = (
        "Айболит поехал в Африку. 多次阅读提供的故事文本后，可以明确得出结论。 "
        "Answer: Айболит направлялся к Лимпопо."
    )
    assert rag_core.answer_needs_language_repair(mixed_answer, "ru") is True


def test_rag_query_repairs_invalid_russian_answer(monkeypatch):
    class FakeDoc:
        def __init__(self, page_content):
            self.page_content = page_content

    class FakeVectorDb:
        index_to_docstore_id = {0: "doc-1"}

        def similarity_search(self, question, k):
            return [FakeDoc("Айболит отправился в Африку лечить зверей.")]

    monkeypatch.setattr(rag_core, "vectordb", FakeVectorDb())
    monkeypatch.setattr(rag_core, "needs_reindex", False)
    calls = {"repair": 0}

    def fake_ollama_chat(context, question, model_name, role_prompt=None):
        return (
            "Айболит поехал в Африку. 多次阅读提供的故事文本后，可以明确得出结论。 "
            "Answer: Айболит направлялся к Лимпопо."
        )

    def fake_repair(context, question, draft_answer, model_name, answer_lang, role_prompt=None):
        calls["repair"] += 1
        assert answer_lang == "ru"
        assert "多次阅读" in draft_answer
        return "Айболит поехал в Африку и направлялся к Лимпопо."

    monkeypatch.setattr(rag_core, "ollama_chat", fake_ollama_chat)
    monkeypatch.setattr(rag_core, "repair_answer_language", fake_repair)

    answer, context = rag_core.rag_query(
        "Куда поехал Айболит?",
        "qwen2.5:14b",
        8,
        role_prompt="Отвечай только на русском языке.",
    )

    assert calls["repair"] == 1
    assert answer == "Айболит поехал в Африку и направлялся к Лимпопо."
    assert "Айболит отправился в Африку лечить зверей." in context
