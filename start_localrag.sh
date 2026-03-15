#!/bin/bash
# LocalRAG start script for Linux/Mac

if ! command -v docker &> /dev/null; then
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

cd "$(dirname "$0")"

compose_args=(-f docker-compose.yml)
mode="release"
if [[ "${1:-}" == "dev" ]]; then
    compose_args+=(-f docker-compose.dev.yml)
    mode="development"
fi

if grep -qi microsoft /proc/version 2>/dev/null || [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    export HOST_FS_ROOT="${HOST_FS_ROOT:-/mnt/c}"
    export HOST_DOCS_PATH="${HOST_DOCS_PATH:-/mnt/c/Temp/PDF}"
    export DOCS_PATH="${DOCS_PATH:-/hostfs/c/Temp/PDF}"
fi

echo "Starting LocalRAG in ${mode} mode..."
read -r -p "Rebuild image? (y/N): " build
if [[ "$build" =~ ^[Yy]$ ]]; then
    docker compose "${compose_args[@]}" up -d --build
else
    docker compose "${compose_args[@]}" up -d
fi

echo "LocalRAG UI: http://localhost:7860"
echo "Use ./start_localrag.sh dev for development mode."
