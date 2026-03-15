# app.py — LocalRAG fully functional with Ollama + FAISS + Gradio UI
# Env (опционально):
#   LOCALRAG_DOCS_DIR=/path/to/docs
#   LOCALRAG_EMBED_MODEL=nomic-embed-text
#   OLLAMA_HOST=http://localhost:11434

from __future__ import annotations

import json
import logging
import os
import shutil
import threading
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import gradio as gr
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

# ---------- Paths / Config ----------
BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "index" / "faiss"
DOCS_DIR = Path(os.environ.get("LOCALRAG_DOCS_DIR", str(BASE_DIR / "docs")))
EMBED_MODEL = os.environ.get("LOCALRAG_EMBED_MODEL", "nomic-embed-text")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

SUPPORTED_EXTS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".py",
    ".js",
    ".json",
    ".csv",
    ".yml",
    ".yaml",
}

# ---------- Global state ----------
_vs: FAISS | None = None
_index_lock = threading.Lock()
_status_msg = "Loading index…"
current_language = "en"
translations: Dict[str, str] = {}
default_translations = {
    "title": "LocalRAG",
    "current_folder": "Current documents folder",
    "refresh": "Refresh status",
    "reindex": "Reindex documents",
    "topk": "Documents to retrieve (top-k)",
    "temperature": "Temperature",
    "model": "LLM model (Ollama)",
    "your_question": "Your question",
    "ask": "Ask",
    "answer": "Answer",
    "retrieved_context": "Retrieved context",
    "index_ready": "Index ready. {chunks} chunks from {files} files.",
    "index_built": "Reindex finished. {chunks} chunks from {files} files.",
    "index_building": "Indexing…",
    "no_ollama": "Ollama is not reachable at {host}. Start Ollama first.",
    "reindex_started": "Reindex started…",
}


# ---------- i18n ----------
def load_translations(lang: str) -> Dict[str, str]:
    fp = BASE_DIR / "locales" / f"{lang}.json"
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default_translations


def t(key: str, **kwargs) -> str:
    s = translations.get(key, default_translations.get(key, key))
    return s.format(**kwargs) if kwargs else s


# ---------- Embeddings via Ollama ----------
class OllamaEmbeddings:
    def __init__(self, model: str = EMBED_MODEL, host: str = OLLAMA_HOST):
        self.model = model
        self.host = host

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_one(text)

    def _embed_one(self, text: str) -> List[float]:
        resp = requests.post(
            f"{self.host}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


# ---------- Loading / Splitting ----------
def _make_loader_for_ext(path: Path):
    ext = path.suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(str(path))
    if ext == ".docx":
        return Docx2txtLoader(str(path))
    return TextLoader(str(path), encoding="utf-8")


def load_documents(dirpath: Path) -> List[Document]:
    docs: List[Document] = []
    if not dirpath.exists():
        return docs
    for p in dirpath.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            try:
                docs.extend(_make_loader_for_ext(p).load())
            except Exception as e:
                logging.warning("Skip %s: %s", p, e)
    return docs


# ---------- Index ----------
def build_index(dirpath: Path) -> Tuple[FAISS, int, int]:
    docs = load_documents(dirpath)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000 if docs else 400, chunk_overlap=200 if docs else 50
    )
    chunks = splitter.split_documents(
        docs
        or [Document(page_content="LocalRAG empty index", metadata={"source": "none"})]
    )

    emb = OllamaEmbeddings()
    vs = FAISS.from_documents(chunks, emb)
    INDEX_DIR.parent.mkdir(parents=True, exist_ok=True)
    vs.save_local(str(INDEX_DIR))
    files_count = len({c.metadata.get("source", "unknown") for c in chunks})
    return vs, len(chunks), files_count


def load_index() -> FAISS | None:
    if not INDEX_DIR.exists():
        return None
    emb = OllamaEmbeddings()
    try:
        return FAISS.load_local(
            str(INDEX_DIR), emb, allow_dangerous_deserialization=True
        )
    except Exception as e:
        logging.error("Failed to load index: %s", e)
        return None


def ensure_index_async():
    def _run():
        global _vs, _status_msg
        with _index_lock:
            _status_msg = t("index_building")
            _vs, chunks, files = build_index(DOCS_DIR)
            _status_msg = t("index_ready", chunks=chunks, files=files)

    threading.Thread(target=_run, daemon=True).start()


# ---------- Ollama chat ----------
def ollama_list_models() -> List[str]:
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def ollama_chat(model: str, messages: List[Dict], temperature: float = 0.2) -> str:
    r = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=600,
    )
    r.raise_for_status()
    j = r.json()
    if "message" in j and "content" in j["message"]:
        return j["message"]["content"]
    if "messages" in j and j["messages"]:
        return j["messages"][-1].get("content", "")
    return j.get("response", "")


# ---------- Handlers for UI ----------
def backend_refresh_status() -> Tuple[str, List[str], str | None]:
    global _vs, _status_msg
    models = ollama_list_models()
    if not models:
        status = f"{t('current_folder')}: `{DOCS_DIR}`\n\n> " + t(
            "no_ollama", host=OLLAMA_HOST
        )
        return status, [], None

    if _vs is None and not _index_lock.locked():
        ensure_index_async()

    status = f"{t('current_folder')}: `{DOCS_DIR}`\n\n{_status_msg}"
    default = next((m for m in models if "qwen" in m or "llama" in m), models[0])
    return status, models, default


def backend_reindex_documents() -> str:
    if _index_lock.locked():
        return _status_msg

    def _run():
        global _vs, _status_msg
        with _index_lock:
            _status_msg = t("index_building")
            if INDEX_DIR.exists():
                shutil.rmtree(INDEX_DIR)
            _vs, chunks, files = build_index(DOCS_DIR)
            _status_msg = t("index_built", chunks=chunks, files=files)

    threading.Thread(target=_run, daemon=True).start()
    return t("reindex_started")


def backend_answer(
    question: str, top_k: int, temperature: float, model_name: str
) -> Tuple[str, str]:
    global _vs
    q = (question or "").strip()
    if not q:
        return "Enter a question.", ""
    if _vs is None:
        _vs = load_index()
        if _vs is None:
            return "Index is not ready yet.", ""

    docs = _vs.similarity_search(q, k=max(1, int(top_k)))
    ctx_lines, ctx_text = [], []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "")
        snippet = d.page_content[:300].replace("\n", " ").strip()
        ctx_lines.append(f"{i}. **{Path(src).name}** — {snippet}…")
        ctx_text.append(f"[{i}] {d.page_content}\n(Source: {src})")

    system = (
        "You are a precise assistant working with retrieved snippets. "
        "Answer strictly from the provided context. "
        "If the answer is not in the context, say it is not available."
    )
    user_prompt = f"Question:\n{q}\n\nContext:\n" + "\n\n".join(ctx_text)

    try:
        answer = ollama_chat(
            model_name,
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            float(temperature),
        )
    except Exception as e:
        answer = f"Ollama error: {e}"
    return answer, "\n".join(ctx_lines)


# ---------- Language ----------
def update_language(lang: str):
    global current_language, translations
    current_language = lang
    translations = load_translations(lang)
    return gr.update()


def apply_i18n(c: Dict[str, gr.Component]):
    c["refresh_btn"].value = t("refresh")
    c["reindex_btn"].value = t("reindex")
    c["topk_slider"].label = t("topk")
    c["temp_slider"].label = t("temperature")
    c["model_dd"].label = t("model")
    c["question_tb"].label = t("your_question")
    c["ask_btn"].value = t("ask")
    c["answer_tb"].label = t("answer")
    c["ctx_acc"].label = t("retrieved_context")
    c["status_md"].value = f"{t('current_folder')}: `{DOCS_DIR}`\n\n{_status_msg}"


# ---------- UI wiring ----------
from ui import create_interface  # noqa: E402


def bind_callbacks(demo: gr.Blocks, c: Dict[str, gr.Component]):
    # Refresh
    def on_refresh():
        status, models, default = backend_refresh_status()
        return gr.update(value=status), gr.update(choices=models, value=default)

    c["refresh_btn"].click(fn=on_refresh, outputs=[c["status_md"], c["model_dd"]])

    # Reindex
    c["reindex_btn"].click(fn=backend_reindex_documents, outputs=[c["status_md"]])

    # Ask
    def on_ask(q, k, t, m):
        return backend_answer(q, int(k), float(t), m or "")

    c["ask_btn"].click(
        fn=on_ask,
        inputs=[c["question_tb"], c["topk_slider"], c["temp_slider"], c["model_dd"]],
        outputs=[c["answer_tb"], c["ctx_md"]],
    )

    # Languages (ui.py v2: кнопки lang_XX_btn присутствуют)
    for code, key in [
        ("en", "lang_en_btn"),
        ("ru", "lang_ru_btn"),
        ("nl", "lang_nl_btn"),
        ("zh", "lang_zh_btn"),
        ("he", "lang_he_btn"),
    ]:
        if key in c:
            c[key].click(fn=lambda _=None, cc=code: update_language(cc)).then(
                fn=lambda: (apply_i18n(c),), outputs=[]
            )

    # Init
    translations.update(load_translations(current_language))
    apply_i18n(c)
    status, models, default = backend_refresh_status()
    c["status_md"].value = status
    c["model_dd"].choices = models
    c["model_dd"].value = default


def main():
    demo, controls = create_interface()
    bind_callbacks(demo, controls)
    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)


if __name__ == "__main__":
    main()
