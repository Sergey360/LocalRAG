# LocalRAG Monitoring and MayAlerts Routing Setup

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | Ops observability |
| Stage | Setup |
| GitLab issue | `#43` |
| Artifact version | `1.0` |
| Date | `2026-06-06` |
| Status | Ready for external import and live credential binding |
| Primary project | `https://lab.it360.ru/myprojects/localrag` |
| Local workspace target | `C:\Sergey\Lab360\localrag` |

## Scope

This setup artifact turns the design contract from
`artifacts/ops-observability/design/2026-06-06-observability-contract-alert-policy.md`
into import-ready monitoring and routing configuration stored in the repository.

The current worker has GitLab API credentials, but no Uptime Kuma, Graylog,
MayAlerts, or n8n credentials. Because of that, this issue stores the external
configuration as versioned artifacts and verifies the GitLab intake target with
a non-mutating API check. Live import must bind the variables listed below in
the target NAS/external services.

## Versioned Setup Outputs

| Output | Artifact |
| --- | --- |
| Uptime Kuma monitor plan for test and prod endpoints plus push jobs | `artifacts/ops-observability/setup/2026-06-06-uptime-kuma-monitor-plan.json` |
| Graylog event definitions for service errors and critical workflows | `artifacts/ops-observability/setup/2026-06-06-graylog-event-definitions.json` |
| MayAlerts source, dedupe, n8n intake, and GitLab issue routing | `artifacts/ops-observability/setup/2026-06-06-mayalerts-gitlab-routing.json` |
| MayAlerts dry-run event | `artifacts/ops-observability/setup/fixtures/2026-06-06-mayalerts-dry-run-event.json` |
| Expected GitLab issue payload for the dry run | `artifacts/ops-observability/setup/fixtures/2026-06-06-expected-gitlab-issue.json` |
| Offline and optional GitLab API validator | `scripts/validate_observability_setup.py` |

## Uptime Kuma Provisioning

Create the monitors from
`2026-06-06-uptime-kuma-monitor-plan.json`.

Required monitor coverage:

| Monitor | Environment | Type | Target | Alert |
| --- | --- | --- | --- | --- |
| `localrag-test-health` | test -> `APP_ENV=staging` | HTTP | `${LOCALRAG_TEST_BASE_URL}/api/health` | `localrag_health_down`, `p2` |
| `localrag-test-meta` | test -> `APP_ENV=staging` | HTTP | `${LOCALRAG_TEST_BASE_URL}/api/meta` | `localrag_release_drift`, `p2` |
| `localrag-test-ui` | test -> `APP_ENV=staging` | HTTP | `${LOCALRAG_TEST_BASE_URL}/` | `localrag_ui_unavailable`, `p3` |
| `localrag-test-release-smoke` | test -> `APP_ENV=staging` | Push | `scripts/release_check.py` result | `localrag_release_smoke_failed`, `p2` |
| `localrag-prod-health` | prod | HTTP | `${LOCALRAG_PROD_BASE_URL}/api/health` | `localrag_health_down`, `p1` |
| `localrag-prod-meta` | prod | HTTP | `${LOCALRAG_PROD_BASE_URL}/api/meta` | `localrag_release_drift`, `p2` |
| `localrag-prod-ui` | prod | HTTP | `${LOCALRAG_PROD_BASE_URL}/` | `localrag_ui_unavailable`, `p2` |
| `localrag-prod-release-smoke` | prod | Push | `scripts/release_check.py` result | `localrag_release_smoke_failed`, `p2` |

Test endpoints are routed as `APP_ENV=staging` because the design contract uses
`dev`, `staging`, `prod`, and `ci`. Keep the display tag `env:test` in Uptime
Kuma if that is the local service name, but send `app_env=staging` to
MayAlerts.

## Graylog Provisioning

Create a `localrag-application` stream with the match rule:

```text
service_name:localrag OR _service_name:localrag
```

Then create the event definitions from
`2026-06-06-graylog-event-definitions.json` and attach the
`mayalerts-localrag-webhook` notification.

Covered event definitions:

| Alert | Purpose |
| --- | --- |
| `localrag_service_error_5xx` | Repeated service 5xx failures by route. |
| `localrag_health_down` | Health check failures or unhealthy health payloads. |
| `localrag_index_build_failed` | Failed index build or reindex job. |
| `localrag_indexing_stuck` | Indexing active beyond the allowed window. |
| `localrag_ask_error_rate_high` | Ask workflow failure rate above threshold. |
| `localrag_ollama_unavailable` | Ollama dependency failures. |
| `localrag_default_model_missing` | Default model absent from installed model list. |
| `localrag_release_smoke_failed` | Release smoke check failed health, meta, or ask. |
| `localrag_observability_contract_violation` | Required telemetry field missing or unsafe telemetry detected. |

## MayAlerts and n8n Routing

Create two MayAlerts webhook sources:

| Source | Inbound variable | Secret variable |
| --- | --- | --- |
| `localrag-graylog` | `MAYALERTS_GRAYLOG_SOURCE_WEBHOOK_URL` | `MAYALERTS_GRAYLOG_SOURCE_SECRET` |
| `localrag-uptime-kuma` | `MAYALERTS_UPTIME_KUMA_SOURCE_WEBHOOK_URL` | `MAYALERTS_UPTIME_KUMA_SOURCE_SECRET` |

Configure the MayAlerts outgoing webhook to the n8n intake:

```text
POST ${N8N_LOCALRAG_MAYALERTS_GITLAB_INTAKE_URL}
X-LocalRAG-Alert-Secret: ${N8N_LOCALRAG_MAYALERTS_GITLAB_INTAKE_SECRET}
X-Alert-Fingerprint: <computed fingerprint>
```

The n8n workflow must:

1. Verify the shared secret.
2. Normalize environment and severity aliases.
3. Drop private fields before logging or forwarding.
4. Compute the dedupe fingerprint.
5. Search for an active GitLab issue with the same fingerprint marker.
6. Update the active issue or create a new issue in `myprojects/localrag`.
7. Set `confidential=true` for prod.
8. Return the GitLab issue IID and URL to MayAlerts.

The GitLab create endpoint is:

```text
POST https://lab.it360.ru/api/v4/projects/myprojects%2Flocalrag/issues
```

## Dedupe and Labels

Fingerprint template:

```text
service_name|app_env|alert_name|severity|dedupe_resource|app_release_major_minor
```

Non-prod labels:

```text
area::observability, monitoring, source::mayalerts, alert::non-prod,
env::staging, severity::<p1|p2|p3|p4>, sdlc::triage
```

Prod labels:

```text
area::observability, monitoring, source::mayalerts, alert::prod,
env::prod, severity::<p1|p2|p3|p4>, sdlc::triage
```

## Verification

Offline artifact validation:

```bash
python3 scripts/validate_observability_setup.py
```

Optional non-mutating GitLab project intake check:

```bash
python3 scripts/validate_observability_setup.py --check-gitlab-api
```

The dry-run fixture maps a staging `localrag_health_down` event to this expected
GitLab issue title:

```text
[ALERT][staging][p2][localrag] health down for setup dry run
```

Expected dry-run fingerprint:

```text
localrag|staging|localrag_health_down|p2|app_instance:setup-dry-run|0.9
```

Verification performed on `2026-06-06` in the GitLab NAS worker:

| Check | Result |
| --- | --- |
| Offline artifact validator | Passed |
| Dry-run MayAlerts event to GitLab issue payload | Passed |
| Non-mutating GitLab project API lookup | Passed: HTTP `200`, project id `4`, path `myprojects/localrag` |
| Live Uptime Kuma, Graylog, MayAlerts, and n8n import | Not executed in this worker because those service credentials were not present |

## Privacy Rules

Alert payloads, Uptime Kuma messages, Graylog notifications, MayAlerts logs,
n8n execution logs, and GitLab issues must not include:

- raw user questions;
- raw answers;
- source passages;
- raw filesystem paths;
- cookies, authorization headers, or secrets;
- custom prompts.

Use correlation IDs, route names, model names, embedding model names, counts,
hashes, status values, and safe release identifiers as evidence instead.

## Definition of Done Coverage

- [x] Documented Uptime Kuma monitors for test and prod endpoints and push jobs.
- [x] Documented Graylog event definitions for service errors and critical workflows.
- [x] Configured MayAlerts source, dedupe, n8n webhook, and GitLab issue routing as versioned artifacts.
- [x] Added a dry-run fixture and validator for the alert-to-GitLab intake path.
- [x] Kept all setup outputs in versioned repository artifacts, not only inside n8n.
