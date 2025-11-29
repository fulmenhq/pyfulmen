#!/usr/bin/env python3
"""Utility helpers to manage the prepublish sentinel file."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def _load_version_file(path: Path = Path("VERSION")) -> str:
    try:
        return path.read_text().strip()
    except FileNotFoundError as exc:  # pragma: no cover - VERSION should exist
        raise SystemExit("VERSION file missing") from exc


def write_sentinel(path: Path, version: str | None) -> None:
    if version is None:
        version = _load_version_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": version, "timestamp": time.time()}
    path.write_text(json.dumps(payload, indent=2))
    print(f"✓ Recorded prepublish sentinel at {path} for v{version}")


def verify_sentinel(path: Path) -> None:
    if not path.exists():
        raise SystemExit("❌ Prepublish sentinel not found")
    data = json.loads(path.read_text())
    sentinel_version = data.get("version")
    version_file = _load_version_file()
    if sentinel_version != version_file:
        raise SystemExit(
            f"❌ Prepublish sentinel version {sentinel_version} does not match VERSION {version_file}"
        )
    print(f"✓ Prepublish sentinel verified for v{version_file}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["write", "verify"], help="Operation to perform"
    )
    parser.add_argument("--sentinel", required=True, help="Path to sentinel file")
    parser.add_argument(
        "--version", help="Explicit version when writing (defaults to VERSION file)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sentinel = Path(args.sentinel)
    if args.action == "write":
        write_sentinel(sentinel, args.version)
    else:
        verify_sentinel(sentinel)


if __name__ == "__main__":
    main()
