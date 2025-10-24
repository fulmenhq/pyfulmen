#!/usr/bin/env python3
"""
Validate Pathfinder checksum fixtures.

Recomputes checksums for sample files and compares against the manifest
in tests/fixtures/pathfinder/checksum-fixtures.yaml.

Useful for:
- Verifying fixture integrity after git operations
- Cross-language validation (gofulmen/tsfulmen teams can run this)
- CI/CD validation
"""

import sys
from pathlib import Path

import yaml

from pyfulmen.fulhash import Algorithm, hash_file


def main():
    """Validate all sample files against fixture manifest."""
    # Paths
    repo_root = Path(__file__).parent.parent
    fixtures_yaml = (
        repo_root / "tests" / "fixtures" / "pathfinder" / "checksum-fixtures.yaml"
    )
    sample_files_dir = repo_root / "tests" / "fixtures" / "pathfinder" / "sample-files"

    # Load fixture manifest
    with open(fixtures_yaml) as f:
        manifest = yaml.safe_load(f)

    print("=" * 70)
    print("Pathfinder Fixture Validation")
    print("=" * 70)
    print(f"\nManifest: {fixtures_yaml.relative_to(repo_root)}")
    print(f"Sample files: {sample_files_dir.relative_to(repo_root)}")

    # Validate each file fixture
    file_fixtures = manifest.get("file_fixtures", [])
    errors = []
    validated = 0

    print(f"\n{'File':<25} {'Algorithm':<10} {'Status'}")
    print("-" * 70)

    # Map fixture names to actual files
    fixture_file_map = {
        "empty-file": "empty.txt",
        "hello-world-txt": "hello-world.txt",
        "single-char-txt": "single-char.txt",
        "unicode-emoji-txt": "unicode-emoji.txt",
    }

    for fixture in file_fixtures:
        name = fixture["name"]

        # Skip fixtures without corresponding sample files
        if name not in fixture_file_map:
            continue

        filename = fixture_file_map[name]
        filepath = sample_files_dir / filename

        if not filepath.exists():
            errors.append(f"Missing file: {filename}")
            print(f"{filename:<25} {'N/A':<10} ✗ MISSING")
            continue

        # Validate both algorithms
        for algo_key, algo_enum in [
            ("xxh3_128", Algorithm.XXH3_128),
            ("sha256", Algorithm.SHA256),
        ]:
            expected = fixture["checksums"][algo_key]
            actual_digest = hash_file(filepath, algo_enum)
            actual = actual_digest.formatted

            if actual == expected:
                print(f"{filename:<25} {algo_enum.value:<10} ✓ PASS")
                validated += 1
            else:
                errors.append(
                    f"{filename} ({algo_enum.value}): expected {expected}, got {actual}"
                )
                print(f"{filename:<25} {algo_enum.value:<10} ✗ FAIL")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Validated: {validated}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✅ All fixtures valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
