# LocalRAG Platform and Delivery Setup Baseline

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Stage | Setup |
| GitLab issue | `#10` |
| Milestone | `SDLC Stage 04: Platform and Delivery Setup` |
| Artifact version | `1.0` |
| Date | `2026-06-06` |
| Status | Ready for manual provisioning and downstream automation |
| Primary project | `https://lab.it360.ru/myprojects/localrag` |
| Local workspace target | `C:\Sergey\Lab360\localrag` |
| Repository topology | `mono` |

## Source Inputs

This setup baseline uses the current repository state and these prior artifacts:

- `docs/discovery-and-analysis.md`
- `docs/solution-design.md`
- `RELEASE.md`
- `.gitlab-ci.yml`
- `docker-compose.yml`
- `.env.example`
- `tests/kiwi_sync_mapping.json`
- `scripts/kiwi_sync_pytest.py`
- `artifacts/ops-observability/design/2026-06-06-observability-contract-alert-policy.md`
- `deploy/platform-delivery/platform-delivery-baseline.json`
- `deploy/coolify/localrag.env.example`

No external GitLab, Kiwi, Cloudflare, Coolify, Graylog, Uptime Kuma, or
MayAlerts state was mutated by this issue. Secret values are not stored in the
repository.

## Environment Confirmation

The delivery profile confirms three runtime environments.

| Environment | `APP_ENV` | Git/ref policy | Base URL variable | Data profile | Promotion gate |
| --- | --- | --- | --- | --- | --- |
| `dev` | `dev` | `dev` branch and feature branches | `LOCALRAG_DEV_BASE_URL` | Developer local documents or safe seeded fixtures | `pytest_ci` passes; live quality gate optional unless release work depends on it. |
| `staging` | `staging` | Manual deploy from protected branch or release candidate tag | `LOCALRAG_STAGING_BASE_URL` | Safe seeded corpus approved for smoke and eval | `pytest_ci`, `quality_gate_live`, release smoke, and required Uptime Kuma checks pass. |
| `prod` | `prod` | Protected tag or protected main release promotion only | `LOCALRAG_PROD_BASE_URL` | Approved production document source and model cache | Staging green, package/tag approved, Cloudflare TLS active, monitoring and alert routing armed. |

Runtime metadata now includes `service_name`, `app_env`, `app_release`, and
`app_instance_id` in `/api/meta` and `/api/health.app`, using local-safe
defaults when unset.

## GitLab CI/CD Baseline

The current CI pipeline remains the baseline:

| Area | Baseline |
| --- | --- |
| Pipeline file | `.gitlab-ci.yml` |
| Stages | `test`, `quality`, `package`, `publish` |
| Required branch check | `pytest_ci` on `dev` |
| Manual compatibility matrix | `pytest_matrix_manual` for Python `3.11`, `3.12`, `3.13` |
| Manual live quality gate | `quality_gate_live` against `LOCALRAG_EVAL_BASE_URL` |
| Release package | `package_release` writes `dist/` artifacts |
| Public mirror publish | `github_publish_main` and `github_publish_tag` |

Baseline checks:

```sh
python -m py_compile main.py app/app.py
pytest -q
python scripts/release_check.py --base-url "$LOCALRAG_EVAL_BASE_URL" --expected-model qwen3.5:9b
python scripts/model_eval.py --base-url "$LOCALRAG_EVAL_BASE_URL" --seed-file eval/rag_eval_extended.json --models qwen3.5:9b --output temp/extended_eval_ci.json
python scripts/assert_eval_gate.py --report temp/extended_eval_ci.json --model qwen3.5:9b --min-strict 1.0 --min-loose 1.0 --min-hit-ratio 1.0
```

### GitLab Secret Map

| Variable | Scope | Masked | Protected | Required for | Owner |
| --- | --- | --- | --- | --- | --- |
| `LOCALRAG_EVAL_BASE_URL` | `staging`, `prod` | No | Yes | `quality_gate_live` | Release operator |
| `GITHUB_PUSH_TOKEN` | `prod` | Yes | Yes | GitHub mirror publish | Repository owner |
| `KIWI_USERNAME` | `ci` | Yes | Yes | `scripts/kiwi_sync_pytest.py` when NAS fallback is disabled | Test manager |
| `KIWI_PASSWORD` | `ci` | Yes | Yes | `scripts/kiwi_sync_pytest.py` when NAS fallback is disabled | Test manager |
| `CLOUDFLARE_API_TOKEN` | `staging`, `prod` | Yes | Yes | DNS/TLS automation | Platform operator |
| `CLOUDFLARE_ZONE_ID` | `staging`, `prod` | Yes | Yes | DNS/TLS automation | Platform operator |
| `COOLIFY_DEPLOY_WEBHOOK_URL` | `dev`, `staging`, `prod` | Yes | Yes | Coolify deploy trigger | Platform operator |
| `COOLIFY_API_TOKEN` | `staging`, `prod` | Yes | Yes | Coolify application management when automated | Platform operator |
| `GRAYLOG_HTTP_INPUT_URL` | `staging`, `prod` | No | Yes | Structured log ingestion | Observability operator |
| `GRAYLOG_HTTP_INPUT_TOKEN` | `staging`, `prod` | Yes | Yes | Structured log ingestion | Observability operator |
| `UPTIME_KUMA_PUSH_TOKEN` | `dev`, `staging`, `prod` | Yes | Yes | Optional Uptime Kuma push/API automation | Observability operator |
| `MAYALERTS_SOURCE_SECRET` | `dev`, `staging`, `prod` | Yes | Yes | MayAlerts source authentication | Observability operator |
| `MAYALERTS_GITLAB_TOKEN` | `staging`, `prod` | Yes | Yes | Alert-to-GitLab issue routing | Observability operator |

`LOCALRAG_EVAL_BASE_URL` and `GRAYLOG_HTTP_INPUT_URL` are not inherently
secrets, but they should still be environment-scoped. Any variable that exposes
internal network naming can be protected even when not masked.

## Kiwi TCMS Baseline

| Field | Baseline |
| --- | --- |
| Endpoint | `https://kiwi.it360.ru/json-rpc/` |
| Product | `LocalRAG` |
| Classification | `Application` |
| Version | `0.9.0` |
| Build template | `localrag-0.9.0-${CI_COMMIT_SHORT_SHA}` |
| Source ref | `${CI_COMMIT_SHA}` |
| Existing mapping file | `tests/kiwi_sync_mapping.json` |
| Existing mapping run id | `113` |
| Sync script | `scripts/kiwi_sync_pytest.py` |
| Default JUnit output | `temp/kiwi_pytest_report.xml` |

Baseline product/version/build action:

1. Confirm Kiwi product `LocalRAG` exists under classification `Application`.
2. Confirm or create version `0.9.0`.
3. Create build names from `localrag-0.9.0-${CI_COMMIT_SHORT_SHA}` for CI runs.
4. Keep API regression coverage mapped through `tests/kiwi_sync_mapping.json`.
5. For a setup-stage run, use the current mapping as the smoke/API baseline and
   create any additional manual setup cases in Kiwi rather than overloading the
   pytest mapping with non-automated provisioning checks.

Manual dry-run command:

```sh
python scripts/kiwi_sync_pytest.py --dry-run --disable-nas-fallback --pytest-args -q
```

## Cloudflare DNS/TLS Plan

The production domain is not hard-coded in application code. Replace
`localrag.example.com` and `coolify-origin.example.net` with the approved zone
and Coolify ingress target during provisioning.

| Environment | Record | Type | Target | Proxy | TLS |
| --- | --- | --- | --- | --- | --- |
| `dev` | `dev.localrag.example.com` | `CNAME` | `coolify-origin.example.net` | On | Full strict after origin cert is installed |
| `staging` | `staging.localrag.example.com` | `CNAME` | `coolify-origin.example.net` | On | Full strict before release smoke |
| `prod` | `localrag.example.com` | `CNAME` | `coolify-origin.example.net` | On | Full strict before traffic cutover |

TLS/security baseline:

- Cloudflare SSL/TLS mode: `Full (strict)`.
- Minimum TLS version: `1.2`.
- Always Use HTTPS: enabled.
- Automatic HTTPS Rewrites: enabled.
- Origin certificate: Cloudflare Origin Certificate or public ACME certificate
  installed at the Coolify reverse proxy.
- HSTS: enable only after staging and prod hostnames have served HTTPS
  successfully and rollback risk is accepted.
- Cache: do not cache `/api/*`; static assets may use normal browser/CDN cache
  rules when filenames or query versions are stable.
- Access: allow Uptime Kuma and MayAlerts to reach `/api/health` and
  `/api/meta`; restrict `/docs` outside dev/staging if FastAPI docs remain
  enabled.

## Coolify Application Baseline

| Field | Baseline |
| --- | --- |
| Application name | `localrag` |
| Type | Docker Compose |
| Compose file | `docker-compose.yml` |
| Environment template | `deploy/coolify/localrag.env.example` |
| Public port | `7860` behind Coolify reverse proxy |
| Healthcheck | `GET /api/health` |
| Volumes | `ollama_data`, `vectorstore` bind mount, `hf_cache` bind mount |
| Default model | `qwen3.5:9b` |
| Default embedding model | `intfloat/multilingual-e5-large` |

Required Coolify environment variables:

```text
SERVICE_NAME
APP_ENV
APP_VERSION
APP_RELEASE
APP_INSTANCE_ID
BUILD_DATE_UTC
LLM_MODEL
MODEL_NAME
OLLAMA_TAG
OLLAMA_BASE_URL
EMBED_MODEL
EMBEDDINGS_MODEL_NAME
HF_HOME
HOST_FS_ROOT
HOST_FS_MOUNT
DOCS_PATH
PDF_PATH
HOST_DOCS_PATH
GRAYLOG_HTTP_INPUT_URL
GRAYLOG_HTTP_INPUT_TOKEN
MAYALERTS_SOURCE_SECRET
```

Provisioning notes:

- Use `deploy/coolify/localrag.env.example` as the value baseline, then replace
  host paths and secrets per environment.
- `APP_RELEASE` should map to the image, tag, package, or Git SHA used for the
  deployment.
- `DOCS_PATH` and `HOST_DOCS_PATH` must refer to approved mounted paths. Do not
  expose private path values in alerts or public status pages.
- GPU scheduling remains host/Coolify-specific. Keep the Compose GPU
  reservation if the target supports NVIDIA runtime; otherwise record the
  target-specific override as an environment deployment note.

## Monitoring Baseline

The monitoring setup follows
`artifacts/ops-observability/design/2026-06-06-observability-contract-alert-policy.md`.

### Graylog Event Definitions

Create or prepare Graylog event definitions for these alerts:

| Alert | Environments | Severity baseline | Signal |
| --- | --- | --- | --- |
| `localrag_health_down` | `staging`, `prod` | `p1` prod, `p2` staging | `/api/health` non-2xx, timeout, or `ok=false` for 3 consecutive checks |
| `localrag_release_drift` | `staging`, `prod` | `p2` | `/api/meta` release/version differs from expected deployment manifest |
| `localrag_index_build_failed` | all | `p2` prod/staging, `p3` dev | `index.status=build_failed` or reindex job failure |
| `localrag_indexing_stuck` | all | `p2` prod/staging, `p3` dev | `index.status=indexing` exceeds the environment window |
| `localrag_ask_error_rate_high` | `staging`, `prod` | `p1` prod if sustained, `p2` staging | `/api/ask` failures exceed threshold or synthetic ask fails |
| `localrag_ollama_unavailable` | all | `p1` prod, `p2` staging, `p3` dev | Ollama model list/generation unavailable |
| `localrag_default_model_missing` | `staging`, `prod` | `p2` | Default model from `/api/meta` is absent from installed Ollama models |
| `localrag_release_smoke_failed` | `staging`, `prod` | `p2` | `scripts/release_check.py` fails |
| `localrag_observability_contract_violation` | all | `p2` prod/staging, `p3` dev | Required field missing or unsafe private payload detected |

Every Graylog event must include the required base fields from the observability
contract and must not include raw questions, answers, source passages, local
filesystem paths, cookies, or custom role prompts.

### Uptime Kuma Checks

| Check | Environment | URL template | Interval | Expected result |
| --- | --- | --- | --- | --- |
| `localrag-dev-health` | `dev` | `${LOCALRAG_DEV_BASE_URL}/api/health` | 60s | HTTP `200` |
| `localrag-staging-health` | `staging` | `${LOCALRAG_STAGING_BASE_URL}/api/health` | 60s | HTTP `200`, `ok=true`, `app.app_env=staging` |
| `localrag-staging-meta` | `staging` | `${LOCALRAG_STAGING_BASE_URL}/api/meta` | 300s | `name=LocalRAG`, `default_model=qwen3.5:9b`, `app_release` set |
| `localrag-prod-health` | `prod` | `${LOCALRAG_PROD_BASE_URL}/api/health` | 30s | HTTP `200`, `ok=true`, `app.app_env=prod` |
| `localrag-prod-ui` | `prod` | `${LOCALRAG_PROD_BASE_URL}/` | 60s | HTTP `200`, body contains `LocalRAG` |

### MayAlerts Source and GitLab Routing

| Field | Baseline |
| --- | --- |
| Source | `localrag-platform-delivery` |
| Source secret variable | `MAYALERTS_SOURCE_SECRET` |
| GitLab token variable | `MAYALERTS_GITLAB_TOKEN` |
| GitLab project path | `myprojects/localrag` |
| Fingerprint | `service_name|app_env|alert_name|severity|dedupe_resource|app_release_major_minor` |
| Non-prod labels | `area::observability`, `monitoring`, `source::mayalerts`, `alert::non-prod`, `sdlc::triage`, env label, severity label |
| Prod labels | `area::observability`, `monitoring`, `source::mayalerts`, `alert::prod`, `sdlc::triage`, env label, severity label |
| Prod visibility | Confidential by default |
| Title template | `[ALERT][${APP_ENV}][${SEVERITY}][localrag] ${ALERT_SUMMARY}` |

Alert bodies must include the privacy checklist from the observability contract:

- raw question text included: `no`
- raw answer text included: `no`
- source passages included: `no`
- raw filesystem paths included: `no`

## Provisioning Order

1. Create protected GitLab CI/CD variables from the secret map.
2. Confirm Kiwi product `LocalRAG`, version `0.9.0`, and CI build naming.
3. Create Coolify applications for `dev`, `staging`, and `prod` with the
   environment template values adjusted per environment.
4. Configure Cloudflare DNS records and Full strict TLS for the approved zone.
5. Configure Uptime Kuma checks against the deployed base URLs.
6. Configure Graylog event definitions and MayAlerts source secret.
7. Enable alert-to-GitLab routing to `myprojects/localrag`.
8. Run `pytest_ci`, staging release smoke, and `quality_gate_live` before any
   prod promotion.

## Definition of Done Coverage

- [x] Prepare CI/CD baseline and secret map.
- [x] Confirm environments: `dev`, `staging`, `prod`.
- [x] Prepare Kiwi product/version/build baseline.
- [x] Prepare Cloudflare DNS/TLS plan.
- [x] Prepare Coolify application and environment variable set.
- [x] Provision monitoring baseline: Graylog event definitions, Uptime Kuma
  checks, MayAlerts source/secret, and alert-to-GitLab routing.
