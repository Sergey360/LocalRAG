#!/usr/bin/env python3
"""Create a public release archive for LocalRAG from a git ref."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DIST_DIR = ROOT_DIR / "dist"
VERSION_FILE = ROOT_DIR / "VERSION"
PUBLIC_MIRROR_IGNORE_FILE = ROOT_DIR / ".public-mirrorignore"
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
    parser = argparse.ArgumentParser(description="Package LocalRAG into a public release zip archive")
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=DEFAULT_DIST_DIR,
        help="Output directory for release artifacts",
    )
    parser.add_argument(
        "--source-ref",
        default="HEAD",
        help="Git ref to package, for example HEAD, origin/main, or v0.9.0",
    )
    return parser.parse_args()


def read_public_mirror_excludes() -> set[str]:
    if not PUBLIC_MIRROR_IGNORE_FILE.exists():
        return set()

    excludes: set[str] = set()
    for raw_line in PUBLIC_MIRROR_IGNORE_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        excludes.add(line.rstrip("/"))
    return excludes


def should_exclude_relative(relative: Path, public_excludes: set[str]) -> bool:
    normalized = relative.as_posix()
    if any(part in EXCLUDE_DIR_NAMES for part in relative.parts):
        return True
    if relative.name in EXCLUDE_FILE_NAMES:
        return True
    if relative.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    for exclude in public_excludes:
        if normalized == exclude or normalized.startswith(f"{exclude}/"):
            return True
    return False


def git_sha(source_ref: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", source_ref],
            cwd=ROOT_DIR,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:  # noqa: BLE001
        return None


def git_dirty(source_ref: str) -> bool:
    if source_ref != "HEAD":
        return False
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


def build_manifest(
    version: str,
    archive_name: str,
    archive_sha256: str,
    files_added: list[str],
    source_ref: str,
) -> dict[str, object]:
    return {
        "name": "LocalRAG",
        "version": version,
        "archive": archive_name,
        "sha256": archive_sha256,
        "git_sha": git_sha(source_ref),
        "git_dirty": git_dirty(source_ref),
        "source_ref": source_ref,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": files_added,
    }


def create_release_archive(archive_path: Path, source_ref: str, public_excludes: set[str]) -> list[str]:
    files_added: list[str] = []
    temp_archive_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as handle:
            temp_archive_path = Path(handle.name)

        subprocess.run(
            ["git", "archive", "--format=zip", f"--output={temp_archive_path}", source_ref],
            cwd=ROOT_DIR,
            check=True,
        )

        with ZipFile(temp_archive_path, "r") as source_zip, ZipFile(
            archive_path,
            "w",
            compression=ZIP_DEFLATED,
        ) as release_zip:
            for member in sorted(source_zip.infolist(), key=lambda item: item.filename):
                if member.is_dir():
                    continue
                relative = Path(member.filename)
                if should_exclude_relative(relative, public_excludes):
                    continue
                release_zip.writestr(member.filename, source_zip.read(member.filename))
                files_added.append(member.filename)
    finally:
        if temp_archive_path is not None and temp_archive_path.exists():
            temp_archive_path.unlink()

    return files_added


def main() -> int:
    args = parse_args()
    source_ref = args.source_ref
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    dist_dir = args.dist_dir.resolve()
    dist_dir.mkdir(parents=True, exist_ok=True)
    public_excludes = read_public_mirror_excludes()

    archive_name = f"LocalRAG-v{version}.zip"
    archive_path = dist_dir / archive_name
    files_added = create_release_archive(archive_path, source_ref, public_excludes)

    archive_sha256 = sha256_file(archive_path)
    sha_path = dist_dir / f"{archive_name}.sha256"
    sha_path.write_text(f"{archive_sha256}  {archive_name}\n", encoding="utf-8")

    manifest = build_manifest(version, archive_name, archive_sha256, files_added, source_ref)
    manifest_path = dist_dir / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write(payload.encode("utf-8", errors="replace"))
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
