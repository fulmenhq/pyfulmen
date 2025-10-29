#!/usr/bin/env python3
"""
Validate SSOT provenance before pushing.

This script ensures that PyFulmen is not pushed when Crucible
(or other SSOT sources) have uncommitted changes (dirty state).

Exit codes:
  0 - All sources clean
  1 - One or more sources dirty
  2 - Provenance file missing or invalid
"""

import json
import sys
from pathlib import Path


def validate_provenance() -> int:
    """
    Validate SSOT provenance.

    Returns:
        0 if all sources clean, 1 if any dirty, 2 if validation fails
    """
    provenance_path = Path(".goneat/ssot/provenance.json")

    # Check if provenance file exists
    if not provenance_path.exists():
        print("❌ Provenance file not found: .goneat/ssot/provenance.json")
        print("   Run 'make sync' to generate provenance metadata")
        return 2

    # Load and parse provenance
    try:
        provenance = json.loads(provenance_path.read_text())
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in provenance file: {e}")
        return 2

    # Validate schema
    if "sources" not in provenance:
        print("❌ Provenance file missing 'sources' field")
        return 2

    sources = provenance["sources"]
    if not sources:
        print("⚠️  No SSOT sources configured")
        return 0

    # Check each source for dirty status
    dirty_sources = []
    for source in sources:
        name = source.get("name", "unknown")
        is_dirty = source.get("dirty", False)
        dirty_reason = source.get("dirty_reason", "")

        if is_dirty:
            dirty_sources.append((name, dirty_reason))

    # Report results
    if dirty_sources:
        print("❌ Cannot push PyFulmen with dirty SSOT sources:")
        print()
        for name, reason in dirty_sources:
            print(f"   • {name}: {reason}")
        print()
        print("Resolution:")
        print("  1. Commit and push changes in SSOT source(s)")
        print("  2. Re-run 'make sync' to update provenance")
        print("  3. Try push again")
        return 1

    # All clean
    print("✅ All SSOT sources clean")
    for source in sources:
        name = source.get("name", "unknown")
        version = source.get("version", "unknown")
        commit = source.get("commit", "unknown")[:8]
        print(f"   • {name}: v{version} ({commit})")
    return 0


if __name__ == "__main__":
    sys.exit(validate_provenance())
