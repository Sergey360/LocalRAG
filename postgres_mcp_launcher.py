#!/usr/bin/env python3
"""
Helper script to launch the Postgres MCP server using connection profiles
defined in an INI-style configuration file (default: notebook.cfg).
"""
from __future__ import annotations

import argparse
import configparser
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable
from urllib.parse import quote_plus


REQUIRED_KEYS = ("db_host", "db_port", "db_user", "db_passwd", "db_db")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch postgres-mcp against a database profile from notebook.cfg",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default="notebook.cfg",
        help="Path to the INI file with database sections",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Name of the section to use (case-sensitive)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available database profiles and exit",
    )
    parser.add_argument(
        "--command",
        default="postgres-mcp",
        help="Command used to launch the MCP server",
    )
    parser.add_argument(
        "--access-mode",
        choices=("unrestricted", "restricted"),
        default="unrestricted",
        help="Access mode flag passed to postgres-mcp",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse"),
        default="stdio",
        help="Transport flag passed to postgres-mcp",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command that would be executed and exit",
    )
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments forwarded to postgres-mcp after '--'",
    )
    return parser.parse_args(list(argv))


def load_profiles(config_path: Path) -> Dict[str, configparser.SectionProxy]:
    parser = configparser.ConfigParser()
    read_files = parser.read(config_path, encoding="utf-8")
    if not read_files:
        raise FileNotFoundError(f"Config file not found: {config_path}")

    profiles: Dict[str, configparser.SectionProxy] = {}
    for section in parser.sections():
        section_data = parser[section]
        if all(key in section_data for key in REQUIRED_KEYS):
            profiles[section] = section_data
    return profiles


def build_database_uri(profile: configparser.SectionProxy) -> str:
    user = quote_plus(profile["db_user"])
    password = quote_plus(profile["db_passwd"])
    host = profile["db_host"]
    port = profile.get("db_port", "5432")
    database = profile["db_db"]
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    config_path = Path(args.config).expanduser().resolve()
    profiles = load_profiles(config_path)

    if not profiles:
        print(
            f"No profiles with required keys {REQUIRED_KEYS} found in {config_path}",
            file=sys.stderr,
        )
        return 1

    if args.list:
        print("Available profiles:")
        for name in sorted(profiles):
            section = profiles[name]
            host = section.get("db_host", "unknown")
            db_name = section.get("db_db", "unknown")
            print(f"  {name} -> {host}/{db_name}")
        return 0

    profile_name = args.profile or next(iter(profiles))
    if profile_name not in profiles:
        available = ", ".join(sorted(profiles))
        print(
            f"Profile '{profile_name}' not found. Available profiles: {available}",
            file=sys.stderr,
        )
        return 1

    database_uri = build_database_uri(profiles[profile_name])

    env = os.environ.copy()
    env["DATABASE_URI"] = database_uri

    command = [
        args.command,
        f"--access-mode={args.access_mode}",
        f"--transport={args.transport}",
    ]

    extra = [arg for arg in args.extra_args if arg != "--"]
    command.extend(extra)

    if args.dry_run:
        env_preview = {k: v for k, v in env.items() if k == "DATABASE_URI"}
        print("Environment variables:")
        for key, value in env_preview.items():
            print(f"  {key}={value}")
        print("Command:")
        print("  " + " ".join(shlex.quote(part) for part in command))
        return 0

    try:
        completed = subprocess.run(command, env=env, check=False)
    except FileNotFoundError as exc:
        print(
            f"Failed to start MCP. Command '{args.command}' not found: {exc}",
            file=sys.stderr,
        )
        return 1

    return completed.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
