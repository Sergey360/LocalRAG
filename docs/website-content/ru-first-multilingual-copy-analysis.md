# Russian-First Multilingual Copy Analysis

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | Website content |
| Stage | Analysis |
| Issue | #49 - Russian-first multilingual copywriting analysis |
| Artifact version | 1.0 |
| Date | 2026-06-06 |
| Status | Ready for design and content implementation |

## Purpose

This artifact corrects the current English-first website/content direction and
defines a Russian-first multilingual copy strategy for LocalRAG. Russian should
be treated as the source language for public positioning, UX wording, objections,
CTA hierarchy, proof framing, and downstream localization into English, Dutch,
Chinese, and Hebrew.

The goal is not to translate the existing English landing page sentence by
sentence. The goal is to express the product in natural Russian first, then adapt
the same meaning to each target language with local idiom, local search intent,
language-specific proof, and interface constraints.

## Required Skill Standards Applied

This analysis explicitly applies the project standards named in issue #49:

- `ru-text`: Russian typography, UX wording, clarity, and anti-bureaucratic
  style. Russian copy must use natural syntax, correct punctuation, readable
  button and form labels, direct verbs, and concrete nouns. It must avoid heavy
  officialese, inflated abstractions, literal English word order, and unclear
  borrowed terms when a precise Russian phrase works better.
- `ru-web-copy-editor`: website positioning, CTA clarity, proof, objections,
  anti-calque rewriting, and unsupported-claim handling. Every marketing claim
  must have a visible proof point, a limitation note, or a `verify before
  publish` flag. CTAs must say what happens next, not just sound attractive.

These standards are mandatory acceptance inputs for future Russian website copy,
localized page briefs, UI labels, SEO metadata, generated illustrations, motion
briefs, responsive layouts, and browser QA.

## Source Inputs

Repository sources used:

- `Readme.md`, `Readme.ru.md`, `Readme.nl.md`, `Readme.zh.md`,
  `Readme.he.md`
- `app/locales/en.json`, `app/locales/ru.json`, `app/locales/nl.json`,
  `app/locales/zh.json`, `app/locales/he.json`
- `web/templates/main_content.html` and current web/static UI assets
- Prior analysis artifacts from `origin/codex/issue-4`,
  `origin/codex/issue-28`, and `origin/codex/issue-32`:
  - `docs/discovery-and-analysis.md`
  - `docs/website-content/content-brief-page-map.md`
  - `artifacts/seo/analysis/2026-06-06-seo-intent-keyword-brief.md`
- Current public messaging reviewed on 2026-06-06:
  - `https://localrag.dev/`
  - `https://dev.localrag.dev/`

## Current Copy Diagnosis

The product strategy is strong, but the current public site is English-first.
It already advertises EN/RU/NL/ZH/HE, local document search, source-backed
answers, OCR-ready PDFs, visible retrieval controls, free/community use, and a
corporate path. However, the live public homepage and the prior website brief
frame the product primarily in English and then imply multilingual support as a
feature.

For LocalRAG, Russian should not be a translated locale at the end of the
content pipeline. It should be the first content design language because the
repository already has a substantial Russian README, Russian app locale, Russian
eval notes, Russian user-facing examples, and issue context that asks for
Russian copy skills.

The main correction:

- Start page strategy from a Russian message: private local document Q&A with
  verifiable sources and visible model/retrieval controls.
- Keep technical terms only where they help the audience: `RAG`, `Ollama`,
  `FAISS`, `top-k`, `LLM`, `embedding`, `retrieval`, `quality gate`.
- Replace literal English web phrases with Russian product language.
- Treat multilingual pages as meaning-localized adaptations, not direct
  translations.
- Flag every unsupported public claim before design/development repeats it.

## Russian-First Positioning

### Audience

Primary Russian-language audience:

- Developers, researchers, consultants, analysts, and technical power users who
  work with private local folders and do not want to upload files to hosted AI
  services by default.
- Russian-speaking users who need answers across mixed Russian/English
  documents and want to inspect the source behind each answer.
- Solo builders and internal tool owners evaluating local RAG before a team
  rollout.

Secondary audience:

- Teams evaluating a private or on-premise document assistant.
- Open-source reviewers who want to understand architecture, release discipline,
  supported formats, and runtime defaults quickly.
- Multilingual users who need separate interface language and answer language.

The Russian page should assume the reader is practical and skeptical. It should
answer: what runs locally, what is actually implemented, what depends on the
selected model/OCR/source quality, and what the next step costs in effort.

### Offer

Recommended Russian source positioning:

> LocalRAG помогает задавать вопросы по локальным документам и проверять ответы
> по найденным фрагментам источников. Файлы остаются на вашем компьютере в
> базовом сценарии, а модели, язык ответа и параметры поиска остаются видимыми в
> интерфейсе.

Short Russian offer for hero/metadata:

> Локальный ИИ-поиск по приватным документам с проверяемыми ответами.

Longer Russian offer:

> Подключите папку с PDF, сканами, заметками, таблицами и кодом, задавайте
> вопросы через локальный RAG на Ollama и открывайте фрагменты источников,
> которые легли в основу ответа.

Do not lead with "мультиязычный RAG" for general audiences. Use it as a proof
point after the privacy and verification promise. For technical pages, `RAG`
can be in the headline.

### Proof

Use proof that exists in the repository or current product surface:

| Claim | Current proof | Russian copy treatment |
| --- | --- | --- |
| Local-first default | README, Docker Compose runtime, Ollama default, local FAISS index | "В базовом сценарии файлы обрабатываются локально" |
| Source provenance | README and app context panel expose source/path/page/lines where available | "Ответ можно проверить по найденным фрагментам" |
| Mixed file support | README and locale copy list PDF, DOCX, TXT, MD, HTML, JSON, CSV, YAML, code | List formats as practical proof, not as a heroic claim |
| Multilingual UI | Locale JSON files for EN/RU/NL/ZH/HE | "Интерфейс доступен на пяти языках" with native QA requirement |
| Separate answer language | App settings and locale labels | "Язык интерфейса и язык ответа настраиваются отдельно" |
| Model control | Ollama model manager in app locale/UI | "Модели Ollama выбираются и управляются в интерфейсе" |
| Retrieval quality discipline | Eval scripts and quality gate | "Качество retrieval проверяется eval-набором" |

### CTA hierarchy

Russian CTAs must describe the next action:

| Position | Russian CTA | English meaning | Notes |
| --- | --- | --- | --- |
| Hero primary | `Запустить локально` | Run locally | Link to GitHub/setup, not a vague product tour |
| Hero secondary | `Посмотреть интерфейс` | See product UI | Anchor to screenshots/product section |
| Team/corporate secondary | `Обсудить внедрение` | Discuss rollout | Use only where corporate scope is shown |
| Feature sections | `Проверить источники`, `Выбрать модель`, `Настроить язык ответа` | Inspect sources, choose model, set answer language | Use for demos or anchors |
| Setup page | `Склонировать репозиторий`, `Открыть UI`, `Переиндексировать папку` | Clone repo, open UI, reindex folder | Action-specific CTAs |
| Quality page | `Запустить eval`, `Проверить release gate` | Run eval, verify release gate | Technical audience only |
| Footer | `GitHub`, `Документация API`, `Release notes`, `Связаться по внедрению` | Navigation | Keep concise |

Avoid Russian CTAs such as `Начать путь`, `Раскрыть знания`, `Узнать больше`
when a concrete action is available.

### Objections

| Objection | Russian answer direction |
| --- | --- |
| "Мои документы уходят в облако?" | Say the default product path uses local files, local index, and Ollama. Do not claim every deployment is isolated unless the deployment is audited. |
| "Насколько можно доверять ответу?" | Say each answer should be checked against retrieved source fragments. Quality depends on source quality, OCR, index freshness, retrieval settings, and selected model. |
| "Это замена DMS/ECM/поисковой системе?" | No. LocalRAG is document Q&A over a folder, not a full document management system with permissions, retention, legal hold, or team collaboration. |
| "Поддерживает ли русский и смешанные языки?" | Yes at the UI and answer-language level; model quality still depends on the selected LLM and embeddings. |
| "Работает ли со сканами?" | Use careful wording: OCR-heavy PDFs and scans are a target workflow, but OCR quality and parsing quality vary. |
| "Можно ли использовать в компании?" | There is a corporate/integration direction, but connectors, governance, access control, monitoring, and support terms must be scoped and verified per rollout. |

### Claims that must be verified before publication

These claims appear or are implied in current public/local copy and must not be
reused without evidence:

| Claim | Risk | Required verification |
| --- | --- | --- |
| `5.0 / 5.0` rating and `23 user reviews` | High-risk social proof if no review source exists | Provide review source, date, methodology, and permission, or remove |
| "Free today" / free for pilots | Pricing and license can change | Confirm license, free-use boundaries, commercial use terms, and date |
| Corporate connectors for file shares, object storage, knowledge bases, SQL content | Some may be planned rather than shipped | Split "available now" from "custom scope" and list evidence per connector |
| Private deployment, access control, monitoring, quality checks for production teams | Can imply enterprise readiness | Verify implemented capabilities, support scope, and deployment model |
| "without sending sensitive files to the cloud" | Strong privacy claim depends on configuration | Say "in the default local workflow" and document network/model assumptions |
| OCR-ready PDFs / scans | Can imply universal OCR success | State supported workflow and quality dependency; show tested examples |
| Multilingual support | Could imply perfect translation or answer quality | State UI languages and configurable answer language; require native review |
| "Real screens from current build" | Can drift as UI changes | Tie screenshots to version/date or refresh before launch |

## Home Page Russian Copy Brief

The homepage should be written in Russian first, then localized.

### 1. Header/navigation

Goal: make the product and next action obvious.

Russian guidance:

- Brand: `LocalRAG`
- Navigation: `Зачем`, `Возможности`, `Интерфейс`, `Интеграции`,
  `Стоимость`, `Ссылки`
- Primary header CTA: `Запустить локально`
- Language switcher labels can remain `EN`, `RU`, `NL`, `ZH`, `HE`; full
  language names are useful in accessibility labels.

Notes:

- Avoid `Продукт` if the section is really a feature walkthrough.
- If the public site has no Russian localized route yet, language switchers must
  not imply completed Russian pages.

### 2. Hero

Goal: explain LocalRAG in one screen without hype.

Recommended Russian hero:

> Локальный ИИ-поиск по приватным документам.
>
> Подключите папку с PDF, сканами, заметками, таблицами и кодом. Задавайте
> вопросы через локальный RAG на Ollama и проверяйте ответы по найденным
> фрагментам источников.

Primary CTA: `Запустить локально`

Secondary CTA: `Посмотреть интерфейс`

Proof strip:

- `Файлы остаются локально в базовом сценарии`
- `Ответы с фрагментами источников`
- `Интерфейс: EN/RU/NL/ZH/HE`
- `Ollama, FAISS, multilingual-e5`
- `Настройки модели и retrieval в UI`

Do not use `локальная AI для документов` as the final Russian headline. Use
`локальный ИИ-поиск`, `локальные ответы по документам`, or technical `локальный
RAG` depending on the page.

### 3. Social proof/rating

Goal: use only verified proof.

Current public `5.0 / 5.0` and `23 user reviews` must be removed or marked as
unpublished until there is evidence. Replace with product proof:

- `v0.9.0`
- `pytest/release checks`
- `source provenance`
- `5 UI languages`
- `Docker Compose`
- `Ollama model manager`

### 4. Problem framing

Goal: show the real problem without dramatic exaggeration.

Russian direction:

> Реальные папки редко похожи на демо-набор: в них лежат PDF, сканы, заметки,
> таблицы, код, разные языки и неидеальные имена файлов. Обычный чат не
> показывает, какой фрагмент повлиял на ответ. LocalRAG строится вокруг этой
> проверки.

Avoid:

- `разблокируйте знания`
- `революционный поиск`
- `корпоративный уровень` without proof

### 5. Why LocalRAG

Goal: turn differentiators into evidence.

Section cards:

| Russian title | Body direction |
| --- | --- |
| `Работает с папкой, которую вы уже используете` | No mandatory upload flow in the default local scenario. |
| `Ответ можно проверить` | Open retrieved passages, page/line references where available. |
| `Не боится смешанных документов` | PDFs, scans, text, tables, code, mixed languages; quality still depends on parsing/OCR/model. |
| `Настройки остаются на виду` | Model, embeddings, top-k, answer language, roles, and debug metadata stay in the UI. |

### 6. Product workflow

Goal: show the practical sequence.

Russian section flow:

1. `Выберите папку с документами`
2. `Переиндексируйте файлы`
3. `Задайте вопрос`
4. `Откройте найденные источники`
5. `При необходимости смените модель, язык ответа или роль`

Copy should mention `top-k` only inside advanced controls. For general sections,
use `сколько фрагментов искать`.

### 7. Screens and preview

Goal: prove the UI exists and is not a mockup.

Russian guidance:

- Caption screenshots by workflow, not by decorative description:
  - `Ответ и найденный контекст`
  - `Настройки модели и эмбеддингов`
  - `Выбор папки и переиндексация`
  - `Роли ответа`
- Add version/date metadata near screenshots or in alt text.
- If an interactive preview calls a local backend, explain the boundary in UX
  microcopy without exposing internal variables as the main user-facing text.

### 8. Integrations/corporate

Goal: separate current product from scoped services.

Russian direction:

> Базовый LocalRAG рассчитан на локальную работу с папкой. Корпоративный слой
> проектируется отдельно: коннекторы, права доступа, API, очереди, мониторинг и
> проверки качества зависят от конкретного внедрения.

CTA: `Обсудить внедрение`

Do not present planned connectors as shipped features unless the implementation
is available and documented.

### 9. Pricing/lead capture

Goal: avoid unsupported commercial claims.

Russian structure:

- `Community`: `Запустить локально`, `Открытый исходный код`, `Для личной
  работы, оценки и пилотов` if license permits.
- `Corporate`: `Индивидуальный объем`, `Интеграции и внедрение`, `Обсудить
  требования`.

Lead capture copy:

- Use `Обсудить внедрение`, not `Купить`.
- Ask for only necessary fields: name, work email, organization, use case,
  expected document sources, deployment constraints.
- Add privacy notice for lead data before publishing a form.

### 10. Final CTA/footer

Russian direction:

> Хотите проверить LocalRAG на своих документах? Запустите локально и начните с
> небольшой папки. Если нужен корпоративный контур, обсудим источники данных,
> ограничения и критерии качества.

CTAs:

- `Открыть GitHub`
- `Запустить локально`
- `Обсудить корпоративное внедрение`

## Planned Subpage Copy Brief

| Page | Russian source goal | Required sections | Primary CTA |
| --- | --- | --- | --- |
| `/features/private-document-qa` | Explain private local document Q&A without broad security claims | Problem, local default, source checking, limits, screenshots | `Запустить локально` |
| `/features/ollama-rag` | Speak to technical users searching for Ollama RAG | Ollama model manager, FAISS, embeddings, runtime defaults, setup caveats | `Настроить модель` |
| `/features/pdf-ocr-rag` | Capture PDF/scans intent carefully | PDF/scans workflow, OCR limits, page references, tested examples | `Проверить PDF-папку` |
| `/features/source-citations` | Make verification the trust center | Context panel, path/page/line metadata, stale index risks, examples | `Посмотреть источники` |
| `/features/multilingual-rag` | Explain multilingual UX as product design, not magic translation | UI languages, answer language, multilingual embeddings, mixed documents, native QA | `Настроить язык ответа` |
| `/features/response-roles` | Show roles as workflow control | Analyst/Engineer/Archivist, custom roles, prompts, defaults, risks | `Выбрать роль` |
| `/guide/getting-started` | Reduce time to first answer | Prerequisites, Docker, Ollama, default paths, first reindex, first question | `Склонировать репозиторий` |
| `/guide/models-and-embeddings` | Help choose local models responsibly | Default model, recommended models, resource tradeoffs, license checks | `Проверить модели` |
| `/guide/retrieval-quality` | Prove quality discipline to technical readers | Eval scripts, quality gate, source hit ratio, OCR-heavy cases | `Запустить eval` |
| `/faq/privacy-security` | Handle risk questions plainly | Data flow, local/default assumptions, logs, Docker/Ollama boundary, unsupported compliance claims | `Проверить архитектуру` |
| `/for-teams` | Position corporate scope without overclaiming | Use cases, connectors as scoped work, governance needs, QA plan, rollout steps | `Обсудить внедрение` |
| `/compare/privategpt` | Compare without unfair claims | Audience, local workflow, UI, source evidence, setup, limits | `Сравнить сценарии` |
| `/compare/localgpt` | Differentiate product UX and release discipline | Folder workflow, multilingual controls, provenance, eval, setup | `Запустить LocalRAG` |
| `/compare/notebooklm` | Capture private/local alternative intent | Local default vs hosted product, source checking, team/privacy caveats | `Выбрать локальный сценарий` |

Subpages must inherit the Russian source message, then adapt per language.
Do not clone the homepage copy into each feature page.

## Multilingual Localization Strategy

### Core rule

Russian is the source of meaning. English, Dutch, Chinese, and Hebrew are
localized by meaning, audience expectations, search intent, and UI constraints.
Only technical identifiers remain stable.

### What is localized by meaning

- Positioning, headlines, body copy, proof explanations, objections, FAQ
  answers, pricing/lead copy, feature benefits, SEO titles/descriptions, error
  explanations, empty states, screenshot captions, alt text, and form hints.
- CTA verbs must fit local idiom and the actual action.
- Privacy and reliability claims must keep the same limitation level in every
  language.

### What stays technical

Keep these stable across languages unless a local equivalent is standard:

- `LocalRAG`
- `RAG`
- `Ollama`
- `FAISS`
- `FastAPI`
- `Docker Compose`
- `pytest`
- `Kiwi TCMS`
- `qwen3.5:9b`
- `intfloat/multilingual-e5-large`
- `top-k`
- `LLM`
- `embedding` / `embeddings` when used in technical UI
- environment variables such as `RAG_BACKEND_URL`, `DOCS_PATH`,
  `HOST_DOCS_PATH`
- file extensions and route names

When a technical term is new to the audience, add a short explanation near the
first use instead of replacing it everywhere.

### Language-specific strategy

| Language | Role in content system | Localization risks | Proof/example needs |
| --- | --- | --- | --- |
| Russian | Source language for strategy and page copy | English calques, mixed Latin/Russian syntax, overuse of `AI`, bureaucratic wording | Russian screenshots or captions, Russian/private-folder examples, clear local data-flow wording |
| English | International technical and open-source audience | Losing Russian-first nuance, generic SaaS tone, overclaiming privacy | Developer proof, README/setup links, eval and source provenance examples |
| Dutch | Practical EU technical audience | Too formal `u` vs informal `je`, literal English compounds, privacy claims sounding like compliance | EU privacy caution without GDPR claims, Dutch file/folder examples, native review |
| Chinese | High-context technical audience | Direct translation of "private" and "local" can imply security guarantees; line length in UI | Chinese UI screenshots, concise metadata, explanation of local runtime and model dependency |
| Hebrew | RTL audience | Layout/CTA truncation, mixed LTR technical terms, punctuation around Latin model names | RTL browser QA, Hebrew examples, source/path display checks with LTR paths |

### Per-language proof

Each localized landing page should include at least one language-specific proof
or example:

- Russian: a Russian question and answer with a visible source fragment.
- English: setup/runtime proof and source context screenshot.
- Dutch: local folder example and privacy limitation note reviewed by a native
  speaker.
- Chinese: mixed Chinese/English document example and short local-runtime note.
- Hebrew: RTL UI screenshot, Hebrew answer-language example, and LTR source path
  rendering check.

## Russian Copy Rules by Surface

### UI labels

- Use short nouns for stable labels: `Вопрос`, `Ответ`, `Источники`,
  `Модель`, `Роль`, `История`, `Настройки`.
- Use clear verbs for actions: `Спросить`, `Переиндексировать`,
  `Выбрать папку`, `Скачать`, `Удалить`, `Применить`.
- Avoid inflated labels: `Осуществить переиндексацию`,
  `Произвести отправку запроса`, `Конфигурационные параметры`.
- Keep `debug`, `top-k`, `embedding`, and model names technical when they are
  controls for technical users. Add helper text when needed.

### Buttons and CTAs

- Button text must fit the action and expected result.
- Prefer `Запустить локально` to `Начать`.
- Prefer `Обсудить внедрение` to `Связаться` when the action is a rollout
  conversation.
- Prefer `Открыть источники` or `Проверить источники` to vague `Подробнее`.

### FAQ

- Answer the risk first, then explain.
- Use precise boundaries: `в базовом локальном сценарии`, `если вы не
  подключили внешний сервис`, `зависит от модели`, `нужно проверить на вашем
  корпусе`.
- Do not bury limitations at the end of long paragraphs.

### Pricing and lead capture

- Avoid `бесплатно навсегда` unless legally approved.
- Use `Community` and `Corporate` only with clear scope.
- For corporate copy, say `индивидуальный объем работ` or `обсуждается по
  требованиям`, not `enterprise-ready` without proof.
- Lead forms must state what happens after submission and how contact data is
  handled.

### Feature pages

- Each feature page must answer:
  - what user problem it solves;
  - what product surface proves it;
  - which limits apply;
  - what the next action is.
- A feature is not a claim unless there is product evidence, screenshot,
  command, API endpoint, test, or documented plan.

### SEO metadata

- Russian titles should start with the intent, then the brand:
  - `Локальный ИИ-поиск по документам - LocalRAG`
  - `RAG на Ollama для приватных документов - LocalRAG`
  - `Ответы по PDF с проверкой источников - LocalRAG`
- Russian meta descriptions should stay under practical length limits and avoid
  stacked buzzwords.
- Do not translate English keyword clusters literally. Use Russian search
  language: `локальный ИИ`, `поиск по документам`, `вопросы по PDF`,
  `RAG на Ollama`, `приватные документы`, `ответы с источниками`.

### Error and empty states

- Say what happened and what to do next.
- Good:
  - `Документы не найдены. Добавьте файлы в папку и запустите
    переиндексацию.`
  - `Ollama недоступна. Проверьте, запущен ли сервис, и обновите список
    моделей.`
  - `Индекс устарел. Переиндексируйте папку перед новым вопросом.`
- Avoid:
  - `Произошла ошибка`
  - `Некорректное состояние`
  - `Не удалось выполнить операцию` without next step

## Anti-Calque Checklist

Use this checklist before Russian copy moves to design or development:

| English/source phrase | Avoid | Prefer |
| --- | --- | --- |
| Local AI for documents | `Локальная AI для документов` | `Локальный ИИ-поиск по документам` |
| Source-backed answers | `source-backed ответы` | `ответы с опорой на источники` |
| Run it locally | `Запусти это локально` | `Запустить локально` |
| Discuss rollout | `Обсудить rollout` | `Обсудить внедрение` |
| Retrieval controls | `контролы retrieval` | `настройки поиска`, `параметры retrieval` for technical UI |
| Visible workflow | `видимый workflow` | `понятный рабочий сценарий` |
| Corporate layer | `корпоративный слой` everywhere | `корпоративный контур`, `интеграционный слой` depending on context |
| Current product surface | `текущая продуктовая поверхность` | `что уже видно в интерфейсе` |
| Quality gate | `ворота качества` | `quality gate`, `порог качества` |
| Lead capture | `захват лидов` | `форма заявки`, `контактная форма` |
| Custom scope | `кастомный скоуп` | `индивидуальный объем работ` |
| Private documents | `приватные документы` if legal/security context is unclear | `личные`, `закрытые`, `внутренние` by audience; keep `приватные` for SEO only when useful |

Typography rules:

- Use Russian quotation marks: `«...»`.
- Use an em dash in Russian prose where appropriate, but keep UI labels short.
- Use non-breaking spaces in final web copy for values like `5 языков`,
  `v0.9.0`, `PDF и DOCX` where the renderer supports them.
- Do not over-capitalize Russian headings. Prefer sentence case:
  `Как LocalRAG работает с источниками`, not `Как LocalRAG Работает С
  Источниками`.
- Keep product and model identifiers exact.

## Unsupported-Claim Checklist

Before implementation, each page must answer yes/no:

- Is this claim implemented today, planned, or custom-scope?
- Is there repository evidence, screenshot evidence, test evidence, or external
  evidence?
- Does the claim depend on user configuration, selected model, OCR quality,
  network settings, or deployment architecture?
- Does the claim imply compliance, security certification, guaranteed accuracy,
  or enterprise readiness?
- Is the same limitation preserved in every language?
- Is social proof real, dated, sourced, and allowed to publish?
- Are screenshots from the current build and versioned?
- Are generated illustrations clearly illustrative and not presented as product
  evidence?

Claims that fail the checklist must be rewritten, footnoted, or removed.

## How This Analysis Informs UX/UI and Visual Work

### UX/UI design

- Russian copy length is the source sizing constraint. Design components must
  fit Russian labels first, then test English, Dutch, Chinese, and Hebrew.
- Primary workflows should remain visible: folder, reindex status, question,
  answer, source context, model, answer language, retrieval settings.
- CTAs must match real actions. Do not use decorative primary buttons for
  non-actions.
- The homepage should show a usable product path in the first viewport, not only
  abstract positioning.

### Generated illustrations

- Use illustrations only to support concepts that screenshots cannot show:
  local folder boundary, retrieval flow, source verification, corporate
  integration architecture.
- Do not use generic dark AI imagery as proof.
- Russian captions and alt text must describe the product state or workflow.
- Generated visuals must not imply security/compliance features that are not
  implemented.

### 3D, motion, and scroll effects

- Motion should explain progression: folder -> index -> retrieval -> answer ->
  source check.
- Avoid effects that delay reading the Russian hero, obscure screenshots, or
  make source proof feel decorative.
- If 3D is used, it should visualize local document flow or retrieval graph with
  product labels, not abstract glowing technology.
- All motion must respect reduced-motion preferences and keep CTA targets
  stable.

### Responsive layout

- Test Russian labels as the longest baseline for header nav, buttons, cards,
  FAQ accordions, pricing tables, and form labels.
- Hebrew requires RTL QA with mixed LTR tokens: `LocalRAG`, `Ollama`,
  `qwen3.5:9b`, file paths, and URLs.
- Chinese needs line-height and wrapping checks in compact cards.
- Dutch can produce long compound nouns; avoid narrow fixed-width cards.

### Browser QA

Required browser QA scenarios for downstream stages:

- Russian homepage at desktop, tablet, and mobile widths.
- Language switcher preserves meaning and layout across EN/RU/NL/ZH/HE.
- Header CTAs do not wrap awkwardly or overlap.
- Screenshot captions and alt text match the current UI.
- Pricing/lead capture copy does not imply unsupported terms.
- FAQ answers keep limitation notes visible.
- Error and empty states fit in the UI and provide next steps.
- Hebrew RTL layout renders nav, buttons, paths, and source context correctly.
- Generated illustrations or motion do not hide content, overlap text, or create
  false product claims.

## Acceptance Criteria for Design and Implementation Stages

Content acceptance:

- Russian source copy exists for the homepage before English/Dutch/Chinese/Hebrew
  adaptation begins.
- Every page has a Russian brief with audience, offer, proof, CTA, objections,
  and unsupported-claim notes.
- Public claims are tagged as `implemented`, `custom scope`, `planned`, or
  `verify before publish`.
- The `5.0 / 5.0` and `23 user reviews` claim is removed or backed by a dated
  source before publication.
- Pricing/free/corporate claims have license and scope verification.

Localization acceptance:

- EN/RU/NL/ZH/HE pages are localized by meaning, not line-by-line translation.
- Technical identifiers remain stable.
- Each target language has native or specialist QA for headline, CTA, FAQ,
  pricing, and error/empty states.
- Hebrew receives explicit RTL layout QA.

UX/UI acceptance:

- Russian copy fits in navigation, hero, cards, buttons, form fields, FAQ,
  pricing, and error states at mobile and desktop widths.
- The first viewport shows product identity, local/private document value,
  verification value, and one clear primary CTA.
- Product screenshots are current, versioned or date-scoped, and not replaced by
  generic AI visuals.
- Any generated imagery, 3D, motion, or scroll effect supports a specific
  product explanation and passes reduced-motion/responsive checks.

QA acceptance:

- Browser QA includes Russian-first pages and all five locales.
- Unsupported claims are checked before merge to public site.
- SEO metadata is localized and does not duplicate English phrasing literally.
- Error and empty states provide next steps in each locale.
- Analysis gate #5 remains blocked until this issue is closed and the resulting
  MR is reviewable or merged.

## Definition of Done Coverage

- [x] Russian-first copy strategy exists as a versioned repository artifact.
- [x] Artifact explicitly references `ru-text` and `ru-web-copy-editor`
  standards.
- [x] Artifact maps Russian and multilingual copy needs to
  pages/sections/CTAs.
- [x] Artifact flags unsupported claims and language-specific risks.
- [x] Artifact provides concrete acceptance criteria for design and
  implementation stages.
