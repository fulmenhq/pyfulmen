#!/usr/bin/env python3
"""Validate built distribution artifacts before publishing.

This script inspects the contents of wheels and source distributions in
``dist/`` to ensure critical files are present (package roots, ``py.typed``,
README, LICENSE) so we catch packaging regressions before publishing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import json
import tarfile
import zipfile

DIST_DIR = Path("dist")
REQUIRED_FILES = ["pyfulmen/__init__.py", "pyfulmen/py.typed"]
ANCILLARY_FILES = ["README.md", "LICENSE"]


@dataclass
class ArtifactReport:
    name: str
    kind: str
    missing: list[str]

    @property
    def ok(self) -> bool:
        return not self.missing


def _ensure_dist_dir() -> None:
    if not DIST_DIR.exists():
        raise SystemExit(
            "❌ dist/ directory not found. Run 'make release-build' first."
        )


def _find_artifacts(suffix: str) -> list[Path]:
    return sorted(DIST_DIR.glob(f"*{suffix}"))


def _contains_any(members: list[str], needle: str) -> bool:
    return any(member.endswith(needle) for member in members)


def _inspect_wheel(path: Path) -> ArtifactReport:
    missing: list[str] = []
    with zipfile.ZipFile(path) as zf:
        members = zf.namelist()
    for required in REQUIRED_FILES + ANCILLARY_FILES:
        if not _contains_any(members, required):
            missing.append(required)
    return ArtifactReport(path.name, "wheel", missing)


def _inspect_sdist(path: Path) -> ArtifactReport:
    missing: list[str] = []
    with tarfile.open(path, "r:gz") as tf:
        members = [member.name for member in tf.getmembers()]
    for required in REQUIRED_FILES + ANCILLARY_FILES:
        if not _contains_any(members, required):
            missing.append(required)
    return ArtifactReport(path.name, "sdist", missing)


def run(validation_mode: str = "full") -> int:
    _ensure_dist_dir()
    wheels = _find_artifacts(".whl")
    sdists = _find_artifacts(".tar.gz")

    if not wheels:
        print("❌ No wheel artifacts found in dist/. Run 'make release-build'.")
        return 1
    if not sdists:
        print("❌ No source distributions (tar.gz) found in dist/.")
        return 1

    reports: list[ArtifactReport] = []
    for wheel in wheels:
        reports.append(_inspect_wheel(wheel))
    for sdist in sdists:
        reports.append(_inspect_sdist(sdist))

    summary = {
        "artifacts": [report.__dict__ for report in reports],
        "status": "ok" if all(report.ok for report in reports) else "failed",
    }

    print(json.dumps(summary, indent=2))
    if summary["status"] != "ok":
        print("❌ Distribution validation failed")
        for report in reports:
            if report.missing:
                print(f"  - {report.name} missing: {', '.join(report.missing)}")
        return 1

    print("✅ Distribution contents valid")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        default="full",
        help="Reserved for future toggles (currently unused)",
    )
    args = parser.parse_args()
    raise SystemExit(run(args.mode))


if __name__ == "__main__":
    main()
