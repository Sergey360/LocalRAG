# LocalRAG Approved Copy Integration

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | Website content |
| Stage | Dev |
| Issue | #30 - Integrate approved copy into product |
| Date | 2026-06-06 |
| Source artifact | `artifacts/website-content/design/2026-06-06-draft-page-copy.md` |
| Implementation status | Integrated into active product UI |

## Integrated Surfaces

| Approved copy section | Product target | Localization keys |
| --- | --- | --- |
| Home SEO title and meta description | `web/templates/index.html` | `home_seo_title`, `home_meta_description` |
| Global navigation copy | `web/templates/main_content.html` header anchors | `nav_why`, `nav_features`, `nav_how_it_works`, `nav_start`, `nav_quality` |
| Home hero | `web/templates/main_content.html#home` | `home_hero_title`, `home_hero_subhead`, `home_hero_microcopy`, `cta_run_locally`, `cta_view_interface` |
| Product proof strip | `web/templates/main_content.html#home` linked proof list | `proof_local_files`, `proof_source_context`, `proof_languages`, `proof_stack`, `proof_visible_settings`, `proof_quality_checks` |
| Problem framing | `web/templates/main_content.html#why` | `problem_kicker`, `problem_heading`, `problem_body` |
| Product promise | `web/templates/main_content.html#features` linked feature cards | `promise_index_*`, `promise_context_*`, `promise_sources_*`, `promise_settings_*` |
| Privacy boundary and source trust | Trust block below features | `privacy_*`, `source_trust_*` |
| Workflow preview | `web/templates/main_content.html#workflow` linked workflow steps | `workflow_heading`, `workflow_step_*` |
| Quality teaser and final CTA | `web/templates/main_content.html#quality` | `quality_*`, `final_cta_*`, `cta_open_api_docs` |
| Footer short copy and links | `web/templates/main_content.html` footer | `footer_short_copy`, `footer_api_docs`, `footer_release_notes` |

## Localization Scope

The Russian source copy was integrated first, then adapted into existing UI
languages:

- `app/locales/ru.json`
- `app/locales/en.json`
- `app/locales/nl.json`
- `app/locales/zh.json`
- `app/locales/he.json`

The content remains tied to live product controls through anchors:

- `#start` and `#status-card` for local folder and reindexing copy.
- `#settings-card` for model, answer language, and retrieval settings.
- `#ask-form` and `#product-interface` for the question workflow.
- `#context-panel` for source provenance copy.
- `/docs` for API documentation.

## Deferred Copy

Screenshot captions and unsupported social-proof replacements from the design
artifact were not published in the UI because they are marked `[VERIFY]` or are
instructions for avoiding unverified claims. They remain versioned in the source
artifact for a future screenshot-refresh or public marketing page pass.
