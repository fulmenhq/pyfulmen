#!/usr/bin/env python3
"""Compute authoritative xxh3-128 values for FulHash fixtures.

This script reads the fixtures.yaml file, computes xxh3-128 digests for all
entries (block and streaming), and outputs updated fixture values.

Usage:
    uv run python scripts/compute_fulhash_fixtures.py
"""

import hashlib
from pathlib import Path

import xxhash
import yaml


def compute_xxh3_128(data: bytes) -> str:
    """Compute xxh3-128 digest and return formatted checksum string."""
    h = xxhash.xxh3_128(data)
    hex_digest = h.hexdigest()
    return f"xxh3-128:{hex_digest}"


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 digest and return formatted checksum string."""
    h = hashlib.sha256(data)
    hex_digest = h.hexdigest()
    return f"sha256:{hex_digest}"


def process_block_fixture(fixture: dict) -> dict:
    """Compute digests for a block fixture."""
    # Get input data
    if "input" in fixture:
        encoding = fixture.get("encoding", "utf-8")
        data = fixture["input"].encode(encoding)
    elif "input_bytes" in fixture:
        data = bytes(fixture["input_bytes"])
    else:
        raise ValueError(f"Fixture '{fixture['name']}' missing input or input_bytes")

    # Compute digests
    xxh3_computed = compute_xxh3_128(data)
    sha256_computed = compute_sha256(data)

    # Update fixture
    fixture["xxh3_128"] = xxh3_computed

    # Verify SHA-256 if present
    if "sha256" in fixture:
        if fixture["sha256"] != sha256_computed:
            print(f"  ⚠️  SHA-256 mismatch in '{fixture['name']}':")
            print(f"      Expected: {fixture['sha256']}")
            print(f"      Computed: {sha256_computed}")
    else:
        fixture["sha256"] = sha256_computed

    return fixture


def process_streaming_fixture(fixture: dict) -> dict:
    """Compute digests for a streaming fixture."""
    # Initialize hashers
    xxh3_hasher = xxhash.xxh3_128()
    sha256_hasher = hashlib.sha256()

    # Process chunks
    for chunk in fixture["chunks"]:
        if "value" in chunk:
            encoding = chunk.get("encoding", "utf-8")
            data = chunk["value"].encode(encoding)
        elif "size" in chunk and "pattern" in chunk:
            # Handle pattern-based chunks (e.g., "repeating-A")
            pattern = chunk["pattern"]
            size = chunk["size"]
            if pattern == "repeating-A":
                data = b"A" * size
            elif pattern == "repeating-B":
                data = b"B" * size
            elif pattern == "repeating-C":
                data = b"C" * size
            else:
                raise ValueError(f"Unknown pattern: {pattern}")
        else:
            raise ValueError("Chunk missing value or size/pattern")

        xxh3_hasher.update(data)
        sha256_hasher.update(data)

    # Get digests
    xxh3_hex = xxh3_hasher.hexdigest()
    sha256_hex = sha256_hasher.hexdigest()

    fixture["expected_xxh3_128"] = f"xxh3-128:{xxh3_hex}"
    fixture["expected_sha256"] = f"sha256:{sha256_hex}"

    return fixture


def main():
    """Compute xxh3-128 values for all fixtures."""
    # Load fixtures
    fixtures_path = Path("config/crucible-py/library/fulhash/fixtures.yaml")
    print(f"Loading fixtures from: {fixtures_path}")

    with open(fixtures_path) as f:
        data = yaml.safe_load(f)

    print(f"\n📊 Processing {len(data.get('fixtures', []))} block fixtures...")

    # Process block fixtures
    for fixture in data.get("fixtures", []):
        name = fixture["name"]
        print(f"  • {name}")
        process_block_fixture(fixture)

    print(
        f"\n🌊 Processing {len(data.get('streaming_fixtures', []))} streaming fixtures..."
    )

    # Process streaming fixtures
    for fixture in data.get("streaming_fixtures", []):
        name = fixture["name"]
        print(f"  • {name}")
        process_streaming_fixture(fixture)

    # Update notes to indicate values are computed
    if "notes" in data:
        notes = data["notes"]
        # Remove placeholder language
        notes = notes.replace(
            "xxh3-128 values are placeholders - replace with actual computed "
            "values after initial implementation",
            "xxh3-128 values computed using xxhash v3.6.0 (Python reference implementation)",
        )
        notes = notes.replace(
            "replace with actual computed values", "computed by PyFulmen v0.1.6"
        )
        data["notes"] = notes

    # Write updated fixtures
    output_path = fixtures_path
    print(f"\n✍️  Writing updated fixtures to: {output_path}")

    with open(output_path, "w") as f:
        yaml.dump(
            data, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

    print("\n✅ Done! All xxh3-128 values computed and updated.")
    print("\n📋 Summary:")
    print(f"   - Block fixtures: {len(data.get('fixtures', []))}")
    print(f"   - Streaming fixtures: {len(data.get('streaming_fixtures', []))}")
    print("\n🔍 Next steps:")
    print(f"   1. Review the updated {fixtures_path}")
    print("   2. Run: uv run pytest tests/unit/fulhash (once tests are written)")
    print("   3. Report completion to EA Steward for Crucible sync")


if __name__ == "__main__":
    main()
