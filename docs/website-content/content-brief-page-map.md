# LocalRAG Website Content Brief and Page Map

This artifact records the analysis-stage content plan for the `website-content`
track. It defines audience assumptions, tone of voice, page inventory,
section-level copy guidance, CTA options, and messaging priorities for the
LocalRAG website.

## Issue Context

| Item | Value |
| --- | --- |
| GitLab issue | `#28` |
| Track | `website-content` |
| Stage hook | `analysis` |
| Primary project | `https://lab.it360.ru/myprojects/localrag` |
| Local workspace target | `C:\Sergey\Lab360\localrag` |
| Related tracks | `image-generation`, `ops-observability`, `seo`, `video-generation` |

## Product Position

LocalRAG is a local-first multilingual RAG application for asking questions over
private files on the user's own machine. The strongest positioning is not
"another chat UI"; it is a practical private-document question answering system
with grounded answers, source provenance, multilingual UX, local model control,
and release-quality retrieval checks.

Recommended one-line positioning:

> LocalRAG lets you ask grounded questions over private local documents with
> multilingual answers, source provenance, and local Ollama models.

## Audience Assumptions

Primary audience:

- Developers and technical power users who want private document Q&A without
  sending files to hosted AI services.
- Solo builders, consultants, researchers, and internal tool owners managing
  mixed local document folders.
- Teams evaluating local AI workflows before they allow wider use of RAG over
  sensitive files.

Secondary audience:

- Open-source reviewers who need to understand architecture, quality gates, and
  runtime defaults quickly.
- Multilingual users who need separate interface and answer language control.
- Windows-first users who want Docker-based setup with a predictable local
  documents path.

Likely user questions:

- Will my documents leave my machine?
- Which file types and languages are supported?
- How does LocalRAG show where an answer came from?
- Which local models does it use, and can I change them?
- What makes it more reliable than a demo RAG app?
- How do I install it, index documents, and ask the first question?

## Tone Of Voice

Voice attributes:

- Practical and engineering-led.
- Calm, precise, and evidence-oriented.
- Transparent about local runtime requirements and model limitations.
- Confident about privacy, provenance, multilingual UX, and quality discipline
  without sounding inflated.

Writing rules:

- Prefer concrete nouns: "local files", "source context", "Ollama model",
  "FAISS index", "answer language".
- Tie benefits to proof points: supported formats, source page/line references,
  model manager, eval gate, Docker Compose runtime.
- Avoid broad AI hype such as "unlock knowledge", "revolutionary", or
  "enterprise-grade" unless backed by specific release evidence.
- State limitations plainly: quality depends on the selected local model,
  document quality, OCR quality, and index freshness.
- Keep feature copy short enough for UI and SEO reuse; move detailed technical
  explanation into docs sections.

## Messaging Priorities

1. Privacy-first local document handling: files stay on the user's machine and
   are indexed locally.
2. Grounded answers with provenance: answers are paired with retrieved context,
   source paths, page numbers, and line ranges where available.
3. Multilingual product design: UI language and answer language are separate,
   with English, Russian, Dutch, Chinese, and Hebrew UI support.
4. Practical local model control: Ollama-backed answer models, in-app model
   manager, recommended model catalog, and configurable embedding model.
5. Real-world retrieval quality: hybrid retrieval, reranking, source-aware
   heuristics, and eval gates for OCR-heavy and mixed-format corpora.
6. Simple release-oriented setup: Docker Compose, start scripts, health/meta
   endpoints, and pytest/release checks.

## CTA Set

Primary CTAs:

- `Get LocalRAG`: links to install or clone instructions.
- `Start locally`: anchors to the quick-start section.
- `View source`: links to the public source repository when published.

Secondary CTAs:

- `See how retrieval works`: anchors to architecture or provenance section.
- `Review supported files`: anchors to supported formats and languages.
- `Run quality checks`: anchors to eval and release gate guidance.
- `Open API docs`: points to `/docs` when the app is running.

Low-friction in-page CTAs:

- `Add documents`
- `Reindex`
- `Ask a question`
- `Choose model`
- `Inspect sources`

CTA hierarchy recommendation:

- First viewport: `Start locally` primary, `View source` secondary.
- Setup page: `Clone repository` primary, `Open the UI` secondary.
- Architecture/reliability page: `Run the eval gate` secondary.
- Footer: `GitHub`, `API docs`, `Release notes`.

## Site Map

Recommended initial website structure:

| Page | Purpose | Primary CTA |
| --- | --- | --- |
| Home | Explain what LocalRAG is, who it is for, and why local-first grounded RAG matters. | `Start locally` |
| Features | Inventory the core product capabilities with evidence and screenshots. | `Review supported files` |
| How It Works | Explain ingestion, embeddings, FAISS retrieval, role-aware prompts, and source provenance. | `See retrieval flow` |
| Setup | Provide installation, default runtime, Docker Compose, paths, and first-question flow. | `Get LocalRAG` |
| Quality And Evaluation | Show test, release smoke, eval gate, and reliability discipline. | `Run quality checks` |
| Use Cases | Map LocalRAG to practical workflows and audience-specific tasks. | `Try your folder` |
| FAQ | Answer privacy, model, language, setup, file type, and troubleshooting questions. | `Start locally` |
| Release Notes | Link current version, release defaults, and change history. | `View release notes` |

The first implementation can ship as a single landing page with anchored
sections for Home, Features, How It Works, Setup, Quality, Use Cases, and FAQ.
Dedicated pages can follow once SEO and documentation needs justify the split.

## Section Inventory

### Home

Copy goal:

Introduce LocalRAG as a private local-document Q&A app, immediately showing the
privacy, grounding, and multilingual value proposition.

Required sections:

- Hero: product name, one-line positioning, primary and secondary CTAs.
- Trust proof strip: `Local files`, `Ollama`, `FAISS`, `Source provenance`,
  `5 UI languages`, `Docker Compose`.
- Problem framing: real local folders are messy, multilingual, and hard to cite.
- Product promise: ask questions, retrieve grounded context, inspect sources,
  control local models.
- Screenshot preview: home screen and settings/model manager screenshots.
- Quick start preview: add documents, reindex, ask a question.

Suggested hero copy direction:

- Headline: `LocalRAG`
- Supporting line: `Private document Q&A with local models, multilingual
  answers, and source-backed context.`
- Short body: `Index PDFs, office files, text, code, and structured data on your
  own machine, then ask questions through a local Ollama-backed RAG workflow.`

### Features

Copy goal:

Translate technical capabilities into user-facing benefits while keeping proof
points visible.

Feature sections:

- Local-first document handling: documents folder, host/container path mapping,
  no hosted AI dependency for private files.
- Supported file coverage: PDF, DOCX, TXT, Markdown, HTML, JSON, CSV, YAML, and
  source code formats.
- Source provenance: file path, page references, line ranges, retrieved context
  panel.
- Multilingual UX: separate UI and answer language controls; English, Russian,
  Dutch, Chinese, Hebrew.
- Response roles: Analyst, Engineer, Archivist, custom shared roles, editable
  prompts, role style presets.
- Model control: Ollama model manager, recommended models, manual model tags,
  default model selection, embedding model selection.
- History and settings: browser-saved preferences, question history, debug
  metadata.

### How It Works

Copy goal:

Make the system understandable to technical visitors without requiring them to
read source code.

Section flow:

- Load and normalize files from the documents folder.
- Split content into chunks with metadata.
- Build multilingual embeddings and persist a FAISS index.
- Retrieve candidate chunks with hybrid scoring and reranking.
- Build a role-aware prompt with answer-language rules.
- Generate the answer with a local Ollama model.
- Return answer plus source context for inspection.

Important proof points:

- Embedding default: `intfloat/multilingual-e5-large`.
- Answer model default: `qwen3.5:9b`.
- Retrieval focuses on OCR-heavy PDFs, title/cover queries, and mixed corpora.
- Source context is presented as part of the answer workflow, not hidden.

### Setup

Copy goal:

Reduce the time from interest to first local answer.

Section flow:

- Prerequisites: Docker Desktop or Docker Compose, Ollama runtime through the
  stack, supported local machine resources.
- Windows default path: `C:\Temp\PDF`.
- Clone and configure: use `.env.example` only when overrides are needed.
- Start stack: `docker compose up -d --build` or release-first start scripts.
- First question: add documents, open `http://localhost:7860`, reindex, choose
  model, ask.
- Non-default path guidance: explain `HOST_FS_ROOT`, `HOST_FS_MOUNT`,
  `DOCS_PATH`, and `HOST_DOCS_PATH`.

### Quality And Evaluation

Copy goal:

Show that the project treats retrieval quality and release checks as first-class
work, not an afterthought.

Section flow:

- Unit and API tests with `pytest`.
- Release smoke check with health, metadata, default model, UI flow, and model
  manager checks.
- Extended eval set for RAG answer quality.
- Quality gate assertions for strict score, loose score, and source hit ratio.
- GitLab CI and Kiwi TCMS integration for structured development workflow.

Suggested evidence modules:

- `pytest -q`
- `python scripts/release_check.py --base-url http://localhost:7860`
- `python scripts/model_eval.py ...`
- `python scripts/assert_eval_gate.py ...`

### Use Cases

Copy goal:

Help visitors recognize practical fit without overpromising.

Use case inventory:

- Ask questions over a private project folder.
- Review local PDFs with source page references.
- Query multilingual research or operational notes.
- Inspect code and structured files together with prose documents.
- Build a local AI demo that has real eval and release checks.
- Compare local model behavior with the same indexed corpus.

Out-of-scope framing:

- LocalRAG is not positioned as a hosted SaaS knowledge base.
- It is not a replacement for document management permissions.
- It does not guarantee answer quality independent of model, source, and OCR
  quality.

### FAQ

Recommended questions:

- Do my documents leave my machine?
- Which file formats are supported?
- Which languages are supported?
- Can the interface language differ from the answer language?
- Which models are recommended?
- Can I use a custom Ollama model?
- What happens when documents change?
- How does LocalRAG cite sources?
- How do I change the documents folder?
- What should I run before a release?

## Visual And Media Brief

Website content should coordinate with the image and video tracks:

- Use real screenshots for the primary product proof, especially home screen,
  settings, model manager, role selector, and retrieved context panel.
- Use a simple architecture diagram for the retrieval flow rather than abstract
  AI imagery.
- Video should show the first-run workflow: add files, reindex, ask, inspect
  sources, switch role or answer language.
- Avoid dark, generic AI backgrounds that obscure the product UI.

## SEO Content Notes

Primary keyword themes:

- local RAG
- private document question answering
- Ollama RAG
- multilingual RAG
- source provenance RAG
- local AI document search
- FAISS document Q&A

Recommended title pattern:

- `LocalRAG - Local RAG for Private Document Question Answering`

Recommended meta description direction:

- `Run private multilingual document Q&A on your machine with Ollama, FAISS,
  source provenance, local model control, and release-quality RAG evaluation.`

## Content Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Privacy claims sound absolute. | Say documents are handled locally by the app and avoid claims about every user's machine, network, or model configuration. |
| Model quality is overpromised. | Tie answer quality to context, selected model, OCR quality, and eval checks. |
| Technical terms overwhelm non-experts. | Pair each technical term with the user-visible benefit. |
| Website duplicates README. | Use the website for orientation and conversion; keep long commands and release details in docs. |
| Multilingual support is misread as perfect translation. | State supported UI languages and configurable answer language, not universal translation quality. |

## Done Criteria Coverage

- Content brief and audience assumptions: covered in Product Position, Audience
  Assumptions, Tone Of Voice, and Messaging Priorities.
- Site/page map and section inventory: covered in Site Map and Section
  Inventory.
- CTA set and messaging priorities: covered in CTA Set and Messaging
  Priorities.
