# LocalRAG Verify Cycle Evidence

## Scope

This artifact covers the 2026-06-06 SDLC verify stage for:

- #16 `[TASK][verify] Verification`
- #31 `[TRACK][website-content][verify] Content QA`
- #35 `[TRACK][seo][verify] SEO QA`
- #38 `[TRACK][image-generation][verify] Visual QA for generated images`
- #41 `[TRACK][video-generation][verify] Playback and performance QA for generated video`
- #45 `[TRACK][ops-observability][verify] Verify alert-to-issue loop`

The final verification baseline is `origin/dev` at `9b1a33c` plus the verify hotfix in this branch. Stale NAS workers for #16 and #35 started from pre-!19 `3d92605`; they were stopped and their runtime fixes were reapplied cleanly on top of `9b1a33c` without reusing stale locale changes.

## Automated Tests

| Check | Command | Result |
| --- | --- | --- |
| Targeted regression for verify hotfix | `python -m pytest -q tests/test_model_language_guard.py::test_repair_answer_language_uses_non_thinking_payload_for_qwen3 tests/test_models_manager_api.py::test_models_pull_endpoint_starts_job tests/test_models_manager_api.py::test_models_pull_endpoint_translates_not_found_error tests/test_models_manager_api.py::test_embedding_models_pull_endpoint_starts_job` | `4 passed` |
| Full local regression suite | `python -m pytest -q` | `96 passed`, `2 warnings` |
| SEO/observability focused suite before hotfix | `python -m pytest -q tests/test_seo_artifacts.py tests/test_observability_runtime.py` | `9 passed`, `2 warnings` |

Fixes applied during verification:

- `app/app.py`: Ollama `/api/generate` calls no longer pass `headers=None`, preserving compatibility with tests and lightweight request adapters.
- `main.py`: model-pull endpoints now call pull starters with `correlation_id` only when the starter supports that parameter, preserving production correlation IDs and test monkeypatch compatibility.

## Browser QA

Local server:

- URL: `http://127.0.0.1:7860/`
- Environment: `APP_ENV=verify`, `LOCALRAG_SKIP_STARTUP=1`, `SKIP_INDEX_BOOTSTRAP=1`
- Public base for SEO checks: `SEO_PUBLIC_BASE_URL=http://127.0.0.1:7860`

Browser verification was executed after restarting Uvicorn with the verify hotfix.

| Viewport | Locales | Result |
| --- | --- | --- |
| Desktop `1440x1000` | EN, RU, NL, ZH, HE | Passed |
| Mobile `390x844` | RU, HE, ZH | Passed |

Assertions:

- `body` and app language matched requested locale for all checks.
- HE used `dir=rtl`; other locales used `dir=ltr`.
- No horizontal overflow outside the animated loader line.
- No `????` placeholder text remained in RU/ZH/HE content.
- Hero and walkthrough poster images loaded from WebP with `naturalWidth=1600`.
- Hero and poster alt text matched each locale JSON.
- Hero title, walkthrough heading, and walkthrough caption matched each locale JSON.

Generated local evidence files:

- `C:\Sergey\Lab360\.codex-temp\localrag-media-integration\.verify-logs\localrag-browser-qa-after-fix.json`
- `C:\Sergey\Lab360\.codex-temp\localrag-media-integration\.verify-logs\localrag-verify-after-fix-desktop-en.png`
- `C:\Sergey\Lab360\.codex-temp\localrag-media-integration\.verify-logs\localrag-verify-after-fix-desktop-ru.png`
- `C:\Sergey\Lab360\.codex-temp\localrag-media-integration\.verify-logs\localrag-verify-after-fix-mobile-ru.png`
- `C:\Sergey\Lab360\.codex-temp\localrag-media-integration\.verify-logs\localrag-verify-after-fix-mobile-he.png`
- `C:\Sergey\Lab360\.codex-temp\localrag-media-integration\.verify-logs\localrag-verify-after-fix-mobile-zh.png`

## Content QA

Russian copy was checked against the implemented locale file and browser render:

- The hero states the product plainly: local AI search over private documents.
- Proof and limitation language avoids unsupported privacy or performance claims.
- The generated media block explains the poster/script and clearly marks the full video as a separate release asset until storage is approved.
- RU/ZH/HE media strings no longer contain placeholder question marks after MR !19.

## Media QA

Generated website media assets are integrated through responsive `picture` sources:

- Hero image: `web/static/media/image/localrag-hero-product-2026-06-06-1600x900.webp`
- Walkthrough poster: `web/static/media/video/localrag-product-walkthrough-v2-75s-poster-1600x900.webp`
- Transcript: `web/static/media/video/localrag-product-walkthrough-v2-75s-transcript.ru.md`
- Captions: `web/static/media/video/localrag-product-walkthrough-v2-75s.ru.vtt`

The browser check verified both hero and poster rendering on desktop and mobile. No MP4/WebM binary is committed in this cycle; the video remains a release asset pending an approved storage target.

## SEO QA

Verified by automated tests and browser render:

- localized title and description render through the SEO context;
- JSON-LD schema is present and parseable;
- Hebrew render sets RTL direction;
- sitemap and robots artifacts remain covered by `tests/test_seo_artifacts.py`.

Current implementation is still cookie-locale based. Locale-specific `hreflang` URLs should be added only after public locale routes or query-parameter locale pages are defined.

## Observability QA

The repository observability validator passed in the NAS worker evidence:

- Uptime Kuma monitor plan covers test/prod HTTP and push jobs.
- Graylog event definitions cover service errors and critical workflows.
- MayAlerts routing targets `myprojects/localrag`.
- Dry-run MayAlerts event renders the expected GitLab issue payload.
- GitLab project lookup succeeded for project id `4`.

Live alert injection was not executed because the worker did not expose `MAYALERTS_*`, `GRAYLOG_*`, `UPTIME_KUMA_*`, or `N8N_*` endpoint/secret environment variables. The applicable verify evidence is the repository-backed dry-run plus GitLab API lookup.
