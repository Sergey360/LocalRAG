# 🦙 LocalRAG — локальный RAG по PDF и другим документам

**LocalRAG** — это автономная система Retrieval-Augmented Generation (RAG), которая работает полностью локально на собственном ПК. Объединяет использование [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm), [Ollama](https://ollama.com), и небольшой Watcher, который автоматически переиндексирует документы при изменениях.

## 🚀 Возможности

- 📁 Работа с большими PDF, DOCX, TXT, HTML, Markdown.
- 🔁 Автоматическое обновление индекса при добавлении или удалении файлов.
- 🧠 Локальный запуск LLM (по умолчанию `nous-hermes2-mistral`).
- 📖 Хорошая поддержка русского языка.
- 🔒 Полностью оффлайн — никакие данные не покидают вашу машину.
- 🧩 Расширяемость под любые источники данных и модели.

## ⚙️ Быстрый старт

1. Установить Docker или Docker Desktop: https://www.docker.com/products/docker-desktop
2. Склонировать репозиторий и перейти в папку проекта:

   "git clone https://github.com/Sergey360/LocalRAG.git"
   "cd LocalRAG"

3. Отредактировать `.env`:
    ```
    PDF_PATH=C:/Temp/PDF
    OLLAMA_MODEL=nous-hermes2-mistral
    WORKSPACE_ID=1
    ```

4. Убедитесь, что папка PDF_PATH (`C:/Temp/PDF`) содержит документы.
5. Запускаем!

   "docker compose up -d"

6. Открыть в браузере:

   "http://localhost:3001"

7. Создай workspace в интерфейсе AnythingLLM и добавить файлы.

## 🧩 Компоненты

| Компонент     | Назначение                           |
| ------------- | ------------------------------------ |
| `ollama`      | Запускает LLM локально               |
| `anythingllm` | Интерфейс + RAG + векторизация       |
| `rag-watcher` | Следит за папкой и обновляет индексы |

## ⚠️ Примечания

- Docker должен иметь доступ к `C:/Temp/PDF` (см. Docker → Settings → Resources → File Sharing).
- Модель подтянется автоматически при первом запуске (может занять ~10 минут).
- Индексация работает с Workspace ID, указанным в `.env`.

## 🧠 Автор

©️ **[Sergey360](https://github.com/Sergey360/LocalRAG), [LocalRAG](https://github.com/Sergey360) 2025**
