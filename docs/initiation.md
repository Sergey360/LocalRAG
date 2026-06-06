# LocalRAG Initiation Confirmation

This document records the Stage 01 initiation confirmation for the `localrag`
project.

## Project Profile

| Item | Confirmation |
| --- | --- |
| Project | `localrag` |
| Stage | `init` |
| Milestone | `SDLC Stage 01: Initiation` |
| Primary GitLab project | `https://lab.it360.ru/myprojects/localrag` |
| Repository topology | `mono` |
| Additional repositories | `0` |
| Delivery model | `public` |

## Repository Topology

The initialized project skeleton is a single repository containing:

- FastAPI application code in `main.py`, `app/`, and `web/`.
- Runtime and delivery configuration in `Dockerfile`, `docker-compose.yml`,
  `docker-compose.dev.yml`, `.env.example`, and `.gitlab-ci.yml`.
- Release and quality automation in `scripts/`, `pytest.ini`, `eval/`, and
  `tests/`.
- Public-facing project documentation and localized READMEs in the repository
  root.

No additional repositories are required for the current initiation stage.

## Delivery Model

The delivery model is confirmed as public. The repository contains public mirror
automation and a public release packaging path:

- `.public-mirrorignore` defines files omitted from the public mirror.
- `scripts/publish_github_snapshot.sh` publishes a sanitized public snapshot.
- `scripts/package_release.py` creates public release archives.
- `RELEASE.md` documents the release checks and public GitHub publish workflow.

## Workspace Confirmation

| Workspace | Path | Status |
| --- | --- | --- |
| Target local workspace | `C:\Sergey\Lab360\localrag` | Confirmed as the required Windows workspace target. |
| Active GitLab worker checkout | `/home/devops/workspace/gitlab/.codex-worker-runs/myprojects_localrag/issue-2-1-20260606T093920Z` | Verified during issue execution. |

The current execution worker is Linux-based and does not have `/mnt/c` mounted,
so it cannot physically create or inspect `C:\Sergey\Lab360\localrag` as a
Windows filesystem path. That path remains the confirmed local Windows workspace
target for this project.

## Execution Model

Standard execution path is confirmed. The issue was handled on the GitLab worker
checkout for branch `codex/issue-2`; no Chrome MCP or NAS-only UI validation was
required because the issue labels do not include `cap::chrome-mcp` and
`exec::nas`.
