# LocalRAG Discovery and Analysis

## Issue Context

- GitLab issue: `#4`
- Project: `localrag`
- Stage: `analysis`
- Milestone: `SDLC Stage 02: Discovery and Analysis`
- Primary GitLab project: <https://lab.it360.ru/myprojects/localrag>
- Local workspace target: `C:\Sergey\Lab360\localrag`
- Repository topology: `mono`

## Project Statement

LocalRAG is a local-first Retrieval-Augmented Generation application for answering questions over private documents on a user's own machine. The project combines document ingestion, multilingual embeddings, persistent vector search, role-aware prompting, and local Ollama model inference to provide grounded answers with visible source provenance.

The product exists to make private document question answering practical for local folders that contain mixed file types, multilingual content, OCR-heavy sources, inconsistent filenames, and retrieval quality challenges. Its design priority is privacy, explainability, multilingual usability, and repeatable release quality rather than cloud collaboration or hosted model orchestration.

## Goals

- Provide local question answering over private files without sending document content to external AI services.
- Return answers grounded in retrieved context with source path, page, and line provenance where available.
- Support multilingual users through localized UI text and independently configurable answer language.
- Support different answer styles through built-in roles and shared custom roles.
- Provide in-app operational controls for document folder selection, indexing, model selection, and Ollama model management.
- Maintain release discipline through automated tests, smoke checks, and retrieval quality gates.

## Scope

### In Scope

- FastAPI web application and API endpoints for document Q&A, health, metadata, models, roles, history, and reindexing.
- Local document ingestion for supported text and document formats, including PDF, DOCX, TXT, Markdown, HTML, JSON, CSV, YAML, and source code files.
- Local embeddings using `intfloat/multilingual-e5-large` by default.
- Persistent FAISS vector index storage and retrieval.
- Hybrid retrieval, reranking, source-priority heuristics, and context construction.
- Local answer generation through Ollama, with `qwen3.5:9b` as the current release default answer model.
- Source provenance in returned context, including file path and page or line references when available.
- Multilingual UI support for English, Russian, Dutch, Chinese, and Hebrew.
- Independent interface language and answer language settings.
- Built-in answer roles and editable custom roles with prompt, language, model, style, and artwork settings.
- Docker Compose runtime, release-first start scripts, and development hot-reload configuration.
- Runtime observability with request correlation IDs, structured privacy-safe log events, health/meta endpoints, and Prometheus text metrics.
- Automated unit/API tests, release smoke checks, model eval scripts, and quality gate assertions.
- Kiwi TCMS synchronization support for structured test management.

### Out of Scope

- Hosted SaaS deployment or multi-tenant cloud operation.
- Cloud LLM providers as the default answer generation path.
- Enterprise identity management, SSO, RBAC, or audit logging.
- Real-time collaborative editing, shared team workspaces, or remote document libraries.
- Browser-based document annotation workflows beyond source provenance display.
- Full document management features such as versioning, retention policy, legal hold, or e-discovery.
- Guaranteed OCR correction or document conversion quality for every input source.
- Native mobile applications.
- Managed production observability stack operation beyond the repository-provided metrics, structured logs, and setup artifacts.

## Actors

| Actor | Description | Primary Needs |
| --- | --- | --- |
| Local user | Person asking questions over private local documents. | Private Q&A, source traceability, language control, simple setup. |
| Power user | User tuning models, roles, prompts, answer language, and document paths. | Configurability, repeatable role behavior, model visibility. |
| Developer/maintainer | Person extending and validating the application. | Clear architecture, tests, release gates, reproducible local runtime. |
| Release operator | Person preparing a release candidate or validating a deployment. | Smoke checks, health metadata, model defaults, eval evidence. |
| Test manager | Person synchronizing or reviewing structured test coverage. | Kiwi TCMS mapping, stable automated tests, traceable quality checks. |

## Use Cases

| ID | Use Case | Primary Actor | Acceptance Intent |
| --- | --- | --- | --- |
| UC-01 | Ask a question over indexed local documents. | Local user | The system returns an answer grounded in retrieved document context. |
| UC-02 | Inspect source evidence for an answer. | Local user | The response exposes file, page, or line provenance where available. |
| UC-03 | Reindex a local documents folder. | Local user | The index refreshes after document changes and reports status. |
| UC-04 | Change interface language. | Local user | The UI renders in a supported language without changing answer language unless configured. |
| UC-05 | Change answer language. | Local user | Generated answers follow the selected answer language. |
| UC-06 | Select a built-in answer role. | Power user | The answer style changes according to the selected role prompt. |
| UC-07 | Create or edit a custom role. | Power user | The custom role persists prompt, language, model, style, and artwork settings. |
| UC-08 | Manage local Ollama models. | Power user | Installed models can be listed and managed from the UI. |
| UC-09 | Run API and retrieval regression tests. | Developer/maintainer | The test suite validates API behavior, retrieval quality, roles, language guards, and model eval scripts. |
| UC-10 | Validate a release candidate. | Release operator | Smoke checks and model eval gates verify runtime health and answer quality before release. |

## Non-Functional Requirements

| ID | Requirement | Verification Approach |
| --- | --- | --- |
| NFR-01 Privacy | Document content and answer generation must remain local by default. The default runtime uses local file mounts, local FAISS index storage, and Ollama for model inference. | Review configuration defaults, runtime docs, and Docker Compose settings. |
| NFR-02 Explainability | Answers must expose retrieved source context with provenance when available. | API and retrieval tests; manual inspection of answer context panel. |
| NFR-03 Multilingual UX | The application must support localized UI strings for English, Russian, Dutch, Chinese, and Hebrew. | Locale file checks and UI smoke testing. |
| NFR-04 Answer language control | Interface language and answer language must be independently configurable. | API/UI tests for language guard behavior and role defaults. |
| NFR-05 Retrieval quality | Retrieval must handle mixed local corpora and OCR-heavy sources well enough to satisfy the project eval gate. | `scripts/model_eval.py` plus `scripts/assert_eval_gate.py`. |
| NFR-06 Reproducibility | The application must provide a reproducible Docker Compose runtime and release-first start scripts. | Docker Compose smoke test and release checklist. |
| NFR-07 Maintainability | Core behavior must remain covered by automated tests and release scripts. | `pytest -q`, compile checks, and CI pipeline. |
| NFR-08 Operability | The runtime must expose health, metadata, correlation ID, structured log, and metrics signals for validation. | `GET /api/health`, `GET /api/meta`, `GET /metrics`, `X-Request-ID`, structured log events, and `scripts/release_check.py`. |
| NFR-09 Performance | Indexing and answering should remain practical for local personal document collections, with persistent index reuse between runs. | Manual timing during release validation and regression checks around reindex behavior. |
| NFR-10 Portability | The default path mapping must support Windows host paths through Docker while allowing non-default Linux/WSL paths via environment variables. | Startup script review, Docker Compose review, and manual path override test. |

## Acceptance Criteria

| ID | Criteria |
| --- | --- |
| AC-01 | A user can start the application with the release-first Docker Compose path and open the web UI at `http://localhost:7860`. |
| AC-02 | The application can ingest supported local documents and build or reuse a persistent FAISS index. |
| AC-03 | A user can ask a question and receive an answer generated by a local Ollama model. |
| AC-04 | The answer response includes retrieved context and source provenance where source metadata is available. |
| AC-05 | A user can configure interface language independently from answer language. |
| AC-06 | Built-in roles and custom roles influence answer prompt behavior without breaking default question answering. |
| AC-07 | The model manager reports installed Ollama models and supports expected management actions through the UI/API surface. |
| AC-08 | Health, metadata, correlation ID headers, and metrics endpoints report runtime status and release defaults. |
| AC-09 | The automated test suite passes for API, validation, history, roles, models, retrieval, and eval script behavior. |
| AC-10 | Release validation can run the smoke check and extended eval gate against a running candidate environment. |
| AC-11 | Documentation clearly states project statement, scope, actors, use cases, out-of-scope items, NFRs, risks, and acceptance criteria. |

## Risks

| ID | Risk | Impact | Mitigation |
| --- | --- | --- | --- |
| R-01 | Local Ollama model availability varies by machine. | Users may start the app but fail to generate answers. | Keep model manager visible, document default model, expose `/api/models`, and validate expected model in release checks. |
| R-02 | OCR-heavy or low-quality documents can weaken retrieval. | Answers may miss relevant context or produce weak grounding. | Maintain eval cases for OCR-heavy sources, hybrid retrieval, reranking, and source-priority heuristics. |
| R-03 | Large local folders can make indexing slow or resource intensive. | First-run experience may be poor on low-resource machines. | Reuse persistent indexes, expose reindex status, and keep documents path configurable. |
| R-04 | Windows-to-container path mapping can be misconfigured. | Users may not see expected files or provenance paths. | Keep `HOST_FS_ROOT`, `HOST_FS_MOUNT`, `DOCS_PATH`, and `HOST_DOCS_PATH` documented and covered by startup defaults. |
| R-05 | Multilingual prompt and role behavior can regress when defaults change. | Answers may use the wrong language or style. | Preserve language guard tests, role API tests, and localized default prompt coverage. |
| R-06 | Release quality can drift if eval gates are skipped. | A build may pass smoke tests while answer quality regresses. | Keep eval scripts and CI quality gate documented as release validation steps. |
| R-07 | Broad custom-role configurability may produce invalid or confusing role states. | Users may get inconsistent prompt/model/language behavior. | Normalize role data server-side and client-side, and keep role regression tests. |
| R-08 | Docker, Python, embedding model, and Ollama dependencies can change over time. | Reproducibility may degrade across environments. | Pin and document release defaults, use CI compile/test checks, and package release artifacts with manifests. |

## Assumptions and Constraints

- The default execution model is local and single-user.
- The current release baseline is `0.9.0`.
- The default answer model is `qwen3.5:9b`.
- The default embedding model is `intfloat/multilingual-e5-large`.
- The default Windows host documents path is `C:\Temp\PDF`; issue context also identifies the local workspace target as `C:\Sergey\Lab360\localrag`.
- Docker Compose is the primary supported runtime path.
- Browser/UI validation is not required for this issue because the issue labels do not include `cap::chrome-mcp` and `exec::nas`.

## Definition of Done Coverage

- Project statement and scope: covered in `Project Statement`, `Goals`, and `Scope`.
- Actors, use cases, and out-of-scope: covered in `Actors`, `Use Cases`, and `Out of Scope`.
- Non-functional requirements and risks: covered in `Non-Functional Requirements` and `Risks`.
- Acceptance criteria: covered in `Acceptance Criteria`.
