# LocalRAG Planning and Decomposition

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Stage | Plan |
| Issue | #12 - Planning and Decomposition |
| Artifact version | 1.0 |
| Date | 2026-06-06 |
| Status | Ready for executable issue creation |
| Primary project | `https://lab.it360.ru/myprojects/localrag` |
| Repository topology | `mono` |
| Additional repositories | `0` |
| Local workspace target | `C:\Sergey\Lab360\localrag` |

## Purpose

This planning artifact turns the merged analysis and design artifacts into an
executable delivery plan. It defines the stage tasks, implementation slices,
dependencies, and Definition of Done rules needed to create downstream GitLab
issues for the LocalRAG public website and supporting product-readiness work.

The plan is intentionally scoped to the current mono-repository. No additional
repositories are needed for this stage.

## Required Inputs

- `docs/initiation.md`
- `docs/discovery-and-analysis.md`
- `docs/solution-design.md`
- `docs/website-content/content-brief-page-map.md`
- `docs/website-content/ru-first-multilingual-copy-analysis.md`
- `artifacts/website-content/design/2026-06-06-draft-page-copy.md`
- `artifacts/seo/design/2026-06-06-seo-structure-metadata-plan.md`
- `artifacts/image-generation/design/2026-06-06-image-direction-briefs.md`
- `artifacts/video-generation/design/2026-06-06-ru-first-motion-video-addendum.md`
- `artifacts/ops-observability/design/2026-06-06-observability-contract-alert-policy.md`
- `artifacts/ops-observability/setup/2026-06-06-monitoring-mayalerts-routing.md`

## Planning Principles

- Build the usable product experience first, not a separate marketing shell.
- Keep Russian copy as the source baseline for layout, metadata, CTA length,
  claim strength, screenshots, and QA.
- Treat the current FastAPI app, README, screenshots, tests, and release scripts
  as implementation evidence. Do not publish claims without evidence.
- Split work into independently reviewable GitLab issues with one primary owner,
  one validation path, and a clear release slice.
- Keep website, observability, generated media, SEO, and localization work
  loosely coupled so a blocked asset or locale does not block the first release
  slice.
- Preserve the mono-repo topology unless a later deployment or ownership need
  creates a concrete reason to split repositories.

## Stage Task Map

| Stage task | Output | Primary dependencies | Exit criteria |
| --- | --- | --- | --- |
| Planning backlog creation | GitLab issues created from the backlog below | This document | Every P0/P1 issue has scope, dependencies, DoD, and release slice. |
| Implementation setup | Public website route/component foundation and page data contract | Planning backlog, solution design, SEO plan, copy artifact | The website can render the Russian homepage locally with structured metadata placeholders. |
| Content and SEO implementation | Russian-first pages, metadata, schema, hreflang-ready data | Setup foundation, copy artifact, SEO plan | Crawlable pages expose approved copy, claim statuses, and validated metadata. |
| Product proof and visual assets | Screenshots, generated/static visuals, alt text, responsive media | Setup foundation, image/video briefs, current UI state | First-viewport proof and workflow/source visuals render without unsupported claims. |
| Runtime proof integration | Health/meta links, release checks, quality proof blocks | Current app APIs and release scripts | Website points to verifiable product checks without leaking private content. |
| Localization expansion | EN/NL/ZH/HE copy and route metadata | Russian baseline complete, locale QA capacity | Localized pages preserve claim strength and pass layout/RTL checks. |
| Observability implementation | Structured telemetry, correlation IDs, alert routing follow-up issues | Observability design and setup artifacts | Monitoring work is split into implementation issues with privacy-safe fields and alerts. |
| Browser and release verification | QA reports, screenshots, smoke/eval evidence | Website implementation, assets, locales, observability hooks | Required desktop/mobile/RTL/reduced-motion checks and release commands pass or have tracked follow-ups. |

## Release Slices

| Slice | Goal | Included issue groups | Release gate |
| --- | --- | --- | --- |
| R0 - Planning baseline | Make the downstream work executable. | PLAN-01 through PLAN-04 | This artifact is merged; P0/P1 GitLab issues can be opened. |
| R1 - Russian website MVP | Ship a Russian-first public product page with real proof and safe claims. | WEB-01 through WEB-06, SEO-01, QA-01 | Homepage and collapsed guide/FAQ sections render locally; metadata validates; Python tests pass. |
| R2 - Structured public site | Split MVP content into crawlable pages and add richer proof media. | WEB-07 through WEB-10, SEO-02, ASSET-01 through ASSET-03, QA-02 | Key public routes, visuals, and schema are browser-verified on desktop and mobile. |
| R3 - Localization and RTL | Publish approved localized variants without stronger claims. | LOC-01 through LOC-04, SEO-03, QA-03 | EN/NL/ZH/HE pages pass locale, wrapping, and Hebrew RTL checks. |
| R4 - Observability and release discipline | Implement privacy-safe telemetry and release evidence. | OBS-01 through OBS-06, REL-01 through REL-03, QA-04 | Health/meta, logs, metrics, MayAlerts routing, smoke checks, and eval gates produce traceable evidence. |

## Executable Issue Backlog

### Planning and Coordination

| ID | Proposed GitLab issue title | Type | Priority | Slice | Dependencies | Acceptance summary |
| --- | --- | --- | --- | --- | --- | --- |
| PLAN-01 | Create website implementation epic and child issue set | Task | P0 | R0 | This document | P0/P1 child issues exist with labels, dependencies, DoD, and release slice. |
| PLAN-02 | Confirm owner approval rules for public claims and commercial CTAs | Task | P0 | R0 | Claim status register | Approval-required claims are either removed, noindexed, or assigned to owner review. |
| PLAN-03 | Define asset storage and generated-media approval path | Task | P1 | R0 | Image/video briefs | Media paths, size limits, prompt storage, and approval checklist are documented. |
| PLAN-04 | Define browser QA matrix and execution environment | Task | P1 | R0 | Solution design, labels/capabilities | Desktop/mobile/reduced-motion/RTL checks are mapped to local or NAS execution rules. |

### Website Implementation

| ID | Proposed GitLab issue title | Type | Priority | Slice | Dependencies | Acceptance summary |
| --- | --- | --- | --- | --- | --- | --- |
| WEB-01 | Build structured page data contract for public website content | Feature | P0 | R1 | PLAN-01, SEO plan, copy artifact | Page data includes route, locale, metadata, headings, CTA, claim status, proof source, and noindex state. |
| WEB-02 | Implement Russian homepage shell in the existing web surface | Feature | P0 | R1 | WEB-01, solution design | `/` renders Russian hero, proof strip, workflow, screenshots/proof, quality block, FAQ, and final CTA. |
| WEB-03 | Add responsive navigation and footer for public pages | Feature | P0 | R1 | WEB-01 | Header/footer support Russian labels, active routes, CTA, and mobile wrapping at 390px. |
| WEB-04 | Implement current product proof modules | Feature | P0 | R1 | WEB-02, current screenshots | Source context, model/settings, language, reindex, and eval proof blocks are visible and evidence-backed. |
| WEB-05 | Add guide/getting-started content as an MVP section or route | Feature | P0 | R1 | WEB-01, README verification | Commands and expected health/meta results match current runtime docs. |
| WEB-06 | Add privacy/security FAQ content with limitations | Feature | P0 | R1 | WEB-01, claim register | FAQ states local default boundaries and configuration limits without compliance overclaiming. |
| WEB-07 | Split `/features` from the homepage MVP | Feature | P1 | R2 | WEB-02, WEB-04 | Feature page covers implemented capabilities, limitations, proof, and CTA. |
| WEB-08 | Split `/how-it-works` retrieval flow page | Feature | P1 | R2 | WEB-02, ASSET-02 | Route explains folder, chunks, embeddings, FAISS, Ollama, answer, and sources. |
| WEB-09 | Split `/guide/retrieval-quality` page | Feature | P1 | R2 | WEB-05, REL-01 | Page documents pytest, release checks, eval gate, and score-publication rules. |
| WEB-10 | Add `/release-notes` public page from release sources | Feature | P2 | R2 | REL-01, VERSION, release notes | Page exposes verified version/defaults and known limitations. |

### SEO and Metadata

| ID | Proposed GitLab issue title | Type | Priority | Slice | Dependencies | Acceptance summary |
| --- | --- | --- | --- | --- | --- | --- |
| SEO-01 | Implement Russian metadata contract for MVP pages | Task | P0 | R1 | WEB-01, SEO plan | Title, description, canonical, robots, Open Graph, and image alt fields are rendered for MVP pages. |
| SEO-02 | Add JSON-LD schema for implemented public pages | Task | P1 | R2 | WEB-07 through WEB-10 | Schema mirrors visible content only and excludes ratings, offers, and unverified organization claims. |
| SEO-03 | Add hreflang and localized metadata alternates | Task | P1 | R3 | LOC-01 through LOC-04 | Published locale routes emit correct alternates and self-canonicals. |
| SEO-04 | Prepare noindex handling for planned/custom-scope pages | Task | P1 | R2 | WEB-01, PLAN-02 | Planned, duplicate, custom-scope, and approval-gated routes use explicit robots policy. |

### Assets, Motion, and Video

| ID | Proposed GitLab issue title | Type | Priority | Slice | Dependencies | Acceptance summary |
| --- | --- | --- | --- | --- | --- | --- |
| ASSET-01 | Capture and optimize current product screenshots | Task | P0 | R1 | WEB-02, current app runnable | Screenshots are dated/versioned, optimized, and mapped to alt text and captions. |
| ASSET-02 | Create static retrieval-flow visual fallback | Task | P0 | R2 | Image direction brief | Visual shows folder to sources flow, supports mobile crop, and avoids cloud/security symbols. |
| ASSET-03 | Generate approved hero/source-proof image variants | Task | P1 | R2 | PLAN-03, image direction brief | Prompts, selected outputs, constraints, alt text, and approvals are committed before use. |
| ASSET-04 | Implement optional motion loop with reduced-motion fallback | Feature | P2 | R2 | ASSET-02, solution design | Motion explains workflow, respects `prefers-reduced-motion`, and does not block CTA/content. |
| ASSET-05 | Prepare 75s Russian walkthrough video plan and poster | Task | P2 | R2 | Video addendum, ASSET-03 | Poster, transcript outline, claim constraints, and storage decision are ready. |

### Localization

| ID | Proposed GitLab issue title | Type | Priority | Slice | Dependencies | Acceptance summary |
| --- | --- | --- | --- | --- | --- | --- |
| LOC-01 | Add English public website copy and metadata | Task | P1 | R3 | Russian MVP complete | English preserves Russian claim strength and technical terms. |
| LOC-02 | Add Dutch public website copy and metadata | Task | P1 | R3 | Russian MVP complete | Dutch copy avoids GDPR/compliance implication and passes wrapping checks. |
| LOC-03 | Add Chinese public website copy and metadata | Task | P1 | R3 | Russian MVP complete | Chinese copy is concise and passes compact layout checks. |
| LOC-04 | Add Hebrew public website copy, metadata, and RTL layout support | Feature | P1 | R3 | Russian MVP complete | Hebrew pages use `dir="rtl"` with safe LTR rendering for product tokens, paths, and URLs. |

### Observability and Release Readiness

| ID | Proposed GitLab issue title | Type | Priority | Slice | Dependencies | Acceptance summary |
| --- | --- | --- | --- | --- | --- | --- |
| OBS-01 | Add request correlation ID middleware | Feature | P1 | R4 | Observability contract | `X-Request-ID` is accepted, generated, returned, and included in privacy-safe logs. |
| OBS-02 | Add structured log field contract for HTTP/RAG/index events | Feature | P1 | R4 | OBS-01 | Required fields are emitted without raw questions, answers, source passages, or private paths. |
| OBS-03 | Add `/metrics` endpoint with Prometheus-safe labels | Feature | P2 | R4 | OBS-02 | Metrics avoid high-cardinality/private labels and include required service/app labels. |
| OBS-04 | Add `/api/meta` observability fields | Feature | P2 | R4 | OBS-01 | Meta includes service/app environment fields where configured without leaking private deployment data. |
| OBS-05 | Implement MayAlerts/GitLab routing payloads | Task | P2 | R4 | Monitoring routing artifacts, OBS-02 | Alert fingerprints, project path, severity, and evidence payloads match the setup plan. |
| OBS-06 | Add observability contract validation script | Task | P2 | R4 | OBS-02, OBS-03 | Script checks required fields and unsafe payload patterns in sample logs/metrics. |
| REL-01 | Verify release defaults in website and docs | Task | P0 | R1 | WEB-05, VERSION, README | Version, default model, embedding model, supported languages, and paths match repository sources. |
| REL-02 | Add release QA evidence artifact template | Task | P1 | R2 | QA-01 | Template records commands, screenshots, browser checks, eval reports, and known limits. |
| REL-03 | Extend release check output for website proof links | Task | P2 | R4 | WEB-02, release_check.py | Smoke output can cite public proof routes without requiring private content. |

### Quality Assurance

| ID | Proposed GitLab issue title | Type | Priority | Slice | Dependencies | Acceptance summary |
| --- | --- | --- | --- | --- | --- | --- |
| QA-01 | Add MVP website verification checklist | Task | P0 | R1 | WEB-02 through WEB-06, SEO-01 | Checklist covers 390px mobile, desktop, CTA targets, text wrapping, metadata, and claim statuses. |
| QA-02 | Run browser QA for structured public routes | Task | P1 | R2 | WEB-07 through WEB-10, ASSET-01 through ASSET-04 | Desktop/mobile screenshots, reduced-motion, visual assets, and no-overlap checks are recorded. |
| QA-03 | Run localization and Hebrew RTL browser QA | Task | P1 | R3 | LOC-01 through LOC-04, SEO-03 | EN/NL/ZH wrapping and HE RTL/LTR token handling are verified. |
| QA-04 | Run release smoke and eval gate for public release candidate | Task | P1 | R4 | REL-01, observability implementation as available | `pytest`, release smoke, and eval gate results are recorded or tracked as blocking follow-ups. |

## Dependency Graph

```text
R0 planning
  -> WEB-01 page data contract
    -> WEB-02 homepage MVP
      -> WEB-03 navigation/footer
      -> WEB-04 product proof modules
      -> WEB-05 getting-started guide
      -> WEB-06 privacy/security FAQ
      -> SEO-01 metadata
      -> REL-01 release defaults verification
      -> QA-01 MVP verification
    -> WEB-07 features route
    -> WEB-08 how-it-works route
    -> WEB-09 retrieval-quality route
    -> WEB-10 release-notes route
    -> SEO-02 schema
    -> SEO-04 noindex handling
  -> PLAN-03 asset approval path
    -> ASSET-01 screenshots
    -> ASSET-02 retrieval visual fallback
      -> ASSET-04 optional motion loop
    -> ASSET-03 generated image variants
      -> ASSET-05 video poster/plan
  -> Russian MVP complete
    -> LOC-01 English
    -> LOC-02 Dutch
    -> LOC-03 Chinese
    -> LOC-04 Hebrew RTL
      -> SEO-03 hreflang/localized metadata
      -> QA-03 locale QA
  -> OBS-01 correlation IDs
    -> OBS-02 structured logs
      -> OBS-03 metrics
      -> OBS-05 MayAlerts/GitLab routing
      -> OBS-06 validation script
    -> OBS-04 meta fields
```

## Critical Path

1. Create downstream P0/P1 issues from this backlog.
2. Implement the structured page data contract.
3. Render the Russian homepage MVP with verified copy and proof modules.
4. Add MVP metadata and verify release defaults.
5. Capture or select current proof media.
6. Run MVP QA and fix layout/claim issues.
7. Split structured routes and add schema.
8. Expand locales and run RTL/localization QA.
9. Implement observability and release-evidence follow-ups.

The first releasable increment is R1. R2 through R4 can proceed in parallel once
the Russian MVP and page data contract are stable.

## Definition of Done by Work Type

### Documentation

- Scope, owner, inputs, outputs, dependencies, and non-goals are stated.
- Acceptance criteria are specific enough to create or close GitLab issues.
- Claims are tagged as `implemented`, `planned`, `custom scope`, or
  `verify-before-publish`.
- Links point to repository files, current artifacts, or approved external
  references.
- Markdown is readable in GitLab and does not rely on unsupported formatting.

### Website and Frontend

- The route or component renders the intended content without placeholder
  claims.
- Layout is checked at desktop and 390px mobile widths.
- Buttons, navigation, screenshots, media, and long Russian labels do not
  overlap or resize fixed-format controls unexpectedly.
- Product proof appears before abstract benefit copy.
- `prefers-reduced-motion` is respected for animated or canvas content.
- Basic automated tests or smoke checks run where available.

### SEO and Content

- Title, description, canonical, robots policy, Open Graph data, and image alt
  text are present for published pages.
- Schema mirrors visible page content and omits ratings, offers, testimonials,
  customer logos, or compliance claims unless approved.
- Localized metadata preserves the Russian source meaning and claim strength.
- Noindex rules are explicit for planned, thin, duplicate, approval-gated, or
  custom-scope pages.
- Metadata values are verified against current repository sources before
  publication.

### Generated Assets and Motion

- Purpose, prompt, target page/block, alt text, constraints, crop guidance, and
  approval state are recorded.
- Assets are optimized and stored under approved repository paths before use.
- Visuals do not imply cloud upload, security certification, compliance,
  customer proof, ratings, or universal OCR/model quality.
- Static fallbacks exist for motion, video, canvas, and 3D elements.
- Browser QA confirms the asset is visible, readable, correctly cropped, and
  non-overlapping on desktop and mobile.

### Localization

- Russian remains the source baseline.
- Translations preserve technical identifiers such as `LocalRAG`, `Ollama`,
  `FAISS`, `RAG`, model tags, routes, paths, and commands.
- EN/NL/ZH copy is checked for meaning, claim strength, and line wrapping.
- Hebrew pages set `dir="rtl"` and keep LTR tokens readable.
- Native or domain review is tracked before public launch where required.

### Backend/API and Observability

- New fields, endpoints, and middleware are covered by focused tests.
- Logs, metrics, and alerts never include raw questions, answers, source
  passages, document contents, cookie values, custom role prompts, or private
  local paths.
- Correlation IDs propagate through request, background job, and alert evidence
  paths where applicable.
- Health/meta changes remain backward compatible or are documented.
- Sample log/metric/alert payloads satisfy the observability contract.

### QA and Release

- The relevant local command set is recorded with pass/fail results.
- For code changes, run at least compile checks and targeted tests; run full
  `pytest -q` for broad route/runtime changes.
- For public website changes, record desktop/mobile browser evidence and
  reduced-motion checks.
- For localization changes, record locale wrapping and Hebrew RTL evidence.
- For release-candidate validation, run `scripts/release_check.py` and model
  eval gates against a running candidate environment when available.
- Blocking failures have linked follow-up issues with owner, severity, and
  release-slice impact.

## Issue Template for Downstream Work

```markdown
## What To Do

Implement <specific output>.

## Inputs

- <artifact or source file>

## Scope

- <included work>

## Out of Scope

- <excluded work>

## Dependencies

- Blocks: <issue IDs>
- Blocked by: <issue IDs>

## Acceptance Criteria

- [ ] <observable result>
- [ ] <validation result>
- [ ] <documentation or evidence result>

## Definition of Done

- [ ] Work type DoD from `docs/planning-and-decomposition.md` is satisfied.
- [ ] Relevant tests/checks are run and recorded.
- [ ] Claims and metadata are verified against current repository sources.
```

## Execution Notes

- Standard execution path applies.
- Browser/UI validation is not required for this planning issue because the
  issue labels do not include `cap::chrome-mcp` and `exec::nas`.
- The active GitLab worker checkout is Linux-based; the Windows path
  `C:\Sergey\Lab360\localrag` remains the confirmed local workspace target from
  project context.

## Definition of Done Coverage for Issue #12

- Split work into executable issues: covered by `Executable Issue Backlog` and
  `Issue Template for Downstream Work`.
- Define dependencies and release slices: covered by `Release Slices`,
  `Dependency Graph`, and `Critical Path`.
- Define DoD per work type: covered by `Definition of Done by Work Type`.
