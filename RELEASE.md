# LocalRAG Release Notes

## Target version

`0.9.0`

## What is release-ready in this revision

- Base Docker stack is production-like and no longer bind-mounts source code.
- Development hot-reload moved to `docker-compose.dev.yml`.
- Default answer model aligned to `qwen3.5:9b`.
- App exposes runtime metadata via `GET /api/meta`.
- App exposes JSON liveness endpoint via `GET /api/health`.
- GitLab CI syntax-checks entrypoints before running tests.
- Root start scripts are release-first and tested on Windows and WSL.

## Release smoke checklist

1. `pytest -q`
2. Start the stack with release defaults, not a developer-specific `.env` override
3. Verify `GET /api/health`
4. Verify `GET /api/meta` reports `default_model=qwen3.5:9b`
5. Open the UI and ask `Куда поехал Айболит?`
6. Verify the answer starts with `Айболит поехал в Африку.`
7. Switch answer role and verify the response updates
8. Open settings and verify model manager responds
9. Run the extended eval set and require a full pass for the release candidate

Automated smoke:

```sh
python scripts/release_check.py --base-url http://localhost:7860
```

Extended quality gate:

```sh
python scripts/model_eval.py --base-url http://localhost:7860 --seed-file eval/rag_eval_extended.json --models qwen3.5:9b --output temp/extended_eval.json
python scripts/assert_eval_gate.py --report temp/extended_eval.json --model qwen3.5:9b --min-strict 1.0 --min-loose 1.0 --min-hit-ratio 1.0
```

GitLab manual quality gate:

- Job: `quality_gate_live`
- Required variable: `LOCALRAG_EVAL_BASE_URL`
- Expected target: a running LocalRAG instance with the release candidate build

## Release smoke without local overrides

If a local `.env` file exists, it overrides runtime defaults for model and documents path.
For release validation, start the stack with release defaults or an isolated environment.

Example:

```sh
docker compose --env-file .env.example up --build -d
```

## Release packaging

Create a release archive with checksum and manifest:

```sh
python scripts/package_release.py
```

Artifacts are written to `dist/`:

- `LocalRAG-v<version>.zip`
- `LocalRAG-v<version>.zip.sha256`
- `release-manifest.json`

## Development start

```sh
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Production-like start

```sh
docker compose up --build -d
```

Release-first start scripts are also valid and tested:

```powershell
.\start_localrag.bat
```

```bash
./start_localrag.sh
```

## GitHub publish from GitLab CI

The public GitHub repository should receive a squashed publish from GitLab `main`, not the full development history from `dev`.

Required GitLab CI variable:

- `GITHUB_PUSH_TOKEN`

Optional GitLab CI variables:

- `GITHUB_PUSH_REPO` default: `https://github.com/Sergey360/LocalRAG.git`
- `GITHUB_PUBLISH_BRANCH` default: `main`
- `GITHUB_PUBLISH_GIT_NAME` default: `GitLab CI`
- `GITHUB_PUBLISH_GIT_EMAIL` default: `gitlab-ci@example.invalid`
- `PUBLIC_MIRROR_IGNORE_FILE` default: `.public-mirrorignore`

Jobs:

- `github_publish_main` publishes the current `main` snapshot to GitHub as a single squashed commit
- `github_publish_tag` republishes the tagged snapshot and creates the same tag in GitHub

By default the public mirror excludes GitLab-specific files listed in `.public-mirrorignore`.
