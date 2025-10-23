"""Tests for FulHash against Crucible fixtures.

Validates that hash_bytes and hash_string produce digests matching
the authoritative values in config/crucible-py/library/fulhash/fixtures.yaml
"""

from pathlib import Path

import pytest
import yaml

from pyfulmen.fulhash import Algorithm, hash_bytes, hash_string

# Load fixtures once at module level
FIXTURES_PATH = Path("config/crucible-py/library/fulhash/fixtures.yaml")
with open(FIXTURES_PATH) as f:
    FIXTURES_DATA = yaml.safe_load(f)

BLOCK_FIXTURES = FIXTURES_DATA["fixtures"]


class TestBlockFixtures:
    """Test block hashing against all Crucible fixtures."""

    @pytest.mark.parametrize("fixture", BLOCK_FIXTURES, ids=lambda f: f["name"])
    def test_xxh3_128_block_hash(self, fixture):
        """Test xxh3-128 block hashing matches fixture."""
        # Get input data
        if "input" in fixture:
            data = fixture["input"].encode(fixture["encoding"])
        elif "input_bytes" in fixture:
            data = bytes(fixture["input_bytes"])
        else:
            pytest.fail(f"Fixture '{fixture['name']}' missing input")

        # Compute hash
        digest = hash_bytes(data, Algorithm.XXH3_128)

        # Verify against fixture
        expected = fixture["xxh3_128"]
        assert digest.formatted == expected, (
            f"XXH3-128 mismatch for '{fixture['name']}'\n"
            f"  Expected: {expected}\n"
            f"  Got:      {digest.formatted}"
        )

        # Verify hex length (32 chars for xxh3-128)
        assert len(digest.hex) == 32

    @pytest.mark.parametrize("fixture", BLOCK_FIXTURES, ids=lambda f: f["name"])
    def test_sha256_block_hash(self, fixture):
        """Test SHA-256 block hashing matches fixture."""
        # Get input data
        if "input" in fixture:
            data = fixture["input"].encode(fixture["encoding"])
        elif "input_bytes" in fixture:
            data = bytes(fixture["input_bytes"])
        else:
            pytest.fail(f"Fixture '{fixture['name']}' missing input")

        # Compute hash
        digest = hash_bytes(data, Algorithm.SHA256)

        # Verify against fixture
        expected = fixture["sha256"]
        assert digest.formatted == expected, (
            f"SHA-256 mismatch for '{fixture['name']}'\n"
            f"  Expected: {expected}\n"
            f"  Got:      {digest.formatted}"
        )

        # Verify hex length (64 chars for sha256)
        assert len(digest.hex) == 64

    @pytest.mark.parametrize("fixture", BLOCK_FIXTURES, ids=lambda f: f["name"])
    def test_hash_string_wrapper(self, fixture):
        """Test hash_string wrapper for text fixtures."""
        # Skip byte-only fixtures
        if "input" not in fixture:
            pytest.skip("No text input for this fixture")

        text = fixture["input"]
        encoding = fixture["encoding"]

        # Test with xxh3-128
        digest_xxh3 = hash_string(text, Algorithm.XXH3_128, encoding=encoding)
        assert digest_xxh3.formatted == fixture["xxh3_128"]

        # Test with sha256
        digest_sha256 = hash_string(text, Algorithm.SHA256, encoding=encoding)
        assert digest_sha256.formatted == fixture["sha256"]


class TestFixtureEdgeCases:
    """Test specific edge cases from fixtures."""

    def test_empty_input(self):
        """Test empty input (important edge case)."""
        digest_xxh3 = hash_bytes(b"", Algorithm.XXH3_128)
        digest_sha256 = hash_bytes(b"", Algorithm.SHA256)

        # Find empty-input fixture
        empty_fixture = next(f for f in BLOCK_FIXTURES if f["name"] == "empty-input")

        assert digest_xxh3.formatted == empty_fixture["xxh3_128"]
        assert digest_sha256.formatted == empty_fixture["sha256"]

    def test_unicode_emoji(self):
        """Test Unicode emoji handling."""
        # Find unicode-emoji fixture
        unicode_fixture = next(f for f in BLOCK_FIXTURES if f["name"] == "unicode-emoji")

        text = unicode_fixture["input"]
        digest = hash_string(text, Algorithm.XXH3_128, encoding="utf-8")

        assert digest.formatted == unicode_fixture["xxh3_128"]

        # Verify the bytes match expected
        expected_bytes = bytes(unicode_fixture["input_bytes"])
        actual_bytes = text.encode("utf-8")
        assert actual_bytes == expected_bytes

    def test_binary_sequence(self):
        """Test raw binary data."""
        # Find binary-sequence fixture
        binary_fixture = next(f for f in BLOCK_FIXTURES if f["name"] == "binary-sequence")

        data = bytes(binary_fixture["input_bytes"])
        digest = hash_bytes(data, Algorithm.XXH3_128)

        assert digest.formatted == binary_fixture["xxh3_128"]


class TestDefaultAlgorithm:
    """Test default algorithm behavior."""

    def test_default_is_xxh3_128(self):
        """Test that default algorithm is XXH3-128."""
        digest = hash_bytes(b"test")
        assert digest.algorithm == Algorithm.XXH3_128

        digest_str = hash_string("test")
        assert digest_str.algorithm == Algorithm.XXH3_128

    def test_explicit_algorithm_override(self):
        """Test explicit algorithm selection."""
        data = b"test"

        digest_xxh3 = hash_bytes(data, Algorithm.XXH3_128)
        digest_sha256 = hash_bytes(data, Algorithm.SHA256)

        # Different algorithms produce different results
        assert digest_xxh3.hex != digest_sha256.hex
        assert digest_xxh3.algorithm == Algorithm.XXH3_128
        assert digest_sha256.algorithm == Algorithm.SHA256
