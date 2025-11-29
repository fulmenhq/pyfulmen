#!/usr/bin/env python3
"""Install freshly built artifacts into an isolated prefix and import them.

This script is uv-first: by default it uses ``uv pip install`` to install the
wheel from ``dist/`` into a temporary directory, then imports key modules to
ensure the package behaves correctly once installed. A secondary "pip"
installer mode runs ``python -m pip`` (still under ``uv run``) to provide
compatibility coverage without depending on system Python outside uv.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import importlib
import json
import subprocess
import sys
import tempfile
import textwrap

DIST_DIR = Path("dist")
DEFAULT_IMPORTS = [
    "pyfulmen",
    "pyfulmen.logging",
    "pyfulmen.fulpack",
    "pyfulmen.error_handling",
]


def _latest_wheel() -> Path:
    wheels = sorted(
        DIST_DIR.glob("*.whl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not wheels:
        raise SystemExit(
            "❌ No wheel artifacts in dist/. Run 'make release-build' first."
        )
    return wheels[0]


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _install(installer: str, wheel: Path, target: Path) -> None:
    if installer == "uv":
        _run(["uv", "pip", "install", "--quiet", "--target", str(target), str(wheel)])
    elif installer == "pip":
        _run(
            [
                "uv",
                "tool",
                "run",
                "pip",
                "install",
                "--quiet",
                "--target",
                str(target),
                str(wheel),
            ]
        )
    else:
        raise SystemExit(f"Unknown installer '{installer}'")


def _import_modules(target: Path) -> dict[str, str]:
    sys.path.insert(0, str(target))
    results: dict[str, str] = {}
    for module in DEFAULT_IMPORTS:
        try:
            importlib.import_module(module)
            results[module] = "ok"
        except Exception as exc:  # noqa: BLE001 - want to show exact failure
            results[module] = f"failed: {exc}"
    sys.path.pop(0)
    return results


def verify(installer: str) -> int:
    wheel = _latest_wheel()
    with tempfile.TemporaryDirectory(prefix="pyfulmen-install-") as tmp:
        target = Path(tmp)
        _install(installer, wheel, target)
        results = _import_modules(target)

    failures = {mod: status for mod, status in results.items() if status != "ok"}
    payload = {
        "installer": installer,
        "wheel": wheel.name,
        "results": results,
    }
    print(json.dumps(payload, indent=2))
    if failures:
        print("❌ Local install verification failed:")
        for mod, status in failures.items():
            print(f"  - {mod}: {status}")
        return 1

    print(
        textwrap.dedent(
            f"""\
            ✅ Local install verification succeeded using '{installer}'.
            Wheel: {wheel.name}
            """
        ).strip()
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--installer",
        choices=["uv", "pip"],
        default="uv",
        help="Installer backend. 'uv' (default) uses 'uv pip', 'pip' uses 'uv tool run pip'.",
    )
    args = parser.parse_args()
    raise SystemExit(verify(args.installer))


if __name__ == "__main__":
    main()
