import sys
import json
import html
import logging
import asyncio
import os
import re
import threading
import uuid
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import uvicorn
from fastapi import BackgroundTasks, Body, Cookie, FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

sys.path.append(str((Path(__file__).parent / "app").resolve()))
from app import (  # noqa: E402
    DEFAULT_TOP_K,
    OLLAMA_BASE_URL,
    get_default_model,
    get_default_embedding_model_name,
    is_embedding_model_available_locally,
    get_default_docs_path_display,
    get_docs_path_display,
    get_embedding_model_name,
    get_embedding_runtime_info,
    get_index_status,
    get_index_status_meta,
    get_indexed_file_count,
    list_available_embedding_models,
    normalize_embedding_model_name,
    get_ollama_models,
    prepare_embedding_model_artifact,
    get_retrieval_debug_snapshot,
    list_browsable_directories,
    load_persisted_index,
    rag_query,
    rebuild_index,
    set_embedding_model,
    set_docs_path,
)

BASE_DIR = Path(__file__).resolve().parent
LOCALES_DIR = BASE_DIR / "app" / "locales"
VERSION_FILE = BASE_DIR / "VERSION"
SERVER_PROFILE_FILE = BASE_DIR / "server_profile.json"
LANGS = ["en", "ru", "nl", "zh", "he"]
DEFAULT_LANG = "en"
DEFAULT_ANSWER_LANGUAGE_SETTING = "interface"
STATUS_KEY_MAP = {
    "loading": "status_loading",
    "ready_loaded": "status_ready_loaded",
    "indexing": "status_indexing",
    "build_failed": "status_build_failed",
    "ready_ask": "status_ready_ask",
    "no_documents": "status_no_documents",
    "saved_failed": "status_saved_failed",
    "changes_detected": "status_changes_detected",
}
ROLE_PRESETS = {
    "analyst": {
        "label_key": "role_analyst",
    },
    "engineer": {
        "label_key": "role_engineer",
    },
    "archivist": {
        "label_key": "role_archivist",
    },
}
DEFAULT_ROLE = "analyst"
ROLE_STYLE_PRESETS = {
    "concise": {"label_key": "style_concise"},
    "balanced": {"label_key": "style_balanced"},
    "detailed": {"label_key": "style_detailed"},
}
CUSTOM_ROLE_STYLE_OPTIONS = {"", "inherit", "concise", "balanced", "detailed"}


def load_app_version() -> str:
    version = os.environ.get("APP_VERSION", "").strip()
    if version:
        return version
    try:
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        version = ""
    return version or "0.9.0"


APP_NAME = "LocalRAG"
APP_VERSION = load_app_version()
BUILD_DATE_UTC = os.environ.get("BUILD_DATE_UTC", "").strip()
DEFAULT_ROLE_STYLE = "balanced"
MODEL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._:/-]+$")
ROLE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
PLACEHOLDER_TRANSLATION_PATTERNS = {
    "ru": re.compile(r"^[\?\s:;,\.\-\(\)\{\}\[\]!/0-9A-Za-z]+$"),
    "zh": re.compile(r"^[\?\s:;,\.\-\(\)\{\}\[\]!/0-9A-Za-z]+$"),
    "he": re.compile(r"^[\?\s:;,\.\-\(\)\{\}\[\]!/0-9A-Za-z]+$"),
}
CONTEXT_HEADER_PAGE_RE = re.compile(r"\bpage\s+(?P<page>\d+)\b", re.IGNORECASE)
CONTEXT_HEADER_LINES_RE = re.compile(
    r"\blines\s+(?P<start>\d+)\s*-\s*(?P<end>\d+)\b",
    re.IGNORECASE,
)
CONTEXT_HEADER_LINE_RE = re.compile(r"\bline\s+(?P<line>\d+)\b", re.IGNORECASE)
RECOMMENDED_MODEL_CATALOG = [
    {
        "name": "qwen3.5:9b",
        "summary_key": "model_catalog_qwen3_5_9b",
    },
    {
        "name": "qwen3:8b",
        "summary_key": "model_catalog_qwen3_8b",
    },
    {
        "name": "qwen3:14b",
        "summary_key": "model_catalog_qwen3_14b",
    },
    {
        "name": "gemma3:12b",
        "summary_key": "model_catalog_gemma3_12b",
    },
    {
        "name": "aya-expanse:8b",
        "summary_key": "model_catalog_aya_expanse_8b",
    },
]
RECOMMENDED_EMBEDDING_MODEL_CATALOG = [
    {
        "name": "intfloat/multilingual-e5-large",
        "summary_key": "embedding_model_catalog_e5_large",
    },
    {
        "name": "BAAI/bge-m3",
        "summary_key": "embedding_model_catalog_bge_m3",
    },
    {
        "name": "Alibaba-NLP/gte-multilingual-base",
        "summary_key": "embedding_model_catalog_gte_multilingual_base",
    },
]
ROLE_IMAGE_LIBRARY = [
    {"value": "analyst", "path": "roles/analyst.png"},
    {"value": "engineer", "path": "roles/engineer.png"},
    {"value": "archivist", "path": "roles/archivist.png"},
    {"value": "strategist", "path": "roles/strategist.png"},
    {"value": "scout", "path": "roles/scout.png"},
    {"value": "alchemist", "path": "roles/alchemist.png"},
    {"value": "inquisitor", "path": "roles/inquisitor.png"},
    {"value": "bard", "path": "roles/bard.png"},
    {"value": "mentor", "path": "roles/mentor.png"},
    {"value": "summoner", "path": "roles/summoner.png"},
    {"value": "scribe", "path": "roles/scribe.png"},
    {"value": "astrologer", "path": "roles/astrologer.png"},
    {"value": "oracle", "path": "roles/oracle.png"},
    {"value": "blacksmith", "path": "roles/blacksmith.png"},
    {"value": "curator", "path": "roles/curator.png"},
    {"value": "guardian", "path": "roles/guardian.png"},
]
ROLE_IMAGE_DEFAULTS = {
    "analyst": "analyst",
    "engineer": "engineer",
    "archivist": "archivist",
}
PROMPT_LANGUAGE_RULES = {
    "en": (
        "Answer only in English. Do not mix English with Russian, Chinese, Korean, "
        "Hebrew, or any other language unless you are directly quoting the source context."
    ),
    "ru": (
        "\u041e\u0442\u0432\u0435\u0447\u0430\u0439 \u0442\u043e\u043b\u044c\u043a\u043e \u043d\u0430 \u0440\u0443\u0441\u0441\u043a\u043e\u043c \u044f\u0437\u044b\u043a\u0435, \u0435\u0441\u0442\u0435\u0441\u0442\u0432\u0435\u043d\u043d\u043e \u0438 \u0441\u043e\u0432\u0440\u0435\u043c\u0435\u043d\u043d\u043e. "
        "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439 \u043a\u0438\u0440\u0438\u043b\u043b\u0438\u0446\u0443 \u0434\u043b\u044f \u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043a\u043e\u0432, \u0441\u0432\u044f\u0437\u043e\u043a \u0438 \u0441\u043b\u0443\u0436\u0435\u0431\u043d\u044b\u0445 \u0441\u043b\u043e\u0432. "
        "\u041d\u0435 \u0441\u043c\u0435\u0448\u0438\u0432\u0430\u0439 \u0440\u0443\u0441\u0441\u043a\u0438\u0439 \u0441 \u0430\u043d\u0433\u043b\u0438\u0439\u0441\u043a\u0438\u043c, \u043a\u0438\u0442\u0430\u0439\u0441\u043a\u0438\u043c, \u043a\u043e\u0440\u0435\u0439\u0441\u043a\u0438\u043c, \u0438\u0432\u0440\u0438\u0442\u043e\u043c \u0438\u043b\u0438 \u0434\u0440\u0443\u0433\u0438\u043c\u0438 "
        "\u044f\u0437\u044b\u043a\u0430\u043c\u0438, \u043a\u0440\u043e\u043c\u0435 \u043f\u0440\u044f\u043c\u044b\u0445 \u043a\u043e\u0440\u043e\u0442\u043a\u0438\u0445 \u0446\u0438\u0442\u0430\u0442 \u0438\u0437 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442\u0430."
    ),
    "nl": (
        "Answer only in Dutch. Do not mix Dutch with other languages unless you are "
        "directly quoting the source context."
    ),
    "zh": (
        "Answer only in Simplified Chinese. Do not mix Chinese with other languages "
        "unless you are directly quoting the source context."
    ),
    "he": (
        "Answer only in Hebrew. Do not mix Hebrew with other languages unless you are "
        "directly quoting the source context."
    ),
}
ROLE_PROMPT_LIBRARY = {
    "en": {
        "analyst": (
            "Role: Analyst.\n"
            "Use only the provided context and avoid speculation.\n"
            "Preferred structure:\n"
            "Short conclusion:\n"
            "Facts from context:\n"
            "Risks or uncertainties:"
        ),
        "engineer": (
            "Role: Engineer.\n"
            "Use only the provided context and stay implementation-oriented.\n"
            "Preferred structure:\n"
            "Short answer:\n"
            "Steps:\n"
            "Validation:"
        ),
        "archivist": (
            "Role: Archivist.\n"
            "Preserve source intent and be precise about what is explicitly known from context.\n"
            "Preferred structure:\n"
            "Direct answer:\n"
            "Context evidence:\n"
            "Missing data:"
        ),
    },
    "ru": {
        "analyst": (
            "\u0420\u043e\u043b\u044c: \u0410\u043d\u0430\u043b\u0438\u0442\u0438\u043a.\n"
            "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439 \u0442\u043e\u043b\u044c\u043a\u043e \u043f\u0440\u0435\u0434\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u043d\u044b\u0439 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442 \u0438 \u043d\u0435 \u0434\u043e\u0434\u0443\u043c\u044b\u0432\u0430\u0439 \u0444\u0430\u043a\u0442\u044b.\n"
            "\u041f\u0440\u0435\u0434\u043f\u043e\u0447\u0442\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442:\n"
            "\u041a\u0440\u0430\u0442\u043a\u0438\u0439 \u0432\u044b\u0432\u043e\u0434:\n"
            "\u0424\u0430\u043a\u0442\u044b \u0438\u0437 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442\u0430:\n"
            "\u041d\u0435\u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u043d\u043e\u0441\u0442\u0438 \u0438\u043b\u0438 \u0440\u0438\u0441\u043a\u0438:"
        ),
        "engineer": (
            "\u0420\u043e\u043b\u044c: \u0418\u043d\u0436\u0435\u043d\u0435\u0440.\n"
            "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439 \u0442\u043e\u043b\u044c\u043a\u043e \u043f\u0440\u0435\u0434\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u043d\u044b\u0439 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442 \u0438 \u043e\u0442\u0432\u0435\u0447\u0430\u0439 \u043f\u0440\u0430\u043a\u0442\u0438\u0447\u043d\u043e.\n"
            "\u041f\u0440\u0435\u0434\u043f\u043e\u0447\u0442\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442:\n"
            "\u041a\u043e\u0440\u043e\u0442\u043a\u0438\u0439 \u043e\u0442\u0432\u0435\u0442:\n"
            "\u0428\u0430\u0433\u0438:\n"
            "\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430:"
        ),
        "archivist": (
            "\u0420\u043e\u043b\u044c: \u0410\u0440\u0445\u0438\u0432\u0430\u0440\u0438\u0443\u0441.\n"
            "\u0421\u043e\u0445\u0440\u0430\u043d\u044f\u0439 \u0441\u043c\u044b\u0441\u043b \u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u0430 \u0438 \u0442\u043e\u0447\u043d\u043e \u043e\u0442\u0434\u0435\u043b\u044f\u0439 \u0438\u0437\u0432\u0435\u0441\u0442\u043d\u043e\u0435 \u043e\u0442 \u043d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u043e\u0433\u043e.\n"
            "\u041f\u0440\u0435\u0434\u043f\u043e\u0447\u0442\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442:\n"
            "\u041f\u0440\u044f\u043c\u043e\u0439 \u043e\u0442\u0432\u0435\u0442:\n"
            "\u041e\u043f\u043e\u0440\u0430 \u043d\u0430 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442:\n"
            "\u0427\u0435\u0433\u043e \u043d\u0435 \u0445\u0432\u0430\u0442\u0430\u0435\u0442:"
        ),
    },
}
STYLE_PROMPT_LIBRARY = {
    "en": {
        "concise": (
            "Style: concise. Keep the answer brief, clean, and free from repetition."
        ),
        "balanced": (
            "Style: balanced. Use moderate detail and clear section breaks."
        ),
        "detailed": (
            "Style: detailed. Be thorough, but stay grounded strictly in the context."
        ),
    },
    "ru": {
        "concise": (
            "\u0421\u0442\u0438\u043b\u044c: \u043a\u0440\u0430\u0442\u043a\u043e. \u041f\u0438\u0448\u0438 \u043a\u043e\u0440\u043e\u0442\u043a\u043e, \u043f\u043e \u0434\u0435\u043b\u0443 \u0438 \u0431\u0435\u0437 \u043f\u043e\u0432\u0442\u043e\u0440\u043e\u0432."
        ),
        "balanced": (
            "\u0421\u0442\u0438\u043b\u044c: \u0441\u0431\u0430\u043b\u0430\u043d\u0441\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u043e. \u0414\u0430\u0439 \u0434\u043e\u0441\u0442\u0430\u0442\u043e\u0447\u043d\u043e \u0434\u0435\u0442\u0430\u043b\u0435\u0439, \u043d\u043e \u0431\u0435\u0437 \u043b\u0438\u0448\u043d\u0435\u0439 \u0432\u043e\u0434\u044b."
        ),
        "detailed": (
            "\u0421\u0442\u0438\u043b\u044c: \u043f\u043e\u0434\u0440\u043e\u0431\u043d\u043e. \u0414\u0430\u0439 \u043f\u043e\u043b\u043d\u044b\u0439 \u0440\u0430\u0437\u0431\u043e\u0440, \u043d\u043e \u0441\u0442\u0440\u043e\u0433\u043e \u0432 \u0440\u0430\u043c\u043a\u0430\u0445 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442\u0430."
        ),
    },
}


def load_translations(lang: str):
    with open(LOCALES_DIR / "en.json", "r", encoding="utf-8") as fh:
        fallback = json.load(fh)
    locale_file = LOCALES_DIR / f"{lang}.json"
    if locale_file.exists():
        with open(locale_file, "r", encoding="utf-8") as fh:
            current = json.load(fh)
        if lang in PLACEHOLDER_TRANSLATION_PATTERNS:
            pattern = PLACEHOLDER_TRANSLATION_PATTERNS[lang]
            for key, value in list(current.items()):
                if not isinstance(value, str):
                    continue
                if value.count("?") < 3:
                    continue
                if pattern.match(value.strip()):
                    current[key] = fallback.get(key, value)
        merged = dict(fallback)
        merged.update(current)
        return merged
    return fallback


def translate(key: str, lang: str) -> str:
    return load_translations(lang).get(key, key)


def localize_context_header(header: str, t_local) -> str:
    localized = str(header or "")
    localized = localized.replace(
        "[unknown source]",
        f"[{t_local('context_source_unknown')}]",
    )
    localized = CONTEXT_HEADER_PAGE_RE.sub(
        lambda match: t_local("context_source_page").format(page=match.group("page")),
        localized,
    )
    localized = CONTEXT_HEADER_LINES_RE.sub(
        lambda match: t_local("context_source_lines").format(
            start=match.group("start"),
            end=match.group("end"),
        ),
        localized,
    )
    localized = CONTEXT_HEADER_LINE_RE.sub(
        lambda match: t_local("context_source_line").format(line=match.group("line")),
        localized,
    )
    return localized


def localize_context_preview(ctx_text: str, t_local) -> str:
    chunks = [chunk.strip() for chunk in str(ctx_text or "").split("\n---\n") if chunk.strip()]
    localized_chunks: list[str] = []
    for chunk in chunks:
        lines = chunk.splitlines()
        if not lines:
            continue
        lines[0] = localize_context_header(lines[0], t_local)
        localized_chunks.append("\n".join(lines))
    return "\n---\n".join(localized_chunks)


logging.basicConfig(
    filename=str(BASE_DIR / "localrag.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

_index_bootstrap_lock = threading.Lock()
_index_bootstrap_done = False


def ensure_index_ready_on_startup() -> None:
    global _index_bootstrap_done
    if _index_bootstrap_done:
        return
    with _index_bootstrap_lock:
        if _index_bootstrap_done:
            return
        if os.environ.get("SKIP_INDEX_BOOTSTRAP", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            logging.info("Skipping index bootstrap due to SKIP_INDEX_BOOTSTRAP")
            _index_bootstrap_done = True
            return
        if load_persisted_index():
            logging.info("Loaded persisted index on startup")
        else:
            rebuild_index()
            logging.info("Rebuilt index on startup")
        _index_bootstrap_done = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("LOCALRAG_SKIP_STARTUP", "").strip().lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        ensure_index_ready_on_startup()
    yield


TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"
APP_STATIC_DIR = BASE_DIR / "app" / "static"
app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
if APP_STATIC_DIR.exists():
    app.mount(
        "/app-static",
        StaticFiles(directory=str(APP_STATIC_DIR)),
        name="app-static",
    )
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
STATIC_VERSION = os.environ.get("STATIC_VERSION")
HISTORY_COOKIE_NAME = "localrag_session_id"
HISTORY_MAX_ITEMS = max(1, int(os.environ.get("HISTORY_MAX_ITEMS", "25")))
HISTORY_TEXT_LIMIT = max(200, int(os.environ.get("HISTORY_TEXT_LIMIT", "4000")))
DEFAULT_HISTORY_LIMIT = max(
    1,
    min(
        HISTORY_MAX_ITEMS,
        int(os.environ.get("DEFAULT_HISTORY_LIMIT", str(min(12, HISTORY_MAX_ITEMS)))),
    ),
)


def static_url(path: str) -> str:
    url = app.url_path_for("static", path=path)
    version = STATIC_VERSION
    if version is None:
        try:
            target = (STATIC_DIR / path).resolve()
            version = str(int(target.stat().st_mtime))
        except FileNotFoundError:
            version = None
    if version:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}v={version}"
    return url


templates.env.globals["static_url"] = static_url
templates.env.globals["default_history_limit"] = DEFAULT_HISTORY_LIMIT
templates.env.globals["history_max_items"] = HISTORY_MAX_ITEMS
templates.env.globals["default_role_style"] = DEFAULT_ROLE_STYLE
templates.env.globals["default_answer_language_setting"] = (
    DEFAULT_ANSWER_LANGUAGE_SETTING
)
templates.env.globals["app_version"] = APP_VERSION

llm_lock = asyncio.Lock()
_history_lock = threading.Lock()
_history_store: dict[str, deque[dict[str, Any]]] = {}
_model_pull_lock = threading.Lock()
_server_profile_lock = threading.Lock()
_model_pull_state: dict[str, Any] = {
    "active": False,
    "model": "",
    "status": "idle",
    "completed": None,
    "total": None,
    "error": "",
    "started_at": None,
    "finished_at": None,
}
_embedding_model_pull_lock = threading.Lock()
_embedding_model_pull_state: dict[str, Any] = {
    "active": False,
    "model": "",
    "status": "idle",
    "error": "",
    "started_at": None,
    "finished_at": None,
}


def normalize_role(raw_role: str | None) -> str:
    role = (raw_role or "").strip().lower()
    if role in ROLE_PRESETS:
        return role
    return DEFAULT_ROLE


def normalize_role_id(raw_role: Any) -> str:
    role = str(raw_role or "").strip().lower()
    if role in ROLE_PRESETS:
        return role
    if role.startswith("custom-") and ROLE_ID_PATTERN.match(role):
        return role
    return DEFAULT_ROLE


def trim_role_label(raw_value: Any) -> str:
    value = str(raw_value or "").strip()
    if len(value) <= 80:
        return value
    return value[:77] + "..."


def get_role_display_name(role: str, t_local, fallback_label: str | None = None) -> str:
    role_value = normalize_role_id(role)
    if role_value in ROLE_PRESETS:
        return t_local(ROLE_PRESETS[role_value]["label_key"])
    fallback = trim_role_label(fallback_label)
    if fallback:
        return fallback
    return role_value.replace("_", " ").replace("-", " ").title()


def normalize_role_style(raw_style: str | None) -> str:
    style = (raw_style or "").strip().lower()
    if style in ROLE_STYLE_PRESETS:
        return style
    return DEFAULT_ROLE_STYLE


def normalize_lang(raw_lang: str | None) -> str:
    lang = (raw_lang or "").strip().lower()
    if lang in LANGS:
        return lang
    return DEFAULT_LANG


def normalize_answer_language_setting(raw_value: Any) -> str:
    value = str(raw_value or "").strip().lower()
    if value in {"", "inherit", "interface", "ui", "default"}:
        return DEFAULT_ANSWER_LANGUAGE_SETTING
    if value in LANGS:
        return value
    return DEFAULT_ANSWER_LANGUAGE_SETTING


def get_app_meta() -> dict[str, Any]:
    workspace_files_path = str((BASE_DIR / "files").resolve())
    meta: dict[str, Any] = {
        "name": APP_NAME,
        "version": APP_VERSION,
        "author_name": "Sergey360",
        "author_url": "https://github.com/Sergey360",
        "github_url": "https://github.com/Sergey360/LocalRAG",
        "default_model": get_default_model([]),
        "embedding_model": get_embedding_model_name(),
        "default_embedding_model": get_default_embedding_model_name(),
        "docs_path": get_docs_path_display(),
        "default_docs_path": get_default_docs_path_display(),
        "workspace_files_path": workspace_files_path,
        "supported_languages": list(LANGS),
        "default_answer_language_setting": DEFAULT_ANSWER_LANGUAGE_SETTING,
        "history_max_items": HISTORY_MAX_ITEMS,
        "default_history_limit": DEFAULT_HISTORY_LIMIT,
        "embedding_runtime": get_embedding_runtime_info(),
    }
    if BUILD_DATE_UTC:
        meta["build_date_utc"] = BUILD_DATE_UTC
    return meta


def resolve_answer_language(raw_answer_language: str | None, ui_lang: str) -> str:
    value = (raw_answer_language or "").strip().lower()
    if value in {"", "interface", "ui", "default"}:
        return normalize_lang(ui_lang)
    return normalize_lang(value)


def resolve_role_style_for_request(
    raw_style: Any,
    custom_role: dict[str, str] | None = None,
) -> str:
    value = str(raw_style or "").strip().lower()
    if value in ROLE_STYLE_PRESETS:
        return value
    if custom_role:
        fallback = normalize_custom_role_style(custom_role.get("default_style"))
        if fallback:
            return fallback
    return DEFAULT_ROLE_STYLE


def resolve_answer_language_for_request(
    raw_answer_language: Any,
    ui_lang: str,
    custom_role: dict[str, str] | None = None,
) -> str:
    value = str(raw_answer_language or "").strip().lower()
    if value and value not in {"interface", "ui", "default", "inherit"}:
        return normalize_lang(value)
    if custom_role:
        role_setting = normalize_answer_language_setting(custom_role.get("answer_language"))
        if role_setting != DEFAULT_ANSWER_LANGUAGE_SETTING:
            return normalize_lang(role_setting)
    return normalize_lang(ui_lang)


def resolve_model_for_request(
    raw_model: Any,
    available_models: list[str],
    custom_role: dict[str, str] | None = None,
) -> str:
    model = normalize_model_name(raw_model)
    if model and model in available_models:
        return model
    if custom_role:
        role_model = normalize_model_name(custom_role.get("default_model"))
        if role_model and role_model in available_models:
            return role_model
    default_model = get_default_model(available_models)
    if default_model in available_models:
        return default_model
    return available_models[0] if available_models else ""


def normalize_model_name(raw_value: Any) -> str:
    value = str(raw_value or "").strip()
    if not value:
        return ""
    if not MODEL_NAME_PATTERN.match(value):
        return ""
    return value


def get_role_image_values() -> set[str]:
    return {
        str(item.get("value") or "").strip()
        for item in ROLE_IMAGE_LIBRARY
        if str(item.get("value") or "").strip()
    }


def normalize_custom_role_style(raw_value: Any) -> str:
    value = str(raw_value or "").strip().lower()
    if value in {"", "inherit"}:
        return ""
    if value in ROLE_STYLE_PRESETS:
        return value
    return ""


def normalize_custom_role_profile(raw_role: Any) -> dict[str, str] | None:
    if not isinstance(raw_role, dict):
        return None
    role_id = normalize_role_id(raw_role.get("id"))
    if role_id in ROLE_PRESETS:
        return None
    if not role_id.startswith("custom-"):
        return None
    name = trim_role_label(raw_role.get("name") or raw_role.get("label") or "").strip()
    prompt = str(raw_role.get("prompt") or "").strip()
    if not name or not prompt:
        return None
    image = str(raw_role.get("image") or "").strip()
    if image not in get_role_image_values():
        image = ROLE_IMAGE_LIBRARY[0]["value"] if ROLE_IMAGE_LIBRARY else ""
    return {
        "id": role_id,
        "name": name,
        "description": str(raw_role.get("description") or "").strip(),
        "prompt": prompt,
        "image": image,
        "answer_language": normalize_answer_language_setting(
            raw_role.get("answerLanguage") or raw_role.get("answer_language") or "interface"
        ),
        "default_model": normalize_model_name(
            raw_role.get("defaultModel") or raw_role.get("default_model") or ""
        ),
        "default_style": normalize_custom_role_style(
            raw_role.get("defaultStyle") or raw_role.get("default_style") or ""
        ),
    }


def normalize_custom_roles_payload(raw_roles: Any) -> list[dict[str, str]]:
    source = raw_roles if isinstance(raw_roles, list) else []
    normalized: list[dict[str, str]] = []
    used_ids: set[str] = set()
    for raw_role in source:
        role = normalize_custom_role_profile(raw_role)
        if not role:
            continue
        role_id = role["id"]
        if role_id in used_ids:
            continue
        used_ids.add(role_id)
        normalized.append(role)
    return normalized


def get_default_server_profile() -> dict[str, Any]:
    return {"custom_roles": []}


def load_server_profile() -> dict[str, Any]:
    with _server_profile_lock:
        if not SERVER_PROFILE_FILE.exists():
            return get_default_server_profile()
        try:
            payload = json.loads(SERVER_PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception:
            logging.warning("Failed to read server profile from %s", SERVER_PROFILE_FILE)
            return get_default_server_profile()
        if not isinstance(payload, dict):
            return get_default_server_profile()
        return {
            "custom_roles": normalize_custom_roles_payload(payload.get("custom_roles")),
        }


def save_server_profile(profile: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "custom_roles": normalize_custom_roles_payload(profile.get("custom_roles")),
    }
    with _server_profile_lock:
        SERVER_PROFILE_FILE.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return normalized


def get_server_profile() -> dict[str, Any]:
    return load_server_profile()


def get_server_custom_roles() -> list[dict[str, str]]:
    return list(get_server_profile().get("custom_roles") or [])


def get_server_custom_role(role_id: str | None) -> dict[str, str] | None:
    normalized_role = normalize_role_id(role_id)
    for role in get_server_custom_roles():
        if role.get("id") == normalized_role:
            return dict(role)
    return None


def set_server_custom_roles(raw_roles: Any) -> list[dict[str, str]]:
    profile = save_server_profile({"custom_roles": raw_roles})
    return list(profile.get("custom_roles") or [])


def translate_model_manager_message(message_key: str, t_local, **params: Any) -> str:
    mapping = {
        "invalid_model_name": "models_invalid_name",
        "pull_busy": "models_pull_busy",
        "pull_started": "models_pull_started",
        "model_deleted": "models_delete_success",
    }
    translation_key = mapping.get(message_key)
    if translation_key:
        try:
            return t_local(translation_key).format(**params)
        except Exception:
            return t_local(translation_key)
    raw_text = str(message_key or "").strip()
    if not raw_text:
        return t_local("models_unavailable")
    if "pull model manifest: file does not exist" in raw_text:
        try:
            return t_local("models_not_found_in_ollama").format(**params)
        except Exception:
            return t_local("models_not_found_in_ollama")
    if raw_text.startswith(t_local("error_prefix")):
        return raw_text
    return f"{t_local('error_prefix')}{raw_text}"


def get_pull_status_label(
    status: str,
    t_local,
    error: str = "",
    *,
    model: str = "",
) -> str:
    normalized = str(status or "idle").strip().lower()
    mapping = {
        "idle": "models_pull_status_idle",
        "starting": "models_pull_status_starting",
        "pulling": "models_pull_status_pulling",
        "success": "models_pull_status_success",
        "completed": "models_pull_status_success",
        "error": "models_pull_status_error",
    }
    key = mapping.get(normalized, "models_pull_status_pulling")
    template = t_local(key)
    if normalized == "error" and "pull model manifest: file does not exist" in str(error or ""):
        try:
            return t_local("models_not_found_in_ollama").format(model=model or "-")
        except Exception:
            return t_local("models_not_found_in_ollama")
    if "{error}" in template:
        return template.format(error=error or "-")
    return template


def get_language_label_key(lang: str) -> str:
    return {
        "en": "language_en",
        "ru": "language_ru",
        "nl": "language_nl",
        "zh": "language_zh",
        "he": "language_he",
    }.get(normalize_lang(lang), "language_en")


def get_language_labels(t_local) -> dict[str, str]:
    labels = {"interface": t_local("answer_language_interface")}
    for lang in LANGS:
        labels[lang] = t_local(get_language_label_key(lang))
    return labels


def format_role_image_label(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def get_role_image_catalog(t_local) -> dict[str, dict[str, Any]]:
    shared_options: list[dict[str, str]] = []
    for item in ROLE_IMAGE_LIBRARY:
        value = str(item.get("value") or "").strip()
        if not value:
            continue
        shared_options.append(
            {
                "value": value,
                "label": format_role_image_label(value),
                "src": static_url(str(item.get("path") or "")),
            }
        )

    options_by_value = {option["value"]: option for option in shared_options}
    catalog: dict[str, dict[str, Any]] = {}
    for role in ROLE_PRESETS:
        default_value = ROLE_IMAGE_DEFAULTS.get(role, "")
        default_src = options_by_value.get(default_value, {}).get("src", "")
        if not default_src and shared_options:
            default_value = shared_options[0]["value"]
            default_src = shared_options[0]["src"]
        catalog[role] = {
            "default": default_value,
            "default_src": default_src,
            "options": list(shared_options),
        }
    catalog["_shared"] = {
        "default": shared_options[0]["value"] if shared_options else "",
        "default_src": shared_options[0]["src"] if shared_options else "",
        "options": list(shared_options),
    }
    return catalog


def get_default_role_definitions(t_local) -> list[dict[str, str]]:
    catalog = get_role_image_catalog(t_local)
    definitions: list[dict[str, str]] = []
    for role_id, preset in ROLE_PRESETS.items():
        role_catalog = catalog.get(role_id, {})
        definitions.append(
            {
                "id": role_id,
                "label": t_local(preset["label_key"]),
                "description": t_local(f"{preset['label_key']}_desc"),
                "image": str(role_catalog.get("default") or ""),
                "image_src": str(role_catalog.get("default_src") or ""),
                "builtin": "1",
            }
        )
    return definitions


def get_recommended_models(t_local) -> list[dict[str, str]]:
    return [
        {
            "name": item["name"],
            "summary": t_local(item["summary_key"]),
        }
        for item in RECOMMENDED_MODEL_CATALOG
    ]


def get_model_manager_i18n(t_local) -> dict[str, str]:
    keys = [
        "settings_model_manager",
        "settings_model_manager_hint",
        "models_installed",
        "models_recommended",
        "models_manual_add",
        "models_manual_placeholder",
        "models_pull_button",
        "models_delete_button",
        "models_use_default",
        "models_default_badge",
        "models_default_active",
        "models_installed_badge",
        "models_recommended_for_language",
        "models_refresh",
        "models_invalid_name",
        "models_unavailable",
        "models_no_installed",
        "models_no_recommended",
        "models_size",
        "models_family",
        "models_params",
        "models_quantization",
        "models_added",
        "models_status",
        "models_pull_active",
        "models_pull_completed",
        "models_delete_confirm",
        "models_manual_hint",
        "models_not_found_in_ollama",
    ]
    return {key: t_local(key) for key in keys}


def get_settings_i18n(t_local) -> dict[str, str]:
    keys = [
        "docs_browser_search_placeholder",
        "settings_embedding_model",
        "settings_embedding_model_hint",
        "settings_embedding_model_custom",
        "settings_embedding_model_custom_placeholder",
        "settings_embedding_model_updated",
        "settings_embedding_model_invalid",
        "settings_embedding_model_selected",
        "settings_embedding_runtime",
        "settings_embedding_model_manager_hint",
        "embedding_models_available",
        "embedding_models_recommended",
        "embedding_models_no_available",
        "embedding_models_no_recommended",
        "embedding_models_cached_badge",
        "embedding_models_current_badge",
        "embedding_models_local_path_badge",
        "embedding_models_use_button",
        "embedding_models_prepare_button",
        "embedding_models_prepare_started",
        "embedding_models_prepare_busy",
        "embedding_models_prepare_status_idle",
        "embedding_models_prepare_status_starting",
        "embedding_models_prepare_status_loading",
        "embedding_models_prepare_status_success",
        "embedding_models_prepare_status_error",
        "embedding_models_invalid_name",
        "embedding_model_catalog_e5_large",
        "embedding_model_catalog_bge_m3",
        "embedding_model_catalog_gte_multilingual_base",
        "settings_tabs_label",
        "settings_tab_general",
        "settings_tab_models",
        "settings_tab_roles",
        "settings_custom_roles",
        "settings_custom_roles_hint",
        "settings_custom_roles_empty",
        "settings_custom_roles_name",
        "settings_custom_roles_description",
        "settings_custom_roles_prompt",
        "settings_custom_roles_image",
        "settings_custom_roles_answer_language",
        "settings_custom_roles_default_model",
        "settings_custom_roles_default_model_inherit",
        "settings_custom_roles_default_style",
        "settings_custom_roles_default_style_inherit",
        "settings_custom_roles_save",
        "settings_custom_roles_update",
        "settings_custom_roles_clear",
        "settings_custom_roles_export",
        "settings_custom_roles_import",
        "settings_custom_roles_reset",
        "settings_custom_roles_edit",
        "settings_custom_roles_delete",
        "settings_custom_roles_name_placeholder",
        "settings_custom_roles_description_placeholder",
        "settings_custom_roles_prompt_placeholder",
        "settings_custom_roles_saved",
        "settings_custom_roles_deleted",
        "settings_custom_roles_delete_confirm",
        "settings_custom_roles_name_required",
        "settings_custom_roles_prompt_required",
        "settings_custom_roles_import_invalid",
        "settings_custom_roles_import_success",
        "settings_custom_roles_reset_confirm",
        "settings_custom_roles_reset_done",
        "style_concise",
        "style_balanced",
        "style_detailed",
    ]
    return {key: t_local(key) for key in keys}


def get_model_pull_state() -> dict[str, Any]:
    with _model_pull_lock:
        return dict(_model_pull_state)


def update_model_pull_state(**changes: Any) -> dict[str, Any]:
    with _model_pull_lock:
        _model_pull_state.update(changes)
        return dict(_model_pull_state)


def reset_model_pull_state() -> dict[str, Any]:
    return update_model_pull_state(
        active=False,
        model="",
        status="idle",
        completed=None,
        total=None,
        error="",
        started_at=None,
        finished_at=None,
    )


def get_embedding_model_pull_state() -> dict[str, Any]:
    with _embedding_model_pull_lock:
        return dict(_embedding_model_pull_state)


def update_embedding_model_pull_state(**changes: Any) -> dict[str, Any]:
    with _embedding_model_pull_lock:
        _embedding_model_pull_state.update(changes)
        return dict(_embedding_model_pull_state)


def reset_embedding_model_pull_state() -> dict[str, Any]:
    return update_embedding_model_pull_state(
        active=False,
        model="",
        status="idle",
        error="",
        started_at=None,
        finished_at=None,
    )


def fetch_ollama_model_inventory() -> list[dict[str, Any]]:
    response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
    response.raise_for_status()
    payload = response.json()
    models = payload.get("models", [])
    inventory: list[dict[str, Any]] = []
    for raw_item in models:
        if not isinstance(raw_item, dict):
            continue
        name = str(raw_item.get("name") or "").strip()
        if not name:
            continue
        details = raw_item.get("details")
        if not isinstance(details, dict):
            details = {}
        inventory.append(
            {
                "name": name,
                "size": raw_item.get("size"),
                "modified_at": raw_item.get("modified_at"),
                "digest": raw_item.get("digest"),
                "details": {
                    "family": details.get("family"),
                    "families": details.get("families"),
                    "parameter_size": details.get("parameter_size"),
                    "quantization_level": details.get("quantization_level"),
                    "format": details.get("format"),
                },
            }
        )
    return inventory


def get_recommended_embedding_models(t_local) -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    for item in RECOMMENDED_EMBEDDING_MODEL_CATALOG:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        models.append(
            {
                "name": name,
                "summary": t_local(str(item.get("summary_key") or "")),
                "available": is_embedding_model_available_locally(name),
            }
        )
    return models


def build_model_manager_payload(t_local) -> dict[str, Any]:
    try:
        installed = fetch_ollama_model_inventory()
        installed_names = [item["name"] for item in installed]
        pull_state = get_model_pull_state()
        pull_state["label"] = get_pull_status_label(
            str(pull_state.get("status") or ""),
            t_local,
            str(pull_state.get("error") or ""),
            model=str(pull_state.get("model") or ""),
        )
        payload = {
            "ok": True,
            "installed": installed,
            "default_model": get_default_model(installed_names),
            "recommended": get_recommended_models(t_local),
            "pull": pull_state,
        }
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to build model manager payload: %s", exc)
        pull_state = get_model_pull_state()
        pull_state["label"] = get_pull_status_label(
            str(pull_state.get("status") or ""),
            t_local,
            str(pull_state.get("error") or ""),
            model=str(pull_state.get("model") or ""),
        )
        payload = {
            "ok": False,
            "installed": [],
            "default_model": "",
            "recommended": get_recommended_models(t_local),
            "pull": pull_state,
            "message": f"{t_local('error_prefix')}{t_local('models_unavailable')}",
        }
    return payload


def translate_embedding_model_manager_message(
    message_key: str, t_local, **params: Any
) -> str:
    mapping = {
        "invalid_embedding_model_name": "embedding_models_invalid_name",
        "prepare_busy": "embedding_models_prepare_busy",
        "prepare_started": "embedding_models_prepare_started",
    }
    translation_key = mapping.get(message_key)
    if translation_key:
        try:
            return t_local(translation_key).format(**params)
        except Exception:
            return t_local(translation_key)
    raw_text = str(message_key or "").strip()
    if not raw_text:
        return t_local("embedding_models_invalid_name")
    if raw_text.startswith(t_local("error_prefix")):
        return raw_text
    return f"{t_local('error_prefix')}{raw_text}"


def get_embedding_pull_status_label(status: str, t_local, error: str = "") -> str:
    normalized = str(status or "idle").strip().lower()
    mapping = {
        "idle": "embedding_models_prepare_status_idle",
        "starting": "embedding_models_prepare_status_starting",
        "loading": "embedding_models_prepare_status_loading",
        "success": "embedding_models_prepare_status_success",
        "completed": "embedding_models_prepare_status_success",
        "error": "embedding_models_prepare_status_error",
    }
    key = mapping.get(normalized, "embedding_models_prepare_status_loading")
    template = t_local(key)
    if "{error}" in template:
        return template.format(error=error or "-")
    return template


def build_embedding_model_manager_payload(t_local) -> dict[str, Any]:
    pull_state = get_embedding_model_pull_state()
    pull_state["label"] = get_embedding_pull_status_label(
        str(pull_state.get("status") or ""),
        t_local,
        str(pull_state.get("error") or ""),
    )
    current_model = get_embedding_model_name()
    available_models = list_available_embedding_models()
    return {
        "ok": True,
        "current_model": current_model,
        "default_model": get_default_embedding_model_name(),
        "available": available_models,
        "recommended": get_recommended_embedding_models(t_local),
        "pull": pull_state,
        "runtime": get_embedding_runtime_info(),
    }


def _pull_model_worker(model_name: str) -> None:
    try:
        with requests.post(
            f"{OLLAMA_BASE_URL}/api/pull",
            json={"model": model_name, "stream": True},
            stream=True,
            timeout=(10, 1800),
        ) as response:
            response.raise_for_status()
            saw_updates = False
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                try:
                    event = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                if event.get("error"):
                    update_model_pull_state(
                        active=False,
                        model=model_name,
                        status="error",
                        error=str(event.get("error") or ""),
                        finished_at=datetime.now(timezone.utc).isoformat(),
                    )
                    return
                saw_updates = True
                update_model_pull_state(
                    active=True,
                    model=model_name,
                    status=str(event.get("status") or "pulling"),
                    completed=event.get("completed"),
                    total=event.get("total"),
                    error="",
                )
            final_status = "success" if saw_updates else "completed"
            update_model_pull_state(
                active=False,
                model=model_name,
                status=final_status,
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
    except Exception as exc:  # noqa: BLE001
        logging.error("Model pull failed for %s: %s", model_name, exc)
        update_model_pull_state(
            active=False,
            model=model_name,
            status="error",
            error=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )


def start_model_pull(model_name: str) -> dict[str, Any]:
    normalized = normalize_model_name(model_name)
    if not normalized:
        return {"ok": False, "message": "invalid_model_name"}
    with _model_pull_lock:
        if _model_pull_state.get("active"):
            current_model = str(_model_pull_state.get("model") or "")
            return {
                "ok": False,
                "message": "pull_busy",
                "model": current_model,
            }
        _model_pull_state.update(
            {
                "active": True,
                "model": normalized,
                "status": "starting",
                "completed": None,
                "total": None,
                "error": "",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None,
            }
        )
    threading.Thread(
        target=_pull_model_worker,
        args=(normalized,),
        daemon=True,
    ).start()
    return {"ok": True, "message": "pull_started", "model": normalized}


def _prepare_embedding_model_worker(model_name: str) -> None:
    try:
        update_embedding_model_pull_state(
            active=True,
            model=model_name,
            status="loading",
            error="",
        )
        prepare_embedding_model_artifact(model_name)
        update_embedding_model_pull_state(
            active=False,
            model=model_name,
            status="success",
            error="",
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:  # noqa: BLE001
        logging.error("Embedding model prepare failed for %s: %s", model_name, exc)
        update_embedding_model_pull_state(
            active=False,
            model=model_name,
            status="error",
            error=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )


def start_embedding_model_pull(model_name: str) -> dict[str, Any]:
    normalized = normalize_embedding_model_name(model_name)
    if not normalized:
        return {"ok": False, "message": "invalid_embedding_model_name"}
    with _embedding_model_pull_lock:
        if _embedding_model_pull_state.get("active"):
            current_model = str(_embedding_model_pull_state.get("model") or "")
            return {
                "ok": False,
                "message": "prepare_busy",
                "model": current_model,
            }
        _embedding_model_pull_state.update(
            {
                "active": True,
                "model": normalized,
                "status": "starting",
                "error": "",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None,
            }
        )
    threading.Thread(
        target=_prepare_embedding_model_worker,
        args=(normalized,),
        daemon=True,
    ).start()
    return {"ok": True, "message": "prepare_started", "model": normalized}


def delete_ollama_model(model_name: str) -> dict[str, Any]:
    normalized = normalize_model_name(model_name)
    if not normalized:
        return {"ok": False, "message": "invalid_model_name"}
    pull_state = get_model_pull_state()
    if pull_state.get("active"):
        return {"ok": False, "message": "pull_busy", "model": pull_state.get("model")}
    try:
        response = requests.delete(
            f"{OLLAMA_BASE_URL}/api/delete",
            json={"model": normalized},
            timeout=60,
        )
        response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to delete model %s: %s", normalized, exc)
        return {"ok": False, "message": str(exc)}
    return {"ok": True, "message": "model_deleted", "model": normalized}


def get_prompt_library_lang(lang: str) -> str:
    normalized = normalize_lang(lang)
    if normalized == "ru":
        return "ru"
    return "en"


def get_role_prompt_defaults(lang: str) -> dict[str, str]:
    prompt_lang = get_prompt_library_lang(lang)
    return dict(ROLE_PROMPT_LIBRARY[prompt_lang])


def get_all_role_prompt_defaults() -> dict[str, dict[str, str]]:
    return {lang: get_role_prompt_defaults(lang) for lang in LANGS}


def build_role_prompt(
    lang: str,
    role: str,
    role_style: str,
    custom_role_prompt: str | None = None,
) -> str:
    normalized_lang = normalize_lang(lang)
    role_value = normalize_role(role)
    style_value = normalize_role_style(role_style)
    prompt_lang = get_prompt_library_lang(normalized_lang)
    role_prompt_text = (custom_role_prompt or "").strip() or ROLE_PROMPT_LIBRARY[
        prompt_lang
    ][role_value]
    base_rule = PROMPT_LANGUAGE_RULES.get(
        normalized_lang, PROMPT_LANGUAGE_RULES[DEFAULT_LANG]
    )
    context_rule = {
        "ru": (
            "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439 \u0442\u043e\u043b\u044c\u043a\u043e \u043f\u0440\u0435\u0434\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u043d\u044b\u0439 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442. \u0415\u0441\u043b\u0438 \u043e\u0442\u0432\u0435\u0442\u0430 \u0432 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442\u0435 \u043d\u0435\u0442, "
            "\u0441\u043a\u0430\u0436\u0438 \u043e\u0431 \u044d\u0442\u043e\u043c \u043f\u0440\u044f\u043c\u043e \u0438 \u043d\u0435 \u0434\u043e\u0434\u0443\u043c\u044b\u0432\u0430\u0439."
        ),
        "en": (
            "Use only the provided context. If the answer is not present in the "
            "context, say so clearly."
        ),
    }[prompt_lang]
    return "\n\n".join(
        [
            base_rule,
            context_rule,
            role_prompt_text,
            STYLE_PROMPT_LIBRARY[prompt_lang][style_value],
        ]
    )


def parse_debug_mode(raw_value: str | None) -> bool:
    value = (raw_value or "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def normalize_history_limit(raw_value: str | int | None) -> int:
    try:
        value = int(raw_value) if raw_value is not None else DEFAULT_HISTORY_LIMIT
    except Exception:
        value = DEFAULT_HISTORY_LIMIT
    return max(1, min(HISTORY_MAX_ITEMS, value))


def ensure_session_id(raw_session_id: str | None) -> str:
    session_id = (raw_session_id or "").strip()
    return session_id or uuid.uuid4().hex


def trim_history_text(value: str) -> str:
    text = str(value or "").strip()
    if len(text) <= HISTORY_TEXT_LIMIT:
        return text
    return text[: HISTORY_TEXT_LIMIT - 3] + "..."


def append_history_entry(
    session_id: str,
    *,
    question: str,
    answer: str,
    status: str,
    model: str,
    top_k: int | None,
    role: str,
    role_label: str = "",
    role_style: str,
) -> None:
    role_value = normalize_role_id(role)
    role_style_value = normalize_role_style(role_style)
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "question": trim_history_text(question),
        "answer": trim_history_text(answer),
        "status": status,
        "model": trim_history_text(model),
        "top_k": top_k,
        "role": role_value,
        "role_label": trim_role_label(role_label),
        "role_style": role_style_value,
    }
    with _history_lock:
        history = _history_store.get(session_id)
        if history is None:
            history = deque(maxlen=HISTORY_MAX_ITEMS)
            _history_store[session_id] = history
        history.append(entry)


def list_history_entries(session_id: str) -> list[dict[str, Any]]:
    with _history_lock:
        history = _history_store.get(session_id)
        if history is None:
            return []
        return list(history)


def clear_history_entries(session_id: str) -> None:
    with _history_lock:
        _history_store.pop(session_id, None)


def render_history_fragment(entries: list[dict[str, Any]], t_local) -> str:
    clear_disabled = " disabled aria-disabled=\"true\"" if not entries else ""
    title = html.escape(t_local("history_title"))
    clear_label = html.escape(t_local("history_clear"))
    question_label = html.escape(t_local("history_question"))
    answer_label = html.escape(t_local("history_answer"))
    model_label = html.escape(t_local("history_model"))
    top_k_label = html.escape(t_local("history_topk"))
    empty_label = html.escape(t_local("history_empty"))
    if entries:
        items: list[str] = []
        for entry in reversed(entries):
            status = str(entry.get("status") or "error")
            is_ok = status == "ok"
            status_key = "history_status_ok" if is_ok else "history_status_error"
            status_class = "is-ok" if is_ok else "is-error"
            status_label = html.escape(t_local(status_key))
            timestamp = html.escape(str(entry.get("timestamp") or ""))
            question = html.escape(str(entry.get("question") or ""))
            answer = html.escape(str(entry.get("answer") or ""))
            model = html.escape(str(entry.get("model") or "-"))
            role_value = normalize_role_id(str(entry.get("role") or DEFAULT_ROLE))
            role_name = html.escape(
                get_role_display_name(
                    role_value,
                    t_local,
                    str(entry.get("role_label") or ""),
                )
            )
            style_value = normalize_role_style(
                str(entry.get("role_style") or DEFAULT_ROLE_STYLE)
            )
            style_name = html.escape(
                t_local(ROLE_STYLE_PRESETS[style_value]["label_key"])
            )
            top_k_raw = entry.get("top_k")
            top_k = html.escape(str(top_k_raw)) if top_k_raw is not None else "-"
            role_label = html.escape(t_local("history_role"))
            style_label = html.escape(t_local("history_style"))
            items.append(
                '<article class="history-item">'
                '<div class="history-item-meta">'
                f'<time class="history-time">{timestamp}</time>'
                f'<span class="history-status {status_class}">{status_label}</span>'
                "</div>"
                '<div class="history-row">'
                f'<span class="history-label">{question_label}</span>'
                f'<p class="history-value">{question}</p>'
                "</div>"
                '<div class="history-row">'
                f'<span class="history-label">{answer_label}</span>'
                f'<pre class="history-value history-answer">{answer}</pre>'
                "</div>"
                '<div class="history-tech">'
                f"{role_label}: <code>{role_name}</code> | "
                f"{style_label}: <code>{style_name}</code> | "
                f"{model_label}: <code>{model}</code> | "
                f"{top_k_label}: <code>{top_k}</code>"
                "</div>"
                "</article>"
            )
        body = "".join(items)
    else:
        body = f'<p class="muted history-empty">{empty_label}</p>'
    return (
        '<div class="history-head">'
        f"<h2>{title}</h2>"
        f'<button class="outline history-clear-btn" hx-post="/api/history/clear" '
        f'hx-target="#history-card" hx-swap="innerHTML"{clear_disabled}>{clear_label}</button>'
        "</div>"
        f'<div class="history-list">{body}</div>'
    )


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    lang: str = Cookie(DEFAULT_LANG),
    session_id: str | None = Cookie(default=None, alias=HISTORY_COOKIE_NAME),
):
    translations = load_translations(lang)
    resolved_session_id = ensure_session_id(session_id)

    def t_local(key: str):
        return translations.get(key, key)

    response = templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "lang": lang,
            "t": t_local,
            "index_status_code": get_index_status_meta()[0],
            "app_meta": get_app_meta(),
            "role_prompt_defaults_by_lang": get_all_role_prompt_defaults(),
            "language_labels": get_language_labels(t_local),
            "role_image_catalog": get_role_image_catalog(t_local),
            "default_role_definitions": get_default_role_definitions(t_local),
            "embedding_model_catalog": [
                str(item.get("name") or "").strip()
                for item in RECOMMENDED_EMBEDDING_MODEL_CATALOG
                if str(item.get("name") or "").strip()
            ],
            "server_profile": get_server_profile(),
            "settings_i18n": get_settings_i18n(t_local),
            "model_manager_i18n": get_model_manager_i18n(t_local),
        },
    )
    response.set_cookie("lang", lang)
    response.set_cookie(
        HISTORY_COOKIE_NAME,
        resolved_session_id,
        httponly=True,
        samesite="lax",
    )
    return response


@app.post("/api/ask", response_class=HTMLResponse)
async def api_ask(
    request: Request,
    lang: str = Cookie(DEFAULT_LANG),
    session_id: str | None = Cookie(default=None, alias=HISTORY_COOKIE_NAME),
):
    form = await request.form()
    translations = load_translations(lang)
    resolved_session_id = ensure_session_id(session_id)

    def t_local(key: str):
        return translations.get(key, key)

    question = form.get("question", "").strip()
    requested_model = form.get("model", "").strip()
    model = requested_model
    role = normalize_role_id(form.get("role", DEFAULT_ROLE))
    custom_role = get_server_custom_role(role)
    role_label = trim_role_label(
        form.get("role_label", "") or (custom_role or {}).get("name", "")
    )
    role_style = resolve_role_style_for_request(
        form.get("role_style"),
        custom_role,
    )
    custom_role_prompt = (
        str((custom_role or {}).get("prompt") or "").strip()
        or form.get("custom_role_prompt", "").strip()
    )
    answer_lang = resolve_answer_language_for_request(
        form.get("answer_language"),
        lang,
        custom_role,
    )
    debug_mode = parse_debug_mode(form.get("debug_mode", "0"))
    raw_topk = form.get("topk", str(DEFAULT_TOP_K))
    top_k: int | None = None
    started_at = datetime.now(timezone.utc)
    user_ip = request.client.host if request.client else "unknown"
    logging.info(
        "Ask request from %s | ui_lang=%s | answer_lang=%s | model=%s | role=%s | style=%s | debug=%s | q='%s...'",
        user_ip,
        lang,
        answer_lang,
        requested_model,
        role,
        role_style,
        debug_mode,
        question[:40],
    )

    def elapsed_ms() -> int:
        return int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)

    def answer_fragment(message: str, *, is_error: bool = False) -> str:
        safe_text = html.escape(message)
        class_attr = ' class="error"' if is_error else ""
        alert = (
            f'<script>showAlert({json.dumps(message)}, "error", 5000);</script>'
            if is_error
            else ""
        )
        return (
            f"{alert}"
            f'<div class="field">'
            f'<label for="answer">{t_local("answer_label")}</label>'
            f'<textarea id="answer" rows="6" readonly{class_attr}>{safe_text}</textarea>'
            f"</div>"
        )

    def html_response(content: str) -> HTMLResponse:
        response = HTMLResponse(content)
        response.set_cookie("lang", lang)
        response.set_cookie(
            HISTORY_COOKIE_NAME,
            resolved_session_id,
            httponly=True,
            samesite="lax",
        )
        return response

    def debug_fragment(status_code: str, retrieval_rows: list[dict[str, Any]] | None = None) -> str:
        if not debug_mode:
            return ""
        role_text = html.escape(get_role_display_name(role, t_local, role_label))
        style_text = html.escape(t_local(ROLE_STYLE_PRESETS[role_style]["label_key"]))
        answer_lang_text = html.escape(
            get_language_labels(t_local).get(answer_lang, answer_lang)
        )
        model_text = html.escape(model or "-")
        top_k_text = html.escape(str(top_k if top_k is not None else "-"))
        status_text = html.escape(status_code)
        latency_text = html.escape(str(elapsed_ms()))
        retrieval_html = ""
        if retrieval_rows:
            retrieval_items = []
            for row in retrieval_rows:
                title_match_badge = (
                    f'<span class="debug-pill">{html.escape(t_local("debug_retrieval_title_match"))}</span>'
                    if row.get("exact_source_title_match")
                    else ""
                )
                all_terms_badge = (
                    f'<span class="debug-pill">{html.escape(t_local("debug_retrieval_all_terms"))}</span>'
                    if row.get("all_terms_present")
                    else ""
                )
                metrics = [
                    f'{html.escape(t_local("debug_retrieval_score"))}: {html.escape(str(row.get("score", "-")))}',
                    f'{html.escape(t_local("debug_retrieval_vector"))}: {html.escape(str(row.get("vector_bonus", "-")))}',
                    f'{html.escape(t_local("debug_retrieval_source_overlap"))}: {html.escape(str(row.get("source_overlap", "-")))}',
                    f'{html.escape(t_local("debug_retrieval_focus_overlap"))}: {html.escape(str(row.get("source_focus_overlap", "-")))}',
                    f'{html.escape(t_local("debug_retrieval_content_overlap"))}: {html.escape(str(row.get("content_overlap", "-")))}',
                    f'{html.escape(t_local("debug_retrieval_quality"))}: {html.escape(str(row.get("quality", "-")))}',
                ]
                retrieval_items.append(
                    '<div class="debug-retrieval-item">'
                    f'<div class="debug-retrieval-head"><strong>#{html.escape(str(row.get("rank", "-")))}</strong>'
                    f'<code>{html.escape(localize_context_header(str(row.get("source_label", "-")), t_local))}</code>{title_match_badge}{all_terms_badge}</div>'
                    f'<div class="debug-retrieval-metrics">{" · ".join(metrics)}</div>'
                    "</div>"
                )
            retrieval_html = (
                '<div class="debug-section">'
                f'<div class="debug-section-title">{html.escape(t_local("debug_retrieval_title"))}</div>'
                + "".join(retrieval_items)
                + "</div>"
            )
        return (
            '<details class="debug-card">'
            f'<summary>{html.escape(t_local("debug_title"))}</summary>'
            '<div class="debug-body">'
            '<div class="debug-row">'
            f'<span>{html.escape(t_local("debug_status"))}</span>'
            f'<code>{status_text}</code>'
            "</div>"
            '<div class="debug-row">'
            f'<span>{html.escape(t_local("history_role"))}</span>'
            f'<code>{role_text}</code>'
            "</div>"
            '<div class="debug-row">'
            f'<span>{html.escape(t_local("settings_role_style"))}</span>'
            f'<code>{style_text}</code>'
            "</div>"
            '<div class="debug-row">'
            f'<span>{html.escape(t_local("settings_answer_language"))}</span>'
            f'<code>{answer_lang_text}</code>'
            "</div>"
            '<div class="debug-row">'
            f'<span>{html.escape(t_local("debug_model"))}</span>'
            f'<code>{model_text}</code>'
            "</div>"
            '<div class="debug-row">'
            f'<span>{html.escape(t_local("debug_topk"))}</span>'
            f'<code>{top_k_text}</code>'
            "</div>"
            '<div class="debug-row">'
            f'<span>{html.escape(t_local("debug_latency_ms"))}</span>'
            f'<code>{latency_text}</code>'
            "</div>"
            f"{retrieval_html}"
            "</div>"
            "</details>"
        )

    def context_fragment(ctx: str) -> str:
        ctx = localize_context_preview(ctx or "", t_local)
        chunks = [chunk.strip() for chunk in ctx.split("\n---\n") if chunk.strip()]
        if chunks:
            body = "".join(f"<pre>{html.escape(chunk)}</pre>" for chunk in chunks)
            open_attr = " open"
        else:
            body = f'<p class="muted">{t_local("context_placeholder")}</p>'
            open_attr = ""
        return (
            f'<details id="context-panel" class="context-card"{open_attr}>'
            f'<summary>{t_local("context_accordion")}</summary>'
            f'<div id="context-content" class="context-body">{body}</div>'
            "</details>"
        )

    def respond(
        answer_text: str,
        ctx_text: str,
        *,
        is_error: bool,
        status_code: str,
        retrieval_rows: list[dict[str, Any]] | None = None,
    ) -> HTMLResponse:
        return html_response(
            answer_fragment(answer_text, is_error=is_error)
            + context_fragment(ctx_text)
            + debug_fragment(status_code, retrieval_rows)
        )

    try:
        top_k = int(raw_topk)
        if top_k < 1 or top_k > 50:
            raise ValueError
    except Exception:
        logging.warning("Invalid top_k from %s: %s", user_ip, raw_topk)
        message = t_local("invalid_topk")
        if question:
            append_history_entry(
                resolved_session_id,
                question=question,
                answer=message,
                status="error",
                model=model,
                top_k=None,
                role=role,
                role_label=role_label,
                role_style=role_style,
            )
        return respond(message, "", is_error=True, status_code="validation_error")

    if not question:
        logging.info("Empty question from %s", user_ip)
        return respond(
            t_local("empty_question"),
            "",
            is_error=True,
            status_code="validation_error",
        )

    available_models = get_ollama_models()
    if not available_models:
        logging.error("No Ollama models available for %s", user_ip)
        message = f'{t_local("error_prefix")}{t_local("models_unavailable")}'
        append_history_entry(
            resolved_session_id,
            question=question,
            answer=message,
            status="error",
            model=model,
            top_k=top_k,
            role=role,
            role_label=role_label,
            role_style=role_style,
        )
        return respond(message, "", is_error=True, status_code="models_unavailable")
    model = resolve_model_for_request(requested_model, available_models, custom_role)
    if not model:
        logging.warning("No resolved model for %s", user_ip)
        message = f'{t_local("error_prefix")}{t_local("models_unavailable")}'
        append_history_entry(
            resolved_session_id,
            question=question,
            answer=message,
            status="error",
            model=requested_model,
            top_k=top_k,
            role=role,
            role_label=role_label,
            role_style=role_style,
        )
        return respond(message, "", is_error=True, status_code="invalid_model")

    try:
        role_prompt = build_role_prompt(
            answer_lang,
            role,
            role_style,
            custom_role_prompt=custom_role_prompt,
        )
        retrieval_rows: list[dict[str, Any]] = []
        async with llm_lock:
            answer, context = rag_query(
                question,
                model,
                top_k,
                role_prompt=role_prompt,
            )
        if debug_mode:
            retrieval_rows = get_retrieval_debug_snapshot(question, top_k)
        raw_answer = answer if isinstance(answer, str) else str(answer)
        trimmed = raw_answer.strip()
        if trimmed == t_local("status_no_documents"):
            logging.warning("No documents/index for %s", user_ip)
            message = t_local("status_no_documents")
            append_history_entry(
                resolved_session_id,
                question=question,
                answer=message,
                status="error",
                model=model,
                top_k=top_k,
                role=role,
                role_label=role_label,
                role_style=role_style,
            )
            return respond(
                t_local("status_no_documents"),
                "",
                is_error=True,
                status_code="no_documents",
                retrieval_rows=retrieval_rows,
            )
        if trimmed.startswith("[Ollama request error") or trimmed.startswith(
            "[No response from LLM"
        ):
            logging.error("LLM error for %s: %s", user_ip, raw_answer)
            message = f'{t_local("error_prefix")}{raw_answer}'
            append_history_entry(
                resolved_session_id,
                question=question,
                answer=message,
                status="error",
                model=model,
                top_k=top_k,
                role=role,
                role_label=role_label,
                role_style=role_style,
            )
            return respond(
                message,
                "",
                is_error=True,
                status_code="llm_error",
                retrieval_rows=retrieval_rows,
            )
        logging.info("Answer OK for %s", user_ip)
        append_history_entry(
            resolved_session_id,
            question=question,
            answer=raw_answer,
            status="ok",
            model=model,
            top_k=top_k,
            role=role,
            role_label=role_label,
            role_style=role_style,
        )
        return respond(
            raw_answer,
            context or "",
            is_error=False,
            status_code="ok",
            retrieval_rows=retrieval_rows,
        )
    except Exception as exc:  # noqa: BLE001
        logging.exception("Exception in /api/ask for %s", user_ip)
        message = f'{t_local("error_prefix")}{exc}'
        append_history_entry(
            resolved_session_id,
            question=question,
            answer=message,
            status="error",
            model=model,
            top_k=top_k,
            role=role,
            role_label=role_label,
            role_style=role_style,
        )
        return respond(message, "", is_error=True, status_code="exception")


@app.get("/api/status", response_class=HTMLResponse)
def api_status(lang: str = Cookie(DEFAULT_LANG)):
    translations = load_translations(lang)

    def t_local(key: str):
        return translations.get(key, key)

    code, params = get_index_status_meta()
    status_key = STATUS_KEY_MAP.get(code)
    if status_key:
        if code == "build_failed":
            status_text = t_local(status_key).format(error=params.get("error", ""))
        elif code == "changes_detected":
            status_text = t_local(status_key)
            preview = params.get("preview")
            if preview:
                status_text += "\n\n" + t_local("status_pending_prefix").format(
                    preview=preview
                )
        else:
            status_text = t_local(status_key)
    else:
        status_text = get_index_status()
    docs_path = html.escape(str(get_docs_path_display()))
    file_count = get_indexed_file_count()

    def format_docs_label(count: int) -> str:
        if lang == "en":
            noun = "file" if count == 1 else "files"
            return f"Current documents folder contains {count} {noun}:"
        base = t_local("docs_folder")
        suffix = ":" if base.endswith(":") else ""
        base_text = base[:-1] if suffix else base
        return f"{base_text} ({count}){suffix}"

    docs_label = html.escape(format_docs_label(file_count))
    status_ready_text = t_local("status_ready_loaded")
    should_disable_reindex = status_text.strip() == status_ready_text
    disable_attr = ' disabled aria-disabled="true"' if should_disable_reindex else ""
    button_label = html.escape(" ".join(status_text.split()))
    raw_progress = params.get("progress")
    try:
        progress_value = max(0, min(100, int(raw_progress)))
    except (TypeError, ValueError):
        progress_value = 0
    progress_markup = ""
    if code == "indexing" and progress_value > 0:
        progress_markup = (
            '<div class="status-progress" aria-label="index progress">'
            f'<div class="status-progress-bar" style="width:{progress_value}%"></div>'
            f'<span class="status-progress-value">{progress_value}%</span>'
            "</div>"
        )
    after_request_js = (
        f"showAlert({json.dumps(t_local('reindex_started'))},'info',4000); "
        "if (document.getElementById('model')) { htmx.trigger('#model','refreshModels'); } "
        "if (window.startStatusPolling) { window.startStatusPolling(); } "
        "htmx.trigger('#status-card','refreshStatus');"
    )
    after_request_attr = html.escape(after_request_js, quote=True)
    return (
        f'<section class="card status-card" id="status-card" data-status-code="{html.escape(code)}" '
        'hx-get="/api/status" hx-trigger="refreshStatus" '
        'hx-target="this" hx-swap="outerHTML">'
        f'<div class="status-meta"><span class="muted">{docs_label}</span>'
        f'<code class="docs-path">{docs_path}</code></div>'
        '<div class="status-body">'
        f'<button id="reindex-btn" class="status-button"{disable_attr} '
        'hx-post="/api/reindex" hx-swap="none" '
        f'hx-on::after-request="{after_request_attr}">{button_label}</button>'
        f"{progress_markup}"
        "</div>"
        "</section>"
    )


@app.get("/api/health", response_class=JSONResponse)
def api_health():
    code, params = get_index_status_meta()
    payload: dict[str, Any] = {
        "ok": True,
        "app": get_app_meta(),
        "index": {
            "status": code,
            "ready": code in {"ready_loaded", "ready_ask", "changes_detected"},
            "documents": get_indexed_file_count(),
            "details": params,
        },
    }
    return JSONResponse(payload)


@app.get("/api/meta", response_class=JSONResponse)
def api_meta():
    return JSONResponse(get_app_meta())


@app.get("/api/models", response_class=HTMLResponse)
def api_models(lang: str = Cookie(DEFAULT_LANG)):
    translations = load_translations(lang)

    def t_local(key: str):
        return translations.get(key, key)

    payload = build_model_manager_payload(t_local)
    models = [item["name"] for item in payload.get("installed", [])]
    if not models:
        return (
            '<select id="model" name="model" disabled '
            'hx-get="/api/models" hx-trigger="refreshModels" '
            'hx-target="#model" hx-swap="outerHTML">'
            f'<option value="">{t_local("models_unavailable")}</option>'
            "</select>"
        )
    default_model = get_default_model(models)
    options = []
    for name in models:
        selected = " selected" if name == default_model else ""
        options.append(f'<option value="{name}"{selected}>{name}</option>')
    return (
        '<select id="model" name="model" '
        'hx-get="/api/models" hx-trigger="refreshModels" '
        'hx-target="#model" hx-swap="outerHTML">'
        + "".join(options)
        + "</select>"
    )


@app.get("/api/models/data", response_class=JSONResponse)
def api_models_data(lang: str = Cookie(DEFAULT_LANG)):
    translations = load_translations(lang)

    def t_local(key: str):
        return translations.get(key, key)

    return JSONResponse(build_model_manager_payload(t_local))


@app.get("/api/models/pull_status", response_class=JSONResponse)
def api_models_pull_status(lang: str = Cookie(DEFAULT_LANG)):
    translations = load_translations(lang)

    def t_local(key: str):
        return translations.get(key, key)

    pull_state = get_model_pull_state()
    pull_state["label"] = get_pull_status_label(
        str(pull_state.get("status") or ""),
        t_local,
        str(pull_state.get("error") or ""),
        model=str(pull_state.get("model") or ""),
    )
    return JSONResponse({"ok": True, "pull": pull_state})


async def read_model_name_from_request(request: Request) -> str:
    try:
        payload = await request.json()
        if isinstance(payload, dict) and "model" in payload:
            return normalize_model_name(payload.get("model"))
    except Exception:
        pass
    form = await request.form()
    return normalize_model_name(form.get("model"))


async def read_embedding_model_name_from_request(request: Request) -> str:
    try:
        payload = await request.json()
        if isinstance(payload, dict) and "embedding_model" in payload:
            return normalize_embedding_model_name(payload.get("embedding_model"))
        if isinstance(payload, dict) and "model" in payload:
            return normalize_embedding_model_name(payload.get("model"))
    except Exception:
        pass
    form = await request.form()
    return normalize_embedding_model_name(
        form.get("embedding_model") or form.get("model")
    )


@app.post("/api/models/pull", response_class=JSONResponse)
async def api_models_pull(request: Request, lang: str = Cookie(DEFAULT_LANG)):
    translations = load_translations(lang)

    def t_local(key: str):
        return translations.get(key, key)

    model_name = await read_model_name_from_request(request)
    result = start_model_pull(model_name)
    message = translate_model_manager_message(
        str(result.get("message") or ""),
        t_local,
        model=result.get("model") or model_name or "-",
    )
    status_code = 200 if result.get("ok") else 400
    return JSONResponse(
        {
            "ok": bool(result.get("ok")),
            "message": message,
            "pull": build_model_manager_payload(t_local).get("pull", {}),
        },
        status_code=status_code,
    )


@app.post("/api/models/delete", response_class=JSONResponse)
async def api_models_delete(request: Request, lang: str = Cookie(DEFAULT_LANG)):
    translations = load_translations(lang)

    def t_local(key: str):
        return translations.get(key, key)

    model_name = await read_model_name_from_request(request)
    result = delete_ollama_model(model_name)
    message = translate_model_manager_message(
        str(result.get("message") or ""),
        t_local,
        model=result.get("model") or model_name or "-",
    )
    status_code = 200 if result.get("ok") else 400
    return JSONResponse(
        {
            "ok": bool(result.get("ok")),
            "message": message,
            "pull": build_model_manager_payload(t_local).get("pull", {}),
        },
        status_code=status_code,
    )


@app.get("/api/embedding-models/data", response_class=JSONResponse)
def api_embedding_models_data(lang: str = Cookie(DEFAULT_LANG)):
    translations = load_translations(lang)

    def t_local(key: str):
        return translations.get(key, key)

    return JSONResponse(build_embedding_model_manager_payload(t_local))


@app.get("/api/embedding-models/pull_status", response_class=JSONResponse)
def api_embedding_models_pull_status(lang: str = Cookie(DEFAULT_LANG)):
    translations = load_translations(lang)

    def t_local(key: str):
        return translations.get(key, key)

    pull_state = get_embedding_model_pull_state()
    pull_state["label"] = get_embedding_pull_status_label(
        str(pull_state.get("status") or ""),
        t_local,
        str(pull_state.get("error") or ""),
    )
    return JSONResponse({"ok": True, "pull": pull_state})


@app.post("/api/embedding-models/pull", response_class=JSONResponse)
async def api_embedding_models_pull(request: Request, lang: str = Cookie(DEFAULT_LANG)):
    translations = load_translations(lang)

    def t_local(key: str):
        return translations.get(key, key)

    model_name = await read_embedding_model_name_from_request(request)
    result = start_embedding_model_pull(model_name)
    message = translate_embedding_model_manager_message(
        str(result.get("message") or ""),
        t_local,
        model=result.get("model") or model_name or "-",
    )
    status_code = 200 if result.get("ok") else 400
    return JSONResponse(
        {
            "ok": bool(result.get("ok")),
            "message": message,
            "pull": build_embedding_model_manager_payload(t_local).get("pull", {}),
        },
        status_code=status_code,
    )


@app.get("/api/history", response_class=HTMLResponse)
def api_history(
    request: Request,
    lang: str = Cookie(DEFAULT_LANG),
    session_id: str | None = Cookie(default=None, alias=HISTORY_COOKIE_NAME),
):
    translations = load_translations(lang)
    resolved_session_id = ensure_session_id(session_id)

    def t_local(key: str):
        return translations.get(key, key)

    history_limit = normalize_history_limit(request.query_params.get("limit"))
    entries = list_history_entries(resolved_session_id)
    if history_limit < len(entries):
        entries = entries[-history_limit:]
    body = render_history_fragment(entries, t_local)
    response = HTMLResponse(body)
    response.set_cookie("lang", lang)
    response.set_cookie(
        HISTORY_COOKIE_NAME,
        resolved_session_id,
        httponly=True,
        samesite="lax",
    )
    return response


@app.post("/api/history/clear", response_class=HTMLResponse)
def api_history_clear(
    lang: str = Cookie(DEFAULT_LANG),
    session_id: str | None = Cookie(default=None, alias=HISTORY_COOKIE_NAME),
):
    translations = load_translations(lang)
    resolved_session_id = ensure_session_id(session_id)
    clear_history_entries(resolved_session_id)

    def t_local(key: str):
        return translations.get(key, key)

    body = render_history_fragment([], t_local)
    response = HTMLResponse(body)
    response.set_cookie("lang", lang)
    response.set_cookie(
        HISTORY_COOKIE_NAME,
        resolved_session_id,
        httponly=True,
        samesite="lax",
    )
    return response


@app.post("/api/reindex")
def api_reindex(background_tasks: BackgroundTasks):
    background_tasks.add_task(rebuild_index)
    return {"status": "reindex started"}


def apply_runtime_settings_update(
    payload: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool]:
    body = payload if isinstance(payload, dict) else {}
    response: dict[str, Any] = {}
    changed = False

    docs_path_value = str(body.get("docs_path") or "").strip()
    if docs_path_value:
        current_docs_path = str(get_docs_path_display() or "").strip()
        if docs_path_value != current_docs_path:
            response["docs_path"] = set_docs_path(docs_path_value)
            changed = True
        else:
            response["docs_path"] = current_docs_path

    embedding_model_value = str(body.get("embedding_model") or "").strip()
    if embedding_model_value:
        current_embedding_model = str(get_embedding_model_name() or "").strip()
        if embedding_model_value != current_embedding_model:
            response["embedding_model"] = set_embedding_model(embedding_model_value)
            changed = True
        else:
            response["embedding_model"] = current_embedding_model

    response["changed"] = changed
    return response, changed


@app.post("/api/docs-path", response_class=JSONResponse)
def api_docs_path(background_tasks: BackgroundTasks, payload: dict[str, Any] = Body(...)):
    raw_path = str((payload or {}).get("docs_path") or "").strip()
    if not raw_path:
        return JSONResponse(
            {"ok": False, "message": "Invalid documents path."},
            status_code=400,
        )
    result, changed = apply_runtime_settings_update({"docs_path": raw_path})
    if changed:
        background_tasks.add_task(rebuild_index)
    return JSONResponse(
        {
            "ok": True,
            "docs_path": result.get("docs_path", raw_path),
            "app": get_app_meta(),
            "index": {"status": get_index_status_meta()[0]},
        }
    )


@app.post("/api/embedding-model", response_class=JSONResponse)
def api_embedding_model(
    background_tasks: BackgroundTasks,
    payload: dict[str, Any] = Body(...),
    lang: str = Cookie(DEFAULT_LANG),
):
    translations = load_translations(lang)

    def t_local(key: str) -> str:
        return translations.get(key, key)

    raw_model = str((payload or {}).get("embedding_model") or "").strip()
    if not raw_model:
        return JSONResponse(
            {"ok": False, "message": t_local("settings_embedding_model_invalid")},
            status_code=400,
        )
    try:
        result, changed = apply_runtime_settings_update({"embedding_model": raw_model})
    except ValueError:
        return JSONResponse(
            {"ok": False, "message": t_local("settings_embedding_model_invalid")},
            status_code=400,
        )
    if changed:
        background_tasks.add_task(rebuild_index)
    return JSONResponse(
        {
            "ok": True,
            "embedding_model": result.get("embedding_model", raw_model),
            "changed": changed,
            "message": t_local("settings_embedding_model_updated").format(
                model=result.get("embedding_model", raw_model)
            ),
            "app": get_app_meta(),
            "index": {"status": get_index_status_meta()[0]},
        }
    )


@app.post("/api/runtime-config", response_class=JSONResponse)
def api_runtime_config(
    background_tasks: BackgroundTasks,
    payload: dict[str, Any] = Body(...),
    lang: str = Cookie(DEFAULT_LANG),
):
    translations = load_translations(lang)

    def t_local(key: str) -> str:
        return translations.get(key, key)

    body = payload if isinstance(payload, dict) else {}
    if not str(body.get("docs_path") or "").strip() and not str(
        body.get("embedding_model") or ""
    ).strip():
        return JSONResponse(
            {"ok": False, "message": t_local("settings_embedding_model_invalid")},
            status_code=400,
        )
    try:
        result, changed = apply_runtime_settings_update(body)
    except ValueError:
        return JSONResponse(
            {"ok": False, "message": t_local("settings_embedding_model_invalid")},
            status_code=400,
        )
    if changed:
        background_tasks.add_task(rebuild_index)
    message_parts: list[str] = []
    if result.get("docs_path"):
        message_parts.append(
            t_local("docs_path_updated").format(path=str(result.get("docs_path") or ""))
        )
    if result.get("embedding_model"):
        message_parts.append(
            t_local("settings_embedding_model_updated").format(
                model=str(result.get("embedding_model") or "")
            )
        )
    return JSONResponse(
        {
            "ok": True,
            "changed": changed,
            "docs_path": result.get("docs_path", get_docs_path_display()),
            "embedding_model": result.get("embedding_model", get_embedding_model_name()),
            "message": " ".join(part for part in message_parts if part),
            "app": get_app_meta(),
            "index": {"status": get_index_status_meta()[0]},
        }
    )


@app.get("/api/fs/dirs", response_class=JSONResponse)
def api_fs_dirs(path: str | None = None, lang: str = Cookie(DEFAULT_LANG)):
    translations = load_translations(lang)

    def t_local(key: str) -> str:
        return translations.get(key, key)

    try:
        payload = list_browsable_directories(path)
    except Exception as exc:  # noqa: BLE001
        logging.exception("Failed to list directories for picker: %s", exc)
        return JSONResponse(
            {"ok": False, "message": t_local("docs_browser_error")},
            status_code=500,
        )
    payload["ok"] = True
    return JSONResponse(payload)


@app.get("/api/profile/custom-roles", response_class=JSONResponse)
def api_profile_custom_roles():
    return JSONResponse({"ok": True, "custom_roles": get_server_custom_roles()})


@app.get("/api/profile/custom-roles/export", response_class=JSONResponse)
def api_profile_custom_roles_export():
    payload = {
        "ok": True,
        "custom_roles": get_server_custom_roles(),
        "profile": get_server_profile(),
    }
    response = JSONResponse(payload)
    response.headers["Content-Disposition"] = (
        'attachment; filename="localrag-custom-roles.json"'
    )
    return response


@app.post("/api/profile/custom-roles", response_class=JSONResponse)
async def api_profile_custom_roles_save(
    request: Request,
    lang: str = Cookie(DEFAULT_LANG),
):
    translations = load_translations(lang)

    def t_local(key: str) -> str:
        return translations.get(key, key)

    try:
        payload = await request.json()
    except Exception:
        payload = {}
    custom_roles = set_server_custom_roles((payload or {}).get("custom_roles"))
    return JSONResponse(
        {
            "ok": True,
            "custom_roles": custom_roles,
            "message": t_local("settings_custom_roles_saved"),
        }
    )


@app.post("/api/lang")
def api_lang(lang: str, response: Response):
    target_lang = lang if lang in LANGS else DEFAULT_LANG
    translations = load_translations(target_lang)

    def t_local(key: str):
        return translations.get(key, key)

    if lang not in LANGS:
        return {
            "ok": False,
            "error": t_local("error_prefix") + f"Invalid language: {lang}",
        }
    response.set_cookie("lang", target_lang)
    return {"lang": target_lang, "ok": True}


@app.post("/api/lang_switch", response_class=HTMLResponse)
async def api_lang_switch(request: Request):
    payload_lang = None
    # Try JSON payload first (hx-vals can be converted to JSON via JS helpers)
    try:
        body = await request.json()
        if isinstance(body, dict):
            payload_lang = body.get("lang")
    except Exception:
        pass

    if payload_lang is None:
        form = await request.form()
        payload_lang = form.get("lang") or request.query_params.get("lang")

    target_lang = payload_lang if payload_lang in LANGS else DEFAULT_LANG
    translations = load_translations(target_lang)
    session_id = ensure_session_id(request.cookies.get(HISTORY_COOKIE_NAME))

    def t_local(key: str):
        return translations.get(key, key)

    try:
        response = templates.TemplateResponse(
            request,
            "main_content.html",
            {
            "request": request,
            "lang": target_lang,
            "t": t_local,
            "index_status_code": get_index_status_meta()[0],
            "app_meta": get_app_meta(),
                "role_prompt_defaults_by_lang": get_all_role_prompt_defaults(),
                "language_labels": get_language_labels(t_local),
                "role_image_catalog": get_role_image_catalog(t_local),
            "default_role_definitions": get_default_role_definitions(t_local),
            "embedding_model_catalog": [
                str(item.get("name") or "").strip()
                for item in RECOMMENDED_EMBEDDING_MODEL_CATALOG
                if str(item.get("name") or "").strip()
            ],
                "server_profile": get_server_profile(),
                "settings_i18n": get_settings_i18n(t_local),
                "model_manager_i18n": get_model_manager_i18n(t_local),
            },
        )
        response.set_cookie("lang", target_lang)
        response.set_cookie(
            HISTORY_COOKIE_NAME,
            session_id,
            httponly=True,
            samesite="lax",
        )
        return response
    except Exception as exc:  # noqa: BLE001
        fallback = load_translations(DEFAULT_LANG)

        def t_fallback(key: str):
            return fallback.get(key, key)

        message = f'{t_fallback("error_prefix")}{exc}'
        return HTMLResponse(
            f'<script>showAlert({json.dumps(message)}, "error", 5000);</script>'
            f'<div style="color:red;">{html.escape(message)}</div>',
            status_code=500,
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "7860")),
        reload=True,
    )
