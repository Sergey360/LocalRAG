# LocalRAG Image Direction and Briefs

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | Image Generation |
| Stage | Design |
| Issue | #36 - Image direction and briefs |
| Artifact version | 1.0 |
| Date | 2026-06-06 |
| Status | Ready for asset generation and implementation planning |

## Purpose

This artifact defines the generated-image direction for the LocalRAG redesign.
Images must support the Russian-first product story: local files, visible
retrieval, Ollama model control, source verification, and quality checks. They
must not become generic AI decoration or imply unverified security,
compliance, ratings, customer proof, or enterprise readiness.

Required source inputs:

- `docs/website-content/ru-first-multilingual-copy-analysis.md`
- `artifacts/website-content/design/2026-06-06-draft-page-copy.md`
- `artifacts/seo/design/2026-06-06-seo-structure-metadata-plan.md`
- `artifacts/video-generation/design/2026-06-06-ru-first-motion-video-addendum.md`
- `docs/solution-design.md`

Russian text in prompts, captions, alt text, and overlays must follow
`ru-text` and `ru-web-copy-editor` standards: concrete wording, direct verbs,
proof-aware claims, and no English calques.

## Visual Direction

The image system should feel like a technical product with a clear workflow:

- real or product-faithful UI surfaces;
- local-folder boundary;
- document fragments and source cards;
- restrained 3D retrieval graph;
- precise labels and overlays;
- enough visual polish to feel premium without hiding the product.

Avoid:

- abstract glowing AI brains, clouds, shields, locks, or compliance seals;
- fake user avatars, fake testimonials, fake ratings;
- stock business people staring at charts;
- dark blurred background images where the product cannot be inspected;
- decorative bokeh/orbs unrelated to document workflow.

## Asset Inventory

| Asset ID | Page/block | Purpose | Format | Priority |
| --- | --- | --- | --- | --- |
| IMG-01 | Home hero | Show local folder -> LocalRAG UI -> source proof in one first-viewport visual. | WebP/AVIF plus fallback PNG | P0 |
| IMG-02 | Problem section | Show mixed real-world folder: PDFs, scans, notes, tables, code, mixed languages. | WebP/AVIF | P1 |
| IMG-03 | Workflow | Explain folder -> chunks -> embeddings -> FAISS -> answer -> sources. | SVG/Canvas/3D capture or WebP | P0 |
| IMG-04 | Source proof | Highlight answer card connected to retrieved file/page/line fragments. | WebP/AVIF | P0 |
| IMG-05 | Model and retrieval controls | Show Ollama model manager, answer language, top-k/retrieval controls. | Product screenshot or faithful composite | P1 |
| IMG-06 | Quality/eval | Visualize pytest, release checks, eval gate, source-hit discipline. | WebP/AVIF | P1 |
| IMG-07 | For teams | Show custom-scope integration layer without claiming shipped connectors. | Diagram/WebP | P2 |
| IMG-08 | Video poster | Russian-first poster for the 75s walkthrough. | WebP 1920x1080 and 1280x720 | P0 |
| IMG-09 | Social preview | LocalRAG share card with Russian headline and product proof. | 1200x630 WebP/PNG | P1 |

## Core Prompts

### IMG-01 Home Hero

Prompt direction:

> Product-faithful hero image for LocalRAG, a local-first document question
> answering app. Show a desktop UI with a Russian headline, a local folder of
> neutral sample documents, a visible source context card, and a subtle local
> boundary around the folder and app window. Premium technical SaaS aesthetic,
> clean light interface, precise labels, no fake ratings, no lock badges, no
> cloud symbols, no people, no generic AI glow.

Required Russian overlays:

- `Локальный ИИ-поиск по документам`
- `Файлы остаются локально в базовом сценарии`
- `Проверить источники`

Alt text:

> Интерфейс LocalRAG рядом с локальной папкой документов и найденным фрагментом
> источника, который подтверждает ответ.

Constraints:

- Do not show customer names or real file names.
- Do not imply certified isolation or compliance.
- Text must remain readable at 1440px desktop and 390px mobile crop.

### IMG-03 Retrieval Flow

Prompt direction:

> Explainer visual for LocalRAG retrieval flow. Inside a visible local-folder
> boundary, documents become text fragments, fragments become embeddings, the
> vectors enter FAISS, Ollama generates an answer, and source cards reconnect to
> the answer. Use clean 3D nodes and thin lines, product UI colors, Russian
> labels, no cloud, no security shield, no abstract AI brain.

Required labels:

- `Папка`
- `Файлы`
- `Фрагменты`
- `Embeddings`
- `FAISS`
- `Ollama`
- `Ответ`
- `Источники`

Alt text:

> Схема LocalRAG: локальные файлы разбиваются на фрагменты, проходят через
> embeddings и FAISS, а ответ связывается с найденными источниками.

Responsive rule:

- Desktop can show the full graph.
- Mobile uses a vertical step flow with the same labels.
- Reduced-motion fallback is a static image with numbered steps.

### IMG-04 Source Proof

Prompt direction:

> Close product-style composition showing an answer panel connected to retrieved
> source fragments. Include neutral file path examples, page and line metadata
> where available, and a Russian CTA. Clean UI, high contrast, readable source
> cards, no fake document content, no personal data.

Required overlays:

- `Ответ не нужно принимать на веру`
- `Путь к файлу`
- `Страница`
- `Строки`

Alt text:

> Ответ LocalRAG соединен с найденными фрагментами источников, где видны путь к
> файлу, страница и строки.

Claim rule:

- If the visual shows page/line references, caption must say `там, где эти
  данные доступны`.

### IMG-08 Video Poster

Prompt direction:

> Russian-first video poster for LocalRAG product walkthrough. Show LocalRAG UI,
> local folder boundary, 3D retrieval graph flattening into a source card, and
> CTA. Premium technical product style, concrete Russian copy, no fake review
> rating, no cloud upload visual, no generic AI background.

Poster copy:

- `LocalRAG`
- `Локальный ИИ-поиск по документам`
- `Запустить локально`

Alt text:

> Постер видео LocalRAG: локальная папка, retrieval-граф и карточка источника
> показывают путь от документа к проверяемому ответу.

## Page Usage

| Page/block | Primary image | Fallback | QA |
| --- | --- | --- | --- |
| Home hero | IMG-01 with optional 6s motion loop | Static WebP | LCP, mobile crop, text readability, no overlap |
| Workflow | IMG-03 or 3D canvas capture | Static step diagram | Canvas-pixel check, reduced-motion, mobile vertical layout |
| Source proof | IMG-04 plus real screenshot when available | Current product screenshot | Claim wording and metadata visibility |
| Quality | IMG-06 | Command/eval card | No invented scores; release values verified |
| For teams | IMG-07 | Simple architecture diagram | All enterprise claims marked custom scope |
| Video | IMG-08 | Static poster | Captions/transcript links and Russian-first copy |

## Implementation Rules

- Store generated source prompts and selected outputs under versioned artifact
  paths before implementation.
- Commit optimized web assets only when size and licensing/storage policy are
  approved.
- Use responsive `picture` sources where possible.
- Provide alt text in every locale; translate by meaning, not word by word.
- Keep images decorative-free when the same information is already clearer as a
  screenshot or diagram.
- Use real product screenshots for implemented UI proof; generated images may
  explain workflow but cannot replace evidence.

## Localization Rules

Russian is the source language for overlays and captions. EN/NL/ZH/HE
adaptations must preserve the same limits:

- EN: use technical product language, avoid generic SaaS hype.
- NL: keep privacy wording cautious; do not imply GDPR compliance.
- ZH: use concise overlays and verify line-height in compact captions.
- HE: use RTL captions and direction-safe LTR tokens for `LocalRAG`, `Ollama`,
  paths, model tags, and URLs.

Generated images with embedded text need separate locale variants unless the
text is limited to stable technical tokens.

## Approval Checklist

Before any generated image is used on the public site:

- [ ] Purpose and page/block are recorded.
- [ ] Prompt is saved.
- [ ] Russian overlay copy is reviewed against `ru-text` and
  `ru-web-copy-editor` rules.
- [ ] Unsupported claims are removed or labelled.
- [ ] Alt text exists for RU and target locales.
- [ ] Desktop, tablet, and mobile crops are checked.
- [ ] Reduced-motion/static fallback exists for motion-linked assets.
- [ ] File size, format, and lazy-loading behavior are acceptable.
- [ ] Visual does not imply cloud upload, certified isolation, fake rating, or
  shipped enterprise connector.

## Downstream Acceptance Criteria

Image-generation and development stages can proceed when:

- P0 image briefs IMG-01, IMG-03, IMG-04, and IMG-08 are generated or replaced
  by current product screenshots/diagrams.
- Each selected asset has prompt, alt text, locale notes, and claim constraints.
- Browser QA verifies assets at mobile and desktop widths.
- Visual effects support the approved Russian-first copy and do not hide CTA or
  proof content.

