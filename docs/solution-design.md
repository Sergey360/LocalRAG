# LocalRAG Solution Design

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Stage | Design |
| Issue | #7 - Solution Design |
| Artifact version | 1.0 |
| Date | 2026-06-06 |
| Status | Ready for setup, planning, implementation, and browser verification |

## Purpose

This solution design turns the approved analysis artifacts into an executable
website and product-front design direction for the new LocalRAG SDLC cycle. It
is Russian-first: Russian copy, Russian button length, Russian proof framing,
and Russian limitation notes are the baseline for layout, motion, QA, and later
localization into English, Dutch, Chinese, and Hebrew.

Required inputs:

- `docs/discovery-and-analysis.md`
- `docs/website-content/content-brief-page-map.md`
- `docs/website-content/ru-first-multilingual-copy-analysis.md`
- `artifacts/website-content/design/2026-06-06-draft-page-copy.md`
- `artifacts/seo/design/2026-06-06-seo-structure-metadata-plan.md`
- `artifacts/video-generation/design/2026-06-06-ru-first-motion-video-addendum.md`
- `artifacts/ops-observability/design/2026-06-06-observability-contract-alert-policy.md`

Russian web copy must follow the standards referenced in the Russian-first
analysis:

- `ru-text`: natural Russian, direct UX wording, readable typography, no
  bureaucratic filler, no literal English word order.
- `ru-web-copy-editor`: concrete offer, proof-led claims, clear CTAs,
  objection handling, unsupported-claim flags, and anti-calque rewriting.

## Product Experience Goal

The public experience should make LocalRAG feel like a serious local-first
product, not a generic AI landing page. The first screen must show:

- product identity: `LocalRAG`;
- Russian value proposition: `Локальный ИИ-поиск по приватным документам`;
- one clear primary action: `Запустить локально`;
- visible product proof: local folder, source context, Ollama/FAISS/retrieval
  controls, or a current product screenshot;
- a hint of the next section on desktop and mobile.

The design should surprise through clarity and product-specific motion:
retrieval graph, local-folder boundary, source-proof overlays, and scroll
transitions that explain the workflow. It must not rely on decorative AI glow,
unsupported lock/compliance imagery, fake ratings, or abstract hero cards.

## Information Architecture

Initial public website structure:

| Route | Purpose | Primary CTA | Key proof | Status |
| --- | --- | --- | --- | --- |
| `/` | Explain LocalRAG and move users to local start or product proof. | `Запустить локально` | local folder, source context, UI languages, Ollama, eval checks | Implement first |
| `/features` | Show implemented product capabilities without hype. | `Проверить источники` | formats, source context, roles, model manager, languages | Implement first or as section |
| `/how-it-works` | Explain the RAG flow. | `Смотреть retrieval flow` | folder -> chunks -> embeddings -> FAISS -> Ollama -> sources | Implement first or as section |
| `/guide/getting-started` | Help a technical user run the product. | `Склонировать репозиторий` | Docker Compose, Ollama, `/api/health`, `/api/meta` | Implement first |
| `/guide/retrieval-quality` | Explain quality and eval discipline. | `Запустить eval` | pytest, release checks, eval gate, source-hit checks | Implement after homepage |
| `/use-cases` | Match product to practical document workflows. | `Проверить на своей папке` | PDF, notes, code, mixed languages, OCR limits | Implement after homepage |
| `/faq/privacy-security` | Answer privacy objections carefully. | `Проверить архитектуру` | local default, configuration limits, source visibility | Implement first or as FAQ section |
| `/for-teams` | Present corporate rollout as custom scope. | `Обсудить внедрение` | integration questions, access boundaries, monitoring, quality | Noindex or approval-required until owner approval |
| `/release-notes` | Show version and release discipline. | `Смотреть текущий релиз` | version, defaults, checks, known limits | Implement when release source is ready |

Subpages may be collapsed into homepage sections for the first implementation
slice, but their copy and metadata must remain structured so they can split
later without rewriting the product story.

## Page Block Design

### Home

1. Hero
   - H1: `Локальный ИИ-поиск по приватным документам.`
   - Body: approved draft copy from website-content artifact.
   - CTAs: `Запустить локально`, `Посмотреть интерфейс`.
   - Visual: real product UI with local-folder boundary and source card, or a
     generated product-faithful illustration if current screenshots are not
     ready.
   - Motion: 6 second reduced loop from folder -> index -> answer -> source.

2. Problem
   - Heading: `Реальные папки редко похожи на демо-набор.`
   - Purpose: show mixed PDFs, scans, notes, tables, code, and languages.
   - Visual: compact document stack, not stock office imagery.

3. Product Promise
   - Four cards: local folder, context-backed answer, sources, visible settings.
   - Cards should be dense and scannable, with icons and one proof sentence.

4. Workflow
   - Steps: add documents, reindex, ask, inspect sources, tune quality.
   - Motion: scroll-triggered retrieval path; no scroll-jacking.

5. Interface Proof
   - Real screenshots with version/date captions.
   - Required states: answer/context, model settings, folder/reindex, roles.

6. Quality
   - Proof modules for tests, smoke checks, eval.
   - Avoid numeric quality claims unless a dated eval run is linked.

7. Final CTA
   - `Проверьте LocalRAG на небольшой папке.`
   - CTAs: `Запустить локально`, `Открыть API docs`.

### Feature and Guide Pages

Feature pages should not become marketing brochures. Each page must include:

- what is implemented now;
- what depends on configuration, OCR, model, or corpus quality;
- one specific CTA;
- a current screenshot, diagram, or code/command proof;
- claim status: `implemented`, `custom scope`, `planned`, or
  `verify-before-publish`.

Guide pages should prioritize task completion: prerequisites, commands, expected
result, recovery actions, and links to health/meta endpoints.

## Visual System

Design tone:

- quiet, technical, high-trust;
- precise Russian typography;
- strong product screenshots and diagrams;
- restrained but memorable motion;
- no oversized decorative cards, no generic AI background, no fake social proof.

Layout rules:

- Russian copy is the sizing baseline.
- Header and CTA labels must fit at 390px mobile width.
- Buttons use concrete actions; avoid vague labels like `Узнать больше`.
- Repeated cards use radius <= 8px and stable dimensions.
- Product proof should appear before abstract benefits.
- Hebrew pages require RTL layout QA with LTR tokens.
- Chinese and Dutch require line-wrap checks for compact cards.

Color and typography:

- Use the existing LocalRAG brand assets as the anchor.
- Avoid one-note palettes dominated by only purple/blue/cream.
- Keep code/model tokens visually distinct but not louder than page headings.
- Use sentence case for Russian headings.
- Do not scale font sizes with viewport width.

## Motion and 3D

Allowed effects:

- 3D retrieval graph for folder -> chunks -> embeddings -> FAISS -> answer ->
  sources.
- Local-folder boundary animation that clarifies the default local scenario.
- Source-proof overlays that connect answer text to retrieved fragments.
- Scroll-linked section transitions when they explain workflow order.
- Small UI microinteractions for language, model, role, and source panels.

Constraints:

- Respect `prefers-reduced-motion`.
- Provide static fallback for all canvas/video effects.
- Do not block main content or CTA targets.
- Do not imply cloud, compliance, air-gap, or enterprise guarantees.
- Verify 3D/canvas is nonblank in browser QA on desktop and mobile.
- Keep motion functional: 150-250ms for UI transitions, longer only for
  explanatory sequences.

## Generated Illustrations

Generated images should support concepts screenshots cannot explain:

- local folder boundary;
- retrieval graph;
- source verification;
- model/retrieval controls;
- corporate integration as custom scope;
- quality/eval gate.

They must not replace real product proof. Every generated visual needs:

- prompt and purpose;
- target page/block;
- alt text;
- claim constraints;
- desktop/mobile crop guidance;
- reduced-motion/static fallback when tied to animation.

## Technical Architecture for Website Implementation

Implementation should reuse the existing web frontend where practical and keep
the first release small enough to verify:

- structured page data for copy, metadata, locale variants, CTAs, and claim
  statuses;
- reusable section components for hero, proof strip, workflow, features,
  screenshots, FAQ, guide steps, and final CTA;
- locale-aware routing and metadata;
- CSS with stable responsive constraints for cards, buttons, nav, media, and
  hero visuals;
- lazy-loaded media and 3D modules;
- no large video binaries committed without an approved storage decision.

If Three.js or a similar 3D layer is used, isolate it as progressive
enhancement. The page must remain usable and visually complete without WebGL.

## SEO and Localization

SEO implementation must follow
`artifacts/seo/design/2026-06-06-seo-structure-metadata-plan.md`:

- Russian metadata is the source baseline.
- Localized EN/NL/ZH/HE metadata must preserve meaning and claim strength.
- Use canonical and hreflang rules once routes exist.
- Do not add ratings, reviews, offers, or organization claims without evidence.
- Use `FAQPage`, `HowTo`, `TechArticle`, and `SoftwareApplication` schema only
  where visible content supports the schema.

Localization rules:

- Translate by meaning, not line by line.
- Keep technical identifiers stable: `LocalRAG`, `Ollama`, `FAISS`, `RAG`,
  `Docker Compose`, model tags, routes, file paths.
- Hebrew requires RTL QA and direction-safe LTR tokens.
- Native review is required before publishing localized captions, CTAs, and
  headline variants.

## Observability and QA Hooks

Public website and app UI should expose enough evidence for verification without
leaking private content:

- `/api/health`, `/api/meta`, and `/metrics` remain machine-readable release and observability signals.
- `X-Request-ID` is returned on every HTTP response and carried into structured runtime logs and Ollama calls.
- Browser QA should capture Russian homepage desktop/tablet/mobile.
- QA must check language switcher, CTAs, responsive wrapping, source proof,
  screenshot captions, generated media, reduced-motion mode, and Hebrew RTL.
- Alert and report text must never include raw questions, answers, source
  passages, or local paths outside safe dev contexts.

## Acceptance Criteria

Design can move to setup/planning when:

- Russian-first page copy and metadata are merged.
- Solution design, SEO plan, image direction, motion/video direction, and
  observability contract exist as versioned artifacts.
- Every page/block has purpose, CTA, proof, limitation handling, visual
  direction, responsive expectations, and QA notes.
- Generated visuals and 3D/motion have implementation constraints and fallbacks.
- Unsupported claims are marked and cannot silently enter development.
- Design gate #8 records a GO/NO-GO decision with links to the merged artifacts.
