# LocalRAG Russian-First Motion and Video Addendum

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | Video Generation |
| Stage | Design |
| Issue | #50 - Russian-first immersive video and motion addendum |
| Artifact version | 1.0 |
| Date | 2026-06-06 |
| Status | Ready for review; design gate #8 remains blocked until this corrective MR is reviewable or merged |
| Baseline | MR !6 / `origin/codex/issue-39` storyboard artifact |

## Purpose

This addendum corrects the MR !6 video direction so the canonical video,
hero-motion, scroll-motion, captions, transcript, and approval criteria are
Russian-first. Russian is the source language for public meaning, on-screen
copy, voiceover, CTA hierarchy, proof framing, and localization into English,
Dutch, Chinese, and Hebrew.

The addendum keeps MR !6 as useful product-walkthrough evidence, but it is not
a production approval. The production track must not move through design gate #8
until this addendum is reviewed with the Russian-first copy requirements.

## Required Inputs Applied

Repository inputs used:

- `artifacts/video-generation/design/2026-06-06-video-concept-storyboard.md`
  from MR !6 / `origin/codex/issue-39`
- `docs/website-content/ru-first-multilingual-copy-analysis.md`
- `docs/website-content/content-brief-page-map.md`
- `docs/discovery-and-analysis.md`
- `artifacts/seo/analysis/2026-06-06-seo-intent-keyword-brief.md`

Required language standards applied:

- `ru-text`: Russian typography, direct UX wording, natural syntax, readable
  buttons, anti-bureaucratic phrasing, and avoidance of literal English word
  order.
- `ru-web-copy-editor`: proof-led website copy, clear CTA intent,
  anti-calque rewriting, objection handling, and unsupported-claim controls.

The local source of these standards for this issue is
`docs/website-content/ru-first-multilingual-copy-analysis.md`. If standalone
`ru-text` or `ru-web-copy-editor` skill files are introduced later, final
voiceover and captions must be rechecked against them before lock.

## Design Correction

MR !6 described a useful English-first 75 second product walkthrough. This
addendum changes the canonical direction:

- Russian is the production source for the main 75 second cut.
- English, Dutch, Chinese, and Hebrew are meaning-localized adaptations, not
  line-by-line translations of English.
- The first viewport and video opening must prove the local-folder workflow
  before showing abstract retrieval motion.
- 3D and scroll motion may surprise visitors, but every animated element must
  explain a product boundary, product state, or proof point.
- Claims must stay tied to current product evidence: local folder indexing,
  FAISS, Ollama model control, answer-language controls, source context, tests,
  smoke checks, and eval gates.

## Russian-First Canonical Storyboard

Canonical cut: `75 seconds`, Russian voiceover, Russian on-screen copy, Russian
default captions, product UI and proof overlays as the primary visual evidence.

| Shot | Timecode | Visual and motion | Russian on-screen copy | Russian voiceover / transcript direction | Proof and constraints |
| --- | --- | --- | --- | --- | --- |
| 1 | 00:00-00:06 | Realistic local folder beside the LocalRAG UI. A translucent local boundary appears around the folder and app window, then settles behind the hero. | `Локальный ИИ-поиск по документам` / `Файлы остаются локально в базовом сценарии` | `LocalRAG начинается с папки на вашем компьютере, а не с обязательной загрузки документов во внешний сервис.` | Use neutral sample names only. Do not imply audited isolation for every deployment. |
| 2 | 00:06-00:13 | Cursor selects a document folder, then starts reindexing. Status changes are highlighted with a compact progress overlay. | `Выберите папку` / `Переиндексируйте файлы` | `Подключите PDF, сканы, заметки, таблицы и код, затем обновите локальный индекс.` | Show only file types supported by repository evidence. OCR quality must be framed as variable. |
| 3 | 00:13-00:21 | 3D retrieval graph grows inside the local boundary: documents become fragments, embeddings flow into FAISS, then the graph collapses back to UI. | `Документы -> фрагменты -> embeddings -> FAISS` | `Файлы делятся на фрагменты. Для них строятся мультиязычные эмбеддинги, а индекс сохраняется в FAISS для поиска.` | Keep technical terms where useful. Labels must remain readable on mobile crops. |
| 4 | 00:21-00:29 | User asks a Russian question in the chat UI. The answer starts appearing while retrieval nodes pulse behind the panel. | `Задайте вопрос` | `Вопрос проходит через локальный RAG-сценарий на Ollama, а не через обычный чат без источников.` | Use a safe sample question. Avoid legal, medical, financial, customer, or credential examples. |
| 5 | 00:29-00:39 | Source context panel opens. File path, page, line range, and retrieved passage are framed by source-proof overlays. | `Проверьте ответ по источникам` | `Ответ можно проверить по найденным фрагментам: путь к файлу, страница или строки показываются там, где эти данные доступны.` | Do not promise page and line references for every file. This shot is mandatory for every cut. |
| 6 | 00:39-00:47 | Settings screen shows separate interface language and answer language controls. Locale badges appear: `RU`, `EN`, `NL`, `ZH`, `HE`. | `Язык интерфейса и ответа настраиваются отдельно` | `Интерфейс доступен на пяти языках, а язык ответа можно выбрать отдельно от языка UI.` | Native QA is required before publishing localized variants. |
| 7 | 00:47-00:54 | Role selector cycles through Analyst, Engineer, Archivist, then shows editable custom role settings. | `Выберите роль ответа` | `Роли помогают менять стиль ответа и промпт, не скрывая модель, язык и найденные источники.` | Use role names visible in the current localized UI or approved captures. |
| 8 | 00:54-01:03 | Ollama model manager and embedding settings. Model tags and prepare/manage controls are highlighted without overfilling the frame. | `Модель и retrieval — на виду` | `Модель Ollama, embeddings и параметры retrieval выбираются в интерфейсе, поэтому настройки не превращаются в чёрный ящик.` | Model defaults must be refreshed immediately before capture. |
| 9 | 01:03-01:10 | CI/terminal-style validation panel overlays the product screen: `pytest`, `release_check.py`, `model_eval.py`, `assert_eval_gate.py`. | `Проверки до релиза` | `Качество retrieval проверяется тестами, smoke-check и eval gate, а не только красивым демо.` | Show command names, not long terminal output. Avoid implying universal answer accuracy. |
| 10 | 01:10-01:15 | Product UI, source panel, logo, and CTA hierarchy. Motion slows; graph nodes fade into source cards, not abstract particles. | `Запустить локально` / `Посмотреть интерфейс` / `Обсудить внедрение` | `LocalRAG — локальный RAG для вопросов по документам: с видимыми источниками, настройками модели и понятным способом проверки.` | End on product evidence and stable CTA targets. |

## Russian CTA Hierarchy

| Priority | CTA | Meaning | Use | Production rule |
| --- | --- | --- | --- | --- |
| Primary | `Запустить локально` | Run locally | Hero, final frame, setup links | Must point to install, GitHub, or quick-start instructions. |
| Secondary | `Посмотреть интерфейс` | See the product UI | Hero and video-adjacent anchors | Must scroll to current screenshots or product demo, not a decorative section. |
| Proof CTA | `Проверить источники` | Inspect sources | Source-provenance shot, feature anchors | Use only where source context is visible. |
| Technical CTA | `Запустить eval` | Run the eval check | Quality/evaluation pages and technical cuts | Use for developer audience only. |
| Team CTA | `Обсудить внедрение` | Discuss rollout | Corporate or integration sections | Use only with custom-scope language, not as proof of shipped enterprise features. |

Avoid vague Russian CTAs such as `Начать путь`, `Раскрыть знания`, `Узнать
больше`, or literal calques like `Запусти это локально` when a concrete action
exists.

## Draft Russian Voiceover Transcript

Use this as the source transcript for timing and caption work. Before recording,
the producer must run one final `ru-text` and `ru-web-copy-editor` pass for
naturalness, CTA clarity, and unsupported claims.

> LocalRAG начинается с папки на вашем компьютере, а не с обязательной загрузки
> документов во внешний сервис.
>
> Подключите PDF, сканы, заметки, таблицы и код, затем обновите локальный
> индекс.
>
> Файлы делятся на фрагменты. Для них строятся мультиязычные эмбеддинги, а
> индекс сохраняется в FAISS для поиска.
>
> Вопрос проходит через локальный RAG-сценарий на Ollama, а не через обычный чат
> без источников.
>
> Ответ можно проверить по найденным фрагментам: путь к файлу, страница или
> строки показываются там, где эти данные доступны.
>
> Интерфейс доступен на пяти языках, а язык ответа можно выбрать отдельно от
> языка UI.
>
> Роли помогают менять стиль ответа и промпт, не скрывая модель, язык и
> найденные источники.
>
> Модель Ollama, embeddings и параметры retrieval выбираются в интерфейсе,
> поэтому настройки не превращаются в чёрный ящик.
>
> Качество retrieval проверяется тестами, smoke-check и eval gate, а не только
> красивым демо.
>
> LocalRAG — локальный RAG для вопросов по документам: с видимыми источниками,
> настройками модели и понятным способом проверки.

## Captions, Subtitles, and Transcript Requirements

Caption files must be created from the Russian timing pass first.

Recommended public asset names:

- `/media/video/localrag-product-walkthrough-v2-75s.mp4`
- `/media/video/localrag-product-walkthrough-v2-75s.webm`
- `/media/video/localrag-product-walkthrough-v2-75s-poster.webp`
- `/media/video/localrag-product-walkthrough-v2-75s.ru.vtt`
- `/media/video/localrag-product-walkthrough-v2-75s.en.vtt`
- `/media/video/localrag-product-walkthrough-v2-75s.nl.vtt`
- `/media/video/localrag-product-walkthrough-v2-75s.zh.vtt`
- `/media/video/localrag-product-walkthrough-v2-75s.he.vtt`
- `/media/video/localrag-product-walkthrough-v2-75s-transcript.ru.md`

Rules:

- Russian is the default caption track for the canonical Russian voiceover.
- EN, NL, ZH, and HE tracks are subtitles unless separate localized voiceover is
  recorded.
- Each caption cue must fit readable two-line display on mobile. Avoid carrying
  desktop-length Russian sentences into a single cue.
- Captions must preserve claim limits. Do not shorten `в базовом сценарии` out
  of privacy statements.
- Transcript pages must include the same limitation wording as the video.
- On-screen text embedded in video must not be the only source of meaning; key
  labels must also exist in captions, transcript, or adjacent HTML.

## Multilingual Adaptation Plan

Russian is the source of meaning. Localized versions adapt intent, CTA verbs,
caption rhythm, and objection handling for each audience. Technical identifiers
stay stable unless a local equivalent is standard: `LocalRAG`, `RAG`, `Ollama`,
`FAISS`, `Docker Compose`, `pytest`, `qwen3.5:9b`,
`intfloat/multilingual-e5-large`, `top-k`, `LLM`, `embedding`, `retrieval`,
file extensions, environment variables, routes, and URLs.

What is translated by meaning:

- Voiceover, transcript, captions, subtitles, on-screen copy, CTA labels,
  source-proof callouts, poster text, alt text, page metadata, approval notes,
  FAQ snippets, and unsupported-claim notes.
- Privacy and reliability limits must keep the same strength in every language.
- CTAs must describe the real next action in the target language.

| Language | Role | Copy and caption direction | Native QA requirement |
| --- | --- | --- | --- |
| RU | Canonical source | Natural Russian with direct verbs: `Запустить локально`, `Проверить источники`, `Выберите папку`. Use `локальный ИИ-поиск` for broad visitors and `локальный RAG` for technical context. | Russian copy review against `ru-text`, `ru-web-copy-editor`, and `ru-first-multilingual-copy-analysis.md`. |
| EN | International technical adaptation | Adapt meaning from Russian, not MR !6 wording. Keep practical product tone: local folder, source evidence, Ollama, FAISS, eval gates. | Native or senior English technical copy review for SaaS-hype removal and privacy-claim parity. |
| NL | Practical EU adaptation | Avoid literal English compounds. Use privacy wording cautiously without implying GDPR compliance. Keep CTAs concrete and test long words in captions. | Native Dutch review for CTA idiom, line length, and privacy limitation wording. |
| ZH | Concise technical adaptation | Keep captions shorter than Russian where possible. Explain local runtime and model dependency plainly. Avoid wording that implies guaranteed security or perfect multilingual quality. | Native Chinese review for technical clarity, caption pacing, and compact UI overlays. |
| HE | RTL adaptation | Hebrew captions and on-screen variants must render RTL while keeping `LocalRAG`, `Ollama`, model tags, URLs, and file paths LTR. | Native Hebrew review plus explicit RTL browser QA for captions, overlays, CTA order, punctuation, and mixed LTR tokens. |

Hebrew RTL constraints:

- Set `dir="rtl"` for Hebrew transcript and subtitle display surfaces.
- Wrap LTR tokens such as `LocalRAG`, `qwen3.5:9b`, `C:\Temp\PDF`, and URLs in
  direction-safe spans or Unicode isolation where the frontend supports it.
- Do not mirror product screenshots unless the actual Hebrew UI is mirrored.
- Check right-aligned captions for punctuation drift around Latin model names.
- Verify source paths remain readable left-to-right inside RTL layouts.

## Hero, Video, and Scroll Motion Direction

Motion should make the visitor feel the product workflow before they read a
long explanation. It must still be product-grounded: folder, index, question,
answer, source proof, model settings, and eval checks.

### First-Viewport Hero

- The first viewport should show `LocalRAG`, the Russian value proposition, a
  real or faithfully captured product surface, and the primary CTA
  `Запустить локально`.
- The hero may use a muted 6 second poster-to-motion loop, but text and CTA
  targets must remain stable.
- The loop should start with a local folder boundary and end with a source card,
  not an abstract glowing AI scene.
- Keep a hint of the next section visible on desktop and mobile so the page does
  not feel like a closed splash screen.

### 3D Retrieval Graph

Build the 3D graph as an explanatory layer, not decorative background.

Required nodes:

- `Папка`
- `Файлы`
- `Фрагменты`
- `Embeddings`
- `FAISS`
- `Ollama`
- `Ответ`
- `Источники`

Required behavior:

- Nodes must stay inside a visible local-folder boundary until the answer/source
  proof appears.
- Edges should animate in the workflow order: folder -> files -> fragments ->
  embeddings -> FAISS -> retrieved sources -> answer.
- Source nodes must reconnect to the visible answer card to reinforce
  verification.
- The graph should fade or flatten into UI overlays before the viewer needs to
  read source text.

Do not show cloud nodes, external API logos, compliance shields, lock badges, or
security seals unless a separate reviewed artifact approves them.

### Local-Folder Boundary

The local boundary is the main privacy visual. It should be a restrained
container around the folder, index, and app UI:

- Label: `Локальная папка` or `Базовый локальный сценарий`.
- Use it to clarify the default workflow, not to claim all deployments are
  air-gapped.
- If the website explains corporate integrations later, animate that as a
  separate scoped layer with `обсуждается по требованиям`, not in the canonical
  product proof loop.

### Source-Proof Overlays

Source proof is the trust center of the video and must survive all formats.

Overlay fields:

- `Файл`
- `Страница`, when available
- `Строки`, when available
- `Фрагмент`
- `Индекс обновлён`, only when the UI state confirms it

Rules:

- Never fabricate confidence scores, citations, ratings, or review counts.
- Use visible sample content only; no private, customer, medical, legal,
  financial, or credential data.
- Keep path examples generic, such as `C:\Temp\PDF\example.pdf` or
  `/docs/example.md`.
- If metadata is missing, say `метаданные зависят от формата`, not `нет
  источника`.

### Scroll-Triggered Transitions

The landing page may use scroll-triggered transitions to connect sections:

1. Hero: folder boundary appears.
2. Workflow: folder cards become chunks and index nodes.
3. Ask: question input pins briefly while answer text appears.
4. Proof: answer card splits to reveal source fragments.
5. Controls: source card slides aside to reveal language, role, model, and
   retrieval settings.
6. Quality: graph lines become validation checks.
7. CTA: product screen returns with `Запустить локально`.

Implementation rules:

- Use scroll progress to scrub explanatory visuals, not to block reading.
- Do not pin sections long enough to trap keyboard or touch users.
- Keep headings, CTAs, and captions in HTML, not only in canvas/video pixels.
- Use `IntersectionObserver` or a small motion runtime for basic transitions.
  If Three.js is used, lazy-load it after the main hero copy is visible.

### Reduced-Motion Fallback

When `prefers-reduced-motion: reduce` is active:

- Replace autoplay motion with the poster image and a static three-step
  workflow: `Папка -> Вопрос -> Источники`.
- Keep video controls available; do not autoplay animated loops.
- Disable parallax, scroll pinning, camera fly-through, particle motion, and
  typewriter effects.
- Provide the transcript link next to the video.
- Preserve all CTAs in the same positions.

### Performance Limits

Target limits for downstream frontend work:

- Hero must render meaningful text and CTA before motion assets load.
- Poster image: WebP or AVIF, `1920x1080` master, responsive derivatives.
- Primary web video: MP4 H.264 and WebM, `1920x1080`, under `25 MB` when
  possible.
- 6 second hero loop: under `3 MB` per format when possible.
- 3D scene: cap device pixel ratio at `1.5`, pause when hidden, and avoid
  continuous animation after the sequence settles.
- Do not load 3D/video assets on small viewports until the hero text, CTA, and
  poster are available.
- Maintain `30fps` target on desktop and a stable fallback on mobile; do not
  let animation cause layout shift or text overlap.

## Differences From MR !6

### Keep

- Product-walkthrough structure: folder, reindex, retrieval flow, question,
  answer, sources, language controls, roles, model manager, quality checks, CTA.
- 75 second canonical cut plus 30 second, 15 second, and 6 second derivatives.
- Self-hosted video assets as the canonical embed.
- Captions, transcript, poster, and `VideoObject` structured data after final
  URLs are known.
- Approval areas for product accuracy, technical accuracy, privacy/claims,
  accessibility, and website/SEO fit.

### Change

- Russian becomes the canonical source language for storyboard, voiceover,
  captions, transcript, CTA hierarchy, and poster text.
- EN/NL/ZH/HE become meaning-localized adaptations with native QA.
- The visual language adds a product-grounded 3D retrieval graph, local-folder
  boundary, source-proof overlays, and scroll-triggered transitions.
- Unsupported claims are listed before production instead of being handled as a
  late review concern.
- Hebrew RTL QA is explicit and required.
- Reduced-motion and performance budgets are production acceptance criteria, not
  optional implementation polish.

### Must Not Go Into Production Yet

- The English-first MR !6 storyboard as the final source script.
- Generic abstract AI backgrounds, dark technology montages, or decorative
  particles that replace product proof.
- Claims such as `5.0 / 5.0`, `23 user reviews`, `enterprise-ready`,
  `air-gapped`, `certified compliance`, or `perfect multilingual answers`
  without dated evidence and approval.
- Planned corporate connectors presented as shipped features.
- A canonical third-party video iframe replacing the self-hosted website embed.
- Screenshots, model names, version numbers, or default settings that are not
  refreshed immediately before final capture.
- Real private, customer, sensitive, medical, legal, financial, or credential
  data in captures.

## Unsupported Claims and Approval Constraints

These claims must be removed, rewritten, or explicitly verified before public
release:

| Claim pattern | Status | Required handling |
| --- | --- | --- |
| `5.0 / 5.0` rating or `23 user reviews` | Unsupported social proof | Provide dated source and permission, or remove. |
| `without sending sensitive files to the cloud` | Too absolute without deployment context | Use `в базовом локальном сценарии` and document runtime assumptions. |
| Air-gapped, certified, HIPAA/GDPR-compliant, or guaranteed isolation | Unsupported compliance/security claim | Exclude unless separately reviewed and documented. |
| Universal OCR/scanned PDF success | Overpromises parsing quality | Say OCR and parsing quality depend on source documents and tooling. |
| Sources for every answer with page and line precision | Overstates metadata availability | Say source metadata appears where available. |
| Perfect multilingual answer quality | Overstates model behavior | Say UI languages and answer-language controls exist; model quality varies. |
| Corporate connectors, permissions, monitoring, governance | Some items are custom scope or planned | Split shipped product from custom implementation scope. |
| Current model defaults and version numbers | Can drift | Refresh from the current build before capture and note capture date. |
| Generated visuals as product proof | Can mislead | Label them as explanatory visuals and pair them with real UI evidence. |

Production approval constraints:

- Product owner approval: claims match current LocalRAG capabilities.
- Engineering approval: UI captures, defaults, file types, quality checks, and
  runtime boundaries are current.
- Russian copy approval: `ru-text`, `ru-web-copy-editor`, and
  `ru-first-multilingual-copy-analysis.md` standards are satisfied.
- Localization approval: EN/NL/ZH/HE captions and CTAs have native or specialist
  review; Hebrew has explicit RTL QA.
- Privacy/claims approval: no unsupported compliance, security, social proof,
  pricing, or corporate-readiness claims.
- Accessibility approval: captions, transcript, contrast, keyboard access,
  reduced-motion fallback, and non-autoplay audio rules are verified.
- Performance approval: video, poster, 3D, and scroll-motion budgets are met on
  desktop and mobile.

## Asset Acceptance Criteria

### Image Generation and Visual Assets

- Generated assets must support one of these specific explanations:
  local-folder boundary, retrieval graph, source verification, model control,
  or quality gates.
- Do not generate generic AI imagery as product evidence.
- Russian labels must be readable at mobile crop sizes.
- Visual prompts must include sample-only file names and must exclude private or
  sensitive document content.
- Poster image must show a real or faithful LocalRAG product state with source
  proof, not only the logo or abstract graph.
- Every visual asset needs alt text in Russian first, then EN/NL/ZH/HE meaning
  adaptations.

### Frontend Implementation

- Use native HTML video with MP4/WebM sources, poster, controls, caption tracks,
  and transcript link.
- Default caption track is Russian for the canonical Russian voiceover.
- Lazy-load heavy video and 3D assets after primary text and CTA render.
- Keep hero text, CTA labels, and source-proof text in HTML when feasible.
- Ensure motion cannot move CTA hit targets during interaction.
- Pause hero video/3D when off-screen or when the tab is hidden.
- Add `VideoObject` structured data only after final URLs, thumbnail, duration,
  transcript, and upload date are known.

### Responsive QA

- Test Russian as the sizing baseline for hero, CTAs, overlays, captions,
  navigation, and source-proof cards.
- Test breakpoints at mobile, tablet, laptop, and wide desktop widths.
- Verify the first viewport shows product identity, local document value,
  source-proof value, and `Запустить локально`.
- Ensure a hint of the next section remains visible in the hero.
- Validate Dutch long labels, Chinese line height, and Hebrew RTL layout before
  localization approval.
- Ensure text never overlaps with video controls, source overlays, or CTA
  buttons.

### Browser QA

- Browser QA must cover Chromium, Firefox, and WebKit/Safari-equivalent engines
  when available in the downstream environment.
- Test Russian homepage/video behavior at desktop and mobile widths.
- Test caption track switching for RU/EN/NL/ZH/HE.
- Test Hebrew RTL transcript, captions, CTAs, mixed LTR tokens, URLs, and source
  paths.
- Verify reduced-motion behavior with browser emulation.
- Verify poster fallback when video fails or autoplay is blocked.
- Verify 3D/canvas is nonblank, correctly framed, and does not hide product UI
  or text.

### Accessibility

- Captions and transcript are required for every public cut.
- Audio must not autoplay with sound.
- Text contrast must remain readable over video and 3D scenes.
- Keyboard users must be able to reach video controls, CTA buttons, language
  selector, and transcript link.
- Avoid flashing, rapid strobing, or motion that interferes with reading.
- Do not rely on color alone to communicate source status or quality checks.
- Reduced-motion users must receive equivalent product meaning through static
  poster, transcript, and workflow summary.

## Downstream Deliverables

Recommended versioned locations:

- `artifacts/video-generation/scripts/` for locked Russian script, localized
  transcripts, captions, and timing notes.
- `artifacts/video-generation/production/` for capture checklist, render
  manifest, compression notes, QA screenshots, and approval records.
- Public media storage for large MP4/WebM files; do not commit large video
  binaries to the application repository unless explicitly approved.

Minimum production package:

- Russian 75 second master transcript.
- RU/EN/NL/ZH/HE WebVTT files.
- Poster image with Russian source text and localized alt text.
- 75 second MP4/WebM.
- 30 second, 15 second, and 6 second derivatives derived from the same shot
  order.
- Capture manifest with app version, date, branch, model defaults, sample data
  source, and reviewer approvals.

## Definition of Done Coverage

- [x] A Russian-first motion/video addendum exists as a versioned repository
  artifact.
- [x] The addendum explicitly references `ru-text`, `ru-web-copy-editor`, and
  `ru-first-multilingual-copy-analysis.md`.
- [x] Russian canonical on-screen copy and voiceover direction exist.
- [x] EN/RU/NL/ZH/HE caption and localization plan exists, including Hebrew RTL
  QA.
- [x] 3D, motion, and scroll effects are specific, implementable, responsive,
  accessible, and tied to product proof.
- [x] Differences from MR !6 are listed.
- [x] Unsupported claims and production approval constraints are listed.
- [x] Asset and implementation acceptance criteria cover image generation,
  frontend development, responsive QA, browser QA, and accessibility.
