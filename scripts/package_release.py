#!/usr/bin/env python3
"""Create a release archive for LocalRAG."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DIST_DIR = ROOT_DIR / "dist"
VERSION_FILE = ROOT_DIR / "VERSION"
EXCLUDE_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    ".vscode",
    "__pycache__",
    "venv",
    "temp",
    "hf_cache",
    "dist",
    "vectorstore",
}
EXCLUDE_FILE_NAMES = {".env"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".log"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package LocalRAG into a release zip archive")
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=DEFAULT_DIST_DIR,
        help="Output directory for release artifacts",
    )
    return parser.parse_args()


def should_exclude(path: Path) -> bool:
    relative = path.relative_to(ROOT_DIR)
    if any(part in EXCLUDE_DIR_NAMES for part in relative.parts):
        return True
    if path.name in EXCLUDE_FILE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    return False


def git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT_DIR,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:  # noqa: BLE001
        return None


def git_dirty() -> bool:
    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=ROOT_DIR,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return bool(status.strip())
    except Exception:  # noqa: BLE001
        return True


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    dist_dir = args.dist_dir.resolve()
    dist_dir.mkdir(parents=True, exist_ok=True)

    archive_name = f"LocalRAG-v{version}.zip"
    archive_path = dist_dir / archive_name

    files_added: list[str] = []
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
            current_dir = Path(dirpath)
            relative_dir = current_dir.relative_to(ROOT_DIR)
            dirnames[:] = [
                name
                for name in dirnames
                if name not in EXCLUDE_DIR_NAMES
                and not any(part in EXCLUDE_DIR_NAMES for part in (relative_dir / name).parts)
            ]
            for filename in sorted(filenames):
                path = current_dir / filename
                if should_exclude(path):
                    continue
                relative = path.relative_to(ROOT_DIR)
                zf.write(path, arcname=str(relative))
                files_added.append(str(relative).replace("\\", "/"))

    archive_sha256 = sha256_file(archive_path)
    sha_path = dist_dir / f"{archive_name}.sha256"
    sha_path.write_text(f"{archive_sha256}  {archive_name}\n", encoding="utf-8")

    manifest = {
        "name": "LocalRAG",
        "version": version,
        "archive": archive_name,
        "sha256": archive_sha256,
        "git_sha": git_sha(),
        "git_dirty": git_dirty(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": files_added,
    }
    manifest_path = dist_dir / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write(payload.encode("utf-8", errors="replace"))
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
