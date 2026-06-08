import json
import logging
import os
import re
import threading
import importlib
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

import gradio as gr
import requests
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from ui import create_interface as ui_create_interface  # type: ignore


# -------------------- Paths / Config --------------------
BASE_DIR = Path(__file__).resolve().parent
DOCS_PATH_RAW = os.environ.get("DOCS_PATH") or os.environ.get("PDF_PATH") or "./files"
INDEX_PATH = Path(os.environ.get("INDEX_PATH", "./vectorstore")).resolve()
HOST_DOCS_PATH_RAW = os.environ.get("HOST_DOCS_PATH") or ""
HOST_FS_ROOT = os.environ.get("HOST_FS_ROOT", "C:/").strip().replace("\\", "/")
HOST_FS_MOUNT = Path(os.environ.get("HOST_FS_MOUNT", "/hostfs/c")).resolve()
APP_STATE_FILE = INDEX_PATH / "app_state.json"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
DEFAULT_LLM_MODEL = "qwen3.5:9b"
DEFAULT_EMBED_MODEL = "intfloat/multilingual-e5-large"

LLM_MODEL_NAME = (
    os.environ.get("LLM_MODEL")
    or os.environ.get("OLLAMA_MODEL")
    or os.environ.get("MODEL_NAME")
    or DEFAULT_LLM_MODEL
)
MODEL_NAME = os.environ.get("MODEL_NAME") or LLM_MODEL_NAME
DEFAULT_MODEL = LLM_MODEL_NAME
MODEL_PREFERENCE_ORDER = [
    LLM_MODEL_NAME,
    DEFAULT_LLM_MODEL,
    "qwen3:14b",
    "gemma3:12b",
    "qwen2.5:14b",
    "aya-expanse:8b",
    "qwen2.5:7b-instruct",
    "phi3:mini",
]

EMBED_MODEL_NAME = (
    os.environ.get("EMBED_MODEL")
    or os.environ.get("EMBEDDINGS_MODEL_NAME")
    or DEFAULT_EMBED_MODEL
)

DEFAULT_TOP_K = int(os.environ.get("TOP_K", "8"))
MAX_CONTEXT_DISPLAY_CHARS = int(os.environ.get("MAX_CONTEXT_DISPLAY_CHARS", "2000"))
NON_THINKING_MODEL_PREFIXES = ("qwen3",)
MIN_VECTOR_CANDIDATES = int(os.environ.get("MIN_VECTOR_CANDIDATES", "40"))
MAX_VECTOR_CANDIDATES = int(os.environ.get("MAX_VECTOR_CANDIDATES", "120"))
MIN_LEXICAL_TERM_LEN = int(os.environ.get("MIN_LEXICAL_TERM_LEN", "2"))
LOW_SIGNAL_PDF_QUALITY_THRESHOLD = float(
    os.environ.get("LOW_SIGNAL_PDF_QUALITY_THRESHOLD", "0.33")
)
DOC_SCAN_LIMIT = int(os.environ.get("DOC_SCAN_LIMIT", "12000"))
QUERY_TOKEN_RE = re.compile(
    r"[0-9A-Za-z"
    r"\u0400-\u04ff"
    r"\u0590-\u05ff"
    r"\u4e00-\u9fff]+"
)
QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "de",
    "do",
    "does",
    "een",
    "en",
    "het",
    "how",
    "in",
    "is",
    "li",
    "na",
    "naar",
    "no",
    "of",
    "on",
    "or",
    "the",
    "to",
    "waar",
    "wat",
    "when",
    "where",
    "who",
    "why",
    "в",
    "во",
    "где",
    "до",
    "для",
    "и",
    "из",
    "или",
    "как",
    "какая",
    "какие",
    "какой",
    "когда",
    "кто",
    "куда",
    "ли",
    "на",
    "но",
    "о",
    "об",
    "от",
    "по",
    "почему",
    "с",
    "что",
    "это",
}
SOURCE_MATCH_STOPWORDS = QUERY_STOPWORDS | {
    "автор",
    "автора",
    "глава",
    "главы",
    "году",
    "год",
    "класс",
    "класса",
    "классе",
    "книги",
    "книга",
    "пособие",
    "пособия",
    "предназначен",
    "предназначена",
    "предназначено",
    "согласно",
    "средней",
    "учебник",
    "учебника",
    "учебное",
    "учителя",
    "школа",
    "школы",
}
SOURCE_FOCUS_STOPWORDS = SOURCE_MATCH_STOPWORDS | {
    "??????",
    "?????",
    "??????",
    "?????",
    "????",
    "????????????",
    "????????????",
    "?????",
    "????????",
}
QUOTED_SPAN_RE = re.compile(r"[«\"](?P<value>[^«»\"]{2,160})[»\"]")
SOURCE_HEADER_YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
SOURCE_HEADER_CLASS_RE = re.compile(r"\b(\d+)\s*класс\b", re.IGNORECASE)
SOURCE_HEADER_PART_RE = re.compile(r"\bчасть\s+([ivxlcdm\d]+)\b", re.IGNORECASE)
SUPPORTED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx",
    ".md",
    ".htm",
    ".html",
    ".py",
    ".js",
    ".json",
    ".csv",
    ".yml",
    ".yaml",
}

# -------------------- i18n --------------------


def load_translations(lang: str) -> Dict[str, str]:
    locale_file = BASE_DIR / "locales" / f"{lang}.json"
    if locale_file.exists():
        with open(locale_file, "r", encoding="utf-8") as f:
            return json.load(f)
    with open(BASE_DIR / "locales" / "en.json", "r", encoding="utf-8") as f:
        return json.load(f)


translations = load_translations("en")
current_language = "en"

# Localized status handling
index_status_code = "loading"  # loading, ready_loaded, indexing, build_failed, ready_ask, no_documents, saved_failed, changes_detected
index_status_params: Dict[str, str] = {}


def _normalize_host_path(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _display_host_path(value: str) -> str:
    normalized = _normalize_host_path(value)
    windows_match = re.match(r"^([A-Za-z]):/(.*)$", normalized)
    if not windows_match:
        return normalized
    remainder = windows_match.group(2).replace("/", "\\")
    if remainder:
        return f"{windows_match.group(1).upper()}:\\{remainder}"
    return f"{windows_match.group(1).upper()}:\\"


def resolve_docs_paths(raw_value: str | None = None) -> tuple[Path, str]:
    candidate = _normalize_host_path(raw_value or HOST_DOCS_PATH_RAW or DOCS_PATH_RAW)
    windows_match = re.match(r"^([A-Za-z]):/(.*)$", candidate)
    if windows_match and HOST_FS_ROOT:
        configured_root = _normalize_host_path(HOST_FS_ROOT).rstrip("/")
        candidate_root = f"{windows_match.group(1).upper()}:"
        if configured_root.upper().startswith(candidate_root) and HOST_FS_MOUNT.exists():
            remainder = [part for part in windows_match.group(2).split("/") if part]
            container_path = HOST_FS_MOUNT.joinpath(*remainder)
            return container_path.resolve(), _display_host_path(candidate)
    return Path(candidate).expanduser().resolve(), _display_host_path(candidate)


def load_runtime_state() -> Dict[str, str]:
    if not APP_STATE_FILE.exists():
        return {}
    try:
        data = json.loads(APP_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        logging.warning("Failed to read runtime state from %s", APP_STATE_FILE)
        return {}
    return data if isinstance(data, dict) else {}


def save_runtime_state() -> None:
    APP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "docs_path_display": _current_docs_path_display,
        "embedding_model": _current_embed_model_name,
    }
    APP_STATE_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


_initial_state = load_runtime_state()
_initial_docs_value = str(
    _initial_state.get("docs_path_display") or HOST_DOCS_PATH_RAW or DOCS_PATH_RAW
)
DOCS_PATH, DOCS_PATH_DISPLAY = resolve_docs_paths(_initial_docs_value)
_current_embed_model_name = str(_initial_state.get("embedding_model") or EMBED_MODEL_NAME).strip()
_current_docs_path = DOCS_PATH
_current_docs_path_display = DOCS_PATH_DISPLAY


def t(key: str) -> str:
    return translations.get(key, key)


def set_index_status(code: str, **params):
    global index_status_code, index_status_params
    index_status_code = code
    index_status_params = params


def get_docs_path() -> Path:
    return _current_docs_path


def get_docs_path_display() -> str:
    return _current_docs_path_display


def get_default_docs_path_display() -> str:
    return _display_host_path(HOST_DOCS_PATH_RAW or DOCS_PATH_RAW)


def get_embedding_model_name() -> str:
    return _current_embed_model_name


def get_default_embedding_model_name() -> str:
    return EMBED_MODEL_NAME


def get_embedding_runtime_info() -> Dict[str, object]:
    info: Dict[str, object] = {
        "device": "cpu",
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_device_name": "",
        "model_loaded": False,
        "model_device": "",
    }
    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        info["cuda_available"] = cuda_available
        info["cuda_device_count"] = int(torch.cuda.device_count())
        if cuda_available:
            info["device"] = "cuda"
            info["cuda_device_name"] = str(torch.cuda.get_device_name(0))
        model_device = get_loaded_embedding_device()
        if model_device:
            info["model_loaded"] = True
            info["model_device"] = model_device
            if str(model_device).startswith("cuda"):
                info["device"] = "cuda"
            else:
                info["device"] = "cpu"
    except Exception:
        return info
    return info


def import_nvml_module():
    try:
        return importlib.import_module("pynvml")
    except ImportError:
        return None


def get_loaded_embedding_device() -> str:
    with embeddings_lock:
        cached_embeddings = _cached_embeddings
    if cached_embeddings is None:
        return ""

    client = getattr(cached_embeddings, "_client", None) or getattr(
        cached_embeddings, "client", None
    )
    if client is None:
        return ""

    try:
        first_param = next(client.parameters())
        return str(first_param.device)
    except Exception:
        pass

    target_device = getattr(client, "_target_device", None)
    if target_device is None:
        return ""
    return str(target_device)


def clear_persisted_index() -> None:
    for filename in ("index.faiss", "index.pkl"):
        target = INDEX_PATH / filename
        try:
            target.unlink()
        except FileNotFoundError:
            continue


def clear_cached_embeddings() -> None:
    global _cached_embeddings
    with embeddings_lock:
        _cached_embeddings = None


def set_docs_path(raw_value: str) -> str:
    global _current_docs_path, _current_docs_path_display, vectordb, indexed_file_count, needs_reindex

    new_path, new_display = resolve_docs_paths(raw_value)
    new_path.mkdir(parents=True, exist_ok=True)
    clear_persisted_index()
    _doc_feature_cache.clear()
    with index_lock:
        _current_docs_path = new_path
        _current_docs_path_display = new_display
        vectordb = None
        indexed_file_count = 0
        needs_reindex = True
        pending_changes.clear()
        set_index_status("changes_detected", preview=new_display)
    save_runtime_state()
    return new_display


def set_embedding_model(raw_value: str) -> str:
    global _current_embed_model_name, vectordb, indexed_file_count, needs_reindex

    model_name = str(raw_value or "").strip()
    if not model_name:
        raise ValueError("Embedding model name is required.")
    if model_name == _current_embed_model_name:
        return model_name

    clear_persisted_index()
    clear_cached_embeddings()
    _doc_feature_cache.clear()
    with index_lock:
        _current_embed_model_name = model_name
        vectordb = None
        indexed_file_count = 0
        needs_reindex = True
        pending_changes.clear()
        set_index_status("changes_detected", preview=model_name)
    save_runtime_state()
    return model_name


def _container_path_to_display(path: Path) -> str:
    resolved = path.resolve()
    host_mount = HOST_FS_MOUNT.resolve()
    try:
        relative = resolved.relative_to(host_mount)
    except ValueError:
        return str(resolved)
    root_display = _display_host_path(HOST_FS_ROOT)
    if not relative.parts:
        return root_display
    suffix = "\\".join(relative.parts)
    if root_display.endswith("\\"):
        return f"{root_display}{suffix}"
    return f"{root_display}\\{suffix}"


def list_browsable_directories(raw_value: str | None = None) -> Dict[str, object]:
    root_path, root_display = resolve_docs_paths(HOST_FS_ROOT or DOCS_PATH_RAW)
    root_path = root_path.resolve()
    requested_path, requested_display = resolve_docs_paths(raw_value or root_display)
    candidate = requested_path.resolve()

    try:
        candidate.relative_to(root_path)
    except ValueError:
        candidate = root_path

    while not candidate.exists() and candidate != root_path:
        candidate = candidate.parent

    if not candidate.exists():
        candidate = root_path
    if candidate.is_file():
        candidate = candidate.parent

    try:
        candidate.relative_to(root_path)
    except ValueError:
        candidate = root_path

    directories = []
    for item in sorted(candidate.iterdir(), key=lambda entry: entry.name.lower()):
        if not item.is_dir():
            continue
        directories.append(
            {
                "name": item.name,
                "path": _container_path_to_display(item),
            }
        )

    parent_path = None
    if candidate != root_path:
        parent_path = _container_path_to_display(candidate.parent)

    return {
        "root_path": root_display,
        "requested_path": requested_display,
        "path": _container_path_to_display(candidate),
        "parent_path": parent_path,
        "directories": directories,
    }


def get_localized_status() -> str:
    code = index_status_code
    params = index_status_params
    if code == "loading":
        return t("status_loading")
    if code == "ready_loaded":
        return t("status_ready_loaded")
    if code == "indexing":
        return t("status_indexing")
    if code == "build_failed":
        return t("status_build_failed").format(error=params.get("error", ""))
    if code == "ready_ask":
        return t("status_ready_ask")
    if code == "no_documents":
        return t("status_no_documents")
    if code == "saved_failed":
        return t("status_saved_failed")
    if code == "changes_detected":
        base = t("status_changes_detected")
        preview = params.get("preview")
        if preview:
            base += "\n\n" + t("status_pending_prefix").format(preview=preview)
        return base
    return code


def get_index_status_meta() -> tuple[str, Dict[str, str]]:
    with index_lock:
        return index_status_code, dict(index_status_params)


# -------------------- Setup --------------------
get_docs_path().mkdir(parents=True, exist_ok=True)
INDEX_PATH.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(BASE_DIR / "localrag.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

index_lock = threading.Lock()
embeddings_lock = threading.Lock()
set_index_status("loading")
needs_reindex = False
pending_changes: List[str] = []
_cached_embeddings = None
vectordb: FAISS | None = None
indexed_file_count = 0
_doc_feature_cache: Dict[str, Dict[str, object]] = {}


def _normalize_source_path(value) -> str | None:
    if not value:
        return None
    try:
        return str(Path(value).resolve())
    except Exception:
        try:
            return str(Path(str(value)).resolve())
        except Exception:
            try:
                return str(value)
            except Exception:
                return None


def _count_sources_from_vectordb(store: FAISS | None) -> int:
    if store is None:
        return 0
    docstore = getattr(store, "docstore", None)
    if docstore is None:
        return 0
    documents = []
    if hasattr(docstore, "_dict"):
        documents = list(docstore._dict.values())
    else:
        index_map = getattr(store, "index_to_docstore_id", {})
        if isinstance(index_map, dict):
            doc_ids = index_map.values()
        else:
            doc_ids = index_map or []
        for doc_id in doc_ids:
            if doc_id is None:
                continue
            try:
                document = docstore.search(doc_id)
            except Exception:
                continue
            if document is not None:
                documents.append(document)
    sources = set()
    for document in documents:
        metadata = getattr(document, "metadata", {}) or {}
        if not isinstance(metadata, dict):
            continue
        source = metadata.get("source")
        normalized = _normalize_source_path(source)
        if normalized:
            sources.add(normalized)
    return len(sources)


def _document_cache_key(document) -> str:
    metadata = getattr(document, "metadata", {}) or {}
    source = str(metadata.get("source") or "")
    page = metadata.get("page")
    return f"{source}|{page}|{str(document.page_content or '')[:160]}"


def _document_source_key(document) -> str:
    metadata = getattr(document, "metadata", {}) or {}
    source = _normalize_source_path(metadata.get("source")) or str(metadata.get("source") or "")
    page = metadata.get("page")
    return f"{source}|{page}"


def _count_lines_in_text(text: str) -> int:
    if not text:
        return 1
    return text.count("\n") + 1


def _compute_line_range(source_text: str, start_index: int, chunk_text: str) -> tuple[int, int]:
    safe_source = str(source_text or "")
    safe_chunk = str(chunk_text or "")
    safe_start = max(0, min(int(start_index or 0), len(safe_source)))
    safe_end = min(len(safe_source), safe_start + len(safe_chunk))
    line_start = safe_source.count("\n", 0, safe_start) + 1
    line_end = safe_source.count("\n", 0, safe_end) + 1
    return line_start, max(line_start, line_end)


def annotate_document_line_ranges(source_docs: List[object], split_docs: List[object]) -> None:
    source_texts = {
        _document_source_key(document): str(document.page_content or "")
        for document in source_docs
    }
    for document in split_docs:
        metadata = getattr(document, "metadata", {}) or {}
        source_text = source_texts.get(_document_source_key(document))
        if source_text is None:
            continue
        start_index = metadata.get("start_index")
        if isinstance(start_index, int):
            line_start, line_end = _compute_line_range(
                source_text, start_index, str(document.page_content or "")
            )
        else:
            line_start, line_end = 1, _count_lines_in_text(str(document.page_content or ""))
        metadata["line_start"] = line_start
        metadata["line_end"] = line_end


def format_document_source_label(document) -> str:
    metadata = getattr(document, "metadata", {}) or {}
    source = str(metadata.get("source") or "")
    if source:
        try:
            source_display = _container_path_to_display(Path(source))
        except Exception:
            source_display = source
    else:
        source_display = "[unknown source]"

    parts = [source_display]
    page = metadata.get("page")
    if isinstance(page, int):
        parts.append(f"page {page + 1}")
    line_start = metadata.get("line_start")
    line_end = metadata.get("line_end")
    if isinstance(line_start, int) and isinstance(line_end, int):
        if line_start == line_end:
            parts.append(f"line {line_start}")
        else:
            parts.append(f"lines {line_start}-{line_end}")
    return "[" + " | ".join(parts) + "]"


def normalize_match_token(token: str) -> str:
    normalized = str(token or "").strip().lower()
    if len(normalized) < 5:
        return normalized
    if not re.search(r"[\u0400-\u04ff]", normalized):
        return normalized
    for suffix in (
        "иями",
        "ями",
        "ами",
        "ией",
        "ией",
        "ией",
        "ого",
        "ему",
        "ому",
        "ими",
        "ыми",
        "иях",
        "ях",
        "ах",
        "ию",
        "ью",
        "ия",
        "ья",
        "ий",
        "ый",
        "ой",
        "ей",
        "ам",
        "ям",
        "ом",
        "ем",
        "ов",
        "ев",
        "ую",
        "юю",
        "ая",
        "яя",
        "ое",
        "ее",
        "у",
        "ю",
        "а",
        "я",
        "е",
        "ы",
        "и",
        "о",
    ):
        if normalized.endswith(suffix) and len(normalized) - len(suffix) >= 4:
            return normalized[: -len(suffix)]
    return normalized


def normalize_match_text(text: str) -> str:
    normalized_tokens = [
        normalize_match_token(token)
        for token in QUERY_TOKEN_RE.findall(str(text or "").lower())
    ]
    return " ".join(token for token in normalized_tokens if token)


def extract_query_terms(text: str) -> List[str]:
    terms: List[str] = []
    for token in QUERY_TOKEN_RE.findall(str(text or "").lower()):
        normalized = normalize_match_token(token)
        if len(normalized) < MIN_LEXICAL_TERM_LEN:
            continue
        if normalized in QUERY_STOPWORDS:
            continue
        if normalized not in terms:
            terms.append(normalized)
    return terms


def extract_source_match_terms(text: str) -> List[str]:
    terms: List[str] = []
    for token in QUERY_TOKEN_RE.findall(str(text or "").lower()):
        normalized = normalize_match_token(token)
        if not normalized:
            continue
        if normalized in SOURCE_MATCH_STOPWORDS:
            continue
        if normalized.isdigit() and len(normalized) < 4:
            continue
        if len(normalized) < 3 and not normalized.isdigit():
            continue
        if normalized not in terms:
            terms.append(normalized)
    return terms


def extract_quoted_query_phrases(text: str) -> List[str]:
    phrases: List[str] = []
    for match in QUOTED_SPAN_RE.finditer(str(text or "")):
        normalized = normalize_match_text(match.group("value"))
        if len(normalized) < 5:
            continue
        if normalized not in phrases:
            phrases.append(normalized)
    return phrases


def extract_source_focus_terms(text: str) -> List[str]:
    terms: List[str] = []
    for token in QUERY_TOKEN_RE.findall(str(text or "").lower()):
        normalized = normalize_match_token(token)
        if not normalized:
            continue
        if normalized in SOURCE_FOCUS_STOPWORDS:
            continue
        if normalized.isdigit() and len(normalized) < 2:
            continue
        if len(normalized) < 4 and not normalized.isdigit():
            continue
        if normalized not in terms:
            terms.append(normalized)
    return terms


def extract_year_terms(text: str) -> List[str]:
    years: List[str] = []
    for match in SOURCE_HEADER_YEAR_RE.finditer(str(text or "")):
        year = match.group(1)
        if year not in years:
            years.append(year)
    return years


def extract_class_terms(text: str) -> List[str]:
    values: List[str] = []
    normalized = str(text or "").lower().replace("\u2013", "-")
    for match in re.finditer(r"\b(\d+(?:\s*-\s*\d+)?)\s*класс\w*\b", normalized):
        for value in re.split(r"\s*-\s*", match.group(1)):
            cleaned = value.strip()
            if cleaned and cleaned not in values:
                values.append(cleaned)
    return values


def extract_part_terms(text: str) -> List[str]:
    values: List[str] = []
    normalized = str(text or "").lower()
    for match in re.finditer(r"\bчаст[ьи]\s+([ivxlcdm\d]+)\b", normalized, re.IGNORECASE):
        cleaned = match.group(1).upper()
        if cleaned and cleaned not in values:
            values.append(cleaned)
    return values


def compute_text_quality_score(text: str) -> float:
    normalized = " ".join(str(text or "").split())
    if not normalized:
        return 0.0

    total = len(normalized)
    letters = sum(ch.isalpha() for ch in normalized)
    digits = sum(ch.isdigit() for ch in normalized)
    punctuation = sum(
        1 for ch in normalized if (not ch.isalnum()) and (not ch.isspace())
    )
    tokens = QUERY_TOKEN_RE.findall(normalized)
    single_char_tokens = sum(1 for token in tokens if len(token) == 1)
    avg_token_length = (
        sum(len(token) for token in tokens) / len(tokens) if tokens else 0.0
    )

    score = 0.0
    letters_ratio = letters / total
    digits_ratio = digits / total
    punctuation_ratio = punctuation / total
    single_char_ratio = (
        single_char_tokens / len(tokens) if tokens else 1.0
    )

    if letters_ratio >= 0.56:
        score += 0.34
    elif letters_ratio >= 0.42:
        score += 0.20

    if digits_ratio <= 0.18:
        score += 0.10
    elif digits_ratio >= 0.30:
        score -= 0.10

    if punctuation_ratio <= 0.16:
        score += 0.14
    elif punctuation_ratio >= 0.28:
        score -= 0.18

    if len(tokens) >= 12:
        score += 0.16
    elif len(tokens) >= 8:
        score += 0.08

    if avg_token_length >= 3.4:
        score += 0.16
    elif avg_token_length >= 2.6:
        score += 0.08
    else:
        score -= 0.08

    if single_char_ratio <= 0.34:
        score += 0.10
    elif single_char_ratio >= 0.55:
        score -= 0.12

    return max(0.0, min(1.0, score))


def is_low_signal_pdf_chunk(document) -> bool:
    metadata = getattr(document, "metadata", {}) or {}
    if bool(metadata.get("synthetic_source_header")):
        return False
    source = str(metadata.get("source") or "").lower()
    if not source.endswith(".pdf"):
        return False
    text = " ".join(str(document.page_content or "").split())
    if not text:
        return True
    quality = compute_text_quality_score(text)
    raw_tokens = QUERY_TOKEN_RE.findall(text)
    token_count = len(raw_tokens)
    meaningful_tokens = [
        token for token in raw_tokens if len(token) >= 4 and any(ch.isalpha() for ch in token)
    ]
    page = metadata.get("page")
    if isinstance(page, int) and page <= 1 and len(meaningful_tokens) >= 2 and quality >= 0.35:
        return False
    if len(text) < 40 and quality < 0.80:
        return True
    if token_count < 6 and quality < 0.70:
        return True
    if quality < LOW_SIGNAL_PDF_QUALITY_THRESHOLD:
        return True
    if token_count < 8 and quality < 0.45:
        return True
    return False


def get_document_features(document) -> Dict[str, object]:
    key = _document_cache_key(document)
    cached = _doc_feature_cache.get(key)
    if cached is not None:
        return cached

    metadata = getattr(document, "metadata", {}) or {}
    source = str(metadata.get("source") or "")
    source_name = Path(source).stem.lower()
    source_title_normalized = normalize_match_text(source_name)
    text = " ".join(str(document.page_content or "").split())
    lower_text = text.lower()
    page = metadata.get("page")
    chunk_index = metadata.get("chunk_index")
    features: Dict[str, object] = {
        "source": source,
        "source_name": source_name,
        "source_title_normalized": source_title_normalized,
        "source_terms": set(extract_source_match_terms(source_name)),
        "source_year_terms": set(extract_year_terms(source_name)),
        "source_class_terms": set(extract_class_terms(source_name)),
        "source_part_terms": set(extract_part_terms(source_name)),
        "text": text,
        "lower_text": lower_text,
        "tokens": set(extract_query_terms(lower_text)),
        "quality": compute_text_quality_score(text),
        "is_early_pdf_chunk": source.lower().endswith(".pdf")
        and (
            (isinstance(page, int) and page <= 1)
            or (isinstance(chunk_index, int) and chunk_index <= 1)
        ),
    }
    _doc_feature_cache[key] = features
    return features


def iter_store_documents(store: FAISS):
    docstore = getattr(store, "docstore", None)
    if docstore is None:
        return []
    if hasattr(docstore, "_dict"):
        items = list(docstore._dict.items())
    else:
        items = []
        index_map = getattr(store, "index_to_docstore_id", {}) or {}
        for doc_id in index_map.values():
            if doc_id is None:
                continue
            try:
                document = docstore.search(doc_id)
            except Exception:
                continue
            if document is None:
                continue
            items.append((doc_id, document))
    return items[:DOC_SCAN_LIMIT]


def _vector_distance_to_bonus(distance: float | None) -> float:
    if distance is None:
        return 0.0
    try:
        numeric = float(distance)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, 1.0 - min(numeric, 1.0)) * 2.0


def _build_retrieval_debug_rows(selected_items: List[Dict[str, object]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for rank, item in enumerate(selected_items, start=1):
        document = item["document"]
        rows.append(
            {
                "rank": rank,
                "source_label": format_document_source_label(document),
                "score": round(float(item.get("score", 0.0)), 3),
                "vector_bonus": round(float(item.get("vector_bonus", 0.0)), 3),
                "content_overlap": int(item.get("content_overlap", 0)),
                "source_overlap": int(item.get("source_overlap", 0)),
                "source_focus_overlap": int(item.get("source_focus_overlap", 0)),
                "quoted_source_hits": int(item.get("quoted_source_hits", 0)),
                "quoted_content_hits": int(item.get("quoted_content_hits", 0)),
                "source_year_hits": int(item.get("source_year_hits", 0)),
                "source_class_hits": int(item.get("source_class_hits", 0)),
                "source_part_hits": int(item.get("source_part_hits", 0)),
                "exact_source_title_match": bool(item.get("exact_source_title_match", False)),
                "all_terms_present": bool(item.get("all_terms_present", False)),
                "quality": round(float(item.get("quality", 0.0)), 3),
            }
        )
    return rows


def retrieve_relevant_docs_with_debug(
    store: FAISS, question: str, top_k: int
) -> tuple[List[object], List[Dict[str, object]]]:
    max_docs = len(getattr(store, "index_to_docstore_id", {}) or {})
    if max_docs == 0:
        return [], []

    effective_k = max(1, min(int(top_k), max_docs))
    vector_limit = min(max(effective_k * 6, MIN_VECTOR_CANDIDATES), max_docs)
    vector_limit = min(vector_limit, MAX_VECTOR_CANDIDATES)
    vector_results = []
    try:
        if hasattr(store, "similarity_search_with_score"):
            vector_results = store.similarity_search_with_score(question, k=vector_limit)
        elif hasattr(store, "similarity_search"):
            vector_results = [
                (document, None)
                for document in store.similarity_search(question, k=vector_limit)
            ]
    except Exception as exc:
        logging.warning("Vector retrieval failed, falling back to lexical scan: %s", exc)

    query_terms = extract_query_terms(question)
    source_query_terms = extract_source_match_terms(question)
    source_focus_terms = extract_source_focus_terms(question)
    quoted_phrases = extract_quoted_query_phrases(question)
    question_year_terms = extract_year_terms(question)
    question_class_terms = extract_class_terms(question)
    question_part_terms = extract_part_terms(question)
    has_source_focus = bool(quoted_phrases or source_focus_terms)
    candidates: Dict[str, Dict[str, object]] = {}
    source_max_scores: Dict[str, float] = defaultdict(float)
    source_match_scores: Dict[str, float] = defaultdict(float)
    source_focus_scores: Dict[str, float] = defaultdict(float)

    def upsert(document, *, vector_distance=None):
        key = _document_cache_key(document)
        entry = candidates.setdefault(
            key,
            {
                "document": document,
                "vector_distance": None,
                "vector_bonus": 0.0,
                "content_overlap": 0,
                "source_overlap": 0,
                "source_focus_overlap": 0,
                "quoted_source_hits": 0,
                "quoted_content_hits": 0,
                "source_year_hits": 0,
                "source_class_hits": 0,
                "source_part_hits": 0,
                "exact_source_title_match": False,
                "early_pdf_bonus": 0.0,
                "all_terms_present": False,
                "quality": 0.0,
                "score": 0.0,
            },
        )
        if vector_distance is not None:
            entry["vector_distance"] = vector_distance
            entry["vector_bonus"] = max(
                float(entry.get("vector_bonus", 0.0)),
                _vector_distance_to_bonus(vector_distance),
            )
        return entry

    for document, distance in vector_results:
        upsert(document, vector_distance=distance)

    for _, document in iter_store_documents(store):
        features = get_document_features(document)
        lower_text = str(features["lower_text"])
        tokens = features["tokens"]
        source_terms = set(features["source_terms"])
        source_year_terms = set(features["source_year_terms"])
        source_class_terms = set(features["source_class_terms"])
        source_part_terms = set(features["source_part_terms"])
        source_title_normalized = str(features["source_title_normalized"])
        quality = float(features["quality"])
        content_overlap = sum(1 for term in query_terms if term in tokens or term in lower_text)
        source_overlap = sum(
            1
            for term in source_query_terms
            if term in source_terms or term in source_title_normalized
        )
        source_focus_overlap = sum(
            1
            for term in source_focus_terms
            if term in source_terms or term in source_title_normalized
        )
        quoted_source_hits = sum(
            1 for phrase in quoted_phrases if phrase and phrase in source_title_normalized
        )
        quoted_content_hits = sum(
            1 for phrase in quoted_phrases if phrase and phrase in lower_text
        )
        source_year_hits = sum(1 for term in question_year_terms if term in source_year_terms)
        source_class_hits = sum(1 for term in question_class_terms if term in source_class_terms)
        source_part_hits = sum(1 for term in question_part_terms if term in source_part_terms)
        exact_source_title_match = any(
            phrase
            and (
                source_title_normalized == phrase
                or source_title_normalized.startswith(f"{phrase} ")
                or f" {phrase} " in f" {source_title_normalized} "
            )
            for phrase in quoted_phrases
        )
        if (
            content_overlap == 0
            and source_overlap == 0
            and source_focus_overlap == 0
            and quoted_source_hits == 0
            and quoted_content_hits == 0
            and source_year_hits == 0
            and source_class_hits == 0
            and source_part_hits == 0
            and not exact_source_title_match
        ):
            continue
        entry = upsert(document)
        entry["content_overlap"] = max(int(entry["content_overlap"]), content_overlap)
        entry["source_overlap"] = max(int(entry["source_overlap"]), source_overlap)
        entry["source_focus_overlap"] = max(int(entry["source_focus_overlap"]), source_focus_overlap)
        entry["quoted_source_hits"] = max(int(entry["quoted_source_hits"]), quoted_source_hits)
        entry["quoted_content_hits"] = max(int(entry["quoted_content_hits"]), quoted_content_hits)
        entry["source_year_hits"] = max(int(entry["source_year_hits"]), source_year_hits)
        entry["source_class_hits"] = max(int(entry["source_class_hits"]), source_class_hits)
        entry["source_part_hits"] = max(int(entry["source_part_hits"]), source_part_hits)
        entry["exact_source_title_match"] = bool(entry["exact_source_title_match"]) or exact_source_title_match
        if bool(features["is_early_pdf_chunk"]) and (
            source_focus_overlap > 0
            or source_overlap > 0
            or quoted_source_hits > 0
            or source_year_hits > 0
            or source_class_hits > 0
            or source_part_hits > 0
            or exact_source_title_match
        ):
            entry["early_pdf_bonus"] = max(float(entry["early_pdf_bonus"]), 3.5)
        entry["all_terms_present"] = bool(entry["all_terms_present"]) or (
            len(source_query_terms) >= 2
            and all(term in lower_text or term in source_title_normalized for term in source_query_terms)
        ) or (
            len(source_focus_terms) >= 2
            and all(term in source_terms or term in source_title_normalized for term in source_focus_terms)
        )
        entry["quality"] = max(float(entry["quality"]), quality)

    def finalize(selected_items: List[Dict[str, object]]) -> tuple[List[object], List[Dict[str, object]]]:
        return [item["document"] for item in selected_items], _build_retrieval_debug_rows(selected_items)

    if not candidates:
        fallback_items: List[Dict[str, object]] = []
        for document, distance in vector_results[:effective_k]:
            features = get_document_features(document)
            vector_bonus = _vector_distance_to_bonus(distance)
            fallback_items.append(
                {
                    "document": document,
                    "vector_distance": distance,
                    "vector_bonus": vector_bonus,
                    "content_overlap": 0,
                    "source_overlap": 0,
                    "source_focus_overlap": 0,
                    "quoted_source_hits": 0,
                    "quoted_content_hits": 0,
                    "source_year_hits": 0,
                    "source_class_hits": 0,
                    "source_part_hits": 0,
                    "exact_source_title_match": False,
                    "early_pdf_bonus": 0.0,
                    "all_terms_present": False,
                    "quality": float(features["quality"]),
                    "score": vector_bonus + (float(features["quality"]) * 1.8),
                }
            )
        return finalize(fallback_items)

    has_lexical_hits = any(
        int(item["content_overlap"]) > 0
        or int(item["source_overlap"]) > 0
        or int(item["source_focus_overlap"]) > 0
        or int(item["quoted_source_hits"]) > 0
        or int(item["quoted_content_hits"]) > 0
        or int(item["source_year_hits"]) > 0
        or int(item["source_class_hits"]) > 0
        or int(item["source_part_hits"]) > 0
        or bool(item["exact_source_title_match"])
        for item in candidates.values()
    )

    for entry in candidates.values():
        document = entry["document"]
        features = get_document_features(document)
        source = str(features["source"])
        score = (
            float(entry["vector_bonus"])
            + (float(entry["source_overlap"]) * 10.0)
            + (float(entry["source_focus_overlap"]) * 14.0)
            + (float(entry["content_overlap"]) * 3.0)
            + (float(entry["quoted_source_hits"]) * 18.0)
            + (float(entry["quoted_content_hits"]) * 8.0)
            + (float(entry["source_year_hits"]) * 12.0)
            + (float(entry["source_class_hits"]) * 10.0)
            + (float(entry["source_part_hits"]) * 12.0)
            + (22.0 if entry["exact_source_title_match"] else 0.0)
            + float(entry["early_pdf_bonus"])
            + (2.5 if entry["all_terms_present"] else 0.0)
            + (float(entry["quality"]) * 1.8)
        )
        entry["score"] = score
        source_max_scores[source] = max(source_max_scores[source], score)
        source_match_scores[source] = max(
            source_match_scores[source],
            float(entry["source_overlap"])
            + float(entry["quoted_source_hits"]) * 2.0
            + float(entry["source_focus_overlap"]) * 1.5
            + float(entry["source_year_hits"]) * 1.5
            + float(entry["source_class_hits"]) * 1.2
            + float(entry["source_part_hits"]) * 1.5
            + (3.0 if entry["exact_source_title_match"] else 0.0),
        )
        source_focus_scores[source] = max(
            source_focus_scores[source],
            float(entry["source_focus_overlap"])
            + float(entry["quoted_source_hits"]) * 2.5
            + float(entry["source_year_hits"]) * 1.0
            + float(entry["source_class_hits"]) * 1.0
            + float(entry["source_part_hits"]) * 1.5
            + (4.0 if entry["exact_source_title_match"] else 0.0),
        )

    ranked = sorted(candidates.values(), key=lambda item: float(item["score"]), reverse=True)

    if has_lexical_hits:
        ranked = [
            item
            for item in ranked
            if not (
                int(item["content_overlap"]) == 0
                and int(item["source_overlap"]) == 0
                and int(item["source_focus_overlap"]) == 0
                and int(item["quoted_source_hits"]) == 0
                and int(item["quoted_content_hits"]) == 0
                and int(item["source_year_hits"]) == 0
                and int(item["source_class_hits"]) == 0
                and int(item["source_part_hits"]) == 0
                and not bool(item["exact_source_title_match"])
                and float(item["quality"]) < 0.45
            )
        ]

    def source_of(item) -> str:
        return str(get_document_features(item["document"])["source"])

    def source_entries_for(source: str) -> List[Dict[str, object]]:
        source_entries = [item for item in ranked if source_of(item) == source]
        source_entries.sort(
            key=lambda item: (
                0 if item["exact_source_title_match"] else 1,
                -int(item["quoted_source_hits"]),
                -int(item["source_focus_overlap"]),
                -int(item["source_year_hits"]),
                -int(item["source_part_hits"]),
                -int(item["source_class_hits"]),
                -int(item["source_overlap"]),
                -int(item["quoted_content_hits"]),
                -int(item["content_overlap"]),
                0 if item["all_terms_present"] else 1,
                int(((getattr(item["document"], "metadata", {}) or {}).get("chunk_index", 10**6))),
                -float(item["score"]),
            )
        )
        return source_entries

    def source_order_key(source: str):
        return (
            -float(source_focus_scores.get(source, 0.0)),
            -float(source_match_scores.get(source, 0.0)),
            -float(source_max_scores.get(source, 0.0)),
            source,
        )

    selected: List[Dict[str, object]] = []
    selected_keys = set()

    if has_source_focus and source_focus_scores:
        best_focus_score = max(source_focus_scores.values())
        focus_sources = [
            source
            for source, focus_score in source_focus_scores.items()
            if focus_score >= max(1.5, best_focus_score - 0.75)
        ]
        focus_sources.sort(key=source_order_key)
        for source in focus_sources:
            for item in source_entries_for(source)[: min(4, effective_k)]:
                key = _document_cache_key(item["document"])
                if key in selected_keys:
                    continue
                selected.append(item)
                selected_keys.add(key)
                if len(selected) >= effective_k:
                    return finalize(selected)
        if selected:
            return finalize(selected)

    strong_sources = [
        source
        for source, source_score in source_max_scores.items()
        if source_score >= 8.0 and source_match_scores.get(source, 0.0) > 0.0
    ]
    strong_sources.sort(key=source_order_key)
    if strong_sources:
        for source in strong_sources:
            for item in source_entries_for(source)[: min(4, effective_k)]:
                key = _document_cache_key(item["document"])
                if key in selected_keys:
                    continue
                selected.append(item)
                selected_keys.add(key)
                if len(selected) >= effective_k:
                    return finalize(selected)
        if selected:
            return finalize(selected)

    for item in ranked:
        key = _document_cache_key(item["document"])
        if key in selected_keys:
            continue
        selected.append(item)
        selected_keys.add(key)
        if len(selected) >= effective_k:
            break
    return finalize(selected)


def retrieve_relevant_docs(store: FAISS, question: str, top_k: int) -> List[object]:
    documents, _ = retrieve_relevant_docs_with_debug(store, question, top_k)
    return documents


def log_gpu_info() -> None:
    pynvml = import_nvml_module()
    if pynvml is None:
        return
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        logging.info(
            "GPU detected: %s, total %.2f GB", name.decode(), mem.total / (1024**3)
        )
    except Exception as exc:  # best effort logging
        logging.warning("Unable to query GPU info: %s", exc)
    finally:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass


log_gpu_info()

# -------------------- Documents / Index --------------------


def build_source_header_text(path: Path) -> str:
    stem = path.stem.replace("_", " ").strip()
    condensed_stem = re.sub(r"\s+", " ", stem).strip()
    normalized_title = re.sub(r"[\(\)\[\]]", " ", condensed_stem)
    normalized_title = re.sub(r"\s+", " ", normalized_title).strip(" .-_")
    lines = [
        f"Заголовок файла: {normalized_title}.",
        f"Файл: {path.name}.",
    ]

    metadata_match = re.search(r"\((?P<meta>[^()]*)\)", condensed_stem)
    metadata_payload = metadata_match.group("meta").strip() if metadata_match else ""
    year_match = SOURCE_HEADER_YEAR_RE.search(metadata_payload or condensed_stem)
    if year_match:
        lines.append(f"Год издания: {year_match.group(1)}.")

    class_match = SOURCE_HEADER_CLASS_RE.search(condensed_stem)
    if class_match:
        lines.append(f"Класс: {class_match.group(1)}.")

    part_match = SOURCE_HEADER_PART_RE.search(condensed_stem)
    if part_match:
        lines.append(f"Часть: {part_match.group(1).upper()}.")

    if metadata_payload:
        author_fragment = metadata_payload
        if year_match:
            author_fragment = author_fragment.replace(year_match.group(1), " ")
        author_fragment = re.sub(r"\bг(?:од)?\.?\b", " ", author_fragment, flags=re.IGNORECASE)
        author_fragment = re.sub(r"\s+", " ", author_fragment).strip(" .-_")
        if author_fragment:
            lines.append(f"Автор или редактор: {author_fragment}.")

    return "\n".join(lines)


def build_source_header_document(path: Path) -> Document:
    header_text = build_source_header_text(path)
    return Document(
        page_content=header_text,
        metadata={
            "source": str(path),
            "page": 0,
            "synthetic_source_header": True,
            "line_start": 1,
            "line_end": len(header_text.splitlines()),
        },
    )


def load_text_like_documents(path: Path) -> List[Document]:
    raw_bytes = path.read_bytes()
    last_exc: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "cp1251", "cp866"):
        try:
            text = raw_bytes.decode(encoding)
            return [Document(page_content=text, metadata={"source": str(path)})]
        except UnicodeDecodeError as exc:
            last_exc = exc
    try:
        text = raw_bytes.decode("utf-8", errors="replace")
        return [Document(page_content=text, metadata={"source": str(path)})]
    except Exception as exc:  # pragma: no cover - defensive fallback
        last_exc = exc
    raise RuntimeError(f"Failed to decode text document {path}: {last_exc}")


def load_documents():
    docs = []
    docs_root = get_docs_path()
    loader_by_suffix = {
        ".txt": load_text_like_documents,
        ".pdf": lambda path: PyPDFLoader(str(path)),
        ".docx": lambda path: Docx2txtLoader(str(path)),
        ".md": load_text_like_documents,
        ".htm": load_text_like_documents,
        ".html": load_text_like_documents,
        ".py": load_text_like_documents,
        ".js": load_text_like_documents,
        ".json": load_text_like_documents,
        ".csv": load_text_like_documents,
        ".yml": load_text_like_documents,
        ".yaml": load_text_like_documents,
    }
    candidate_files = sorted(
        (
            path
            for path in docs_root.rglob("*")
            if path.is_file() and path.suffix.lower() in loader_by_suffix
        ),
        key=lambda path: str(path).lower(),
    )
    for path in candidate_files:
        loader_factory = loader_by_suffix.get(path.suffix.lower())
        if loader_factory is None:
            continue
        try:
            loader_result = loader_factory(path)
            if hasattr(loader_result, "load"):
                file_docs = loader_result.load()
            else:
                file_docs = loader_result
            docs.extend(file_docs)
        except Exception as exc:
            logging.warning("Loader failed for %s: %s", path, exc)
        docs.append(build_source_header_document(path))
    logging.info("Loaded %s document fragments from %s files in %s", len(docs), len(candidate_files), docs_root)
    return docs


def get_embeddings():
    global _cached_embeddings
    with embeddings_lock:
        if _cached_embeddings is not None:
            return _cached_embeddings
    current_embedding_model = get_embedding_model_name()
    try:
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        embeddings = HuggingFaceEmbeddings(
            model_name=current_embedding_model,
            model_kwargs={"device": device},
        )
    except Exception as exc:
        logging.exception("Failed to load embeddings: %s", exc)
        raise RuntimeError(
            f"Embedding model '{current_embedding_model}' is not available. "
            "Download it before running (for offline use run once with internet) "
            "or set EMBED_MODEL (or EMBEDDINGS_MODEL_NAME) to a local path."
        ) from exc
    with embeddings_lock:
        _cached_embeddings = embeddings
    return embeddings


def build_vectorstore():
    set_index_status("indexing", progress=8)
    docs = load_documents()
    if not docs:
        return None, ("no_documents", {}), 0

    set_index_status("indexing", progress=24)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        add_start_index=True,
    )
    raw_splits = []
    for source_doc in docs:
        metadata = getattr(source_doc, "metadata", {}) or {}
        try:
            raw_splits.extend(splitter.split_documents([source_doc]))
        except Exception as exc:
            logging.warning(
                "Failed to split document %s: %s",
                metadata.get("source") or "<unknown>",
                exc,
            )
    annotate_document_line_ranges(docs, raw_splits)
    chunk_positions: Dict[str, int] = defaultdict(int)
    splits = []
    filtered_chunks = 0
    kept_sources = set()
    for doc in raw_splits:
        metadata = getattr(doc, "metadata", {}) or {}
        normalized = _normalize_source_path(metadata.get("source")) or ""
        metadata["chunk_index"] = chunk_positions[normalized]
        chunk_positions[normalized] += 1
        if is_low_signal_pdf_chunk(doc):
            filtered_chunks += 1
            continue
        splits.append(doc)
        if normalized:
            kept_sources.add(normalized)
    if filtered_chunks:
        logging.info("Filtered %s low-signal PDF chunks during indexing", filtered_chunks)
    if not splits:
        return None, ("no_documents", {}), 0
    set_index_status("indexing", progress=46)
    try:
        embeddings = get_embeddings()
    except RuntimeError as exc:
        return None, ("build_failed", {"error": str(exc)}), len(kept_sources)

    set_index_status("indexing", progress=68)
    _doc_feature_cache.clear()
    vectordb = FAISS.from_documents(splits, embeddings)
    set_index_status("indexing", progress=92)
    try:
        INDEX_PATH.mkdir(parents=True, exist_ok=True)
        vectordb.save_local(str(INDEX_PATH))
    except Exception as exc:
        logging.exception("Failed to persist vector store: %s", exc)
        return (
            vectordb,
            ("saved_failed", {}),
            len(kept_sources),
        )
    return vectordb, ("ready_ask", {}), len(kept_sources)


def load_persisted_index() -> bool:
    global vectordb, needs_reindex, indexed_file_count

    if not (INDEX_PATH / "index.faiss").exists():
        return False
    try:
        embeddings = get_embeddings()
        loaded_vectordb = FAISS.load_local(
            str(INDEX_PATH),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    except Exception as exc:
        logging.exception("Failed to load persisted index: %s", exc)
        return False
    count = _count_sources_from_vectordb(loaded_vectordb)
    with index_lock:
        _doc_feature_cache.clear()
        vectordb = loaded_vectordb
        pending_changes.clear()
        needs_reindex = False
        indexed_file_count = count
        set_index_status("ready_loaded")
    return True


def rebuild_index() -> str:
    global vectordb, needs_reindex, indexed_file_count
    with index_lock:
        set_index_status("indexing", progress=2)
    try:
        new_vectordb, status_tuple, source_count = build_vectorstore()
    except Exception as exc:
        logging.exception("Failed to rebuild index: %s", exc)
        with index_lock:
            needs_reindex = True
            set_index_status("build_failed", error=str(exc))
        return get_localized_status()

    with index_lock:
        _doc_feature_cache.clear()
        vectordb = new_vectordb
        pending_changes.clear()
        code, params = status_tuple
        if new_vectordb is not None:
            indexed_file_count = source_count
        elif code == "no_documents":
            indexed_file_count = 0
        needs_reindex = new_vectordb is None and code != "no_documents"
        set_index_status(code, **params)
    return get_localized_status()


def mark_index_dirty(change_description: str | None = None) -> None:
    global needs_reindex
    with index_lock:
        if change_description and change_description not in pending_changes:
            if len(pending_changes) >= 20:
                if pending_changes[-1] != "...":
                    pending_changes.append("...")
            else:
                pending_changes.append(change_description)
        needs_reindex = True
        if pending_changes:
            preview = ", ".join(pending_changes[:3])
            if len(pending_changes) > 3 and pending_changes[-1] != "...":
                preview += ", ..."
            set_index_status("changes_detected", preview=preview)
        else:
            set_index_status("changes_detected")


def build_context_preview(text: str) -> str:
    if not text:
        return ""
    if len(text) <= MAX_CONTEXT_DISPLAY_CHARS:
        return text
    trimmed = text[:MAX_CONTEXT_DISPLAY_CHARS].rstrip()
    return (
        trimmed
        + "\n\n... (context truncated; adjust TOP_K or MAX_CONTEXT_DISPLAY_CHARS)"
    )


def build_context_preview_from_docs(documents: List[object]) -> str:
    blocks = []
    for document in documents:
        text = str(getattr(document, "page_content", "") or "").strip()
        if not text:
            continue
        header = format_document_source_label(document)
        blocks.append(f"{header}\n{text}")
    return build_context_preview("\n---\n".join(blocks))


def build_llm_context_from_docs(documents: List[object]) -> str:
    blocks = []
    for document in documents:
        text = str(getattr(document, "page_content", "") or "").strip()
        if not text:
            continue
        metadata = getattr(document, "metadata", {}) or {}
        source = str(metadata.get("source") or "")
        source_name = Path(source).name if source else "unknown-source"
        parts = [source_name]
        page = metadata.get("page")
        if isinstance(page, int):
            parts.append(f"page {page + 1}")
        line_start = metadata.get("line_start")
        line_end = metadata.get("line_end")
        if isinstance(line_start, int) and isinstance(line_end, int):
            if line_start == line_end:
                parts.append(f"line {line_start}")
            else:
                parts.append(f"lines {line_start}-{line_end}")
        header = "[source: " + " | ".join(parts) + "]"
        blocks.append(f"{header}\n{text}")
    return "\n---\n".join(blocks)


def unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        value = str(item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def infer_answer_language(role_prompt: str | None) -> str | None:
    prompt = str(role_prompt or "").lower()
    if not prompt:
        return None
    if "русском языке" in prompt or "по-русски" in prompt:
        return "ru"
    if "english" in prompt:
        return "en"
    if "dutch" in prompt:
        return "nl"
    if "simplified chinese" in prompt:
        return "zh"
    if "hebrew" in prompt:
        return "he"
    return None


def build_output_language_guard(answer_lang: str | None) -> str:
    guards = {
        "ru": (
            "Return the answer only in Russian. Use Cyrillic for section headers and "
            "service text. Do not output Chinese, English, Korean, or Hebrew words "
            "unless you are giving a short exact quote from the context."
        ),
        "en": (
            "Return the answer only in English. Do not mix in Russian, Chinese, "
            "Hebrew, or Korean except for short exact quotes from the context."
        ),
        "nl": (
            "Return the answer only in Dutch. Do not mix in other languages except "
            "for short exact quotes from the context."
        ),
        "zh": (
            "Return the answer only in Simplified Chinese. Do not mix in other "
            "languages except for short exact quotes from the context."
        ),
        "he": (
            "Return the answer only in Hebrew. Do not mix in other languages except "
            "for short exact quotes from the context."
        ),
    }
    return guards.get(str(answer_lang or "").strip().lower(), "")


def should_disable_thinking(model_name: str | None) -> bool:
    normalized = str(model_name or "").strip().lower()
    return normalized.startswith(NON_THINKING_MODEL_PREFIXES)


def build_ollama_generate_payload(model_name: str, prompt: str) -> dict:
    payload = {"model": model_name, "prompt": prompt, "stream": False}
    if should_disable_thinking(model_name):
        payload["think"] = False
    return payload


def answer_needs_language_repair(answer_text: str, answer_lang: str | None) -> bool:
    text = str(answer_text or "").strip()
    lang = str(answer_lang or "").strip().lower()
    if not text or not lang:
        return False
    lower = text.lower()
    cjk_chars = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text))
    hangul_chars = len(re.findall(r"[\uac00-\ud7af]", text))
    hebrew_chars = len(re.findall(r"[\u0590-\u05ff]", text))
    cyrillic_chars = len(re.findall(r"[А-Яа-яЁё]", text))
    latin_chars = len(re.findall(r"[A-Za-z]", text))

    if lang == "ru":
        if cjk_chars > 0 or hangul_chars > 0:
            return True
        if hebrew_chars >= 3:
            return True
        if any(
            token in lower
            for token in [
                "answer:",
                "short answer:",
                "direct answer:",
                "facts from context:",
                "validation:",
                "conclusion:",
                "steps:",
            ]
        ):
            return True
        if cyrillic_chars > 0 and latin_chars > max(14, int(cyrillic_chars * 0.35)):
            return True
    elif lang in {"en", "nl"}:
        if cjk_chars > 0 or cyrillic_chars > 4 or hebrew_chars > 2 or hangul_chars > 0:
            return True
    elif lang == "zh":
        if cjk_chars < 6 and (cyrillic_chars > 4 or hebrew_chars > 2):
            return True
    elif lang == "he":
        if cjk_chars > 0 or cyrillic_chars > 4 or hangul_chars > 0:
            return True
    return False


def build_repair_prompt(
    *,
    answer_lang: str,
    question: str,
    context: str,
    draft_answer: str,
    role_prompt: str | None,
) -> str:
    repair_instructions = {
        "ru": (
            "Rewrite the draft answer into clean Russian only. Use Cyrillic for all "
            "section headers and service text. Remove Chinese, English, Korean, or "
            "Hebrew fragments unless they are short exact quotes from the context. "
            "Keep only facts supported by the context. Return only the final answer."
        ),
        "en": (
            "Rewrite the draft answer into clean English only. Remove other-language "
            "fragments unless they are short exact quotes from the context. Keep only "
            "facts supported by the context. Return only the final answer."
        ),
        "nl": (
            "Rewrite the draft answer into clean Dutch only. Remove other-language "
            "fragments unless they are short exact quotes from the context. Keep only "
            "facts supported by the context. Return only the final answer."
        ),
        "zh": (
            "Rewrite the draft answer into clean Simplified Chinese only. Remove "
            "other-language fragments unless they are short exact quotes from the "
            "context. Keep only facts supported by the context. Return only the final answer."
        ),
        "he": (
            "Rewrite the draft answer into clean Hebrew only. Remove other-language "
            "fragments unless they are short exact quotes from the context. Keep only "
            "facts supported by the context. Return only the final answer."
        ),
    }
    prompt_parts = [
        repair_instructions.get(answer_lang, "Rewrite the draft answer in the requested language only."),
    ]
    if role_prompt:
        prompt_parts.append("Role instructions:\n" + role_prompt.strip())
    prompt_parts.append(f"Question:\n{question}")
    prompt_parts.append(f"Context:\n{context}")
    prompt_parts.append(f"Draft answer:\n{draft_answer}")
    prompt_parts.append("Final answer:")
    return "\n\n".join(prompt_parts)


def build_answer_prompt(
    *,
    context: str,
    question: str,
    answer_lang: str | None,
    role_prompt: str | None,
) -> str:
    prompt_parts = [
        (
            "Use only the provided context to answer the question. "
            "If the context contains a direct answer, state that answer in the first sentence. "
            "Keep the first sentence short and direct. "
            "For destination, author, class, or identity questions, make the first sentence a single "
            "plain fact without secondary details. "
            "For class, level, year, or audience questions, preserve the exact short designation from "
            "the context in the first sentence when possible, including digits, Roman numerals, or "
            "short audience labels copied from the source. "
            "If both numeric or Roman class labels and worded class labels are visible in the context, include both when they fit in one short sentence. "
            "For list or place questions, keep the key items from the context instead of replacing them "
            "with a generic summary, and repeat the key markers from the context instead of collapsing them. "
            "Do not say that the context is insufficient when the answer is present in the context. "
            "Keep the answer factual and grounded in the retrieved fragments. "
            "If the context mentions both a main destination and narrower locations, route points, "
            "chants, or landmarks, prefer the main destination unless the question explicitly asks "
            "for the narrower place."
        )
    ]
    language_guard = build_output_language_guard(answer_lang)
    if language_guard:
        prompt_parts.append(language_guard)
    prompt_parts.append(
        (
            "Answer contract:\n"
            "- Start with one direct answer sentence.\n"
            "- Then provide a short structured explanation.\n"
            "- For class, level, year, or audience questions, copy the short label from the context verbatim when possible.\n"
            "- If the context shows both numeric or Roman class labels and worded class labels, include both when short.\n"
            "- For list questions, preserve the main items and repeated markers from the context.\n"
            "- If the answer is missing from the context, say that explicitly.\n"
            "- Do not invent facts outside the context."
        )
    )
    if role_prompt:
        prompt_parts.append("Role instructions:\n" + role_prompt.strip())
    prompt_parts.append(f"Context:\n{context}")
    prompt_parts.append(f"Question:\n{question}")
    prompt_parts.append("Answer:")
    return "\n\n".join(prompt_parts)


def trigger_reindex():
    return rebuild_index()


def refresh_status() -> str:
    with index_lock:
        return get_localized_status()


def get_indexed_file_count() -> int:
    with index_lock:
        return indexed_file_count


class ReindexHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return
        path = Path(getattr(event, "dest_path", None) or event.src_path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return
        try:
            rel_path = path.relative_to(get_docs_path())
        except ValueError:
            rel_path = path
        change_description = f"{event.event_type}: {rel_path}"
        logging.info("Watcher change: %s", change_description)
        mark_index_dirty(change_description)


def start_watcher():
    observer = Observer()
    observer.schedule(ReindexHandler(), str(get_docs_path()), recursive=True)
    observer.start()
    threading.Thread(target=observer.join, daemon=True).start()


# -------------------- RAG --------------------


def ollama_chat(
    context: str,
    question: str,
    model_name: str,
    role_prompt: str | None = None,
) -> str:
    answer_lang = infer_answer_language(role_prompt)
    prompt = build_answer_prompt(
        context=context,
        question=question,
        answer_lang=answer_lang,
        role_prompt=role_prompt,
    )
    payload = build_ollama_generate_payload(model_name, prompt)
    try:
        r = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=300)
        r.raise_for_status()
        return r.json().get("response", "[No response from LLM]")
    except Exception as exc:
        logging.error("Ollama request error: %s", exc)
        return f"[Ollama request error: {exc}]"


def repair_answer_language(
    context: str,
    question: str,
    draft_answer: str,
    model_name: str,
    answer_lang: str,
    role_prompt: str | None = None,
) -> str:
    prompt = build_repair_prompt(
        answer_lang=answer_lang,
        question=question,
        context=context,
        draft_answer=draft_answer,
        role_prompt=role_prompt,
    )
    payload = build_ollama_generate_payload(model_name, prompt)
    try:
        r = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=300)
        r.raise_for_status()
        return r.json().get("response", draft_answer)
    except Exception as exc:
        logging.error("Ollama repair error: %s", exc)
        return draft_answer


ROMAN_CLASS_MAP = {
    "i": 1,
    "ii": 2,
    "iii": 3,
    "iv": 4,
    "v": 5,
    "vi": 6,
    "vii": 7,
    "viii": 8,
    "ix": 9,
    "x": 10,
    "xi": 11,
}
CLASS_WORD_FORMS = {
    1: {"gen": "\u043f\u0435\u0440\u0432\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432 \u043f\u0435\u0440\u0432\u043e\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
    2: {"gen": "\u0432\u0442\u043e\u0440\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432\u043e \u0432\u0442\u043e\u0440\u043e\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
    3: {"gen": "\u0442\u0440\u0435\u0442\u044c\u0435\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432 \u0442\u0440\u0435\u0442\u044c\u0435\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
    4: {"gen": "\u0447\u0435\u0442\u0432\u0435\u0440\u0442\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432 \u0447\u0435\u0442\u0432\u0435\u0440\u0442\u043e\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
    5: {"gen": "\u043f\u044f\u0442\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432 \u043f\u044f\u0442\u043e\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
    6: {"gen": "\u0448\u0435\u0441\u0442\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432 \u0448\u0435\u0441\u0442\u043e\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
    7: {"gen": "\u0441\u0435\u0434\u044c\u043c\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432 \u0441\u0435\u0434\u044c\u043c\u043e\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
    8: {"gen": "\u0432\u043e\u0441\u044c\u043c\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432 \u0432\u043e\u0441\u044c\u043c\u043e\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
    9: {"gen": "\u0434\u0435\u0432\u044f\u0442\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432 \u0434\u0435\u0432\u044f\u0442\u043e\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
    10: {"gen": "\u0434\u0435\u0441\u044f\u0442\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432 \u0434\u0435\u0441\u044f\u0442\u043e\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
    11: {"gen": "\u043e\u0434\u0438\u043d\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e \u043a\u043b\u0430\u0441\u0441\u0430", "prep": "\u0432 \u043e\u0434\u0438\u043d\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u043c \u043a\u043b\u0430\u0441\u0441\u0435"},
}
CLASS_NUMERIC_RE = re.compile(
    r"\b(\d+\s*(?:[-\u2013]\s*\d+)?\s*(?:-?\u0433\u043e\s*)?\u043a\u043b\u0430\u0441\u0441(?:\u0430|\u0435)?)\b",
    re.IGNORECASE,
)
CLASS_ROMAN_RE = re.compile(r"\b([ivxlcdm]+\s+\u043a\u043b\u0430\u0441\u0441(?:\u0430|\u0435)?)\b", re.IGNORECASE)
CLASS_GEN_RE = re.compile(
    r"\b((?:\u043f\u0435\u0440\u0432\u043e\u0433\u043e|\u0432\u0442\u043e\u0440\u043e\u0433\u043e|\u0442\u0440\u0435\u0442\u044c\u0435\u0433\u043e|\u0447\u0435\u0442\u0432\u0435\u0440\u0442\u043e\u0433\u043e|\u043f\u044f\u0442\u043e\u0433\u043e|\u0448\u0435\u0441\u0442\u043e\u0433\u043e|\u0441\u0435\u0434\u044c\u043c\u043e\u0433\u043e|\u0432\u043e\u0441\u044c\u043c\u043e\u0433\u043e|\u0434\u0435\u0432\u044f\u0442\u043e\u0433\u043e|\u0434\u0435\u0441\u044f\u0442\u043e\u0433\u043e|\u043e\u0434\u0438\u043d\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u0433\u043e)\s+\u043a\u043b\u0430\u0441\u0441\u0430)\b",
    re.IGNORECASE,
)
CLASS_PREP_RE = re.compile(
    r"\b(\u0432(?:\u043e)?\s+(?:\u043f\u0435\u0440\u0432\u043e\u043c|\u0432\u0442\u043e\u0440\u043e\u043c|\u0442\u0440\u0435\u0442\u044c\u0435\u043c|\u0447\u0435\u0442\u0432\u0435\u0440\u0442\u043e\u043c|\u043f\u044f\u0442\u043e\u043c|\u0448\u0435\u0441\u0442\u043e\u043c|\u0441\u0435\u0434\u044c\u043c\u043e\u043c|\u0432\u043e\u0441\u044c\u043c\u043e\u043c|\u0434\u0435\u0432\u044f\u0442\u043e\u043c|\u0434\u0435\u0441\u044f\u0442\u043e\u043c|\u043e\u0434\u0438\u043d\u043d\u0430\u0434\u0446\u0430\u0442\u043e\u043c)\s+\u043a\u043b\u0430\u0441\u0441\u0435)\b",
    re.IGNORECASE,
)
LOGIC_SCOPE_RE = re.compile(
    r"(\u0432\s+\u0442\u0440\u0443\u0434\u0435[^.]{0,260}?\u0432\s+\u0448\u043a\u043e\u043b\u044c\u043d\u043e\u043c\s+\u0441\u043e\u0447\u0438\u043d\u0435\u043d\u0438\u0438)",
    re.IGNORECASE | re.DOTALL,
)
QUESTION_CHAPTER_RE = re.compile(r"\b\u0433\u043b\u0430\u0432[аеиыу]\s+([ivxlcdm0-9]+)\b", re.IGNORECASE)
CONTEXT_CHAPTER_HEADING_RE = re.compile(
    r"(?:^|\n)\s*\u0433\u043b\u0430\u0432[аеиыу]\s+([ivxlcdm0-9]+)\s*(?:[.:\-]\s*|\n\s*)([^\n]{4,140})",
    re.IGNORECASE,
)
AUTHOR_INITIALS_RE = re.compile(
    r"\b([А-ЯЁ]\.\s*[А-ЯЁ]\.\s*[А-ЯЁ][а-яё-]+)\b"
)
AUTHOR_HEADER_RE = re.compile(r"Автор или редактор:\s*([^\n]+)")
AUTHOR_FULL_NAME_RE = re.compile(
    r"^\s*([А-ЯЁ][а-яё-]+(?:[ \t]+[А-ЯЁ][а-яё-]+){1,2})\s*$"
)


def normalize_inline_whitespace(value: str) -> str:
    return " ".join(str(value or "").replace("\u00ad", "").split())


def normalize_author_name(value: str) -> str:
    normalized = normalize_inline_whitespace(value).strip(" .")
    normalized = re.sub(r"([А-ЯЁ])\.([А-ЯЁ])\.", r"\1. \2.", normalized)
    normalized = re.sub(r"([А-ЯЁ])\.([А-ЯЁ][а-яё-])", r"\1. \2", normalized)
    return normalized.strip()


def replace_first_sentence(answer: str, sentence: str) -> str:
    cleaned_answer = str(answer or "").strip()
    cleaned_sentence = str(sentence or "").strip().rstrip(".?!") + "."
    if not cleaned_answer:
        return cleaned_sentence
    parts = re.split(r"(?<=[.!?])\s+", cleaned_answer, maxsplit=1)
    if len(parts) == 1:
        return cleaned_sentence
    return cleaned_sentence + "\n\n" + parts[1].strip()

def replace_lead_paragraph(answer: str, paragraph: str) -> str:
    cleaned_answer = str(answer or "").strip()
    cleaned_paragraph = str(paragraph or "").strip().rstrip(".?!") + "."
    if not cleaned_answer:
        return cleaned_paragraph
    parts = re.split(r"\n\s*\n", cleaned_answer, maxsplit=1)
    if len(parts) == 1:
        return cleaned_paragraph
    return cleaned_paragraph + "\n\n" + parts[1].strip()




def canonicalize_numeric_class_label(label: str) -> tuple[str | None, int | None]:
    normalized = normalize_inline_whitespace(label).lower()
    digit_match = re.search(r"(\d+\s*(?:[-\u2013]\s*\d+)?)", normalized)
    if digit_match:
        numeric = digit_match.group(1).replace(" ", "").replace("\u2013", "-")
        canonical = f"{numeric} \u043a\u043b\u0430\u0441\u0441"
        if "-" in numeric:
            return canonical, None
        try:
            return canonical, int(numeric)
        except ValueError:
            return canonical, None
    roman_match = re.search(r"\b([ivxlcdm]+)\b", normalized)
    if not roman_match:
        return None, None
    value = ROMAN_CLASS_MAP.get(roman_match.group(1).lower())
    if value is None:
        return None, None
    return f"{value} \u043a\u043b\u0430\u0441\u0441", value


def extract_class_evidence(context: str) -> tuple[str | None, str | None, str | None]:
    lowered = normalize_inline_whitespace(context).lower()
    numeric_label = None
    class_number = None
    for pattern in (CLASS_NUMERIC_RE, CLASS_ROMAN_RE):
        match = pattern.search(lowered)
        if not match:
            continue
        numeric_label, class_number = canonicalize_numeric_class_label(match.group(1))
        if numeric_label:
            break

    gen_label = None
    match = CLASS_GEN_RE.search(lowered)
    if match:
        gen_label = normalize_inline_whitespace(match.group(1)).lower()

    prep_label = None
    match = CLASS_PREP_RE.search(lowered)
    if match:
        prep_label = normalize_inline_whitespace(match.group(1)).lower()

    if class_number in CLASS_WORD_FORMS:
        forms = CLASS_WORD_FORMS[class_number]
        gen_label = gen_label or forms["gen"]
        prep_label = prep_label or forms["prep"]
    return numeric_label, gen_label, prep_label


def infer_document_subject_and_verb(question: str) -> tuple[str, str]:
    lowered = str(question or "").lower()
    if "книга" in lowered:
        return "Книга", "предназначена"
    if "пособие" in lowered:
        return "Пособие", "предназначено"
    if "учебник" in lowered:
        return "Учебник", "предназначен"
    return "Издание", "предназначено"


def to_genitive_class_label(numeric_label: str | None) -> str | None:
    if not numeric_label:
        return None
    normalized = str(numeric_label).strip()
    if normalized.endswith(" класс"):
        return normalized[:-6] + " класса"
    return normalized


def build_class_sentence(question: str, numeric_label: str | None, gen_label: str | None) -> str | None:
    subject, verb = infer_document_subject_and_verb(question)
    numeric_gen = to_genitive_class_label(numeric_label)
    if numeric_gen and gen_label:
        return f"{subject} {verb} для {numeric_gen} ({gen_label})"
    if numeric_gen:
        return f"{subject} {verb} для {numeric_gen}"
    if gen_label:
        return f"{subject} {verb} для {gen_label}"
    return None

def extract_audience_label(context: str) -> str | None:
    lowered = normalize_inline_whitespace(context).lower()
    if "\u0434\u043b\u044f \u0432\u0443\u0437\u043e\u0432" in lowered:
        return "\u0434\u043b\u044f \u0412\u0423\u0417\u043e\u0432"
    match = re.search(
        r"(\u0434\u043b\u044f\s+\u0441\u0442\u0443\u0434\u0435\u043d\u0442\u043e\u0432[^.]{0,120}?\u0432\u0443\u0437\u043e\u0432)",
        lowered,
    )
    if not match:
        return None
    return normalize_inline_whitespace(match.group(1))


def extract_chapter_heading_evidence(question: str, context: str) -> tuple[str | None, str | None]:
    raw_context = str(context or "").replace("\u00ad", "")
    requested_chapter = None
    question_match = QUESTION_CHAPTER_RE.search(str(question or ""))
    if question_match:
        requested_chapter = question_match.group(1).lower()

    for match in CONTEXT_CHAPTER_HEADING_RE.finditer(raw_context):
        chapter_number = str(match.group(1) or "").strip()
        heading = normalize_inline_whitespace(match.group(2)).strip(" .:-")
        if len(heading) < 4:
            continue
        if requested_chapter and chapter_number.lower() != requested_chapter:
            continue
        return chapter_number, heading

    lowered = normalize_inline_whitespace(raw_context).lower()
    if "предмет и задачи науки логики" in lowered:
        chapter_number = question_match.group(1) if question_match else None
        return chapter_number, "Предмет и задачи науки логики"
    return None, None


def build_chapter_heading_sentence(
    question: str, chapter_number: str | None, heading: str | None
) -> str | None:
    if not heading or "глава" not in str(question or "").lower():
        return None
    cleaned_heading = normalize_inline_whitespace(heading)
    letters = [char for char in cleaned_heading if char.isalpha()]
    if letters:
        upper_ratio = sum(1 for char in letters if char.isupper()) / len(letters)
        if upper_ratio >= 0.75:
            cleaned_heading = cleaned_heading.lower().capitalize()
    chapter_label = f"Глава {chapter_number}" if chapter_number else "Глава"
    return f'{chapter_label} называется «{cleaned_heading}»'


def extract_author_evidence(context: str) -> str | None:
    raw_context = str(context or "").replace("\u00ad", "")
    header_match = AUTHOR_HEADER_RE.search(raw_context)
    if header_match:
        candidate = normalize_author_name(header_match.group(1))
        if len(candidate) >= 6:
            return candidate
    for match in AUTHOR_INITIALS_RE.finditer(raw_context):
        candidate = normalize_author_name(match.group(1))
        if len(candidate) >= 6:
            return candidate
    for line in raw_context.splitlines():
        candidate_line = normalize_inline_whitespace(line)
        if not candidate_line or candidate_line.startswith("[source:"):
            continue
        match = AUTHOR_FULL_NAME_RE.match(candidate_line)
        if not match:
            continue
        candidate = normalize_author_name(match.group(1))
        if len(candidate) >= 6:
            return candidate
    return None


def build_author_sentence(author_name: str | None) -> str | None:
    if not author_name:
        return None
    return f"Автор издания — {normalize_author_name(author_name)}"


def refine_answer_with_context_evidence(question: str, answer: str, context: str) -> str:
    refined = str(answer or "").strip()
    lowered_question = str(question or "").lower()
    if not refined:
        return refined

    if "\u043a\u0442\u043e \u0430\u0432\u0442\u043e\u0440" in lowered_question:
        author_name = extract_author_evidence(context)
        author_sentence = build_author_sentence(author_name)
        if author_sentence:
            refined = replace_first_sentence(refined, author_sentence)

    if "\u0434\u043b\u044f \u043a\u043e\u0433\u043e" in lowered_question:
        audience_label = extract_audience_label(context)
        if audience_label:
            subject, verb = infer_document_subject_and_verb(question)
            refined = replace_lead_paragraph(refined, f"{subject} {verb} {audience_label}")

    if "\u043a\u043b\u0430\u0441\u0441" in lowered_question and "\u043a\u0442\u043e \u0430\u0432\u0442\u043e\u0440" not in lowered_question:
        numeric_label, gen_label, prep_label = extract_class_evidence(context)
        sentence = build_class_sentence(question, numeric_label, gen_label)
        if sentence:
            refined = replace_first_sentence(refined, sentence)
            if prep_label and prep_label not in refined.lower():
                refined += f"\n\n\u0412 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442\u0435 \u0442\u0430\u043a\u0436\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u043e: {prep_label}."

    if "\u0433\u043b\u0430\u0432" in lowered_question and (
        "\u043e \u0447\u0435\u043c" in lowered_question
        or "\u043f\u043e\u0441\u0432\u044f\u0449" in lowered_question
    ):
        chapter_number, heading = extract_chapter_heading_evidence(question, context)
        chapter_sentence = build_chapter_heading_sentence(question, chapter_number, heading)
        if chapter_sentence:
            refined = replace_first_sentence(refined, chapter_sentence)

    if "\u043f\u0440\u0430\u0432\u0438\u043b\u044c\u043d\u043e\u0435 \u043c\u044b\u0448\u043b\u0435\u043d\u0438\u0435" in lowered_question and "\u0433\u0434\u0435" in lowered_question:
        match = LOGIC_SCOPE_RE.search(normalize_inline_whitespace(context).lower())
        if match:
            scope = match.group(1)
            scope = scope.replace(
                "\u0432 \u0443\u0447\u0435\u0431\u043d\u043e\u0439 \u0438 \u043e\u0431\u0449\u0435\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0439 \u0440\u0430\u0431\u043e\u0442\u0435",
                "\u0432 \u0443\u0447\u0435\u0431\u043d\u043e\u0439 \u0438 \u0432 \u043e\u0431\u0449\u0435\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0439 \u0440\u0430\u0431\u043e\u0442\u0435",
            )
            refined = replace_first_sentence(
                refined,
                f"\u041f\u0440\u0430\u0432\u0438\u043b\u044c\u043d\u043e\u0435 \u043c\u044b\u0448\u043b\u0435\u043d\u0438\u0435 \u043d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u043e {scope}",
            )

    return refined


def rag_query(
    question: str,
    model_choice: str,
    top_k: int,
    role_prompt: str | None = None,
):
    with index_lock:
        current_vectordb = vectordb
        pending_flag = needs_reindex
    model_name = model_choice or MODEL_NAME or DEFAULT_MODEL
    if (
        current_vectordb is None
        or getattr(current_vectordb, "index_to_docstore_id", None) is None
    ):
        message = t("status_no_documents")
        return message, ""
    try:
        effective_k = int(top_k) if top_k is not None else DEFAULT_TOP_K
    except (TypeError, ValueError):
        effective_k = DEFAULT_TOP_K
    effective_k = max(1, effective_k)
    max_docs = len(current_vectordb.index_to_docstore_id)
    if max_docs == 0:
        return t("status_no_documents"), ""
    docs = retrieve_relevant_docs(current_vectordb, question, min(effective_k, max_docs))
    context = build_llm_context_from_docs(docs)
    answer = ollama_chat(context, question, model_name, role_prompt=role_prompt)
    result = answer.strip() if isinstance(answer, str) else str(answer)
    answer_lang = infer_answer_language(role_prompt)
    if answer_needs_language_repair(result, answer_lang):
        repaired = repair_answer_language(
            context,
            question,
            result,
            model_name,
            answer_lang or "",
            role_prompt=role_prompt,
        )
        repaired_text = repaired.strip() if isinstance(repaired, str) else str(repaired)
        if repaired_text:
            result = repaired_text
    result = refine_answer_with_context_evidence(question, result, context)
    if pending_flag:
        result = f"[{t('status_changes_detected')}]\n\n" + result
    return result, build_context_preview_from_docs(docs)


def get_retrieval_debug_snapshot(question: str, top_k: int) -> List[Dict[str, object]]:
    with index_lock:
        current_vectordb = vectordb
    if current_vectordb is None:
        return []
    try:
        effective_k = int(top_k) if top_k is not None else DEFAULT_TOP_K
    except (TypeError, ValueError):
        effective_k = DEFAULT_TOP_K
    effective_k = max(1, effective_k)
    _, debug_rows = retrieve_relevant_docs_with_debug(current_vectordb, question, effective_k)
    return debug_rows


# -------------------- Models --------------------


def get_default_model(models: List[str] | None = None) -> str:
    available_models = list(models) if models is not None else get_ollama_models()
    if not available_models:
        return DEFAULT_MODEL
    for candidate in unique_preserve_order(MODEL_PREFERENCE_ORDER):
        if candidate in available_models:
            return candidate
    return available_models[0]


def get_ollama_models() -> List[str]:
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        r.raise_for_status()
        models = [m.get("name") for m in r.json().get("models", []) if m.get("name")]
    except Exception as exc:
        logging.error("Failed to fetch Ollama models: %s", exc)
        return []
    return unique_preserve_order(models)


def get_index_status() -> str:
    with index_lock:
        return get_localized_status()


# -------------------- UI wiring via binder --------------------


def setup_ui():
    def binder(_demo: gr.Blocks, c: Dict[str, gr.Component]):
        # Language switching

        def _apply_i18n_updates():
            status = (
                f"**{t('docs_folder')}** `{get_docs_path_display()}`\n\n"
                + get_index_status()
            )
            # Обновить brand_html (заголовок и подзаголовок)
            brand_html = (
                f"<div class='app-brand-wrap'>"
                f"<img class='app-logo' src='{c['logo_src'].value}' alt='LocalRAG'/>"
                f"<div class='app-brand-text'>"
                f"<div class='app-title'>{t('app_title')}</div>"
                f"<div class='app-subtitle'>{t('app_subtitle')}</div>"
                f"</div>"
                f"</div>"
            )
            updates = [
                gr.update(value=brand_html),  # brand_html
                gr.update(value=t("refresh_status")),  # refresh_btn
                gr.update(value=t("reindex_docs")),  # reindex_btn
                gr.update(label=t("top_k_label")),  # topk_slider
                gr.update(label=t("model_label")),  # model_dd
                gr.update(
                    label=t("question_label"),
                    placeholder=translations.get("question_placeholder", None),
                ),  # question_tb
                gr.update(value=t("ask_button")),  # ask_btn
                gr.update(label=t("answer_label")),  # answer_tb
                gr.update(label=t("context_accordion")),  # ctx_acc
                gr.update(value=status),  # status_md
            ]
            return updates

        def change_lang(lang_code: str):
            global translations, current_language
            current_language = lang_code
            translations = load_translations(lang_code)
            return _apply_i18n_updates()

        # Refresh
        def on_refresh():
            status = (
                f"**{t('docs_folder')}** `{get_docs_path_display()}`\n\n"
                + refresh_status()
            )
            models = get_ollama_models()
            default = get_default_model()
            if not models:
                default_choice = None
            else:
                if default not in models:
                    default = models[0]
                default_choice = default
            return gr.update(value=status), gr.update(
                choices=models, value=default_choice
            )

        c["refresh_btn"].click(fn=on_refresh, outputs=[c["status_md"], c["model_dd"]])

        # Reindex
        c["reindex_btn"].click(fn=trigger_reindex, outputs=[c["status_md"]])

        # Ask
        def on_ask(q, k, temp, model_name):
            return rag_query(q, model_name, int(k))

        c["ask_btn"].click(
            fn=on_ask,
            inputs=[
                c["question_tb"],
                c["topk_slider"],
                c["temp_slider"],
                c["model_dd"],
            ],
            outputs=[c["answer_tb"], c["ctx_md"]],
        )

        # Labels (i18n)
        c["refresh_btn"].value = t("refresh_status")
        c["reindex_btn"].value = t("reindex_docs")
        c["topk_slider"].label = t("top_k_label")
        c["model_dd"].label = t("model_label")
        c["question_tb"].label = t("question_label")
        c["ask_btn"].value = t("ask_button")
        c["answer_tb"].label = t("answer_label")
        c["ctx_acc"].label = t("context_accordion")
        c["topk_slider"].value = DEFAULT_TOP_K

        # Wire language buttons if present
        lang_outputs = [
            c["brand_html"],
            c["refresh_btn"],
            c["reindex_btn"],
            c["topk_slider"],
            c["model_dd"],
            c["question_tb"],
            c["ask_btn"],
            c["answer_tb"],
            c["ctx_acc"],
            c["status_md"],
        ]
        if "lang_en" in c:
            c["lang_en"].click(lambda: change_lang("en"), outputs=lang_outputs)
        if "lang_ru" in c:
            c["lang_ru"].click(lambda: change_lang("ru"), outputs=lang_outputs)
        if "lang_nl" in c:
            c["lang_nl"].click(lambda: change_lang("nl"), outputs=lang_outputs)
        if "lang_zh" in c:
            c["lang_zh"].click(lambda: change_lang("zh"), outputs=lang_outputs)
        if "lang_he" in c:
            c["lang_he"].click(lambda: change_lang("he"), outputs=lang_outputs)

        # Initial status and models
        status = (
            f"**{t('docs_folder')}** `{get_docs_path_display()}`\n\n"
            + get_index_status()
        )
        c["status_md"].value = status
        models = get_ollama_models()
        c["model_dd"].choices = models
        if models:
            default_model = get_default_model()
            c["model_dd"].value = default_model if default_model in models else models[0]
        else:
            c["model_dd"].value = None

    demo, _ = ui_create_interface(binder=binder)
    return demo

if __name__ == "__main__":
    start_watcher()
    if not load_persisted_index():
        rebuild_index()
    demo_app = setup_ui()
    # Serve custom favicon if present
    _fav = BASE_DIR / "static" / "favicon.ico"
    favicon = str(_fav) if _fav.exists() else None
    demo_app.launch(server_name="0.0.0.0", server_port=7860, favicon_path=favicon)
