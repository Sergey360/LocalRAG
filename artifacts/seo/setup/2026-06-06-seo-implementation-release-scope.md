# LocalRAG SEO Implementation and Release Scope

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | SEO |
| Stage | Dev |
| Issue | #34 - Implement SEO artifacts |
| Artifact version | 1.0 |
| Date | 2026-06-06 |
| Status | Implemented for current FastAPI app surface |

## Scope Implemented

Issue #34 implements SEO wiring for the app routes that exist in this repository.
It does not create the separate crawlable marketing website proposed in the SEO
design artifact. That separation is intentional because
`artifacts/seo/design/2026-06-06-seo-structure-metadata-plan.md` marks the
running app UI as an app-only surface that should prefer `noindex,follow`
unless it is intentionally published as crawlable content.

Implemented in code:

- localized `<title>` and meta description for EN, RU, NL, ZH-CN, and HE;
- `<html lang>` and Hebrew `dir="rtl"` handling in the root app template;
- canonical URL from `SEO_PUBLIC_BASE_URL`;
- meta robots plus `X-Robots-Tag`;
- Open Graph and Twitter summary metadata;
- JSON-LD `SoftwareApplication` schema limited to current visible/product facts;
- `GET /robots.txt`;
- `GET /sitemap.xml`;
- explicit deployment knobs in `.env.example`, `docker-compose.yml`, and the
  Coolify environment template.

## Runtime Contract

| Setting | Default | Purpose |
| --- | --- | --- |
| `SEO_PUBLIC_BASE_URL` | `https://localrag.dev` | Absolute canonical and sitemap URL base. |
| `SEO_INDEX_APP` | `0` | Keeps the app UI non-indexed by default. Set to `1` only when a deployment intentionally exposes the root app UI as a public crawlable page. |

Default behavior:

- root UI emits `noindex,follow`;
- `robots.txt` disallows crawling all routes;
- `sitemap.xml` is valid but empty.

Indexed opt-in behavior with `SEO_INDEX_APP=1`:

- root UI emits `index,follow`;
- `robots.txt` allows `/`, disallows `/api/`, `/docs`, and `/redoc`;
- `sitemap.xml` includes the canonical root URL.

## Schema Claim Boundaries

The JSON-LD schema intentionally omits:

- ratings and review counts;
- offers and pricing;
- compliance, certification, HIPAA, SOC 2, GDPR, or air-gap claims;
- customer logos and testimonials;
- site-search actions that are not implemented as public website search.

The schema includes only current implementation facts: LocalRAG name, canonical
URL, release version, local document workflow, Ollama/FAISS runtime, supported
file categories, source context where metadata is available, multilingual UI,
answer-language control, roles, and retrieval-quality checks.

## Release Scope Link

`RELEASE.md` now lists the SEO wiring as release-ready scope and adds smoke
checks for:

- `GET /robots.txt`;
- `GET /sitemap.xml`;
- canonical, robots, Open Graph, and JSON-LD tags on the UI.

## Follow-Up Outside This Issue

The public marketing website routes from the SEO plan remain future work:

- `/features`;
- `/how-it-works`;
- `/guide/getting-started`;
- `/guide/retrieval-quality`;
- `/use-cases`;
- `/faq/privacy-security`;
- `/for-teams`;
- `/release-notes`;
- split feature and comparison pages.

Those pages need visible page copy, claim-status review, localized route URLs,
reciprocal hreflang, and browser QA before they should be indexed.

## Definition of Done Coverage

- [x] Implement metadata and schema.
- [x] Update sitemap, robots, and canonical wiring for the current app surface.
- [x] Link implementation to release scope.
- [x] Store output as a versioned repository artifact.

## Verification

Run on 2026-06-06 in the Codex NAS worker:

- `python3 -m py_compile main.py tests/test_seo_artifacts.py` - passed.
- `python3 -m json.tool deploy/platform-delivery/platform-delivery-baseline.json` - passed.
- `pytest -q tests/test_seo_artifacts.py` - blocked because `pytest` is not installed on the host.
- `python3 -m pytest -q tests/test_seo_artifacts.py` - blocked because the `pytest` module is not installed on the host.
- `python3 - <<'PY' ... import main ... PY` - blocked because runtime dependencies such as `uvicorn`, `fastapi`, `jinja2`, and LangChain packages are not installed on the host.
