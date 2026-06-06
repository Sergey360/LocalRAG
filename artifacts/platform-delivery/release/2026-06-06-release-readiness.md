# LocalRAG Release Readiness

## Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Stage | Release |
| GitLab issue | `#18` |
| Date | `2026-06-06` |
| Target version | `0.9.0` |
| Candidate commit | `489406337fbefd213fd3a5f8a7fb50a5d49aa03f` |
| Candidate branch | `dev` |
| Target release branch | `main` |

## Verification Summary

| Check | Evidence | Result |
| --- | --- | --- |
| Full pytest suite | `python -m pytest -q` | `96 passed`, `2 warnings` |
| Targeted verify hotfix tests | `python -m pytest -q tests/test_model_language_guard.py::test_repair_answer_language_uses_non_thinking_payload_for_qwen3 tests/test_models_manager_api.py::test_models_pull_endpoint_starts_job tests/test_models_manager_api.py::test_models_pull_endpoint_translates_not_found_error tests/test_models_manager_api.py::test_embedding_models_pull_endpoint_starts_job` | `4 passed` |
| Browser locale QA | `.verify-logs/localrag-browser-qa-after-fix.json` | `8/8` checks passed |
| Release package | `python scripts/package_release.py --source-ref 489406337fbefd213fd3a5f8a7fb50a5d49aa03f` | Passed |
| Release smoke health/meta | `python scripts/release_check.py --base-url http://127.0.0.1:7860 --expected-model qwen3.5:9b` | Health and meta passed |
| Release smoke ask | same command | Blocked by unavailable local Ollama/model runtime |

## Package Evidence

`scripts/package_release.py` produced:

- `dist/LocalRAG-v0.9.0.zip`
- `dist/LocalRAG-v0.9.0.zip.sha256`
- `dist/release-manifest.json`

Package metadata:

- archive: `LocalRAG-v0.9.0.zip`
- sha256: `1c6e6f3c0d3ee30a25d8027148022aef746bfe8cd8d68dddedce5c28eba10ae7`
- source ref: `489406337fbefd213fd3a5f8a7fb50a5d49aa03f`
- git dirty: `false`

## Release Smoke Result

The release smoke script was run against the local verify server:

```sh
python scripts/release_check.py --base-url http://127.0.0.1:7860 --expected-model qwen3.5:9b
```

Passed checks:

- `/api/health` returned `ok=true`.
- `/api/meta` reported `default_model=qwen3.5:9b`.
- Runtime metadata reported `app_release=0.9.0`, `service_name=localrag`, and supported languages `EN/RU/NL/ZH/HE`.

Blocked check:

- `/api/ask` returned `Models unavailable. Check the Ollama service.`

This is an environment limitation in the local verify runtime, not a code regression. A full release smoke and extended eval gate still require a release candidate environment with Ollama available and `qwen3.5:9b` installed.

## Rollback Plan

Rollback target:

- Keep the previous `main` commit available before merging the release MR.
- If the release MR is merged and a deployment fails, redeploy the previous known-good `main` SHA from GitLab or Coolify.
- If a public GitHub mirror publish runs from `main`, publish a revert commit rather than force-pushing the public mirror.

Rollback commands/operators:

- GitLab: create a revert MR for the release merge commit, or redeploy the prior `main` SHA if the deployment platform supports pinned refs.
- Coolify: redeploy the previous successful deployment/ref from the application deployment history.
- DNS/TLS: no DNS cutover is required for this content refresh; do not change Cloudflare records as part of rollback unless a later deploy step changes routing.

Rollback validation:

- `GET /api/health` returns `ok=true`.
- Root page renders.
- Monitoring/health checks return to the previous green state.

## Backup Posture

This release changes source code, static media, documentation, and repository artifacts. It does not intentionally migrate user data, FAISS indexes, model caches, or document storage.

Backup expectations before production go-live:

- Preserve the previous GitLab `main` SHA and release package manifest.
- Keep deployment platform rollback history enabled.
- Do not delete existing document volumes, FAISS index volumes, Ollama model volumes, or environment secrets during deployment.
- If a production deployment uses persistent volumes, verify that volume snapshots or host backups are current before go-live.

## Go / No-Go Recommendation

Recommendation: **Go for `dev -> main` release MR creation, no automatic production deploy yet.**

Rationale:

- All code-level and browser verification checks passed after the verify hotfix.
- Release package generation is reproducible and clean.
- The remaining release smoke gap depends on runtime model availability and must be completed in staging or the actual deployment environment before approving go-live traffic.

Required before production traffic:

- Start the release candidate with Ollama reachable.
- Install or expose `qwen3.5:9b`.
- Run `scripts/release_check.py` until all checks pass.
- Run the extended eval gate from `RELEASE.md` or GitLab `quality_gate_live` with `LOCALRAG_EVAL_BASE_URL`.
