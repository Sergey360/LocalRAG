@echo off
REM LocalRAG start script for Windows

where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo Please install Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b
)

cd /d %~dp0

set "COMPOSE_ARGS=-f docker-compose.yml"
set "MODE=release"
if /i "%~1"=="dev" (
    set "COMPOSE_ARGS=-f docker-compose.yml -f docker-compose.dev.yml"
    set "MODE=development"
)

echo Starting LocalRAG in %MODE% mode...
set /p build="Rebuild image? (y/N): "
if /i "%build%"=="y" (
    docker compose %COMPOSE_ARGS% up -d --build
) else (
    docker compose %COMPOSE_ARGS% up -d
)
echo LocalRAG UI: http://localhost:7860
echo Use "start_localrag.bat dev" for development mode.
pause
