# LocalRAG SEO Structure and Metadata Plan

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | SEO |
| Stage | Design |
| Issue | #33 - SEO structure and metadata plan |
| Artifact version | 1.0 |
| Date | 2026-06-06 |
| Source language | Russian |
| Target locales | RU, EN, NL, ZH, HE |
| Status | Ready for website design and implementation planning |

## Purpose

This design-stage artifact defines the SEO structure for the LocalRAG website:
metadata, page headings, schema, internal linking, canonical rules, localized
metadata rules, visual-media SEO requirements, and acceptance criteria for
downstream design, implementation, and browser verification.

The plan is Russian-first. Russian page copy, heading length, CTA wording,
limitations, proof framing, and metadata are the source design constraints.
English, Dutch, Chinese, and Hebrew pages must localize meaning and search
intent rather than translate Russian or English line by line.

## Required Inputs

This plan uses the merged analysis and content artifacts required by issue #33:

- `docs/discovery-and-analysis.md`
- `docs/website-content/content-brief-page-map.md`
- `docs/website-content/ru-first-multilingual-copy-analysis.md`
- `artifacts/seo/analysis/2026-06-06-seo-intent-keyword-brief.md`
- `artifacts/website-content/design/2026-06-06-draft-page-copy.md`

Russian web copy and metadata must follow the standards referenced in the
Russian-first analysis:

- `ru-text`: natural Russian, clear UX wording, direct verbs, correct
  typography, no bureaucratic filler, no English word-order calques.
- `ru-web-copy-editor`: concrete positioning, clear CTAs, visible proof,
  objection handling, and explicit unsupported-claim flags.

## SEO Design Principles

1. Russian is the source language for meaning, layout sizing, metadata length,
   and CTA specificity.
2. Public marketing pages and the local FastAPI app surface must stay separate.
   The app route can stay interactive; crawlable SEO pages should live on the
   public website.
3. The public site must not use `/docs` for SEO documentation if the running
   FastAPI app uses `/docs` for Swagger UI. Use `/guide/*` for crawlable guides.
4. Every public claim must be tagged as `implemented`, `custom scope`,
   `planned`, or `verify-before-publish`.
5. Screenshots are product proof only when current, versioned or dated, and
   matched to the visible UI.
6. Generated illustrations, 3D, and motion can explain the product flow, but
   they must not replace product proof or imply unsupported security,
   compliance, or enterprise capabilities.
7. Localized pages must preserve the same limitations as the Russian source
   page. Privacy, quality, OCR, pricing, and enterprise claims cannot become
   stronger in translation.

## Claim Status Register

| Claim family | Status | Allowed wording direction | Required proof or limitation |
| --- | --- | --- | --- |
| Local-first document workflow | `implemented` | "В базовом локальном сценарии LocalRAG работает с папкой на вашем компьютере, локальным индексом и Ollama." | README, Docker Compose, local FAISS index, Ollama default. Must mention configuration dependence. |
| Source provenance | `implemented` | "Ответ можно проверить по найденным фрагментам, пути к файлу, страницам и строкам, где метаданные доступны." | README/app behavior/tests. Must not claim guaranteed correctness. |
| Supported formats | `implemented` | "PDF, DOCX, TXT, Markdown, HTML, JSON, CSV, YAML и файлы кода." | README/parser support. Must note parsing/OCR quality limits. |
| EN/RU/NL/ZH/HE UI | `implemented` | "Интерфейс доступен на EN/RU/NL/ZH/HE." | Locale files. Requires native/language QA before publication. |
| Separate answer language | `implemented` | "Язык интерфейса и язык ответа настраиваются отдельно." | App settings and locale copy. Must note answer quality depends on model/context. |
| Ollama model control | `implemented` | "Модели Ollama выбираются и управляются в интерфейсе." | App surface and tests. Verify screenshots before publication. |
| Eval/release quality checks | `implemented` | "pytest, release checks и eval-набор помогают отслеживать регрессии retrieval." | Scripts/tests. Exact scores require a dated run. |
| OCR-heavy PDFs/scans | `implemented with limitation` | "LocalRAG рассчитан на работу с PDF и OCR-heavy источниками, но качество зависит от OCR и разбора." | Tests/examples. Avoid "OCR всегда работает". |
| Model and embedding selection guide | `planned` | "Руководство по моделям и embeddings должно объяснять default values, tradeoffs и проверки лицензий." | Publish only after current recommendations and release defaults are verified. |
| Developer implementation page | `planned` | "Техническая страница может объяснять FastAPI, FAISS, Ollama, eval и API surface." | Publish only when it adds material beyond README and avoids duplicate quick-start copy. |
| Corporate connectors, governance, access control, monitoring | `custom scope` | "Корпоративный контур проектируется отдельно под источники, права, мониторинг и критерии качества." | Owner approval and implementation evidence per rollout. |
| Pricing/free/pilot claims | `verify-before-publish` | Do not publish exact commercial terms in SEO metadata. | License/commercial approval. |
| Ratings, review counts, customer logos, testimonials | `verify-before-publish` | Do not publish until sourced, dated, and approved. | Evidence and permission. |
| Compliance/security certification | `verify-before-publish` | Do not claim GDPR, HIPAA, SOC 2, air-gap, or certified security. | External/legal/security verification. |

## Metadata Structure

Every crawlable page must expose the same metadata contract across locales.

| Field | Requirement |
| --- | --- |
| `<html lang>` | Locale-specific: `ru`, `en`, `nl`, `zh-CN`, `he`. Hebrew pages must also use `dir="rtl"`. |
| Title tag | Intent first, brand second. Russian titles should generally end with `- LocalRAG`. Keep under practical SERP length. |
| Meta description | One concrete promise plus one proof point or limitation. Avoid stacked buzzwords and unsourced guarantees. |
| Canonical URL | Self-canonical per locale URL. No canonical from localized pages to Russian unless the localized page is intentionally unavailable. |
| Hreflang | Include all published locale alternates plus `x-default`. Do not emit alternates for unpublished locales. |
| Open Graph | `og:type`, localized `og:title`, localized `og:description`, canonical `og:url`, locale-specific `og:locale`, and current preview image. |
| Twitter/X cards | `summary_large_image` only when the image is current and descriptive. |
| Robots | Default `index,follow` for public pages. Use `noindex,follow` for thin, duplicate, staging, search, filter, parameter, or app-only pages. |
| Structured data | JSON-LD per page type. Schema must mirror visible content and claim status. |
| Image metadata | Descriptive filename, localized alt text, caption, width/height, lazy loading except the LCP image. |
| Last modified | Use visible release/date metadata for release notes, guides, screenshots, and technical articles where accurate. |

### Russian Metadata Rules

- Start with Russian search intent, then brand:
  - `Локальный ИИ-поиск по документам - LocalRAG`
  - `RAG на Ollama для приватных документов - LocalRAG`
  - `Ответы по PDF с проверкой источников - LocalRAG`
- Use natural Russian search language:
  - `локальный ИИ`
  - `поиск по документам`
  - `вопросы по PDF`
  - `RAG на Ollama`
  - `приватные документы`
  - `ответы с источниками`
- Avoid literal English calques:
  - Avoid `локальная AI для документов`.
  - Prefer `локальный ИИ-поиск по документам`.
  - Avoid `source-backed ответы`.
  - Prefer `ответы с опорой на источники`.

### Localized Metadata Rules

| Locale | Search and copy direction | Required QA |
| --- | --- | --- |
| RU | Source locale. Practical, skeptical, action-oriented. Keep limitations near the claim. | `ru-text` and `ru-web-copy-editor` review. |
| EN | Technical/open-source audience. Use "local RAG", "private documents", "Ollama", "source citations". Avoid generic SaaS tone. | Verify not stronger than RU privacy/security claims. |
| NL | Practical EU technical audience. Avoid GDPR/compliance implication unless verified. | Native review for compounds, tone, and privacy wording. |
| ZH | Concise high-context technical audience. Explain local runtime boundaries carefully. | Line length and technical-token wrapping QA. |
| HE | RTL audience with LTR technical tokens. Keep CTAs short and paths readable. | RTL browser QA with `LocalRAG`, `Ollama`, URLs, and file paths. |

### Homepage Metadata Examples by Locale

These examples define the translation level expected for other pages.

| Locale | Title | Description |
| --- | --- | --- |
| RU | `Локальный ИИ-поиск по документам - LocalRAG` | `Задавайте вопросы по PDF, заметкам, таблицам и коду через локальный RAG на Ollama. Проверяйте ответы по найденным фрагментам источников.` |
| EN | `Local AI Search for Private Documents - LocalRAG` | `Ask grounded questions over PDFs, notes, tables, and code with local RAG on Ollama, then inspect the source passages behind each answer.` |
| NL | `Lokale AI-zoekfunctie voor prive documenten - LocalRAG` | `Stel vragen over PDF's, notities, tabellen en code met lokale RAG op Ollama en controleer antwoorden aan de hand van gevonden bronfragmenten.` |
| ZH | `本地私有文档 AI 搜索 - LocalRAG` | `用基于 Ollama 的本地 RAG 询问 PDF、笔记、表格和代码，并查看支撑答案的来源片段。` |
| HE | `חיפוש AI מקומי במסמכים פרטיים - LocalRAG` | `שאלו שאלות על PDF, הערות, טבלאות וקוד באמצעות RAG מקומי עם Ollama, ובדקו את קטעי המקור שעליהם מבוססת התשובה.` |

## Page Metadata Matrix

Russian metadata below is the source baseline. Localized metadata must preserve
the same intent, proof, and limitation level.

| Route | Indexing | RU title | RU meta description | Primary schema | Claim status |
| --- | --- | --- | --- | --- | --- |
| `/` | `index,follow` | `Локальный ИИ-поиск по документам - LocalRAG` | `Задавайте вопросы по PDF, заметкам, таблицам и коду через локальный RAG на Ollama. Проверяйте ответы по найденным фрагментам источников.` | `WebSite`, `SoftwareApplication`, `Organization` | `implemented` with privacy limitation |
| `/features` | `index,follow` | `Возможности LocalRAG для локального RAG и приватных документов` | `Локальная индексация файлов, ответы с источниками, Ollama model manager, многоязычный интерфейс, роли ответа и eval-проверки качества.` | `CollectionPage`, `SoftwareApplication`, `BreadcrumbList` | `implemented` |
| `/how-it-works` | `index,follow` | `Как работает LocalRAG: Ollama, FAISS и проверяемые источники` | `Посмотрите путь от локальной папки к embeddings, FAISS retrieval, role-aware prompt и ответу с найденными источниками.` | `TechArticle`, `BreadcrumbList` | `implemented` with quality limitation |
| `/guide/getting-started` | `index,follow` | `Как запустить LocalRAG локально с Docker и Ollama` | `Склонируйте LocalRAG, добавьте документы, запустите Docker Compose, переиндексируйте папку и задайте первый вопрос по локальным файлам.` | `HowTo`, `TechArticle`, `BreadcrumbList` | `implemented`; verify current commands before publish |
| `/guide/models-and-embeddings` | `noindex,follow` until full guide exists; then `index,follow` | `Модели и embeddings для локального RAG - LocalRAG` | `Выбирайте Ollama-модель ответа и embedding model для локального RAG, учитывая ресурсы машины, язык корпуса, качество и лицензионные ограничения.` | `TechArticle`, `BreadcrumbList` | `planned`; recommendations `verify-before-publish` |
| `/guide/retrieval-quality` | `index,follow` | `Проверка качества retrieval в LocalRAG` | `LocalRAG использует pytest, release checks, eval-набор и quality gate, чтобы отслеживать качество ответов и source hit ratio.` | `TechArticle`, `BreadcrumbList` | `implemented`; exact scores `verify-before-publish` |
| `/use-cases` | `index,follow` | `Сценарии LocalRAG: вопросы по PDF, заметкам, таблицам и коду` | `Используйте LocalRAG для локальных проектных папок, PDF, смешанных языков, исследовательских заметок, кода и проверки локальных моделей.` | `CollectionPage`, `BreadcrumbList` | `implemented` plus limits |
| `/faq` | `index,follow` when populated; otherwise redirect to `/faq/privacy-security` | `FAQ LocalRAG: локальный RAG, документы, модели и источники` | `Короткие ответы о запуске LocalRAG, локальной обработке документов, форматах, моделях Ollama, языках, источниках и переиндексации.` | `FAQPage`, `BreadcrumbList` | `implemented` where backed by current docs |
| `/faq/privacy-security` | `index,follow` | `Приватность и безопасность LocalRAG: что остается локально` | `Ответы на вопросы о локальной обработке документов, Ollama, индексе, источниках, внешних сервисах и ограничениях приватности LocalRAG.` | `FAQPage`, `BreadcrumbList` | `implemented` with explicit limitation |
| `/for-teams` | `index,follow` after approval; otherwise `noindex,follow` | `LocalRAG для команд и локальных внедрений` | `Обсудите локальный или on-premise RAG по внутренним документам: источники, права доступа, API, мониторинг, качество retrieval и rollout-план.` | `Service`, `BreadcrumbList` | `custom scope`; owner approval required |
| `/release-notes` | `index,follow` | `LocalRAG release notes и качество релизов` | `Следите за версиями LocalRAG, runtime defaults, изменениями retrieval, поддержкой моделей и release quality checks.` | `TechArticle`, `BreadcrumbList` | `implemented`; verify version/model values |
| `/developers` | `noindex,follow` until it is materially different from README; then `index,follow` | `LocalRAG для разработчиков: FastAPI, FAISS, Ollama и eval` | `Разберите архитектуру LocalRAG, API surface, локальный индекс FAISS, Ollama runtime, retrieval checks и release workflow.` | `TechArticle`, `BreadcrumbList` | `planned`; avoid duplicate README content |
| `/features/private-document-qa` | `index,follow` when split page is published | `Вопросы по приватным документам без обязательного upload-сценария - LocalRAG` | `Работайте с локальной папкой, индексом и найденным контекстом. Приватность зависит от конфигурации, моделей и подключенных сервисов.` | `TechArticle`, `BreadcrumbList` | `implemented` with privacy limitation |
| `/features/ollama-rag` | `index,follow` when split page is published | `RAG на Ollama для приватных документов - LocalRAG` | `Выбирайте локальную модель ответа, управляйте моделями через UI, используйте FAISS-индекс и multilingual embeddings для собственных файлов.` | `TechArticle`, `BreadcrumbList` | `implemented` |
| `/features/pdf-ocr-rag` | `index,follow` when split page is published | `Вопросы по PDF и сканам с проверкой источников - LocalRAG` | `Задавайте вопросы по PDF, сканам и смешанным папкам, проверяя найденные фрагменты. Качество зависит от разбора документа и OCR.` | `TechArticle`, `BreadcrumbList` | `implemented with limitation` |
| `/features/source-citations` | `index,follow` when split page is published | `Ответы с источниками и найденным контекстом - LocalRAG` | `Проверяйте ответы по retrieved context: путям к файлам, страницам и строкам там, где такие метаданные доступны.` | `TechArticle`, `BreadcrumbList` | `implemented` |
| `/features/multilingual-rag` | `index,follow` when split page is published | `Многоязычный RAG и отдельный язык ответа - LocalRAG` | `Интерфейс EN/RU/NL/ZH/HE и отдельный язык ответа помогают работать со смешанными корпусами, но качество зависит от модели и контекста.` | `TechArticle`, `BreadcrumbList` | `implemented` with QA requirement |
| `/features/response-roles` | `index,follow` when split page is published | `Роли ответа для локального RAG - LocalRAG` | `Analyst, Engineer, Archivist и пользовательские роли помогают менять стиль, формат и приоритеты ответа под задачу.` | `TechArticle`, `BreadcrumbList` | `implemented` |
| `/compare/privategpt` | `index,follow` only after fair comparison review | `LocalRAG и PrivateGPT: сравнение локальных RAG-сценариев` | `Сравните локальный workflow, интерфейс, источники, модели и ограничения без неподтвержденных заявлений о конкурентах.` | `Article`, `BreadcrumbList` | `verify-before-publish` |
| `/compare/localgpt` | `index,follow` only after fair comparison review | `LocalRAG и localGPT: сравнение локального поиска по документам` | `Сравните folder workflow, многоязычные настройки, source provenance, eval и запуск локального RAG.` | `Article`, `BreadcrumbList` | `verify-before-publish` |
| `/compare/notebooklm` | `index,follow` only after fair comparison review | `LocalRAG как локальная альтернатива NotebookLM` | `Разберите локальный сценарий, проверку источников и ограничения по приватности без преувеличения возможностей.` | `Article`, `BreadcrumbList` | `verify-before-publish` |

## Schema Strategy

Schema must describe visible page content only. Do not add ratings, reviews,
offers, customer logos, compliance, or enterprise guarantees unless verified.

### Global Schema

Use on public pages where applicable:

- `WebSite`: homepage only. Include `name`, `url`, `inLanguage`, and
  `potentialAction` only if site search exists. Do not invent site search.
- `Organization`: public owner/publisher only if name, URL, logo, and profiles
  are verified. Otherwise use minimal `SoftwareApplication` publisher data or
  omit.
- `SoftwareApplication`: homepage and features pages. Use `applicationCategory:
  "DeveloperApplication"` or `"ProductivityApplication"`. Avoid `aggregateRating`
  and commercial `offers` until approved.
- `BreadcrumbList`: every non-homepage public page.

### Page-Specific Schema

| Page type | Schema | Required content match |
| --- | --- | --- |
| Setup guide | `HowTo` + `TechArticle` | Steps must be visible on the page and match current commands. |
| FAQ | `FAQPage` | Only include questions and answers visible on the page. Preserve limitations in answers. |
| How it works / quality guides | `TechArticle` | Use visible sections, current model names, and current release defaults only after verification. |
| Feature pages | `TechArticle` or `WebPage` | Use feature proof and limitations visible on page. |
| Use cases | `CollectionPage` | Cards must avoid unsupported vertical/compliance claims. |
| For teams | `Service` only after owner approval | Mark custom scope in visible copy. Do not use `Offer` unless pricing/support terms are approved. |
| Release notes | `TechArticle` | Version, model defaults, and dates must be checked against `VERSION`, README, and release notes. |
| Comparison pages | `Article` | Must be fair, current, sourced, and reviewed before indexing. |

### Schema Field Rules

- `name` and `headline`: localized page H1 or close equivalent.
- `description`: localized meta description or page intro.
- `inLanguage`: page locale.
- `dateModified`: only when the page has a reliable update date.
- `image`: product screenshot or explanatory image that is visible on page and
  has descriptive alt text.
- `softwareVersion`: only when tied to a verified release value.
- `operatingSystem`: use only if documented; avoid over-specific claims.
- `featureList`: include implemented features only.
- `applicationSubCategory`, `keywords`, and `about`: optional; keep concise and
  mapped to the SEO intent brief.

## Heading Strategy

### Global Rules

- One H1 per page.
- H1 answers the page intent in Russian first, then localized by meaning.
- H2 sections must match reader questions and scanning behavior.
- H3 is for repeated units inside a section: steps, cards, FAQ groups,
  limitations, examples.
- Do not use decorative headings that hide limitations. If a section makes a
  privacy, quality, OCR, or corporate claim, include the limitation in the same
  section or immediately adjacent supporting text.
- Russian headings use sentence case, not title case.

### Homepage Heading Model

| Level | Heading | Intent |
| --- | --- | --- |
| H1 | `Локальный ИИ-поиск по приватным документам.` | Brand and primary search intent. |
| H2 | `Реальные папки редко похожи на демо-набор.` | Problem framing. |
| H2 | `Что делает LocalRAG` | Capability overview. |
| H2 | `От папки до проверяемого ответа` | Workflow and interaction path. |
| H2 | `Возможности, которые уже видны в продукте` | Implemented proof. |
| H2 | `Интерфейс без макетов` | Screenshot/product proof. |
| H2 | `Проверка качества не вынесена за скобки.` | QA/eval proof. |
| H2 | `Проверьте LocalRAG на небольшой папке.` | Final conversion. |

### Subpage Heading Models

| Route | H1 | Required H2 flow |
| --- | --- | --- |
| `/features` | `Возможности LocalRAG без маркетингового тумана.` | `Локальная папка и индекс`; `Форматы документов`; `Проверяемые ответы`; `Модели Ollama`; `Многоязычная работа`; `Роли и стили ответа`; `История и debug`; `Ограничения` |
| `/how-it-works` | `От локальной папки к ответу с источниками.` | `Загрузка файлов`; `Нормализация и разбиение`; `Embeddings`; `FAISS-индекс`; `Retrieval и reranking`; `Role-aware prompt`; `Ответ Ollama`; `Проверка источников`; `Что влияет на качество` |
| `/guide/getting-started` | `Первый локальный ответ за один короткий сценарий.` | `Перед запуском`; `Папка по умолчанию для Windows`; `Запуск`; `Первый вопрос`; `Нестандартные пути`; `Что проверить, если не работает` |
| `/guide/models-and-embeddings` | `Выбор модели должен быть проверяемым, а не случайным.` | `Default answer model`; `Embedding model`; `Ресурсы машины`; `Язык корпуса`; `Качество и скорость`; `Лицензии и ограничения`; `Как сравнивать модели` |
| `/guide/retrieval-quality` | `Retrieval нужно проверять, а не угадывать.` | `API и unit tests`; `Release smoke checks`; `Eval-набор`; `Регрессии retrieval`; `Перед публикацией чисел качества` |
| `/use-cases` | `Для задач, где документ должен оставаться рядом с ответом.` | `Личная исследовательская папка`; `Проектная документация`; `PDF и сканы`; `Смешанные языки`; `Сравнение локальных моделей`; `Демо локального RAG`; `Где LocalRAG не должен притворяться другой системой` |
| `/faq` | `Короткие ответы о LocalRAG перед запуском.` | `Локальная обработка`; `Форматы`; `Модели`; `Языки`; `Источники`; `Переиндексация`; `Качество`; `Корпоративный сценарий` |
| `/faq/privacy-security` | `Приватность и безопасность LocalRAG без лишних обещаний.` | Use FAQ questions as H2/H3 depending on accordion semantics. Required questions: cloud boundary, formats, language controls, source display, changed documents, corporate use. |
| `/for-teams` | `Локальный RAG можно развивать в корпоративный контур.` | `Источники данных`; `Права и границы доступа`; `API и интеграции`; `Мониторинг и качество`; `Пилот`; `Что нужно согласовать до внедрения` |
| `/release-notes` | `Изменения продукта должны быть проверяемыми.` | `Текущий релиз`; `Runtime defaults`; `Что изменилось`; `Проверки перед релизом`; `Известные ограничения` |
| `/developers` | `Архитектура LocalRAG должна быть понятна без чтения всего кода.` | `Runtime surface`; `API endpoints`; `Ingestion and indexing`; `Retrieval quality`; `Release workflow`; `Extension points`; `Что остается в README` |

## Homepage Block Design Contract

Each homepage block must satisfy content, SEO, accessibility, interaction, and
browser QA requirements. Russian copy length is the sizing baseline.

| Block | Purpose and reader question | Content and CTA | Proof and claim status | Visual hierarchy | Interaction states | Responsive behavior | Accessibility | Browser QA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Header/navigation | "Where am I, and what can I do next?" | Brand, anchors: `Зачем`, `Возможности`, `Как работает`, `Запуск`, `Качество`, `FAQ`; CTA `Запустить локально`. | Navigation and install CTA are `implemented`; external repo link `verify-before-publish`. | Compact sticky or top header; brand first, CTA last. | Active section state, focus state, language menu open/closed, mobile menu open/closed. | Russian labels must fit without overlap at mobile and desktop; collapse to menu when needed. | Semantic `nav`, visible focus, language labels with full accessible names. | Test RU desktop/tablet/mobile; test HE RTL nav and mixed LTR tokens. |
| Hero | "What is LocalRAG and why should I care?" | H1, subhead, CTAs `Запустить локально` and `Посмотреть интерфейс`, Docker/Ollama microcopy. | Local workflow `implemented` with configuration limitation. | H1 dominates; proof strip visible without forcing scroll past CTA. | CTA hover/focus/pressed, screenshot/media load fallback. | First viewport must reveal product identity and hint of next section on mobile and desktop. | H1 first in DOM; no text embedded only in images. | Check LCP image, text wrapping, no motion blocking read. |
| Proof strip | "What is real today?" | Local files, source fragments, EN/RU/NL/ZH/HE, Ollama/FAISS, model/retrieval UI, pytest/eval/release checks. | All `implemented`; exact version values `verify-before-publish`. | Low-height factual strip under hero. | Links or tooltips optional; no modal required. | Wrap into two rows on narrow screens without truncating Russian. | If icons are used, labels remain visible to screen readers. | Verify no unsupported ratings/reviews/logos appear. |
| Problem framing | "What problem is this solving?" | Mixed folders, PDFs, scans, tables, code, languages, imperfect filenames; LocalRAG centers checking sources. | Problem claim `implemented` as product positioning; OCR has limitation. | Text section with one supporting visual max. | Optional "show example folder" expand state. | Avoid narrow columns that break Russian lines awkwardly. | Use real text, not image-only copy. | Check Russian copy no English calques. |
| Product promise | "What does it actually do?" | Cards: index folder, answer with context, show sources, visible settings. CTA can anchor to features. | `implemented`; source metadata only "where available". | Four equal cards or dense grid; no nested cards. | Card hover/focus states if clickable; otherwise no fake affordance. | Grid becomes single column; equal minimum heights not required if content remains readable. | Cards use headings and lists, not generic div-only structure. | Verify no card overlaps at 320px width. |
| Workflow preview | "How do I get from files to an answer?" | Steps: add documents, reindex, ask, inspect sources, tune quality. CTA `Переиндексировать папку` or `Задать первый вопрос` when demo exists. | `implemented`; quality depends on model/OCR/index. | Numbered stepper or flow diagram; source check should be a visible final step. | Step hover/focus, reduced-motion step animation disabled. | Horizontal stepper becomes vertical; no hidden step labels. | Ordered list semantics if possible. | Test with long Russian step labels and HE RTL. |
| Feature proof | "Which features are available now?" | Local processing, formats, multilingual UI, answer language, roles, quality checks. | `implemented`; no social proof. | Scannable feature grid with proof badges. | Links to split feature pages where available. | Avoid narrow fixed cards for Dutch and Russian. | Icons have accessible labels; no color-only status. | Verify each feature link resolves or is hidden until page exists. |
| Screenshots | "Is this a real product?" | Current UI screenshots: answer/context, settings, folder/reindex, roles/language. CTA `Посмотреть интерфейс`. | Screenshots `verify-before-publish`; app features `implemented`. | Screenshots are primary proof; captions close to image. | Carousel/tab states if used; keyboard accessible. | Mobile uses stacked screenshots; no tiny unreadable UI thumbnails as sole proof. | Alt text names workflow and version/date where possible. | Compare captions to current UI before release; no stale UI elements. |
| Quality teaser | "How is reliability checked?" | API/unit tests, release smoke checks, eval set, quality gate. CTA `Запустить eval`. | `implemented`; exact scores `verify-before-publish`. | Technical proof block; commands can be secondary. | Copy command buttons if implemented must show copied/failure state. | Code lines wrap or scroll horizontally without breaking layout. | Code blocks have labels; buttons have accessible names. | Verify commands match current scripts. |
| Final CTA/footer | "What should I do next?" | Start with a small folder; CTAs `Запустить локально`, `Открыть API docs`; footer links. | `implemented`; commercial CTA `approval required`. | Strong closing CTA, then compact footer. | Link hover/focus, external link indication. | Footer columns collapse cleanly. | Landmark footer; clear link text. | Check `API docs` points to app `/docs`, not public SEO `/docs`. |

## Subpage Design Contract

Each subpage must answer one primary reader question and include a visible next
action, proof, limitation, and QA expectation.

| Route | Purpose and reader question | Content and CTA | Proof and claim status | Visual hierarchy and media | Interaction states | Responsive/accessibility/browser QA |
| --- | --- | --- | --- | --- | --- | --- |
| `/features` | Help visitors scan what LocalRAG already does. "Which capabilities are real?" | Capability sections, CTA variants `Проверить источники`, `Настроить модель`, `Настроить язык ответа`, `Выбрать роль`. | Implemented feature proof only; no ratings/logos. | Dense feature grid with screenshots or icons; limitations row at end. | Feature links hover/focus; inactive future links hidden. | RU labels fit cards; icons are decorative unless named; all links resolve. |
| `/how-it-works` | Explain the technical flow. "How does my folder become an answer?" | File load, chunking, embeddings, FAISS, retrieval/reranking, prompt, Ollama answer, sources. CTA `Смотреть retrieval flow`. | Implemented architecture; quality limitation required. | Architecture diagram can use generated illustration or lightweight 3D only if it labels folder, index, retrieval, answer, sources. | Step highlight, optional diagram hover labels, reduced-motion fallback. | Diagram text accessible in adjacent HTML; mobile diagram becomes vertical; QA for text overlap. |
| `/guide/getting-started` | Reduce time to first answer. "How do I run it?" | Prereqs, Windows path, start command, first question, non-default paths, troubleshooting. CTA `Склонировать репозиторий`. | Implemented commands, but verify against README before publishing. | Procedure layout with commands and checkpoints. | Copy command buttons, open/closed troubleshooting panels. | Commands readable on mobile; code blocks keyboard accessible; links to app `/docs` are clear. |
| `/guide/models-and-embeddings` | Help technical users choose responsibly. "Which local model and embeddings should I use?" | Default model, embedding model, resource tradeoffs, language quality, license checks, comparison method. CTA `Проверить модели`. | `planned`; current defaults verify before publish; model recommendations need dated evidence. | Comparison table plus measured-example slots, not vague "best model" claims. | Filter/sort states optional; copy model tag buttons if implemented. | Use `noindex,follow` until content is complete; table scrolls on mobile; no unsupported benchmark claims. |
| `/guide/retrieval-quality` | Prove engineering discipline. "How do I know retrieval did not regress?" | Tests, release checks, eval, quality gate, source hit ratio. CTA `Запустить eval`. | Implemented scripts; exact metrics verify before publish. | Evidence modules with command snippets and result placeholders. | Copy commands, expandable explanation for metrics. | No stale numbers; QA command paths; code scrolls on mobile. |
| `/use-cases` | Match product to practical workflows. "Is this useful for my folder?" | Research folder, project docs, PDF/scans, mixed languages, model comparison, local demo, out-of-scope. CTA `Проверить на своей папке`. | Implemented use cases with limitations; no industry compliance claims. | Use-case cards grouped by task, not by persona hype. | Cards link to relevant feature or guide pages. | Out-of-scope block visible; mobile cards do not hide limitation copy. |
| `/faq` | Provide a short FAQ hub. "What should I know before I run LocalRAG?" | Local processing, formats, models, languages, sources, reindexing, quality, corporate scope. CTA `Запустить локально`. | Implemented where backed by current docs; corporate answer custom scope. | FAQ groups link to deeper guide and privacy pages. | Accordion and anchor states. | FAQ schema only includes visible answers; redirect to privacy FAQ if hub is not populated. |
| `/faq/privacy-security` | Handle risk objections plainly. "What stays local, and what does not?" | FAQ on cloud boundary, formats, language, sources, changed docs, corporate use. CTA `Проверить архитектуру`. | Implemented with explicit limitations; corporate answer custom scope. | FAQ accordion or static list; answer starts with direct risk answer. | Accordion open/closed/focus states; URL anchors for questions. | FAQ schema matches visible answers; limitations not hidden in collapsed-only content for crawlers. |
| `/for-teams` | Separate product from scoped rollout. "Can a team use this safely?" | Sources, access boundaries, APIs/integrations, monitoring, quality, pilot. CTA `Обсудить внедрение`. | `custom scope` and `approval required`. | More restrained layout; no enterprise badges. | Lead form states if form exists: idle, validation, submitting, success, error. | Use `noindex,follow` until owner approval; form labels accessible; no unsupported connector claims. |
| `/release-notes` | Make release changes verifiable. "What changed and what defaults apply?" | Current release, runtime defaults, changed retrieval/model support, release checks, known limits. CTA `Смотреть текущий релиз`. | Implemented; version/model values verify before publish. | Chronological release modules, current release summary. | Version filter/tabs optional; no hidden current version. | Dates use ISO or localized format consistently; verify against `VERSION`, README, release notes. |
| `/developers` | Serve technical implementation intent without duplicating README. "How is LocalRAG built and extended?" | FastAPI surface, endpoints, ingestion/indexing, retrieval quality, release workflow, extension boundaries. CTA `Открыть API docs`. | `planned`; duplicate README copy should remain noindex or omitted. | Technical article with diagrams and concise API map. | Endpoint accordion/table states. | Keep app `/docs` separate; code/examples readable; schema uses current endpoints only. |
| `/features/private-document-qa` | Capture private document Q&A intent. "Can I ask questions without an upload workflow?" | Local folder, index, context, source checking, privacy limitation. CTA `Запустить локально`. | Implemented local default; privacy depends on configuration. | Product screenshot plus data-boundary diagram. | Diagram hover/focus labels. | Limitation must be above fold or near privacy claim; localized claims equivalent. |
| `/features/ollama-rag` | Capture Ollama RAG intent. "How does it use Ollama?" | Model manager, local model selection, FAISS, multilingual embeddings, setup caveats. CTA `Настроить модель`. | Implemented; verify model manager screenshot. | UI screenshot and technical flow. | Model selector demo states if interactive. | Model names wrap without breaking; schema has implemented features only. |
| `/features/pdf-ocr-rag` | Capture PDF/scans intent carefully. "Will this work with my scanned PDFs?" | PDF workflow, OCR limitations, page references, tested examples when available. CTA `Проверить PDF-папку`. | Implemented with OCR limitation; examples verify before publish. | Screenshot of sources/page refs plus limitation callout. | Example tabs by file type optional. | Limit copy visible; no "guaranteed OCR" phrasing in any locale. |
| `/features/source-citations` | Make verification the trust center. "Can I check where an answer came from?" | Context panel, path/page/line metadata, stale index risk, examples. CTA `Проверить источники`. | Implemented; metadata available where parser provides it. | Large source-context screenshot; captions cite version/date. | Source example expand/collapse. | Alt text names file/page/line concept; QA for LTR paths in HE. |
| `/features/multilingual-rag` | Explain multilingual UX without magic translation claims. "Can UI and answer language differ?" | UI languages, answer language, multilingual embeddings, mixed documents, native QA. CTA `Настроить язык ответа`. | Implemented with model/context limitation. | Language selector screenshot and examples. | Language switcher states; answer-language dropdown states. | Test EN/RU/NL/ZH/HE layouts; HE RTL; Chinese line height. |
| `/features/response-roles` | Show roles as workflow control. "Can answers fit different tasks?" | Analyst/Engineer/Archivist/custom roles, prompts, defaults, risks. CTA `Выбрать роль`. | Implemented. | Role cards/screenshots; no personality gimmicks in SEO copy. | Role selection active/hover/focus. | Role labels readable; custom role limits clear. |
| `/compare/*` | Capture alternative/comparison intent. "Which local document AI should I choose?" | Fair comparison by scenario, setup, source visibility, models, limits. CTA `Сравнить сценарии` or specific action. | `verify-before-publish`; requires sourced current competitor data. | Comparison table with dates/sources. | Table sorting optional; row focus states. | Use `noindex,follow` until reviewed; no unfair or outdated claims. |

## Internal Linking Strategy

### Navigation and Hub Links

- Header links should target the first release page/anchors:
  - `/` or `/#why`
  - `/features`
  - `/how-it-works`
  - `/guide/getting-started`
  - `/guide/retrieval-quality`
  - `/faq/privacy-security`
- Footer links:
  - Source repository link after verification.
  - App API docs as `http://localhost:7860/docs` or a clearly labeled local app
    docs link, not a crawlable public `/docs` SEO route.
  - Release notes.
  - Commercial contact only after approval.

### Contextual Link Rules

| Source page/section | Link to | Anchor text direction |
| --- | --- | --- |
| Homepage hero | `/guide/getting-started` | `Запустить локально` |
| Homepage source proof | `/features/source-citations` | `Проверить источники` |
| Homepage model proof | `/features/ollama-rag` | `Настроить модель Ollama` |
| Homepage quality teaser | `/guide/retrieval-quality` | `Запустить eval` |
| Problem framing | `/use-cases` | `Посмотреть сценарии` |
| Features overview local files | `/features/private-document-qa` | `Вопросы по приватным документам` |
| Features overview PDF/OCR | `/features/pdf-ocr-rag` | `Вопросы по PDF и сканам` |
| Features overview multilingual | `/features/multilingual-rag` | `Настроить язык ответа` |
| Features overview model/embedding proof | `/guide/models-and-embeddings` when published | `Выбрать модель и embeddings` |
| How it works retrieval | `/guide/retrieval-quality` | `Проверка retrieval` |
| Getting started after first question | `/features/source-citations` | `Проверить найденные источники` |
| FAQ privacy answer | `/how-it-works` | `Посмотреть архитектуру` |
| FAQ corporate answer | `/for-teams` | `Обсудить внедрение` only after approval |
| Release notes model defaults | `/guide/models-and-embeddings` when published | `Выбрать модель и embeddings` |
| Developer/API mentions | `/developers` when published; otherwise app `/docs` | `Разобрать архитектуру` or `Открыть API docs` |

### Link Quality Rules

- Use descriptive Russian anchor text. Avoid `Подробнее` when a concrete action
  exists.
- Do not link to unpublished pages in production navigation. Keep future split
  pages hidden or `noindex,follow` until populated and localized.
- Cross-link feature pages back to:
  - `/guide/getting-started`
  - `/how-it-works`
  - `/faq/privacy-security`
  - `/guide/retrieval-quality` where relevant
- Use breadcrumbs on all non-homepage public pages.
- Avoid duplicating full quick-start commands across many pages. Link to the
  canonical setup guide instead.

## Canonical, Hreflang, and Robots Rules

### Canonical Rules

- Canonical base for public marketing pages: `https://localrag.dev`.
- Use self-canonical absolute URLs for each locale page:
  - `https://localrag.dev/ru/...`
  - `https://localrag.dev/en/...`
  - `https://localrag.dev/nl/...`
  - `https://localrag.dev/zh/...`
  - `https://localrag.dev/he/...`
- If the public site chooses Russian at root (`/`), define one root strategy:
  - Preferred: `/ru/` is the Russian canonical page and `/` redirects or
    selects locale with `x-default`.
  - Alternative: `/` is Russian canonical and `/ru/` redirects to `/`.
  - Do not keep both `/` and `/ru/` indexable with duplicate Russian content.
- Normalize trailing slashes consistently. Choose either slash or no slash and
  redirect the other variant.
- Strip tracking parameters from canonical URLs.
- Search, filter, preview, staging, and app-only parameter pages must not be
  canonical index targets.

### Hreflang Rules

For each published locale page, emit a complete reciprocal set:

| Language | Hreflang |
| --- | --- |
| Russian | `ru` |
| English | `en` |
| Dutch | `nl` |
| Chinese | `zh-CN` |
| Hebrew | `he` |
| Default selector | `x-default` |

Rules:

- Hreflang must point to equivalent pages, not homepage fallbacks unless the
  localized equivalent does not exist and is intentionally omitted from the
  hreflang set.
- Do not publish hreflang for machine-drafted or unreviewed localized pages if
  they are not ready to index.
- Hebrew pages require `dir="rtl"` and browser QA for mixed LTR strings.

### Robots Rules

| Surface | Robots |
| --- | --- |
| Public homepage, feature, guide, FAQ, release notes | `index,follow` after content/claim QA |
| Staging, preview, dev site, generated design QA routes | `noindex,follow` |
| Running app UI routes | Prefer `noindex,follow` unless intentionally public and crawlable |
| Swagger/OpenAPI `/docs` on app host | `noindex,follow` if public; keep separate from SEO guide routes |
| Search/filter/query parameter pages | `noindex,follow` |
| Thin future split pages before content is complete | `noindex,follow` |
| Comparison pages before source/fairness review | `noindex,follow` |
| `/for-teams` before business/legal approval | `noindex,follow` |

## Visual, Media, Motion, and Performance SEO

Visual design can support SEO only when it helps users inspect the product,
understand the workflow, or trust a claim.

### Product Screenshots

- Use real screenshots as primary product proof:
  - answer with found context;
  - model/embedding settings;
  - folder/reindex state;
  - role and answer-language controls.
- Each screenshot must include:
  - descriptive filename;
  - localized alt text;
  - visible caption;
  - version/date metadata near image or in supporting copy;
  - width and height attributes to avoid layout shift.
- Screenshots must be refreshed or reverified before publication.
- Do not blur, crop, darken, or stylize screenshots so heavily that product
  state cannot be inspected.

### Generated Illustrations

- Allowed uses:
  - local folder boundary;
  - ingestion to FAISS index;
  - retrieval flow;
  - source verification;
  - scoped corporate architecture.
- Required labels:
  - `Иллюстрация рабочего сценария`, `Схема retrieval`, or equivalent localized
    label when the asset is conceptual.
- Prohibited uses:
  - security/compliance proof;
  - fake dashboards, fake user reviews, fake customer logos;
  - generic dark AI backgrounds that obscure content.

### 3D

- Use 3D only if it explains document flow, retrieval graph, or source
  verification better than a flat diagram.
- The primary 3D scene must not replace H1, CTA, or product screenshot proof.
- Provide static fallback image and text diagram for unsupported WebGL.
- Use reduced-detail mobile rendering and avoid heavy shaders.
- Required QA:
  - desktop and mobile screenshot nonblank;
  - visible labels;
  - no text overlap;
  - no false claim implied by visual metaphors.

### Animation and Scroll Effects

- Motion purpose: show progression from folder to index to retrieved context to
  answer to source check.
- Recommended timing:
  - UI hover/focus transitions: 120-200 ms.
  - Section entrance: 180-300 ms.
  - Workflow step transitions: 300-600 ms.
  - Avoid long scroll-jacking sequences.
- Reduced-motion fallback:
  - respect `prefers-reduced-motion`;
  - disable parallax, 3D auto-rotation, scroll-linked reveals, and animated
    counters;
  - keep all content visible without animation.
- Mobile behavior:
  - no sticky elements that cover CTAs or source captions;
  - no animation that delays the hero or first screenshot;
  - diagrams stack vertically with visible labels.

### Performance Limits

- LCP image should be a current product screenshot or useful product visual,
  not a decorative abstract image.
- Avoid loading 3D or video before the first meaningful content.
- Lazy-load below-fold screenshots and videos.
- Prefer compressed modern image formats where the implementation stack allows
  them, with PNG fallback for UI screenshots when text clarity matters.
- Prevent cumulative layout shift by reserving image, video, and diagram
  dimensions.
- Keep generated media and motion assets out of metadata preview images unless
  they clearly represent the product.

## Accessibility and Browser QA Expectations

Downstream implementation must verify:

- RU homepage at desktop, tablet, and mobile widths.
- EN/RU/NL/ZH/HE localized pages preserve claim limitations and CTA meaning.
- Hebrew RTL pages render nav, buttons, URLs, model names, and file paths
  correctly.
- Russian navigation, cards, buttons, FAQ accordions, form labels, and metadata
  snippets do not overflow.
- Chinese and Dutch text wraps cleanly in cards and metadata previews.
- Every page has one H1, logical heading order, visible focus states, semantic
  landmarks, and accessible language switcher labels.
- FAQ accordions are keyboard accessible and expose content to crawlers.
- Product screenshots have alt text, captions, and version/date verification.
- Generated illustrations and 3D scenes are marked as explanatory, not product
  evidence.
- Reduced-motion mode keeps all content available without scroll effects.
- Public pages avoid unsupported social proof, pricing, compliance, or security
  claims.
- Canonicals and hreflang are reciprocal and point to live equivalent pages.
- `/guide/*` is used for public SEO guides; app `/docs` remains API docs.

## Implementation Handoff

### Required SEO Components

Implementation should expose a page-level SEO object or equivalent template data
with:

- `locale`
- `dir`
- `route`
- `canonicalUrl`
- `alternateUrls`
- `robots`
- `title`
- `description`
- `openGraphTitle`
- `openGraphDescription`
- `openGraphImage`
- `schema`
- `claimStatuses`
- `lastVerifiedAt` for screenshots, release defaults, comparisons, and metrics

### Required Content Checks Before Publishing

- Validate Russian source copy with `ru-text` and `ru-web-copy-editor` rules.
- Confirm every claim status in the page content.
- Confirm current release values from `VERSION`, README, and release notes.
- Confirm commands from README or scripts for setup and quality pages.
- Confirm screenshots against the current UI build.
- Confirm social proof, pricing, commercial, and security claims have approval
  or are removed.
- Confirm localized pages are reviewed by a native/specialist reviewer where
  required.

## Acceptance Criteria

- [x] Metadata structure is defined for public pages, localized pages, Open
  Graph, robots, canonical URLs, hreflang, schema, images, and verification
  dates.
- [x] Russian-first metadata examples and rules are provided and tied to
  `ru-text` and `ru-web-copy-editor` standards.
- [x] Page-level metadata matrix covers homepage, feature overview, how it
  works, setup, model/embedding guide, quality, use cases, FAQ hub, privacy
  FAQ, teams, release notes, developer page, split feature pages, and
  comparison pages.
- [x] Schema strategy defines allowed JSON-LD types and unsupported schema
  fields to avoid.
- [x] Heading strategy defines one-H1 rule, homepage heading model, and subpage
  heading models.
- [x] Homepage block design contract covers purpose, reader question, content,
  CTA, proof, claim status, visual hierarchy, interaction states, responsive
  behavior, accessibility, and browser QA.
- [x] Subpage design contract covers every planned logical subpage from the SEO
  and website-content artifacts.
- [x] Internal linking strategy defines navigation, contextual links, footer
  links, breadcrumbs, and unpublished-page handling.
- [x] Canonical, hreflang, robots, and `/docs` route-conflict rules are defined.
- [x] Visual-media SEO covers real screenshots, generated illustrations, 3D,
  animation, scroll effects, reduced-motion fallback, performance limits, and
  mobile behavior.
- [x] Unsupported social proof, compliance, security, pricing, corporate, and
  quality claims are flagged with claim statuses and verification requirements.
- [x] Browser QA expectations are explicit for Russian-first pages and
  EN/RU/NL/ZH/HE localization, including Hebrew RTL.
- [x] Output is stored as a versioned repository artifact for downstream design,
  implementation, and verification.

## Definition of Done Coverage

- Define metadata structure: covered in `Metadata Structure`, `Page Metadata
  Matrix`, and `Implementation Handoff`.
- Define schema and heading strategy: covered in `Schema Strategy` and
  `Heading Strategy`.
- Define internal linking and canonical rules: covered in `Internal Linking
  Strategy` and `Canonical, Hreflang, and Robots Rules`.
