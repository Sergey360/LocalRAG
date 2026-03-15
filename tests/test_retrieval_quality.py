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


class FakeDoc:
    def __init__(self, page_content, source, page=0):
        self.page_content = page_content
        self.metadata = {"source": source, "page": page}


class FakeDocStore:
    def __init__(self, documents):
        self._dict = documents

    def search(self, doc_id):
        return self._dict[doc_id]


class FakeVectorDb:
    def __init__(self, documents, vector_results):
        self.docstore = FakeDocStore(documents)
        self.index_to_docstore_id = {idx: doc_id for idx, doc_id in enumerate(documents)}
        self._vector_results = vector_results

    def similarity_search_with_score(self, question, k):
        return self._vector_results[:k]


def test_is_low_signal_pdf_chunk_filters_ocr_noise():
    noisy = FakeDoc(
        "Ах! У Ш Шш Ж sJP jkvJj/ 10",
        "/hostfs/c/Temp/PDF/Букварь.pdf",
    )
    good = FakeDoc(
        (
            "Айболит получил телеграмму и сразу поехал в Африку лечить больных зверей. "
            "Он торопился помочь детям и не стал откладывать поездку."
        ),
        "/hostfs/c/Temp/PDF/Айболит.pdf",
    )

    assert rag_core.is_low_signal_pdf_chunk(noisy) is True
    assert rag_core.is_low_signal_pdf_chunk(good) is False


def test_is_low_signal_pdf_chunk_keeps_cover_pages():
    cover = FakeDoc(
        "УЧЕБНИК ДЛЯ 10-11 КЛАССА",
        "/hostfs/c/Temp/PDF/Алгебра и начала анализа. 10 -11 класс. (А.Н. Колмогоров. 1990 год).pdf",
        page=0,
    )

    assert rag_core.is_low_signal_pdf_chunk(cover) is False


def test_is_low_signal_pdf_chunk_keeps_synthetic_source_headers():
    header = FakeDoc(
        "Заголовок файла: Математика. 5 класс. Файл: Математика. 5 класс - учебное пособие.",
        "/hostfs/c/Temp/PDF/Математика. 5 класс - учебное пособие. (А.И. Маркушевич. 1971 год).pdf",
        page=0,
    )
    header.metadata["synthetic_source_header"] = True

    assert rag_core.is_low_signal_pdf_chunk(header) is False


def test_build_source_header_text_extracts_filename_metadata():
    text = rag_core.build_source_header_text(
        Path("Математика. 5 класс - учебное пособие. (А.И. Маркушевич. 1971 год).pdf")
    )

    assert "Математика. 5 класс" in text
    assert "1971" in text
    assert "А.И. Маркушевич" in text
    assert "Класс: 5." in text


def test_load_documents_reads_supported_files_directly(tmp_path, monkeypatch):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "notes.txt").write_text("alpha beta gamma", encoding="utf-8")
    nested = docs_root / "nested"
    nested.mkdir()
    (nested / "readme.md").write_text("delta epsilon", encoding="utf-8")
    (nested / "ignore.bin").write_bytes(b"\x00\x01")

    monkeypatch.setattr(rag_core, "get_docs_path", lambda: docs_root)

    docs = rag_core.load_documents()
    contents = [doc.page_content for doc in docs]
    sources = [str((getattr(doc, "metadata", {}) or {}).get("source", "")) for doc in docs]

    assert any("alpha beta gamma" in value for value in contents)
    assert any("delta epsilon" in value for value in contents)
    assert any("Заголовок файла:" in value for value in contents)
    assert all(not source.endswith("ignore.bin") for source in sources)


def test_extract_author_evidence_prefers_full_name_lines():
    context = (
        "[source: Айболит.txt | lines 1-12]\n"
        "Корней Чуковский\n"
        "Айболит\n"
        "Добрый доктор Айболит!"
    )

    assert rag_core.extract_author_evidence(context) == "Корней Чуковский"


def test_extract_author_evidence_normalizes_initial_spacing():
    context = "Автор или редактор: О.В. Творогов."

    assert rag_core.extract_author_evidence(context) == "О. В. Творогов"


def test_retrieve_relevant_docs_prefers_source_and_keyword_matches():
    good_doc = FakeDoc(
        "Айболит получил телеграмму: приезжайте, доктор, в Африку скорей.",
        "/hostfs/c/Temp/PDF/Айболит.txt",
    )
    supporting_doc = FakeDoc(
        "Айболит побежал в путь и повторял: Лимпопо, Лимпопо.",
        "/hostfs/c/Temp/PDF/Айболит.txt",
        page=1,
    )
    noisy_doc = FakeDoc(
        "Ах! У Ш Шш Ж sJP jkvJj/ 10",
        "/hostfs/c/Temp/PDF/Букварь.pdf",
        page=3,
    )
    unrelated_doc = FakeDoc(
        "В географии обсуждается Африка, пустыни и климатические пояса.",
        "/hostfs/c/Temp/PDF/География.pdf",
        page=7,
    )
    store = FakeVectorDb(
        {
            "noise": noisy_doc,
            "good": good_doc,
            "support": supporting_doc,
            "geo": unrelated_doc,
        },
        vector_results=[(noisy_doc, 0.20), (unrelated_doc, 0.24)],
    )

    docs = rag_core.retrieve_relevant_docs(store, "Куда поехал Айболит?", 2)
    sources = [doc.metadata["source"] for doc in docs]

    assert sources[0] == "/hostfs/c/Temp/PDF/Айболит.txt"
    assert all(source == "/hostfs/c/Temp/PDF/Айболит.txt" for source in sources)


def test_retrieve_relevant_docs_prefers_quoted_source_titles():
    algebra_doc = FakeDoc(
        "Пределы и производные рассматриваются в старших классах.",
        "/hostfs/c/Temp/PDF/Алгебра и начала анализа. 10 -11 класс. (А.Н. Колмогоров. 1990 год).pdf",
        page=3,
    )
    russian_doc = FakeDoc(
        "УЧЕБНИК ДЛЯ 1-го КЛАССА",
        "/hostfs/c/Temp/PDF/Русский язык. Учебник для первого класса. Цветной. (М.Л. Закожурникова. 1965 год).pdf",
        page=0,
    )
    store = FakeVectorDb(
        {"ru": russian_doc, "alg": algebra_doc},
        vector_results=[(russian_doc, 0.20)],
    )

    docs = rag_core.retrieve_relevant_docs(
        store,
        "Для какого класса предназначен учебник «Алгебра и начала анализа»?",
        1,
    )

    assert docs[0].metadata["source"].endswith("Алгебра и начала анализа. 10 -11 класс. (А.Н. Колмогоров. 1990 год).pdf")


def test_retrieve_relevant_docs_prefers_exact_named_source_over_content_mentions():
    drawing_doc = FakeDoc(
        "Textbook for universities. Author: Tikhonov.",
        "/hostfs/c/Temp/PDF/Drawing. Textbook for universities (Tikhonov 1983).pdf",
        page=0,
    )
    literature_doc = FakeDoc(
        "The author discusses the drawing of a phrase and the rhythm of speech.",
        "/hostfs/c/Temp/PDF/Literature. Teacher guide (Tvorogov 1981).pdf",
        page=4,
    )
    store = FakeVectorDb(
        {"lit": literature_doc, "draw": drawing_doc},
        vector_results=[(literature_doc, 0.12)],
    )

    docs = rag_core.retrieve_relevant_docs(
        store,
        'Who is the audience of the manual "Drawing" by Tikhonov?',
        2,
    )

    assert docs[0].metadata["source"].endswith("Drawing. Textbook for universities (Tikhonov 1983).pdf")
    assert all("Drawing." in doc.metadata["source"] for doc in docs)


def test_retrieve_relevant_docs_prefers_year_specific_source():
    bukvar_1987 = FakeDoc(
        "БУКВАРЬ\n1 КЛАСС\n1987",
        "/hostfs/c/Temp/PDF/Букварь. 1 класс. (1987 год).pdf",
        page=0,
    )
    bukvar_1959 = FakeDoc(
        "БУКВАРЬ\n1959",
        "/hostfs/c/Temp/PDF/Букварь. 1 класс. (1959 год).pdf",
        page=0,
    )
    arithmetic_1959 = FakeDoc(
        "АРИФМЕТИКА\n1959",
        "/hostfs/c/Temp/PDF/Арифметика. Учебник для первого класса начальной школы. Цветной (А.С. Пчёлко. 1959 год).pdf",
        page=0,
    )
    store = FakeVectorDb(
        {"arith": arithmetic_1959, "b59": bukvar_1959, "b87": bukvar_1987},
        vector_results=[(arithmetic_1959, 0.08), (bukvar_1959, 0.12)],
    )

    docs = rag_core.retrieve_relevant_docs(store, "Для какого класса букварь 1987 года?", 1)

    assert docs[0].metadata["source"].endswith("Букварь. 1 класс. (1987 год).pdf")


def test_retrieve_relevant_docs_prefers_part_specific_source():
    part_one = FakeDoc(
        "Русский язык в картинках. Часть I.",
        "/hostfs/c/Temp/PDF/Русский язык в картинках. Часть I. (И.В. Баранников. 1982 год).pdf",
        page=0,
    )
    plain_russian = FakeDoc(
        "Русский язык. Учебник для первого класса.",
        "/hostfs/c/Temp/PDF/Русский язык. Учебник для первого класса. Цветной. (М.Л. Закожурникова. 1965 год).pdf",
        page=0,
    )
    history_part = FakeDoc(
        "История СССР. Часть 3.",
        "/hostfs/c/Temp/PDF/История СССР. Часть 3. 10 класс. (А.М. Пенкратова. 1952 год).pdf",
        page=0,
    )
    store = FakeVectorDb(
        {"ru": plain_russian, "part1": part_one, "history": history_part},
        vector_results=[(plain_russian, 0.10), (history_part, 0.14)],
    )

    docs = rag_core.retrieve_relevant_docs(
        store,
        "Какая часть указана у книги «Русский язык в картинках»?",
        1,
    )

    assert docs[0].metadata["source"].endswith(
        "Русский язык в картинках. Часть I. (И.В. Баранников. 1982 год).pdf"
    )


def test_retrieve_relevant_docs_prefers_class_specific_materials():
    didactic = FakeDoc(
        "Дидактические материалы по математике для 5 класса средней школы.",
        "/hostfs/c/Temp/PDF/Дидактические материалы по математике для 5 класса средней школы. (А.С. Чесноков. 1990 год).pdf",
        page=0,
    )
    geography = FakeDoc(
        "География. 8 класс.",
        "/hostfs/c/Temp/PDF/География. 8 класс. ( Н.Н. Баранский. 1933 год).pdf",
        page=0,
    )
    history = FakeDoc(
        "История СССР. Часть 3. 10 класс.",
        "/hostfs/c/Temp/PDF/История СССР. Часть 3. 10 класс. (А.М. Пенкратова. 1952 год).pdf",
        page=0,
    )
    store = FakeVectorDb(
        {"geo": geography, "hist": history, "did": didactic},
        vector_results=[(geography, 0.09), (history, 0.11)],
    )

    docs = rag_core.retrieve_relevant_docs(
        store,
        "Кто автор дидактических материалов по математике для 5 класса?",
        1,
    )

    assert docs[0].metadata["source"].endswith(
        "Дидактические материалы по математике для 5 класса средней школы. (А.С. Чесноков. 1990 год).pdf"
    )


def test_rag_query_uses_hybrid_retrieval_context(monkeypatch):
    good_doc = FakeDoc(
        "Айболит получил телеграмму: приезжайте, доктор, в Африку скорей.",
        "/hostfs/c/Temp/PDF/Айболит.txt",
    )
    noisy_doc = FakeDoc(
        "Ах! У Ш Шш Ж sJP jkvJj/ 10",
        "/hostfs/c/Temp/PDF/Букварь.pdf",
    )
    store = FakeVectorDb(
        {"noise": noisy_doc, "good": good_doc},
        vector_results=[(noisy_doc, 0.20)],
    )

    monkeypatch.setattr(rag_core, "vectordb", store)
    monkeypatch.setattr(rag_core, "needs_reindex", False)

    def fake_ollama_chat(context, question, model_name, role_prompt=None):
        assert "в Африку скорей" in context
        assert "sJP jkvJj" not in context
        assert "[source: Айболит.txt" in context
        return "Айболит поехал в Африку."

    monkeypatch.setattr(rag_core, "ollama_chat", fake_ollama_chat)

    answer, context = rag_core.rag_query(
        "Куда поехал Айболит?",
        "qwen3:8b",
        2,
        role_prompt="Отвечай только на русском языке.",
    )

    assert answer == "Айболит поехал в Африку."
    assert "Африку" in context
    assert "sJP jkvJj" not in context
    assert "Айболит.txt" in context


def test_retrieve_relevant_docs_keeps_strong_source_focus():
    doc_a = FakeDoc(
        "Айболит получил телеграмму от зверей: приезжайте, доктор, в Африку скорей.",
        "/hostfs/c/Temp/PDF/Айболит.txt",
    )
    doc_b = FakeDoc(
        "Айболит побежал помогать детям и зверям.",
        "/hostfs/c/Temp/PDF/Айболит.txt",
        page=1,
    )
    unrelated = FakeDoc(
        "В 1914 году министр Вандервельде прислал телеграмму армии.",
        "/hostfs/c/Temp/PDF/История СССР.pdf",
        page=8,
    )
    store = FakeVectorDb(
        {"a": doc_a, "b": doc_b, "u": unrelated},
        vector_results=[(unrelated, 0.18)],
    )

    docs = rag_core.retrieve_relevant_docs(store, "Кто прислал телеграмму Айболиту?", 5)

    assert len(docs) >= 1
    assert all(doc.metadata["source"] == "/hostfs/c/Temp/PDF/Айболит.txt" for doc in docs)


def test_refine_answer_with_context_evidence_adds_class_variants():
    question = "Для какого класса книга «Родная речь»?"
    answer = "Книга предназначена для первого класса."
    context = (
        "[source: Родная речь. 1 класс. (1963 год).pdf | page 2 | lines 1-12]\n"
        "КНИГА ДЛЯ ЧТЕНИЯ В I КЛАССЕ НАЧАЛЬНОЙ ШКОЛЫ"
    )

    refined = rag_core.refine_answer_with_context_evidence(question, answer, context)

    assert "1 класса" in refined
    assert "первого класса" in refined
    assert "в первом классе" in refined


def test_refine_answer_with_context_evidence_expands_logic_scope_list():
    question = "Где, согласно учебнику логики, необходимо правильное мышление?"
    answer = "Правильное мышление необходимо везде."
    context = (
        "[source: Логика | page 1 | lines 1-11]\n"
        "В труде и в быту, в учебной и общественной работе, в научном трактате и в школьном сочинении — везде и всегда необходимо правильное мышление."
    )

    refined = rag_core.refine_answer_with_context_evidence(question, answer, context)

    assert "в труде" in refined
    assert "в быту" in refined
    assert "в учебной и в общественной работе" in refined


def test_annotate_document_line_ranges_and_context_preview():
    source_doc = FakeDoc(
        "первая строка\nвторая строка\nтретья строка\nчетвертая строка",
        "/hostfs/c/Temp/PDF/notes.txt",
    )
    split_doc = FakeDoc(
        "вторая строка\nтретья строка",
        "/hostfs/c/Temp/PDF/notes.txt",
    )
    split_doc.metadata["start_index"] = len("первая строка\n")

    rag_core.annotate_document_line_ranges([source_doc], [split_doc])
    preview = rag_core.build_context_preview_from_docs([split_doc])

    assert split_doc.metadata["line_start"] == 2
    assert split_doc.metadata["line_end"] == 3
    assert "C:\\Temp\\PDF\\notes.txt" in preview
    assert "lines 2-3" in preview


def test_refine_answer_with_context_evidence_prefers_chapter_heading():
    question = "О чем глава I в учебнике логики Виноградова?"
    answer = "Глава I рассказывает о логике."
    context = (
        "[source: Логика | page 1 | lines 1-8]\n"
        "ГЛАВА I\n"
        "ПРЕДМЕТ И ЗАДАЧИ НАУКИ ЛОГИКИ\n"
        "Логика мышления и наука логики."
    )

    refined = rag_core.refine_answer_with_context_evidence(question, answer, context)

    assert "Глава I называется" in refined
    assert "Предмет и задачи науки логики" in refined


def test_refine_answer_with_context_evidence_normalizes_author_name():
    question = "Кто автор учебника «История СССР. Часть 3»?"
    answer = "Автор учебника — А.М. Панкратова."
    context = (
        "[source: История СССР. Часть 3. 10 класс. (А.М. Пенкратова. 1952 год).pdf | page 1 | lines 1-12]\n"
        "А.М. Пенкратова\n"
        "История СССР\n"
        "Часть 3"
    )

    refined = rag_core.refine_answer_with_context_evidence(question, answer, context)

    assert "Автор издания — А. М. Пенкратова." in refined


def test_refine_answer_with_context_evidence_keeps_author_priority_over_class():
    question = "Кто автор дидактических материалов по математике для 5 класса?"
    answer = (
        "Издание предназначено для 5 класса (пятого класса).\n\n"
        "С. Чесноков.\n\n"
        "Чесноков."
    )
    context = (
        "[source: Дидактические материалы | page 1 | lines 1-4]\n"
        "Заголовок файла: Дидактические материалы по математике для 5 класса средней школы. А.С. Чесноков. 1990 год.\n"
        "Файл: Дидактические материалы по математике для 5 класса средней школы. (А.С. Чесноков. 1990 год).pdf.\n"
        "Год издания: 1990.\n"
        "Автор или редактор: А.С. Чесноков."
    )

    refined = rag_core.refine_answer_with_context_evidence(question, answer, context)

    assert refined.startswith("Автор издания — А. С. Чесноков.")
    assert "Издание предназначено для 5 класса" not in refined.split("\n\n", 1)[0]


def test_retrieve_relevant_docs_with_debug_returns_scores():
    logic_doc = FakeDoc(
        "ГЛАВА I\nПРЕДМЕТ И ЗАДАЧИ НАУКИ ЛОГИКИ",
        "/hostfs/c/Temp/PDF/Логика С.Н. Виноградов. 1954 год) - crop.pdf",
        page=0,
    )
    unrelated_doc = FakeDoc(
        "В учебнике русского языка перечислены предметы в классе.",
        "/hostfs/c/Temp/PDF/Русский язык. Учебник для первого класса.pdf",
        page=10,
    )
    store = FakeVectorDb(
        {"logic": logic_doc, "ru": unrelated_doc},
        vector_results=[(unrelated_doc, 0.12)],
    )

    docs, debug_rows = rag_core.retrieve_relevant_docs_with_debug(
        store,
        "О чем глава I в учебнике логики Виноградова?",
        2,
    )

    assert docs[0].metadata["source"].endswith("Логика С.Н. Виноградов. 1954 год) - crop.pdf")
    assert debug_rows[0]["rank"] == 1
    assert "page 1" in debug_rows[0]["source_label"]
    assert debug_rows[0]["score"] > 0


def test_retrieve_relevant_docs_prefers_matching_edition_year():
    edition_1959 = FakeDoc(
        "Букварь для первого класса. Издание 1959 года.",
        "/hostfs/c/Temp/PDF/Букварь. 1 класс. (1959 год).pdf",
        page=0,
    )
    edition_1987 = FakeDoc(
        "Букварь для первого класса. Издание 1987 года.",
        "/hostfs/c/Temp/PDF/Букварь. 1 класс. (1987 год).pdf",
        page=0,
    )
    store = FakeVectorDb(
        {"old": edition_1959, "new": edition_1987},
        vector_results=[(edition_1959, 0.11)],
    )

    docs = rag_core.retrieve_relevant_docs(
        store,
        "Для какого класса букварь 1987 года?",
        1,
    )

    assert docs[0].metadata["source"].endswith("Букварь. 1 класс. (1987 год).pdf")


def test_retrieve_relevant_docs_prefers_full_materials_title():
    materials_doc = FakeDoc(
        "Дидактические материалы по математике для 5 класса средней школы.",
        "/hostfs/c/Temp/PDF/Дидактические материалы по математике для 5 класса средней школы. (А.С. Чесноков. 1990 год).pdf",
        page=0,
    )
    geography_doc = FakeDoc(
        "Учебник географии для средней школы. 8 класс.",
        "/hostfs/c/Temp/PDF/География. 8 класс. ( Н.Н. Баранский. 1933 год).pdf",
        page=0,
    )
    store = FakeVectorDb(
        {"geo": geography_doc, "math": materials_doc},
        vector_results=[(geography_doc, 0.09)],
    )

    docs = rag_core.retrieve_relevant_docs(
        store,
        "Кто автор дидактических материалов по математике для 5 класса?",
        1,
    )

    assert docs[0].metadata["source"].endswith(
        "Дидактические материалы по математике для 5 класса средней школы. (А.С. Чесноков. 1990 год).pdf"
    )
