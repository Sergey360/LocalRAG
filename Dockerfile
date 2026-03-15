# syntax=docker/dockerfile:1.7
# Production-ready Dockerfile for LocalRAG (FastAPI + Uvicorn)
FROM python:3.13-slim

WORKDIR /app

# System deps
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY app/requirements.txt ./requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy app, web, locales
COPY main.py ./main.py
COPY VERSION ./VERSION
COPY app/ ./app/
COPY web/ ./web/

# Copy entrypoint
COPY start_localrag.sh ./start_localrag.sh
RUN chmod +x ./start_localrag.sh

# Expose port
EXPOSE 7860

# Healthcheck (simple HTTP GET)
HEALTHCHECK CMD curl --fail http://localhost:7860/api/status || exit 1

# Entrypoint
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
