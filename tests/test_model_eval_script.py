from pathlib import Path
import importlib.util


ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT_DIR / "scripts" / "model_eval.py"
SPEC = importlib.util.spec_from_file_location("localrag_model_eval", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
model_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(model_eval)


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, text: str):
        self._response = FakeResponse(text)

    def post(self, *_args, **_kwargs):
        return self._response


def test_normalize_text_collapses_initial_spacing():
    assert model_eval.normalize_text("А. И. Маркушевич") == model_eval.normalize_text(
        "А.И.Маркушевич"
    )


def test_evaluate_case_accepts_expected_sources_list():
    html = """
    <textarea id="answer">Правильное мышление необходимо в труде и в быту.</textarea>
    <pre>[source: Логика. Учебник для средней школы. (С.Н. Виноградов. 1954 год).pdf | page 3 | lines 1-12]</pre>
    """
    session = FakeSession(html)
    case = {
        "id": "RAG-011",
        "question": "Где, согласно учебнику логики, необходимо правильное мышление?",
        "expected_contains": ["в труде", "в быту"],
        "expected_sources": [
            "Логика С.Н. Виноградов. 1954 год) - crop.pdf",
            "Логика. Учебник для средней школы. (С.Н. Виноградов. 1954 год).pdf",
        ],
    }

    result = model_eval.evaluate_case(
        session,
        "http://127.0.0.1:7860",
        "qwen3.5:9b",
        case,
        topk=6,
        role="archivist",
        answer_language="ru",
        timeout=30,
    )

    assert result["source_hit"] is True
    assert result["pass_strict"] is True
