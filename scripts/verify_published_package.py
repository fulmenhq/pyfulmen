#!/usr/bin/env python3
"""Install PyFulmen from a registry and run smoke tests."""

from __future__ import annotations

from pathlib import Path
import argparse
import importlib
import json
import subprocess
import sys
import tempfile

DEFAULT_IMPORTS = [
    "pyfulmen",
    "pyfulmen.logging",
    "pyfulmen.fulpack",
]


def _read_version() -> str:
    try:
        return Path("VERSION").read_text().strip()
    except FileNotFoundError as exc:  # pragma: no cover - VERSION always exists
        raise SystemExit("VERSION file missing") from exc


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _install(
    package: str,
    version: str,
    index_url: str,
    extra_index_url: str | None,
    target: Path,
) -> None:
    spec = f"{package}=={version}"
    cmd = ["uv", "pip", "install", "--quiet", "--target", str(target), spec]
    if index_url:
        cmd.extend(["--index-url", index_url])
    if extra_index_url:
        cmd.extend(["--extra-index-url", extra_index_url])
    _run(cmd)


def _import_modules(target: Path) -> dict[str, str]:
    sys.path.insert(0, str(target))
    results: dict[str, str] = {}
    for module in DEFAULT_IMPORTS:
        try:
            importlib.import_module(module)
            results[module] = "ok"
        except Exception as exc:  # noqa: BLE001 - we want exact failure
            results[module] = f"failed: {exc}"
    sys.path.pop(0)
    return results


def verify(
    package: str, version: str, index_url: str, extra_index_url: str | None
) -> int:
    with tempfile.TemporaryDirectory(prefix="pyfulmen-published-") as tmp:
        target = Path(tmp)
        _install(package, version, index_url, extra_index_url, target)
        results = _import_modules(target)

        sys.path.insert(0, str(target))
        pkg = importlib.import_module(package)
        reported = getattr(pkg, "__version__", None)
        sys.path.pop(0)

    failures = {mod: status for mod, status in results.items() if status != "ok"}
    payload = {
        "package": package,
        "version": version,
        "index_url": index_url,
        "results": results,
        "reported_version": reported,
    }
    print(json.dumps(payload, indent=2))

    if failures:
        print("❌ Published package verification failed")
        for mod, status in failures.items():
            print(f"  - {mod}: {status}")
        return 1

    if reported and reported != version:
        print(f"❌ Version mismatch: expected {version}, package reports {reported}")
        return 1

    print("✅ Published package verification succeeded")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", default="pyfulmen", help="Package name to verify")
    parser.add_argument(
        "--version", default=None, help="Version to install (defaults to VERSION file)"
    )
    parser.add_argument(
        "--index-url", default="https://pypi.org/simple", help="Registry index URL"
    )
    parser.add_argument(
        "--extra-index-url", default=None, help="Optional secondary index URL"
    )
    args = parser.parse_args()
    version = args.version or _read_version()
    raise SystemExit(
        verify(args.package, version, args.index_url, args.extra_index_url)
    )


if __name__ == "__main__":
    main()
