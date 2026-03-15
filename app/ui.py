"""
UI for LocalRAG with a Material/Pixel-inspired header:
- Left: logo + app title + app subtitle
- Right: compact language buttons (EN, RU, NL, ZH, HE)
This module is layout-only and returns (demo, controls) for event binding in app.py.
"""

from __future__ import annotations

from pathlib import Path
import base64
import gradio as gr

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def _data_uri_from_file(path: Path, mime: str) -> str:
    try:
        raw = path.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""


def _flag_data_uri(svg_name: str) -> str:
    path = STATIC_DIR / "flags" / svg_name
    try:
        raw = path.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        return ""


def _overrides_css() -> str:
    flag_en = _flag_data_uri("gb.svg")
    flag_ru = _flag_data_uri("ru.svg")
    flag_nl = _flag_data_uri("nl.svg")
    flag_zh = _flag_data_uri("cn.svg")
    flag_he = _flag_data_uri("il.svg")
    return "\n".join(
        [
            ".app-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 0 auto 18px; max-width: var(--maxw); padding: 0 16px; }",
            ".app-brand-wrap { display: flex; align-items: center; gap: 12px; }",
            ".app-brand-text { display: flex; flex-direction: column; }",
            ".app-title { font-size: 20px; font-weight: 700; line-height: 1.15; }",
            ".app-subtitle { font-size: 13px; color: var(--muted); line-height: 1.2; }",
            ".langs.compact { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }",
            ".langs.compact .lang { display: inline-flex; }",
            ".langs.compact .lang button { height: 30px; padding: 0 8px !important; font-size: 13px; border-radius: 10px; display: inline-flex; align-items: center; }",
            f".lang.lang-en button::before {{ background-image: url('{flag_en}') !important; }}",
            f".lang.lang-ru button::before {{ background-image: url('{flag_ru}') !important; }}",
            f".lang.lang-nl button::before {{ background-image: url('{flag_nl}') !important; }}",
            f".lang.lang-zh button::before {{ background-image: url('{flag_zh}') !important; }}",
            f".lang.lang-he button::before {{ background-image: url('{flag_he}') !important; }}",
            ".answer-box textarea { resize: vertical; min-height: 160px; font-size: 15px; }",
            ".context-md { font-size: 12.75px; line-height: 1.45; }",
        ]
    )


def create_interface(binder=None):
    css_text = (
        (STATIC_DIR / "style.css").read_text(encoding="utf-8")
        if (STATIC_DIR / "style.css").exists()
        else ""
    )
    css_text += "\n/* overrides: header + flags */\n" + _overrides_css()

    logo_src = _data_uri_from_file(STATIC_DIR / "LocalRAG-logo-s.png", "image/png")

    with gr.Blocks(css=css_text, title="LocalRAG") as demo:
        gr.HTML("<div id='app'></div>")
        controls: dict[str, gr.Component] = {}

        # Header: brand left, language buttons right
        with gr.Row(elem_classes=["app-header"]):
            controls["brand_html"] = gr.HTML(
                "<div class='app-brand-wrap'>"
                f"<img class='app-logo' src='{logo_src}' alt='LocalRAG'/>"
                "<div class='app-brand-text'>"
                "<div class='app-title'>LocalRAG</div>"
                "<div class='app-subtitle'>RAG for your local documents</div>"
                "</div>"
                "</div>"
            )

            # Debug info for flags
            flag_en = _flag_data_uri("gb.svg")
            flag_debug = (
                f"Flag EN length: {len(flag_en)}, starts with: {flag_en[:50]}..."
                if flag_en
                else "Flag EN: EMPTY"
            )
            controls["debug_flags"] = gr.HTML(
                f"<div style='font-size:10px;color:#666;'>{flag_debug}</div>"
            )
            with gr.Row(elem_classes=["langs", "compact"]):
                controls["lang_en"] = gr.Button(
                    "🇬🇧 English", elem_classes=["lang", "lang-en"]
                )
                controls["lang_ru"] = gr.Button(
                    "🇷🇺 Русский", elem_classes=["lang", "lang-ru"]
                )
                controls["lang_nl"] = gr.Button(
                    "🇳🇱 Nederlands", elem_classes=["lang", "lang-nl"]
                )
                controls["lang_zh"] = gr.Button(
                    "🇨🇳 中文", elem_classes=["lang", "lang-zh"]
                )
                controls["lang_he"] = gr.Button(
                    "🇮🇱 עברית", elem_classes=["lang", "lang-he"]
                )

        # Provide logo as state for binder
        controls["logo_src"] = gr.State(logo_src)

        # Status and model
        with gr.Row(elem_classes=["grid", "two", "box"]):
            controls["status_md"] = gr.Markdown("Current documents folder: `…`")
            controls["model_dd"] = gr.Dropdown(
                label="LLM model (Ollama)", choices=[], value=None, interactive=True
            )

        with gr.Row(elem_classes=["grid", "two"]):
            controls["refresh_btn"] = gr.Button("Refresh status")
            controls["reindex_btn"] = gr.Button(
                "Reindex documents", elem_classes=["btn-primary"]
            )

        # Query settings
        with gr.Row(elem_classes=["grid", "two", "box"]):
            controls["topk_slider"] = gr.Slider(
                1, 50, value=8, step=1, label="Documents to retrieve (top-k)"
            )
            controls["temp_slider"] = gr.Slider(
                0.0, 1.0, value=0.2, step=0.1, label="Temperature"
            )

        # Q&A: Answer on top (resizable), then Question, Ask, and Context
        with gr.Column(elem_classes=["box"]):
            controls["answer_tb"] = gr.Textbox(
                label="Answer", lines=8, elem_classes=["answer-box"]
            )
            controls["question_tb"] = gr.Textbox(
                label="Your question", placeholder="Your question…"
            )
            controls["ask_btn"] = gr.Button("Ask", elem_classes=["btn-primary"])
            with gr.Accordion("Retrieved context", open=False) as acc:
                controls["ctx_md"] = gr.Markdown("", elem_classes=["context-md"])
            controls["ctx_acc"] = acc

        # Footer
        gr.HTML(
            "<div class='footer'>"
            "<span>Use via API</span> · <span>Built with Gradio</span> · "
            "<a href='/'>LocalRAG</a> · <span>LocalRAG · Autonomous RAG on local files · MIT · Windows/Linux · Ollama + Python + Gradio</span>"
            "</div>"
        )

        if binder is not None:
            binder(demo, controls)

    return demo, controls
