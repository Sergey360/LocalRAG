# LocalRAG Observability Contract and Alert Policy

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | Ops observability |
| Stage | Design |
| GitLab issue | `#42` |
| Artifact version | `1.0` |
| Date | `2026-06-06` |
| Status | Ready for downstream implementation |
| Primary project | `https://lab.it360.ru/myprojects/localrag` |
| Local workspace target | `C:\Sergey\Lab360\localrag` |

## Source Context

This contract uses the merged analysis artifacts on `dev` as required inputs:

- `docs/discovery-and-analysis.md`
- `docs/website-content/content-brief-page-map.md`
- `docs/website-content/ru-first-multilingual-copy-analysis.md`
- `artifacts/seo/analysis/2026-06-06-seo-intent-keyword-brief.md`

The active service surface reviewed for this design is the FastAPI app in
`main.py`, the RAG/indexing runtime in `app/app.py`, Docker Compose defaults,
and the release smoke check script.

## Observability Goal

LocalRAG must be observable as a local-first RAG product without leaking private
document content, questions, answers, source passages, or local filesystem paths
into logs, metrics, Graylog, MayAlerts, or GitLab issues.

The observability contract must answer four operator questions:

- Is the app reachable and running the expected release?
- Is the local document index ready, stale, rebuilding, or failed?
- Can a user complete the critical RAG workflow: open UI, reindex, ask, inspect
  source context, and control model/language settings?
- Did an alert produce one deduplicated, routed GitLab work item with enough
  evidence to debug the problem without exposing private user data?

## Environment Contract

| Variable | Required values | Owner | Description | Default or fallback |
| --- | --- | --- | --- | --- |
| `SERVICE_NAME` | `localrag` | Runtime | Stable service identifier used in Graylog, metrics, MayAlerts, and GitLab issue titles. | Required for staging/prod; `localrag` in dev. |
| `APP_ENV` | `dev`, `staging`, `prod`, `ci` | Runtime/deploy | Deployment environment. MayAlerts routing and dedupe depend on this value. | `dev` for local runs when unset. |
| `APP_RELEASE` | Semver plus optional git SHA, for example `0.9.0+d103836` | Release | Immutable application release identifier. Should map to Docker image tag, Git SHA, or packaged release. | Fall back to `APP_VERSION`, then `VERSION`, then `unknown`. |
| `APP_VERSION` | Semver, currently `0.9.0` | Release | Product version already exposed by `/api/meta`. | `VERSION` file or `0.9.0`. |
| `APP_INSTANCE_ID` | UUID or host/container ID | Runtime | Distinguishes multiple running instances in the same environment. | Generated at process start in dev; explicit in staging/prod. |
| `BUILD_DATE_UTC` | ISO 8601 UTC timestamp | Release | Optional build metadata already supported in `/api/meta`. | Omit when unknown. |

Operational rule:

- `SERVICE_NAME`, `APP_ENV`, and `APP_RELEASE` are required Graylog fields on
  every structured log event and required labels on every metric series.
- `/api/meta` should expose `name`, `version`, `default_model`,
  `embedding_model`, `docs_path`, `supported_languages`, and `build_date_utc`
  when available. Downstream implementation should add `service_name`,
  `app_env`, `app_release`, and `app_instance_id` to the same payload.

## Correlation ID Contract

| Field | Requirement |
| --- | --- |
| Inbound request header | Accept `X-Request-ID` when provided by a proxy, browser test, release checker, or MayAlerts synthetic check. |
| Generated ID | If absent, generate a UUIDv4 per HTTP request. |
| Response header | Return `X-Request-ID` on every HTTP response, including validation and error responses. |
| Log field | Emit `correlation_id` on every request, background job, Ollama call, indexing event, and alert evidence record created from that request/job. |
| Background jobs | Generate a `job_id` and carry the triggering `correlation_id` when a user request starts the job. Startup jobs use `correlation_id=startup:<app_instance_id>`. |
| Outbound calls | Include `X-Request-ID` on Ollama requests where the client allows custom headers. If Ollama ignores it, keep the ID in LocalRAG logs. |
| UI/debug surface | Do not show correlation IDs in normal UI. They may appear in debug mode, release check output, and GitLab alert evidence. |

Do not derive a correlation ID from user question text, answer text, source
context, document path, or cookie/session values.

## Required Graylog Fields

Graylog GELF additional fields should use the same names with the leading GELF
underscore, for example `_service_name`. The canonical contract below omits the
wire-format underscore for readability.

### Base Fields

| Field | Required | Allowed examples | Notes |
| --- | --- | --- | --- |
| `service_name` | Yes | `localrag` | Must equal `SERVICE_NAME`. |
| `app_env` | Yes | `dev`, `staging`, `prod`, `ci` | Must equal `APP_ENV`. |
| `app_release` | Yes | `0.9.0+d103836` | Must equal `APP_RELEASE`. |
| `app_version` | Yes | `0.9.0` | Product version. |
| `app_instance_id` | Yes | UUID, container ID | Required for dedupe evidence. |
| `correlation_id` | Yes | UUIDv4 | Required on request and job logs. |
| `event_name` | Yes | `http_request_completed`, `rag_query_failed` | Stable machine-readable name. |
| `event_domain` | Yes | `http`, `rag`, `index`, `ollama`, `model`, `ui`, `release`, `observability` | Used for dashboards and alert filters. |
| `event_outcome` | Yes | `success`, `failure`, `validation_error`, `skipped` | Do not encode outcome only in message text. |
| `severity` | Yes | `debug`, `info`, `warning`, `error`, `critical` | Map to Graylog numeric level. |
| `message` | Yes | Short human message | No private content. |
| `timestamp_utc` | Yes | ISO 8601 UTC | Source timestamp, not ingestion timestamp. |
| `host` | Yes | Container/host name | Graylog standard field. |

### HTTP Fields

| Field | Required when | Notes |
| --- | --- | --- |
| `http_method` | HTTP request | `GET`, `POST`. |
| `http_route` | HTTP request | Route template, for example `/api/ask`, not raw URL with query values. |
| `http_status_code` | HTTP response | Numeric code. |
| `http_status_class` | HTTP response | `2xx`, `4xx`, `5xx`. |
| `duration_ms` | HTTP response and jobs | End-to-end duration. |
| `client_ip_hash` | HTTP request | Hash or anonymized value. Do not log raw IP outside local dev. |
| `user_agent_family` | HTTP request | Browser/test family only; avoid full high-cardinality user-agent strings. |
| `lang` | UI/API request | Interface language: `en`, `ru`, `nl`, `zh`, `he`. |
| `answer_language` | Ask request | Resolved answer language. |

### RAG and Index Fields

| Field | Required when | Notes |
| --- | --- | --- |
| `model_name` | RAG/model event | Ollama model tag, for example `qwen3.5:9b`. |
| `embedding_model` | Index/retrieval event | Embedding model name. |
| `top_k` | Ask/retrieval event | Numeric retrieval count. |
| `role_id` | Ask request | Built-in or custom role ID. |
| `role_style` | Ask request | `concise`, `balanced`, `detailed`. |
| `question_chars` | Ask request | Length only. Do not log question text. |
| `answer_chars` | Ask success | Length only. Do not log answer text. |
| `context_chunks` | Ask success | Number of returned context chunks. |
| `source_count` | Ask success | Count of distinct sources, not source paths. |
| `source_path_hashes` | Debug/release only | Optional salted hashes; never full paths in staging/prod logs. |
| `index_status` | Health/index event | `loading`, `ready_loaded`, `indexing`, `build_failed`, `ready_ask`, `no_documents`, `saved_failed`, `changes_detected`. |
| `indexed_file_count` | Health/index event | Numeric count from current runtime. |
| `index_progress_pct` | Indexing event | `0` to `100` when available. |
| `docs_path_hash` | Index/config event | Salted hash of configured path. |
| `docs_path_display_allowed` | Dev only | Full path may be visible only in local dev console/UI. |

### Alert Fields

| Field | Required when | Notes |
| --- | --- | --- |
| `alert_name` | Alert event | Stable MayAlerts alert name. |
| `alert_severity` | Alert event | `p1`, `p2`, `p3`, `p4`. |
| `alert_fingerprint` | Alert event | Dedupe fingerprint generated by MayAlerts. |
| `alert_window` | Alert event | Evaluation window, for example `10m`. |
| `alert_value` | Alert event | Observed value. |
| `alert_threshold` | Alert event | Trigger threshold. |
| `gitlab_project_path` | Routed alert | `myprojects/localrag`. |
| `gitlab_issue_iid` | Routed alert | Internal issue ID when created or updated. |

## Privacy and Claim Rules

Russian-first public copy and observability messages must stay concrete and
evidence-aware. The following rules apply to logs, dashboard labels, MayAlerts
issue text, and browser QA reports:

- Russian UX text is the baseline for copy QA. It must be natural Russian, not
  literal English phrasing. Preferred examples: `Запустить локально`,
  `Проверить источники`, `Переиндексировать папку`, `Выбрать модель`.
- Do not log raw questions, answers, retrieved source passages, document
  contents, local filesystem paths, cookie values, or custom role prompts.
- Do not publish unsupported social proof, ratings, compliance, security, or
  enterprise-readiness claims from alert evidence or dashboards.
- Every user-facing claim in a dashboard, status page, or website QA report must
  be tagged as `implemented`, `custom scope`, `planned`, or
  `verify-before-publish`.

Claim status examples:

| Claim | Status | Evidence or rule |
| --- | --- | --- |
| Local-first default workflow with Docker, local files, FAISS, and Ollama | `implemented` | README, Docker Compose, `/api/meta`. |
| Source context with path/page/line where available | `implemented` | RAG response context and tests. |
| UI languages EN/RU/NL/ZH/HE | `implemented` | Locale JSON files. |
| Separate interface language and answer language | `implemented` | Settings and API request handling. |
| Prometheus `/metrics` endpoint | `implemented` | `GET /metrics` exposes Prometheus text metrics for HTTP, RAG, index, reindex, model pull, embedding prepare, and Ollama dependency signals. |
| Graylog structured middleware | `implemented` | FastAPI middleware emits privacy-safe JSON log events with `correlation_id`, service metadata, route/status, latency, and hashed client IP evidence. |
| MayAlerts to GitLab automation | `planned` | This artifact defines the contract. |
| Corporate connectors, governance, access control, support terms | `custom scope` | Must be scoped per rollout. |
| `5.0 / 5.0`, `23 user reviews`, universal OCR success, GDPR/HIPAA compliance | `verify-before-publish` | Must not be used without source evidence and approval. |

## Health and Status Endpoints

| Endpoint | Status | Purpose | Success contract | Alert use |
| --- | --- | --- | --- | --- |
| `GET /api/health` | Implemented | Machine-readable health and index state. Docker Compose healthcheck already uses it. | `200`, `ok=true`, `app` object present, `index.status` present. | Primary liveness/readiness input. |
| `GET /api/meta` | Implemented | Runtime metadata and release defaults. | `200`, expected `name`, `version`, `default_model`, `embedding_model`, `docs_path`, `supported_languages`. | Release drift and config checks. |
| `GET /api/status` | Implemented | Localized HTML status card for UI polling. | `200`, status card rendered, `data-status-code` present. | Browser/UI smoke signal, not primary machine health. |
| `GET /` | Implemented | Main interactive UI. | `200`, page renders language, settings, model, history, and ask controls. | Synthetic UI check and browser QA. |
| `GET /docs` | Implemented by FastAPI | Swagger UI. | `200` when docs are enabled. | Dev/staging only; not a production health dependency. |

Readiness rule:

- Dev: `/api/health` may be `ok=true` while index status is
  `changes_detected` or `indexing`.
- Staging/prod: readiness for user traffic requires `/api/health` `ok=true`,
  `index.ready=true`, expected `APP_RELEASE`, and at least one installed Ollama
  model for the configured default answer model.

## Metrics Endpoints and Metric Contract

The FastAPI runtime now exposes a dedicated Prometheus text endpoint:

| Endpoint | Status | Format | Access |
| --- | --- | --- | --- |
| `GET /metrics` | Implemented | Prometheus text exposition | Local/dev unrestricted; staging/prod should restrict access through monitoring network or reverse proxy auth. |
| `GET /api/health` | Implemented fallback | JSON | Safe for release checks and Docker health. |
| `GET /api/meta` | Implemented fallback | JSON | Safe for release checks; avoid exposing private deployment details publicly. |

Required metric names:

| Metric | Type | Labels | Description |
| --- | --- | --- | --- |
| `localrag_http_requests_total` | Counter | `service_name`, `app_env`, `app_release`, `route`, `method`, `status_class` | Request volume by route and result. |
| `localrag_http_request_duration_seconds` | Histogram | `service_name`, `app_env`, `app_release`, `route`, `method` | HTTP latency. |
| `localrag_rag_queries_total` | Counter | `service_name`, `app_env`, `app_release`, `outcome`, `model_name`, `answer_language`, `role_id` | Ask workflow count. |
| `localrag_rag_query_duration_seconds` | Histogram | `service_name`, `app_env`, `app_release`, `model_name` | End-to-end ask latency. |
| `localrag_retrieval_context_chunks` | Histogram | `service_name`, `app_env`, `app_release` | Returned context chunk count. |
| `localrag_ollama_requests_total` | Counter | `service_name`, `app_env`, `app_release`, `endpoint`, `outcome`, `model_name` | Ollama dependency calls. |
| `localrag_ollama_request_duration_seconds` | Histogram | `service_name`, `app_env`, `app_release`, `endpoint`, `model_name` | Ollama call latency. |
| `localrag_index_status` | Gauge | `service_name`, `app_env`, `app_release`, `status` | One-hot index status gauge. |
| `localrag_indexed_file_count` | Gauge | `service_name`, `app_env`, `app_release` | Current indexed file count. |
| `localrag_reindex_jobs_total` | Counter | `service_name`, `app_env`, `app_release`, `outcome`, `trigger` | Reindex job count. |
| `localrag_reindex_duration_seconds` | Histogram | `service_name`, `app_env`, `app_release`, `trigger` | Reindex duration. |
| `localrag_model_pull_active` | Gauge | `service_name`, `app_env`, `app_release`, `model_name` | Active Ollama model pull. |
| `localrag_model_pull_failures_total` | Counter | `service_name`, `app_env`, `app_release`, `model_name` | Failed model pulls. |
| `localrag_embedding_prepare_failures_total` | Counter | `service_name`, `app_env`, `app_release`, `embedding_model` | Failed embedding model preparation. |
| `localrag_observability_contract_violations_total` | Counter | `service_name`, `app_env`, `app_release`, `field` | Missing required fields or unsafe payload detection. |

Metrics must avoid labels with raw question text, answer text, source paths,
document names, arbitrary user-agent strings, or custom prompt text.

## Background Jobs

| Job | Current trigger | Current implementation | Required telemetry | Alert conditions |
| --- | --- | --- | --- | --- |
| Startup index bootstrap | FastAPI lifespan unless `LOCALRAG_SKIP_STARTUP` is set | `ensure_index_ready_on_startup()` loads persisted index or calls `rebuild_index()` | `job_id`, `correlation_id`, `trigger=startup`, `index_status`, `duration_ms`, `indexed_file_count`, `outcome`. | Startup index failure, startup duration too high, no persisted index and rebuild failure. |
| Manual reindex | `POST /api/reindex` | FastAPI `BackgroundTasks.add_task(run_reindex_job)` wrapping `rebuild_index()` | Triggering route/correlation, `trigger=manual`, progress, duration, outcome. | `build_failed`, stuck `indexing`, zero indexed files in staging/prod unless expected. |
| Docs path change reindex | `POST /api/docs-path` | Updates runtime path, clears persisted index, schedules `rebuild_index` | `docs_path_hash`, path validation result, trigger, duration, outcome. | Invalid path bursts, rebuild failure, path escapes allowed root. |
| Embedding model change reindex | `POST /api/embedding-model` and `POST /api/runtime-config` | Updates embedding model, clears persisted index, schedules `rebuild_index` | `embedding_model`, local availability, duration, outcome. | Missing model, rebuild failure, repeated changes. |
| Ollama model pull | `POST /api/models/pull` | Threaded `_pull_model_worker` with pull state endpoint | `model_name`, `started_at`, `finished_at`, bytes/progress when available, error. | Pull failed, pull stuck, concurrent pull rejection spike. |
| Embedding model prepare | `POST /api/embedding-models/pull` | Threaded `_prepare_embedding_model_worker` | `embedding_model`, device, vector size, duration, outcome. | Prepare failed, no local artifact after success. |
| Model delete | `POST /api/models/delete` | Synchronous delete request to Ollama | `model_name`, outcome, duration. | Delete failure for expected default model. |
| Legacy Gradio filesystem watcher | `app/app.py` direct run only | `watchdog.Observer` marks index dirty | `watch_event_count`, path hash, status change. | Watcher errors in legacy runtime only. |
| Release smoke check | `scripts/release_check.py` | External script calls `/api/health`, `/api/meta`, `/api/ask` | Release, base URL, check names, outcome, correlation IDs. | Any failed release check in staging/prod. |

## Critical Workflow Inventory

| Workflow | User value | Runtime path | Success signal | Failure signal |
| --- | --- | --- | --- | --- |
| Open app UI | User reaches LocalRAG and sees controls. | `GET /`, static assets, templates. | `200`, controls render, no JS console errors in browser QA. | 5xx, broken static assets, missing Russian text, blocked language switch. |
| Check runtime health | Operator validates release and index state. | `GET /api/health`, `GET /api/meta`. | Expected release/config, `ok=true`, index status known. | Release drift, unknown index status, missing fields. |
| Reindex local folder | User refreshes source corpus. | `POST /api/reindex`, `rebuild_index()`. | `ready_loaded` or `ready_ask`, indexed file count > 0 where expected. | `build_failed`, stuck `indexing`, zero documents outside expected empty-folder dev cases. |
| Ask grounded question | User asks over indexed documents. | `POST /api/ask`, retrieval, prompt build, Ollama generate, HTML answer/context. | Answer returned, context panel available, history entry saved. | Validation error, model unavailable, no documents, LLM error, exception, high latency. |
| Inspect sources | User verifies answer against retrieved fragments. | Context fragment from `rag_query()`. | At least one context chunk when relevant source exists; source metadata localized. | Empty context for known-answer smoke case, unsafe path exposure in logs. |
| Manage answer model | User selects/pulls/deletes Ollama models. | `/api/models/*`, Ollama `/api/tags`, `/api/pull`, `/api/delete`. | Installed model list, pull success, default model resolvable. | Ollama unreachable, pull failure, default model missing. |
| Manage embedding model | User prepares/selects embedding model. | `/api/embedding-models/*`, `prepare_embedding_model_artifact()`. | Local artifact available, vector generated, reindex scheduled if changed. | Prepare failure, CPU/GPU memory error, rebuild failure. |
| Change language settings | User controls interface and answer language independently. | Cookies, form fields, prompt language rules. | RU/EN/NL/ZH/HE UI renders; answer language follows request. | Fallback placeholders, mixed-language answer outside quoted source context. |
| Save custom roles | Power user persists role prompts/settings. | `/api/profile/custom-roles`. | Normalized role profile saved in `server_profile.json`. | Invalid role data, save failure, unsafe prompt logged. |
| Validate release | Operator gates a candidate. | `pytest`, `scripts/release_check.py`, eval scripts. | All configured checks pass with release evidence. | Any failed check or missing expected model/docs path. |

## Russian-First Website and Product QA Matrix

The observability layer must support the Russian-first redesign cycle without
turning marketing copy into unsupported claims. Browser QA should use Russian
text as the baseline, then verify EN/RU/NL/ZH/HE by meaning and layout.

| Page or block | Purpose and reader question | Content, CTA, proof, claim status | Visual hierarchy and states | Responsive, accessibility, browser QA |
| --- | --- | --- | --- | --- |
| Home hero | Explain what LocalRAG is: "Что это и что сделать дальше?" | Russian source line: `Локальный ИИ-поиск по приватным документам.` CTA `Запустить локально`; proof strip uses implemented claims only. | Product name is first-viewport signal; primary CTA visible; loading/error states do not hide status. | Check RU headline wrapping on mobile, CTA tap targets, no unsupported rating/social proof, LCP budget. |
| Home product proof strip | Answer: "Почему верить?" | Local files, Ollama, FAISS, source context, 5 UI languages, Docker Compose; all tagged `implemented`. | Compact evidence row, no decorative overload. | Verify text does not overflow in RU; icons have accessible names. |
| Features | Answer: "Какие возможности уже есть?" | Supported formats, provenance, multilingual UI, roles, model manager; CTA `Проверить источники`. | Feature groups ordered by user workflow, not generic marketing. | Browser QA checks cards/buttons for text fit in all languages. |
| How It Works | Answer: "Как данные проходят через RAG?" | Ingestion, chunks, embeddings, FAISS, retrieval, prompt, Ollama, source context; claims `implemented`. | Flow can use generated illustration or 3D only if it clarifies document flow. | Reduced-motion fallback, no blank canvas, source labels accessible. |
| Setup | Answer: "Как запустить локально?" | Docker Compose, Windows path defaults, `/api/health`, `/api/meta`; CTA `Открыть UI`. | Steps are linear; errors link to exact recovery actions. | Mobile code blocks scroll safely; copy buttons have labels; path examples are not logged remotely. |
| Quality and Evaluation | Answer: "Как проверяется качество?" | `pytest`, release smoke, eval gate, source-hit checks; CTA `Запустить eval`. | Evidence modules show commands and pass/fail state. | QA validates command text, contrast, and no invented certification language. |
| Use Cases | Answer: "Подходит ли мне?" | Private local folders, mixed PDFs, research notes, code/docs; limitations visible. | Scenario sections include one practical CTA each. | Verify claims are `implemented` or `custom scope`; no unsupported enterprise claims. |
| FAQ/privacy | Answer: "Куда уходят документы и что не гарантируется?" | Default local workflow, Ollama/data boundaries, OCR/model limitations; CTA `Проверить архитектуру`. | Objections are direct, not hidden under hype. | QA checks Russian copy for calques and clear limitation notes. |
| Release notes | Answer: "Какая версия и что изменилось?" | Version, default model, embedding model, known limits; claim status `implemented`. | Version/date visible before changelog detail. | Browser QA checks date/version consistency with `/api/meta`. |
| App UI | Answer: "Можно ли выполнить задачу сейчас?" | Ask, context, settings, model manager, history; Russian UI must be natural. | Operational controls remain dense and scannable. | Playwright checks RU labels, interaction states, source panel, keyboard flow. |

Visual effects policy:

- Generated illustrations are allowed for the public website when they show the
  actual product idea: local folder, retrieval flow, model control, source
  verification. They must include alt text and compressed assets.
- 3D is allowed only when it explains the product architecture or document flow.
  It must have a reduced-motion fallback, mobile fallback, and a canvas-pixel
  check so blank canvases fail QA.
- Scroll effects and animation should be short and functional: target
  `150-250ms` for UI transitions, avoid scroll-jacking, and disable nonessential
  motion under `prefers-reduced-motion`.
- Performance budgets for public pages: no decorative effect may block main
  content, cause text overlap, or push Largest Contentful Paint beyond the
  agreed release threshold. Use browser QA evidence before publishing.

## Alert Taxonomy

| Severity | Meaning | Examples | Response |
| --- | --- | --- | --- |
| `p1` | User-critical outage or data-risk event in prod. | App unreachable, `/api/ask` hard failure, Ollama unavailable for all requests, unsafe private content detected in logs. | Immediate MayAlerts notification and GitLab issue. |
| `p2` | Major workflow degraded or release candidate blocked. | Reindex stuck/failed, default model missing, high ask error rate, release smoke failed. | GitLab issue within dedupe policy; notify responsible channel. |
| `p3` | Degraded experience or non-prod failure. | Elevated latency, model pull failure, localized UI fallback, missing expected metric. | GitLab issue when repeated or blocking milestone. |
| `p4` | Hygiene and observability drift. | Missing optional field, dashboard stale, docs mismatch. | Batch into maintenance issue or update existing issue. |

## Baseline Alert Rules

| Alert name | Environment | Severity | Condition | Dedupe resource |
| --- | --- | --- | --- | --- |
| `localrag_health_down` | staging/prod | `p1` prod, `p2` staging | `/api/health` non-2xx, timeout, or `ok=false` for 3 consecutive checks. | `service_name`, `app_env`, `app_instance_id`. |
| `localrag_release_drift` | staging/prod | `p2` | `/api/meta` release/version differs from expected deployment manifest. | `service_name`, `app_env`, expected release. |
| `localrag_index_build_failed` | all | `p2` prod/staging, `p3` dev | `index.status=build_failed` or reindex job outcome failure. | `docs_path_hash`, `embedding_model`, `app_env`. |
| `localrag_indexing_stuck` | all | `p2` prod/staging, `p3` dev | `index.status=indexing` longer than 15m prod, 30m staging/dev, unless release check declares large-corpus exception. | `app_instance_id`, `docs_path_hash`. |
| `localrag_no_documents` | staging/prod | `p2` | `indexed_file_count=0` for 10m where environment expects seeded docs. | `app_env`, `docs_path_hash`. |
| `localrag_ask_error_rate_high` | staging/prod | `p1` prod if sustained, `p2` staging | `/api/ask` failures exceed 5% over 10m or 3 consecutive synthetic ask failures. | `route=/api/ask`, `model_name`, `app_env`. |
| `localrag_ask_latency_high` | staging/prod | `p2` | `/api/ask` p95 latency exceeds 60s for 15m, excluding known model-pull windows. | `route=/api/ask`, `model_name`, `app_env`. |
| `localrag_ollama_unavailable` | all | `p1` prod, `p2` staging, `p3` dev | Ollama `/api/tags` or generation calls fail for 2m prod/staging or 10m dev. | `OLLAMA_BASE_URL`, `app_env`. |
| `localrag_default_model_missing` | staging/prod | `p2` | Default model from `/api/meta` is absent from installed Ollama model list. | `model_name`, `app_env`. |
| `localrag_model_pull_failed` | all | `p2` prod/staging, `p3` dev | Model pull state ends in `error`. | `model_name`, `app_env`. |
| `localrag_embedding_prepare_failed` | all | `p2` prod/staging, `p3` dev | Embedding prepare state ends in `error`. | `embedding_model`, `app_env`. |
| `localrag_release_smoke_failed` | staging/prod | `p2` | `scripts/release_check.py` fails any configured check. | `app_release`, `base_url`. |
| `localrag_ru_copy_or_layout_failed` | staging/prod public site | `p3` | Russian baseline browser QA finds placeholder text, overflow, unsupported claim, or broken CTA. | `page`, `viewport`, `app_release`. |
| `localrag_observability_contract_violation` | all | `p2` prod/staging, `p3` dev | Required Graylog field missing, unsafe raw content detected, or high-cardinality label detected. | `field`, `event_domain`, `app_env`. |

## MayAlerts Dedupe Policy

MayAlerts must produce one active GitLab issue per actionable alert fingerprint.
Repeated evaluations update the existing issue instead of creating duplicates.

### Fingerprint

Use this normalized fingerprint input:

```text
service_name|app_env|alert_name|severity|dedupe_resource|app_release_major_minor
```

Rules:

- `dedupe_resource` is the smallest stable affected resource: route, model,
  embedding model, docs path hash, app instance, page, or synthetic check name.
- Do not include raw URLs with query strings, raw filesystem paths, question
  text, answer text, source excerpts, cookie values, full user agents, or exact
  timestamps.
- Include only major/minor release in the default fingerprint so patch releases
  update the same active operational issue. For release drift and release smoke
  failures, include the full `APP_RELEASE`.
- If severity escalates, update the existing issue title/labels and add an
  escalation comment.

### Dedupe Windows

| Environment | Open issue threshold | Update window | Auto-resolve comment | Reopen rule |
| --- | --- | --- | --- | --- |
| `dev` | Create only after 3 occurrences in 24h, unless `p1` privacy/content leak. | 7 days while issue is open. | Comment after 24h green or maintainer confirmation. | Reopen only if closed less than 7 days ago with same fingerprint. |
| `staging` | Create immediately for `p1`/`p2`; after 2 occurrences in 2h for `p3`. | 14 days while issue is open. | Comment after 3 consecutive green checks or successful release smoke. | Reopen if same fingerprint returns before release promotion. |
| `prod` | Create immediately for `p1`/`p2`; after 2 occurrences in 30m for `p3`. | 30 days while issue is open. | Comment after 30m green for `p1`, 2h green for `p2`, 24h green for `p3`. | Reopen any same fingerprint within 30 days; otherwise create a new issue linked to the old one. |

### Noise Controls

- Suppress `ask_latency_high` during an active model pull or embedding prepare
  only when the alert evidence includes the active job and the workflow is
  expected to slow down.
- Suppress `no_documents` in dev when `DOCS_PATH` points to an intentionally
  empty folder and the release check is not running.
- Never suppress `observability_contract_violation` for unsafe private content
  leakage.
- Batch `p4` hygiene alerts into a weekly maintenance issue unless they block
  a release milestone.

## GitLab Issue Routing

All alert-created work goes to `myprojects/localrag`.

### Non-Prod Routing

| Environment | GitLab issue visibility | Default labels | Assignee/milestone rule |
| --- | --- | --- | --- |
| `dev` | Public/internal project default, non-confidential unless private evidence exists. | `area::observability`, `monitoring`, `source::mayalerts`, `alert::non-prod`, `env::dev`, severity label, `sdlc::triage`. | Assign to current ops-observability owner if configured; otherwise leave unassigned for triage. |
| `staging` | Non-confidential unless evidence includes deployment secrets or private paths. | `area::observability`, `monitoring`, `source::mayalerts`, `alert::non-prod`, `env::staging`, severity label, `sdlc::triage`. | Attach to active release/design milestone when known. |

Non-prod title format:

```text
[ALERT][staging][p2][localrag] reindex stuck for docs path hash <hash-prefix>
```

### Prod Routing

| Environment | GitLab issue visibility | Default labels | Assignee/milestone rule |
| --- | --- | --- | --- |
| `prod` | Confidential by default. | `area::observability`, `monitoring`, `source::mayalerts`, `alert::prod`, `env::prod`, severity label, `sdlc::triage`. | Assign to on-call or release operator if configured; attach to active incident/release milestone when known. |

Prod title format:

```text
[ALERT][prod][p1][localrag] ask workflow unavailable
```

### Issue Body Template

```markdown
## Alert

- Alert: `<alert_name>`
- Severity: `<p1|p2|p3|p4>`
- Environment: `<APP_ENV>`
- Service: `<SERVICE_NAME>`
- Release: `<APP_RELEASE>`
- Fingerprint: `<alert_fingerprint>`
- First seen: `<timestamp_utc>`
- Last seen: `<timestamp_utc>`
- Occurrences: `<count>`

## Current Evidence

- Condition: `<alert_value>` vs threshold `<alert_threshold>` over `<alert_window>`
- Route/workflow/job: `<route_or_workflow>`
- Correlation IDs: `<safe list>`
- Instance: `<app_instance_id>`
- Model: `<model_name or n/a>`
- Embedding model: `<embedding_model or n/a>`
- Index status: `<index_status or n/a>`
- Indexed files: `<indexed_file_count or n/a>`

## Privacy Check

- Raw question text included: `no`
- Raw answer text included: `no`
- Source passages included: `no`
- Raw filesystem paths included: `no`
- Private claim/security claim reviewed: `<yes|n/a>`

## Suggested Triage

1. Check `/api/health` and `/api/meta` for this release.
2. Review Graylog events by `alert_fingerprint` and `correlation_id`.
3. Run or inspect the relevant release/synthetic check.
4. Decide whether this is release-blocking, user-impacting, or hygiene.

## Resolution Notes

- Root cause:
- Fix:
- Verification:
- Follow-up:
```

## Environment-Specific Observability

| Environment | Logs | Metrics | Alerts | Synthetic checks | Browser QA |
| --- | --- | --- | --- | --- | --- |
| `dev` | Console/file logs plus optional Graylog. Privacy rules still apply. | `/api/health`, `/api/meta`, and `/metrics`. | Only repeated failures or privacy/content leaks. | Local release smoke optional. | Run when UI/layout changes. |
| `staging` | Structured Graylog required. | `/metrics` required before production promotion; health/meta remain release fallbacks. | MayAlerts creates GitLab issues for p1/p2 and repeated p3. | Release smoke required; ask workflow uses seeded safe docs. | Required for Russian baseline pages and critical app UI. |
| `prod` | Structured Graylog required, retention policy configured outside this repo. | `/metrics` required and restricted. | MayAlerts immediate routing for p1/p2; confidential GitLab issues. | Health/meta and safe synthetic ask with approved non-private corpus. | Required before public website release and after major UI changes. |

## Downstream Acceptance Criteria

Implementation and verification work can use these acceptance criteria:

1. `SERVICE_NAME`, `APP_ENV`, `APP_RELEASE`, and `APP_INSTANCE_ID` are present in
   `/api/meta`, Graylog events, and metric labels.
2. Every HTTP request has a correlation ID accepted from `X-Request-ID` or
   generated server-side, returned in the response header, and attached to logs.
3. Graylog events contain all required base fields and do not contain raw
   question text, answer text, source passages, raw paths, cookies, or custom
   prompts.
4. `/api/health`, `/api/meta`, `/api/status`, and `/` are covered by health,
   readiness, and synthetic checks according to environment.
5. A Prometheus-compatible `/metrics` endpoint is implemented and checked before
   production promotion.
6. Startup indexing, manual reindex, docs path reindex, embedding model reindex,
   Ollama model pull, embedding prepare, model delete, and release smoke checks
   emit job telemetry with outcome and duration.
7. Critical workflows have success/failure counters, duration histograms, and
   alert rules: UI open, health/meta, reindex, ask, source inspection, model
   manager, embedding manager, language settings, custom roles, release
   validation.
8. MayAlerts creates or updates at most one active GitLab issue per fingerprint
   and follows the dev/staging/prod dedupe windows.
9. Non-prod and prod GitLab issues use the routing labels, title format,
   privacy check, and evidence template defined above.
10. Russian-first website/product QA uses Russian text as the baseline, checks
    page/block purpose, CTA, proof, visual hierarchy, interaction states,
    responsive behavior, accessibility, motion fallback, performance limits,
    and browser evidence.
11. All public claims in observability dashboards, alert text, and browser QA
    reports are tagged `implemented`, `custom scope`, `planned`, or
    `verify-before-publish`.

## Definition of Done Coverage

- [x] Define `SERVICE_NAME`, `APP_ENV`, `APP_RELEASE`, correlation IDs, and
  required Graylog fields.
- [x] List health endpoints, metrics endpoints, background jobs, and critical
  workflows.
- [x] Define MayAlerts dedupe policy and GitLab issue routing for non-prod and
  prod alerts.
- [x] Store the design output as a versioned repository artifact.
- [x] Include Russian-first copy/UX rules, claim safety, visual effects,
  responsive behavior, accessibility, browser QA expectations, and executable
  downstream acceptance criteria for the redesign cycle.
