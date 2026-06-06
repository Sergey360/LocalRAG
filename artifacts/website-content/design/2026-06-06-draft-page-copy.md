# LocalRAG Draft Page Copy

## Artifact Metadata

| Field | Value |
| --- | --- |
| Project | LocalRAG |
| Track | Website content |
| Stage | Design |
| Issue | #29 - Draft page copy |
| Artifact version | 1.0 |
| Date | 2026-06-06 |
| Source language | Russian |
| Status | Draft for design and stakeholder approval |

## Source Inputs

- `docs/website-content/content-brief-page-map.md`
- `docs/website-content/ru-first-multilingual-copy-analysis.md`
- `artifacts/seo/analysis/2026-06-06-seo-intent-keyword-brief.md`
- `Readme.md` and localized README files
- Current repository UI assets and screenshots under `assets/screenshots/`

## Copy Status Labels

Use these labels before moving copy into design, implementation, or public
pages:

- `[READY]` - repository-backed product copy that can move to design.
- `[VERIFY]` - requires current screenshot, version, route, test, or source
  confirmation before publication.
- `[APPROVAL REQUIRED]` - requires owner approval for commercial, legal,
  pricing, privacy, support, or deployment scope.
- `[CUSTOM SCOPE]` - should be presented as scoped implementation work, not a
  shipped default feature.

## Global Navigation Copy

Header:

- Brand: `LocalRAG`
- Navigation: `Зачем`, `Возможности`, `Как работает`, `Запуск`, `Качество`,
  `FAQ`
- Primary CTA: `Запустить локально`
- Secondary CTA where needed: `Посмотреть интерфейс`

Footer:

- `GitHub` `[VERIFY]`
- `Документация API` `[READY]`
- `Release notes` `[READY]`
- `Обсудить внедрение` `[APPROVAL REQUIRED]`

Footer short copy:

> LocalRAG - локальный RAG для вопросов по документам с проверяемыми
> источниками, управлением моделями Ollama и многоязычным интерфейсом.

## Global Trust Blocks

### Product proof strip

Use near the hero or directly below the first product screenshot.

- `Файлы остаются локально в базовом сценарии` `[READY]`
- `Ответы с найденными фрагментами источников` `[READY]`
- `Интерфейс: EN/RU/NL/ZH/HE` `[READY]`
- `Ollama, FAISS, multilingual-e5` `[READY]`
- `Модель и retrieval настраиваются в UI` `[READY]`
- `pytest, eval и release checks` `[READY]`

### Privacy boundary block

Heading:

> Локальный по умолчанию, но без лишних обещаний.

Body:

> В базовом сценарии LocalRAG работает с папкой на вашем компьютере, строит
> локальный индекс и использует модели Ollama. Итоговая приватность зависит от
> вашей конфигурации, сетевых настроек, выбранных моделей и того, подключены ли
> внешние сервисы.

Label: `[READY]`

### Source trust block

Heading:

> Ответ не нужно принимать на веру.

Body:

> LocalRAG показывает найденные фрагменты, путь к файлу, страницы и строки там,
> где эти данные доступны. Это не гарантирует идеальный ответ, но дает понятную
> точку проверки.

Label: `[READY]`

### Unsupported social proof replacement

Use instead of ratings, review counts, or unsourced testimonials.

Heading:

> Доверие строится на проверяемом продукте.

Bullets:

- `Открытый исходный код` `[VERIFY]`
- `Реальные скриншоты текущей версии` `[VERIFY]`
- `Source provenance в ответах` `[READY]`
- `Повторяемый eval-набор` `[READY]`
- `Docker Compose запуск` `[READY]`

Do not publish rating, review count, customer logo, compliance, or pricing
claims until evidence is attached.

## Global CTA Bank

Primary CTAs:

- `Запустить локально`
- `Склонировать репозиторий`
- `Открыть интерфейс`
- `Переиндексировать папку`

Secondary CTAs:

- `Посмотреть интерфейс`
- `Проверить источники`
- `Настроить модель`
- `Настроить язык ответа`
- `Запустить eval`
- `Открыть API docs`

Commercial CTAs:

- `Обсудить внедрение` `[APPROVAL REQUIRED]`
- `Описать корпоративный сценарий` `[APPROVAL REQUIRED]`
- `Запросить оценку интеграции` `[APPROVAL REQUIRED]`

Avoid:

- `Узнать больше`
- `Начать путь`
- `Раскрыть знания`
- `Попробовать магию ИИ`

## Page: Home

Route target: `/`

SEO title:

> Локальный ИИ-поиск по документам - LocalRAG

Meta description:

> Задавайте вопросы по PDF, заметкам, таблицам и коду через локальный RAG на
> Ollama. Проверяйте ответы по найденным фрагментам источников.

### Hero

H1:

> Локальный ИИ-поиск по приватным документам.

Subhead:

> Подключите папку с PDF, сканами, заметками, таблицами и кодом. Задавайте
> вопросы через локальный RAG на Ollama и проверяйте ответы по найденным
> фрагментам источников.

Primary CTA:

> Запустить локально

Secondary CTA:

> Посмотреть интерфейс

Microcopy:

> Для первого запуска нужен Docker Compose и локальный runtime Ollama.

Status: `[READY]`

Hero headline variants:

1. `Локальные ответы по документам с проверкой источников.`
2. `RAG на Ollama для папок с приватными документами.`
3. `Задавайте вопросы по локальным файлам и проверяйте, откуда взят ответ.`

Hero CTA variants:

1. Primary `Запустить локально`; secondary `Открыть инструкцию`
2. Primary `Склонировать репозиторий`; secondary `Посмотреть скриншоты`
3. Primary `Проверить на своей папке`; secondary `Как это работает`

### Problem framing

Kicker:

> Зачем

Heading:

> Реальные папки редко похожи на демо-набор.

Body:

> В рабочих документах смешиваются PDF, сканы, Markdown, таблицы, код, разные
> языки и неидеальные имена файлов. Обычный чат может дать убедительный текст,
> но не всегда показывает, какой фрагмент повлиял на ответ. LocalRAG строится
> вокруг локального поиска, видимых настроек и проверки источников.

Status: `[READY]`

### Product promise

Heading:

> Что делает LocalRAG

Cards:

- `Индексирует локальную папку` - подключите документы, обновите индекс и
  работайте с файлами без обязательного upload-сценария.
- `Отвечает с опорой на контекст` - вопрос проходит через retrieval, а ответ
  сопровождается найденными фрагментами.
- `Показывает источники` - открывайте путь к файлу, страницы и строки там, где
  метаданные доступны.
- `Оставляет настройки видимыми` - выбирайте модель, язык ответа, роль и
  параметры поиска прямо в интерфейсе.

Status: `[READY]`

### Workflow preview

Heading:

> От папки до проверяемого ответа

Steps:

1. `Добавьте документы` - положите файлы в выбранную локальную папку.
2. `Переиндексируйте` - LocalRAG построит FAISS-индекс с метаданными.
3. `Задайте вопрос` - выберите модель Ollama, язык ответа и роль.
4. `Проверьте источники` - сравните ответ с найденными фрагментами.
5. `Настройте качество` - измените top-k, модель или embedding при необходимости.

Status: `[READY]`

### Feature proof

Heading:

> Возможности, которые уже видны в продукте

Feature cards:

- `Локальная обработка документов` - базовый путь рассчитан на папку на вашей
  машине, локальный индекс и модели Ollama.
- `Поддержка разных форматов` - PDF, DOCX, TXT, Markdown, HTML, JSON, CSV,
  YAML и файлы кода.
- `Многоязычный интерфейс` - English, Russian, Dutch, Chinese и Hebrew.
- `Отдельный язык ответа` - интерфейс и язык генерации настраиваются отдельно.
- `Роли ответа` - Analyst, Engineer, Archivist и пользовательские роли с
  собственными настройками.
- `Проверки качества` - pytest, release checks и eval-набор для retrieval.

Status: `[READY]`

### Screenshots

Heading:

> Интерфейс без макетов

Intro:

> Основной экран, настройки модели и найденный контекст должны показываться
> реальными скриншотами текущей версии.

Captions:

- `Ответ и найденный контекст` `[VERIFY]`
- `Настройки модели и embedding` `[VERIFY]`
- `Выбор папки и переиндексация` `[VERIFY]`
- `Роли ответа и язык генерации` `[VERIFY]`

Approval note:

> Перед публикацией подтвердить дату скриншотов, версию приложения и отсутствие
> устаревших UI-элементов. `[VERIFY]`

### Quality teaser

Heading:

> Проверка качества не вынесена за скобки.

Body:

> LocalRAG включает API-тесты, release smoke checks и eval-набор для проверки
> ответов на смешанном корпусе. Это помогает находить регрессии retrieval, а не
> только проверять, что сервер запустился.

CTA:

> Запустить eval

Status: `[READY]`

### Final CTA

Heading:

> Проверьте LocalRAG на небольшой папке.

Body:

> Начните с документов, ответы по которым вы можете быстро проверить вручную.
> Так проще оценить качество модели, retrieval и источников на вашем корпусе.

Primary CTA:

> Запустить локально

Secondary CTA:

> Открыть API docs

Status: `[READY]`

## Page: Features Overview

Route target: `/features`

SEO title:

> Возможности LocalRAG для локального RAG и приватных документов

Meta description:

> Локальная индексация файлов, ответы с источниками, Ollama model manager,
> многоязычный интерфейс, роли ответа и eval-проверки качества.

### Hero

H1:

> Возможности LocalRAG без маркетингового тумана.

Body:

> Эта страница показывает, что уже можно использовать: локальный индекс,
> Ollama-модели, source provenance, многоязычную UX-настройку, роли ответа и
> проверки retrieval.

CTA:

> Посмотреть интерфейс

Status: `[READY]`

### Capability sections

- `Локальная папка и индекс` - LocalRAG работает с выбранной директорией и
  сохраняет индекс FAISS для повторных вопросов.
- `Форматы документов` - используйте PDF, DOCX, текст, Markdown, HTML,
  структурированные файлы и кодовые файлы.
- `Проверяемые ответы` - найденные фрагменты выводятся рядом с ответом, чтобы
  пользователь мог проверить основу генерации.
- `Модели Ollama` - модель ответа можно выбирать и управлять ею через UI.
- `Многоязычная работа` - язык интерфейса и язык ответа разделены.
- `Роли и стили ответа` - роль помогает задать тон, формат и приоритеты
  ответа под задачу.
- `История и debug` - настройки и история помогают воспроизвести сценарий и
  понять, как retrieval повлиял на ответ.

Status: `[READY]`

### Section CTA variants

- `Проверить источники`
- `Настроить модель`
- `Настроить язык ответа`
- `Выбрать роль`

## Page: How It Works

Route target: `/how-it-works`

SEO title:

> Как работает LocalRAG: Ollama, FAISS и проверяемые источники

Meta description:

> Посмотрите путь от локальной папки к embeddings, FAISS retrieval,
> role-aware prompt и ответу с найденными источниками.

### Hero

H1:

> От локальной папки к ответу с источниками.

Body:

> LocalRAG загружает файлы, разбивает текст на фрагменты, строит embeddings,
> ищет релевантный контекст в FAISS и передает его локальной модели Ollama
> вместе с правилами роли и языка ответа.

CTA:

> Смотреть retrieval flow

Status: `[READY]`

### Flow sections

1. `Загрузка файлов` - документы читаются из настроенной локальной папки.
2. `Нормализация и разбиение` - текст делится на фрагменты с метаданными.
3. `Embeddings` - по умолчанию используется `intfloat/multilingual-e5-large`.
4. `FAISS-индекс` - векторный индекс сохраняется для быстрых повторных запросов.
5. `Retrieval и reranking` - LocalRAG выбирает кандидаты и уточняет порядок.
6. `Role-aware prompt` - вопрос, контекст, роль и язык ответа собираются в
   prompt.
7. `Ответ Ollama` - локальная модель генерирует ответ.
8. `Проверка источников` - пользователь видит найденные фрагменты и метаданные.

Status: `[READY]`

### Limits

Heading:

> Что влияет на качество

Body:

> Качество ответа зависит от выбранной модели, качества исходных документов,
> OCR, свежести индекса, настроек retrieval и того, насколько вопрос покрыт
> найденным контекстом.

Status: `[READY]`

## Page: Getting Started

Route target: `/guide/getting-started`

SEO title:

> Как запустить LocalRAG локально с Docker и Ollama

Meta description:

> Склонируйте LocalRAG, добавьте документы, запустите Docker Compose,
> переиндексируйте папку и задайте первый вопрос по локальным файлам.

### Hero

H1:

> Первый локальный ответ за один короткий сценарий.

Body:

> Установите Docker Desktop или Docker Compose, подготовьте папку с документами,
> запустите стек и откройте интерфейс на `http://localhost:7860`.

Primary CTA:

> Склонировать репозиторий

Secondary CTA:

> Открыть UI

Status: `[READY]`

### Setup sections

- `Перед запуском` - нужен Docker runtime, доступные ресурсы машины и локальный
  Ollama runtime через стек.
- `Папка по умолчанию для Windows` - используйте `C:\Temp\PDF` или настройте
  переменные окружения.
- `Запуск` - выполните `docker compose up -d --build` или release-first
  start scripts.
- `Первый вопрос` - добавьте документы, откройте UI, переиндексируйте папку,
  выберите модель и задайте вопрос.
- `Нестандартные пути` - проверьте `HOST_FS_ROOT`, `HOST_FS_MOUNT`,
  `DOCS_PATH` и `HOST_DOCS_PATH`.

Status: `[READY]`

### CTA variants

- `Запустить стек`
- `Переиндексировать папку`
- `Задать первый вопрос`

## Page: Retrieval Quality

Route target: `/guide/retrieval-quality`

SEO title:

> Проверка качества retrieval в LocalRAG

Meta description:

> LocalRAG использует pytest, release checks, eval-набор и quality gate, чтобы
> отслеживать качество ответов и source hit ratio.

### Hero

H1:

> Retrieval нужно проверять, а не угадывать.

Body:

> LocalRAG включает автоматические тесты и eval-сценарии для смешанных
> документов, OCR-heavy PDF и вопросов, где важно попасть в правильный источник.

CTA:

> Запустить eval

Status: `[READY]`

### Evidence sections

- `API и unit tests` - базовая проверка endpoints, валидации, истории, ролей и
  model manager.
- `Release smoke checks` - health, metadata, UI flow и модельные настройки
  перед релизом.
- `Eval-набор` - вопросы по корпусу проверяют strict score, loose score и
  source hit ratio.
- `Регрессии retrieval` - quality gate помогает заметить, когда поиск стал
  хуже после изменения кода или настроек.

Status: `[READY]`

Approval note:

> Перед публикацией конкретных чисел качества подтвердить актуальный eval run,
> дату корпуса и версию модели. `[VERIFY]`

## Page: Use Cases

Route target: `/use-cases`

SEO title:

> Сценарии LocalRAG: вопросы по PDF, заметкам, таблицам и коду

Meta description:

> Используйте LocalRAG для локальных проектных папок, PDF, смешанных языков,
> исследовательских заметок, кода и проверки поведения локальных моделей.

### Hero

H1:

> Для задач, где документ должен оставаться рядом с ответом.

Body:

> LocalRAG подходит, когда нужно быстро спросить локальную папку и затем
> проверить, какие фрагменты действительно поддерживают ответ.

CTA:

> Проверить на своей папке

Status: `[READY]`

### Use case cards

- `Личная исследовательская папка` - задавайте вопросы по заметкам, PDF и
  экспортам, не собирая отдельную базу знаний.
- `Проектная документация` - ищите решения и ограничения в Markdown, DOCX,
  таблицах и коде.
- `PDF и сканы` - проверяйте ответы по страницам и найденным фрагментам, помня
  об ограничениях OCR.
- `Смешанные языки` - задавайте вопрос на одном языке, а ответ получайте на
  выбранном языке.
- `Сравнение локальных моделей` - меняйте Ollama-модели на одном и том же
  индексе и сравнивайте ответы.
- `Демо локального RAG` - показывайте не только генерацию, но и retrieval,
  sources и eval.

Status: `[READY]`

### Out of scope

Heading:

> Где LocalRAG не должен притворяться другой системой

Body:

> LocalRAG не заменяет DMS/ECM, систему прав доступа, юридический архив,
> retention-политику или полноценную SaaS knowledge base. Корпоративные
> источники, права, мониторинг и поддержка должны проектироваться отдельно.

Status: `[READY]` plus `[APPROVAL REQUIRED]` for any commercial packaging.

## Page: Privacy and Security FAQ

Route target: `/faq/privacy-security`

SEO title:

> Приватность и безопасность LocalRAG: что остается локально

Meta description:

> Ответы на вопросы о локальной обработке документов, Ollama, индексе,
> источниках, внешних сервисах и ограничениях приватности LocalRAG.

### FAQ entries

Question:

> Мои документы уходят в облако?

Answer:

> В базовом локальном сценарии LocalRAG работает с папкой на вашем компьютере,
> локальным индексом и Ollama. Не называйте это гарантией изоляции для любой
> установки: итоговая граница данных зависит от конфигурации, сети, моделей и
> внешних сервисов.

Status: `[READY]`

Question:

> Какие форматы поддерживаются?

Answer:

> Основной набор: PDF, DOCX, TXT, Markdown, HTML, JSON, CSV, YAML и файлы кода.
> Качество разбора зависит от структуры документа, OCR и содержимого файла.

Status: `[READY]`

Question:

> Можно ли отдельно выбрать язык интерфейса и язык ответа?

Answer:

> Да. Интерфейс доступен на EN/RU/NL/ZH/HE, а язык ответа выбирается отдельно.
> Качество ответа все равно зависит от выбранной модели и найденного контекста.

Status: `[READY]`

Question:

> Как LocalRAG показывает источники?

Answer:

> Ответ сопровождается найденными фрагментами. Для источников показываются путь
> к файлу, страницы и строки там, где эти метаданные доступны после разбора.

Status: `[READY]`

Question:

> Что делать после изменения документов?

Answer:

> Переиндексируйте папку. Если индекс устарел, LocalRAG может отвечать по
> старому состоянию файлов.

Status: `[READY]`

Question:

> Можно ли использовать в компании?

Answer:

> Базовый продукт можно оценить локально. Корпоративный контур - источники,
> права, мониторинг, API, support и quality gates - нужно согласовать по
> требованиям конкретного внедрения.

Status: `[APPROVAL REQUIRED]` and `[CUSTOM SCOPE]`

## Page: For Teams

Route target: `/for-teams`

SEO title:

> LocalRAG для команд и локальных внедрений

Meta description:

> Обсудите локальный или on-premise RAG по внутренним документам: источники,
> права доступа, API, мониторинг, качество retrieval и rollout-план.

### Hero

H1:

> Локальный RAG можно развивать в корпоративный контур.

Body:

> Базовый LocalRAG рассчитан на локальную работу с папкой. Командный сценарий
> требует отдельного проектирования: источники данных, права доступа, API,
> очереди, мониторинг, критерии качества и правила эксплуатации.

Primary CTA:

> Обсудить внедрение

Secondary CTA:

> Описать источники данных

Status: `[APPROVAL REQUIRED]` and `[CUSTOM SCOPE]`

### Team sections

- `Источники данных` - файловые шары, хранилища, базы знаний и SQL-источники
  не должны называться готовыми коннекторами без доказательства реализации.
  `[APPROVAL REQUIRED]`
- `Права и границы доступа` - описывать только после подтверждения модели
  доступа и deployment-архитектуры. `[APPROVAL REQUIRED]`
- `API и интеграции` - говорить как о scoped engineering work, если конкретный
  endpoint или connector не существует в релизе. `[CUSTOM SCOPE]`
- `Мониторинг и качество` - можно опираться на release checks и eval, но
  production monitoring требует отдельного подтверждения. `[APPROVAL REQUIRED]`
- `Пилот` - начать с ограниченного корпуса, критериев качества и ручной
  проверки источников. `[READY]`

Lead form copy:

> Расскажите, какие документы нужно подключить, где они хранятся, какие
> ограничения по данным важны и как команда будет проверять качество ответов.

Submit CTA:

> Отправить сценарий внедрения

Status: `[APPROVAL REQUIRED]`

## Page: Release Notes

Route target: `/release-notes`

SEO title:

> LocalRAG release notes и качество релизов

Meta description:

> Следите за версиями LocalRAG, runtime defaults, изменениями retrieval,
> поддержкой моделей и release quality checks.

### Hero

H1:

> Изменения продукта должны быть проверяемыми.

Body:

> Release notes фиксируют версию, runtime defaults, изменения retrieval,
> поддержку моделей, миграции, тесты и известные ограничения.

CTA:

> Смотреть текущий релиз

Status: `[READY]`

### Current release module

Fields:

- `Версия` - `v0.9.0` `[VERIFY]`
- `Default answer model` - `qwen3.5:9b` `[VERIFY]`
- `Embedding model` - `intfloat/multilingual-e5-large` `[VERIFY]`
- `App URL` - `http://localhost:7860` `[READY]`
- `API docs` - `http://localhost:7860/docs` `[READY]`

Note:

> Перед публикацией сверить значения с `VERSION`, README и release notes.

## Feature Landing Page Drafts

These drafts support future split pages from the SEO brief. They should not all
block the first landing page release.

### `/features/private-document-qa`

H1:

> Вопросы по приватным документам без обязательного upload-сценария.

Body:

> LocalRAG работает с локальной папкой, строит индекс и отвечает по найденному
> контексту. Это удобно для PDF, заметок, таблиц, кода и смешанных рабочих
> материалов, которые не хочется отправлять в hosted AI по умолчанию.

CTA:

> Запустить локально

Limit copy:

> Приватность зависит от вашей конфигурации и выбранных сервисов.

Status: `[READY]`

### `/features/ollama-rag`

H1:

> RAG на Ollama, который можно проверить в интерфейсе.

Body:

> Выбирайте локальную модель ответа, управляйте моделями через UI, используйте
> FAISS-индекс и multilingual embeddings для вопросов по собственным файлам.

CTA:

> Настроить модель

Status: `[READY]`

### `/features/pdf-ocr-rag`

H1:

> Вопросы по PDF и сканам с осторожной проверкой источников.

Body:

> LocalRAG рассчитан на реальные PDF-папки, где встречаются страницы, сканы,
> OCR-шум и смешанные языки. Проверяйте найденные фрагменты и учитывайте, что
> качество зависит от разбора документа и OCR.

CTA:

> Проверить PDF-папку

Status: `[READY]`

### `/features/source-citations`

H1:

> Источники рядом с ответом.

Body:

> Ответ LocalRAG сопровождается retrieved context: путями к файлам, страницами
> и строками там, где эти метаданные доступны. Это помогает понять, на чем
> основана генерация.

CTA:

> Проверить источники

Status: `[READY]`

### `/features/multilingual-rag`

H1:

> Многоязычный интерфейс и отдельный язык ответа.

Body:

> LocalRAG поддерживает интерфейс на EN/RU/NL/ZH/HE и позволяет отдельно
> выбрать язык ответа. Это полезно для смешанных корпусов, но не отменяет
> зависимость от модели, embeddings и качества найденного контекста.

CTA:

> Настроить язык ответа

Status: `[READY]`

### `/features/response-roles`

H1:

> Роли ответа для разных рабочих задач.

Body:

> Analyst, Engineer, Archivist и пользовательские роли помогают менять стиль,
> формат и приоритеты ответа без ручного переписывания prompt каждый раз.

CTA:

> Выбрать роль

Status: `[READY]`

## Alternative Headline Set

Homepage:

1. `Локальный ИИ-поиск по приватным документам.`
2. `LocalRAG отвечает по вашим файлам и показывает источники.`
3. `RAG на Ollama для локальных папок, PDF и кода.`
4. `Задавайте вопросы по документам без обязательного облачного upload.`

Feature overview:

1. `Возможности LocalRAG, которые можно проверить.`
2. `Локальный RAG: файлы, модели, источники и качество.`
3. `Не только чат: индекс, retrieval, роли и eval.`

Getting started:

1. `Запустите LocalRAG и задайте первый вопрос.`
2. `От Docker Compose до ответа по документам.`
3. `Первый локальный RAG-сценарий без лишней настройки.`

Quality:

1. `Качество retrieval должно быть измеримым.`
2. `Проверяйте не только запуск сервера, но и ответы.`
3. `Eval и source hit ratio для локального RAG.`

For teams:

1. `От локальной папки к управляемому внедрению.`
2. `Командный RAG требует явных границ данных.`
3. `Обсудите источники, доступы и критерии качества.`

## Alternative CTA Set

Install/action CTAs:

- `Запустить локально`
- `Склонировать репозиторий`
- `Открыть инструкцию запуска`
- `Запустить Docker Compose`

Product proof CTAs:

- `Посмотреть интерфейс`
- `Открыть найденные источники`
- `Сравнить ответы моделей`
- `Проверить retrieval flow`

Quality CTAs:

- `Запустить eval`
- `Проверить release gate`
- `Открыть test suite`
- `Сверить source hit ratio`

Commercial CTAs:

- `Обсудить внедрение` `[APPROVAL REQUIRED]`
- `Описать корпоративный сценарий` `[APPROVAL REQUIRED]`
- `Согласовать пилот` `[APPROVAL REQUIRED]`

## Approval Queue

| Copy or claim | Reason approval is needed | Owner/action |
| --- | --- | --- |
| `Обсудить внедрение`, `/for-teams`, lead form copy | Commercial promise and support scope | Product/business owner approval |
| Corporate connectors, file shares, object storage, knowledge bases, SQL sources | May be planned or custom rather than shipped | Verify implemented connectors or mark custom scope |
| Access control, monitoring, governance, production support | Can imply enterprise readiness | Confirm deployment architecture and support terms |
| Any rating, review count, logo, testimonial, or user count | Social proof must be sourced and permitted | Provide evidence or remove |
| Free/community/commercial pricing language | Legal and licensing boundaries can change | Confirm license and commercial-use terms |
| Strong privacy/security wording | High-stakes claim depends on configuration | Keep default-local wording and review externally if needed |
| OCR-ready/scanned PDF claims | Quality varies by OCR and source quality | Use limitation copy and show tested examples |
| Screenshots as current product proof | UI can drift | Refresh screenshots and date/version captions |
| Exact release defaults | Version/model values can drift | Check `VERSION`, README, `.env.example`, and release notes |

## Definition of Done Coverage

- [x] Draft copy by page and section.
- [x] Alternative CTA and headline variants.
- [x] Content requiring approval marked with `[APPROVAL REQUIRED]`,
  `[VERIFY]`, or `[CUSTOM SCOPE]`.
- [x] Output stored as a versioned project artifact in the repository.
