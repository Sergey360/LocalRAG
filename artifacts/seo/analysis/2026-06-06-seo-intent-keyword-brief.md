# SEO Intent and Keyword Brief

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | SEO |
| Stage | Analysis |
| Issue | #32 - SEO intent and keyword brief |
| Artifact version | 1.0 |
| Date | 2026-06-06 |
| Status | Ready for content planning |

## Scope and Inputs

This brief defines keyword clusters, search intent, page targeting, SEO risks, and content gaps for LocalRAG. It is intended as a versioned project artifact for downstream website content, landing page, and documentation work.

Inputs used:

- Repository README and current FastAPI/HTMX app surface.
- Current public product positioning found at `https://localrag.dev/`.
- Light SERP scan on 2026-06-06 for adjacent terms such as `local RAG private documents`, `Ollama local RAG documents private`, and `private document question answering local LLM RAG`.
- Adjacent product/content references:
  - `https://localrag.dev/`
  - `https://gno.sh/features/local-llm`
  - `https://github.com/PromtEngineer/localGPT`
  - `https://openapps.pro/apps/privategpt`

No paid keyword-volume source was available in this workspace. Treat priority as intent-fit priority, not search-volume priority.

## Product Search Positioning

LocalRAG should compete around private, local document question answering rather than generic "RAG framework" language. The strongest discoverable angle is:

> Local-first document AI for private folders, OCR-heavy PDFs, multilingual files, and verifiable answers with source passages.

Important differentiators to preserve in page copy:

- Local-first document handling with no default cloud handoff.
- Source provenance: file path, page number, and line ranges where available.
- Multilingual UI and separate answer-language control.
- Practical folder-based workflow for real local files rather than demo uploads.
- Built-in Ollama model manager and embedding selection.
- Retrieval quality focus: hybrid search, reranking, source-priority heuristics, and eval gates.
- Team/corporate expansion path: connectors, governance, APIs, monitoring, and quality checks.

## Primary Keyword Clusters

Primary clusters should anchor main landing, feature, and comparison pages.

| Cluster | Example keywords | Search intent | Best page target | Priority |
| --- | --- | --- | --- | --- |
| Local AI for private documents | local AI for documents, private AI document search, chat with local documents, AI search local files, offline AI for documents | Find a product that answers questions over local/private files | Public homepage `/` or product landing page | P0 |
| Local RAG with Ollama | local RAG, Ollama RAG, Ollama document chat, local LLM RAG, RAG with Ollama and FAISS | Evaluate or build a local RAG workflow with Ollama | `/features/ollama-rag` and README quick start | P0 |
| Private document question answering | private document Q&A, local document question answering, ask questions over private documents, secure document AI | Solve document search/Q&A without sending files to cloud APIs | `/features/private-document-qa` | P0 |
| Chat with PDFs locally | chat with PDF locally, local PDF AI, ask questions over PDF offline, OCR PDF RAG, search scanned PDFs with AI | Use AI over PDFs, scans, and OCR-heavy files | `/features/pdf-ocr-rag` | P0 |
| Answers with source citations | RAG with citations, AI answers with sources, source-backed AI answers, document QA with citations | Verify answers and reduce hallucination risk | `/features/source-citations` | P0 |
| Private / on-prem RAG for teams | private RAG, on-prem RAG, enterprise local RAG, air-gapped document AI, private knowledge base AI | Evaluate controlled deployment for a team or regulated environment | `/for-teams` or `/enterprise` | P0 |

## Secondary Keyword Clusters

Secondary clusters should support documentation, tutorials, FAQ, integrations, and long-tail traffic.

| Cluster | Example keywords | Search intent | Best page target | Priority |
| --- | --- | --- | --- | --- |
| Multilingual local RAG | multilingual RAG, multilingual document search, local multilingual AI assistant, answer documents in Russian English Dutch Chinese Hebrew | Find document AI that works across languages | `/features/multilingual-rag` | P1 |
| Open-source alternatives | PrivateGPT alternative, localGPT alternative, private NotebookLM alternative, local NotebookLM alternative, open source document AI | Compare tools before choosing | `/compare/privategpt`, `/compare/localgpt`, `/compare/notebooklm` | P1 |
| Developer implementation | FastAPI RAG app, FAISS local document search, intfloat multilingual e5 RAG, LangChain FAISS Ollama RAG, Docker local RAG | Build or inspect architecture | `/developers` and technical posts | P1 |
| Deployment and setup | install LocalRAG, run LocalRAG locally, Docker Ollama RAG setup, local RAG Windows Docker | Install and run the product | `/docs/getting-started` or `/guide/getting-started` | P1 |
| Model and embedding selection | best Ollama model for RAG, embedding model for multilingual RAG, local RAG embedding model, qwen RAG Ollama | Configure quality/performance | `/guide/models-and-embeddings` | P1 |
| Retrieval quality | hybrid retrieval RAG, RAG reranking local, source provenance RAG, RAG eval quality gate | Improve or validate retrieval results | `/guide/retrieval-quality` | P1 |
| Privacy and compliance questions | does local RAG send data to cloud, private AI for legal documents, private AI for internal documents, local document AI security | Validate risk before adoption | `/faq/privacy-security` | P1 |
| Role-based answers | RAG answer roles, document AI analyst role, prompt roles for document QA | Discover advanced workflow controls | `/features/response-roles` | P2 |

## Page Targeting and Intent Map

| Page or route | Current status | Primary intent | Target keyword cluster | Content angle | CTA |
| --- | --- | --- | --- | --- | --- |
| `/` public homepage | Exists publicly outside this repo at `localrag.dev`; app route exists in repo | Commercial investigation and product discovery | Local AI for private documents | Show real UI, local-folder workflow, private documents, source passages, and multilingual controls | Run locally / discuss rollout |
| GitHub or README landing | Exists | Install and technical validation | Deployment and setup | Quick start, supported formats, Docker/Ollama defaults, screenshots, quality gate | Clone repository |
| `/features/private-document-qa` | Proposed | Commercial + product feature research | Private document question answering | Explain folder-based Q&A, supported formats, answer grounding, and source context | Try LocalRAG |
| `/features/ollama-rag` | Proposed | Technical product evaluation | Local RAG with Ollama | Explain Ollama model manager, local model selection, embeddings, FAISS, and Docker defaults | Install locally |
| `/features/pdf-ocr-rag` | Proposed | Problem-aware feature search | Chat with PDFs locally | Focus on OCR-heavy PDFs, scans, filenames, page provenance, and mixed document folders | Test with sample folder |
| `/features/source-citations` | Proposed | Risk reduction and verification | Answers with source citations | Demonstrate file/page/line evidence and why it matters for trust | View screenshots |
| `/features/multilingual-rag` | Proposed | Language-specific product search | Multilingual local RAG | Cover UI languages, answer-language separation, multilingual embeddings, and mixed-language files | Run multilingual demo |
| `/features/response-roles` | Proposed | Advanced workflow discovery | Role-based answers | Analyst, Engineer, Archivist, and custom shared roles with prompt/style/model defaults | Configure roles |
| `/guide/getting-started` | Proposed | Setup/how-to | Deployment and setup | Windows default flow, Linux path mapping, Docker Compose, Ollama dependency, first reindex | Complete install |
| `/guide/models-and-embeddings` | Proposed | Configuration/how-to | Model and embedding selection | Recommended Ollama answer models, embedding model tradeoffs, CPU/CUDA notes | Tune settings |
| `/guide/retrieval-quality` | Proposed | Technical validation | Retrieval quality | Hybrid retrieval, reranking, source-priority heuristics, eval runner, quality gates | Run eval |
| `/for-teams` or `/enterprise` | Proposed | Team/commercial evaluation | Private / on-prem RAG for teams | Connectors, APIs, permissions, monitoring, governance, and rollout discipline | Discuss pilot |
| `/compare/privategpt` | Proposed | Alternative comparison | Open-source alternatives | Compare LocalRAG positioning against PrivateGPT for local setup, UI, source visibility, models, and deployment path | Choose LocalRAG |
| `/compare/localgpt` | Proposed | Alternative comparison | Open-source alternatives | Compare LocalRAG against localGPT around UX, multilingual workflow, source provenance, and release discipline | Choose LocalRAG |
| `/faq/privacy-security` | Proposed | Objection handling | Privacy and compliance questions | Plain answers about local processing, Docker, Ollama, telemetry, data boundaries, and claim limits | Review architecture |

## Recommended Page Order

1. Homepage refinement and canonical metadata.
2. Getting started guide.
3. Feature page: private document Q&A.
4. Feature page: Ollama RAG.
5. Feature page: PDF/OCR RAG.
6. Feature page: source citations.
7. FAQ: privacy and security.
8. Team/enterprise page.
9. Comparison pages after baseline product pages are live.

## Metadata Direction

Use these as working starting points, not final copy.

| Page | Working title tag | Working meta description |
| --- | --- | --- |
| `/` | LocalRAG - Local AI for Private Documents and PDFs | Chat with private local documents, OCR PDFs, and folders using local RAG, Ollama, and source-backed answers without default cloud handoff. |
| `/features/ollama-rag` | Local RAG with Ollama, FAISS, and Private Documents | Run a local RAG workflow with Ollama models, FAISS vector search, multilingual embeddings, and source citations for your own files. |
| `/features/pdf-ocr-rag` | Chat with PDFs Locally, Including OCR Scans | Ask questions over PDFs, scans, and mixed local folders while keeping source passages visible for verification. |
| `/guide/getting-started` | Install LocalRAG with Docker and Ollama | Set up LocalRAG locally, connect a documents folder, reindex files, choose an Ollama model, and ask grounded questions. |
| `/faq/privacy-security` | LocalRAG Privacy and Security FAQ | Understand what stays local, how LocalRAG handles documents, where Ollama runs, and which deployment choices affect data exposure. |

## SEO Risks

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Product app route is not a crawlable marketing page | The FastAPI root is an interactive app, not a structured acquisition page | Keep public marketing pages separate from the authenticated/local app surface; use canonical URLs for the public site |
| `GET /docs` route conflict | The repo uses `/docs` for Swagger UI; SEO docs under the same path can collide | Use `/guide/*` or `/docs/*` only on the public marketing site with clear routing separation |
| Search intent overlap with generic RAG tutorials | Terms like `local RAG` and `Ollama RAG` are crowded with tutorials | Target long-tail product-led queries: private documents, OCR PDFs, source citations, multilingual local RAG |
| Brand collision and capitalization drift | `LocalRAG`, `local RAG`, `localGPT`, and `PrivateGPT` can blur in SERPs | Use consistent brand capitalization and create comparison/disambiguation pages |
| Duplicate content between README, GitHub, GitLab, and public site | Repeated quick-start copy can compete with itself | Define canonical URLs for public pages and keep README more developer/install focused |
| Unsupported compliance claims | Privacy/security searches are high stakes and sensitive | State exact data flow and deployment assumptions; avoid claiming HIPAA/GDPR compliance unless separately documented |
| Multilingual SEO can become thin or inconsistent | The product supports five UI languages, but translated pages need localized intent and hreflang | Create localized landing pages with `hreflang`, translated metadata, and language-specific examples |
| Screenshots and assets may not support image search/accessibility | Current strengths are visual: UI, source context, model manager | Use descriptive alt text, compressed image formats, and consistent screenshot captions |
| No keyword-volume validation | This brief prioritizes intent fit, not search demand | Validate with Google Search Console, Keyword Planner, Ahrefs, Semrush, or similar before committing large content spend |
| Public/private deployment confusion | Users may confuse local app behavior with hosted marketing pages | Add a clear architecture/privacy FAQ and diagrams showing local document flow |

## Content Gaps

| Gap | Impact | Suggested artifact/page |
| --- | --- | --- |
| No crawlable getting-started guide outside README | Setup intent may be captured only by repository pages | `/guide/getting-started` |
| No privacy/security FAQ | Privacy is central to search intent but needs exact answers | `/faq/privacy-security` |
| No feature page for source provenance | Source-backed answers are a strong differentiator | `/features/source-citations` |
| No PDF/OCR-focused page | PDF/OCR queries are likely high-intent and practical | `/features/pdf-ocr-rag` |
| No Ollama-focused page | Ollama is a major entry point for local LLM users | `/features/ollama-rag` |
| No multilingual RAG page | Five UI languages and separate answer language are underused SEO assets | `/features/multilingual-rag` |
| No model/embedding guide | Users need help choosing answer and embedding models | `/guide/models-and-embeddings` |
| No retrieval quality/eval page | The repo has eval gates that can build trust with technical buyers | `/guide/retrieval-quality` |
| No comparison pages | Competitors and alternatives already occupy SERPs | `/compare/privategpt`, `/compare/localgpt`, `/compare/notebooklm` |
| No team/on-prem rollout page | Corporate/integration messaging exists but needs its own page | `/for-teams` or `/enterprise` |

## Definition of Done Coverage

- [x] Define primary and secondary keyword clusters.
- [x] Map search intent to site pages.
- [x] List SEO risks and content gaps.
- [x] Store output as a versioned project artifact in the repository.
