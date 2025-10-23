"""Tests for FulHash streaming API.

Validates that StreamHasher produces identical results to block hashing
and correctly handles chunked data, reset, and streaming fixtures.
"""

from pathlib import Path

import pytest
import yaml

from pyfulmen.fulhash import Algorithm, hash_bytes, stream

# Load fixtures once at module level
FIXTURES_PATH = Path("config/crucible-py/library/fulhash/fixtures.yaml")
with open(FIXTURES_PATH) as f:
    FIXTURES_DATA = yaml.safe_load(f)

BLOCK_FIXTURES = FIXTURES_DATA["fixtures"]
STREAMING_FIXTURES = FIXTURES_DATA["streaming_fixtures"]


class TestStreamHasherBasics:
    """Test basic StreamHasher functionality."""

    def test_stream_factory(self):
        """Test stream() factory function."""
        hasher = stream()
        assert hasher.algorithm == Algorithm.XXH3_128

        hasher_sha = stream(Algorithm.SHA256)
        assert hasher_sha.algorithm == Algorithm.SHA256

    def test_update_returns_self(self):
        """Test update() returns self for chaining."""
        hasher = stream()
        result = hasher.update(b"test")
        assert result is hasher

    def test_reset_returns_self(self):
        """Test reset() returns self for chaining."""
        hasher = stream()
        result = hasher.reset()
        assert result is hasher

    def test_method_chaining(self):
        """Test method chaining works."""
        hasher = stream()
        digest = hasher.update(b"Hello").update(b", ").update(b"World!").digest()
        assert digest.formatted == "xxh3-128:531df2844447dd5077db03842cd75395"


class TestStreamingVsBlock:
    """Test streaming produces same results as block hashing."""

    @pytest.mark.parametrize("fixture", BLOCK_FIXTURES, ids=lambda f: f["name"])
    def test_xxh3_streaming_matches_block(self, fixture):
        """Test XXH3-128 streaming matches block hashing."""
        # Get input data
        if "input" in fixture:
            data = fixture["input"].encode(fixture["encoding"])
        elif "input_bytes" in fixture:
            data = bytes(fixture["input_bytes"])
        else:
            pytest.skip("No input data")

        # Compute block hash
        block_digest = hash_bytes(data, Algorithm.XXH3_128)

        # Compute streaming hash
        hasher = stream(Algorithm.XXH3_128)
        hasher.update(data)
        stream_digest = hasher.digest()

        # Should be identical
        assert stream_digest.formatted == block_digest.formatted
        assert stream_digest.hex == block_digest.hex
        assert stream_digest.bytes == block_digest.bytes

    @pytest.mark.parametrize("fixture", BLOCK_FIXTURES, ids=lambda f: f["name"])
    def test_sha256_streaming_matches_block(self, fixture):
        """Test SHA-256 streaming matches block hashing."""
        # Get input data
        if "input" in fixture:
            data = fixture["input"].encode(fixture["encoding"])
        elif "input_bytes" in fixture:
            data = bytes(fixture["input_bytes"])
        else:
            pytest.skip("No input data")

        # Compute block hash
        block_digest = hash_bytes(data, Algorithm.SHA256)

        # Compute streaming hash
        hasher = stream(Algorithm.SHA256)
        hasher.update(data)
        stream_digest = hasher.digest()

        # Should be identical
        assert stream_digest.formatted == block_digest.formatted
        assert stream_digest.hex == block_digest.hex
        assert stream_digest.bytes == block_digest.bytes


class TestStreamingFixtures:
    """Test against streaming-specific fixtures."""

    def test_streaming_hello_world(self):
        """Test streaming hello-world fixture."""
        fixture = next(f for f in STREAMING_FIXTURES if f["name"] == "streaming-hello-world")

        # XXH3-128
        hasher_xxh3 = stream(Algorithm.XXH3_128)
        for chunk in fixture["chunks"]:
            data = chunk["value"].encode(chunk["encoding"])
            hasher_xxh3.update(data)

        digest_xxh3 = hasher_xxh3.digest()
        assert digest_xxh3.formatted == fixture["expected_xxh3_128"]

        # SHA-256
        hasher_sha = stream(Algorithm.SHA256)
        for chunk in fixture["chunks"]:
            data = chunk["value"].encode(chunk["encoding"])
            hasher_sha.update(data)

        digest_sha = hasher_sha.digest()
        assert digest_sha.formatted == fixture["expected_sha256"]

    def test_streaming_large_chunks(self):
        """Test streaming large chunks fixture."""
        fixture = next(f for f in STREAMING_FIXTURES if f["name"] == "streaming-large-chunks")

        # Build chunks according to fixture spec
        chunks = []
        for chunk_spec in fixture["chunks"]:
            size = chunk_spec["size"]
            pattern = chunk_spec["pattern"]

            if pattern == "repeating-A":
                chunks.append(b"A" * size)
            elif pattern == "repeating-B":
                chunks.append(b"B" * size)
            elif pattern == "repeating-C":
                chunks.append(b"C" * size)

        # XXH3-128
        hasher_xxh3 = stream(Algorithm.XXH3_128)
        for chunk in chunks:
            hasher_xxh3.update(chunk)

        digest_xxh3 = hasher_xxh3.digest()
        assert digest_xxh3.formatted == fixture["expected_xxh3_128"]

        # SHA-256
        hasher_sha = stream(Algorithm.SHA256)
        for chunk in chunks:
            hasher_sha.update(chunk)

        digest_sha = hasher_sha.digest()
        assert digest_sha.formatted == fixture["expected_sha256"]


class TestStreamingChunks:
    """Test chunked updates."""

    def test_single_vs_multiple_updates(self):
        """Test single update vs multiple updates produce same result."""
        data = b"Hello, World!"

        # Single update
        hasher1 = stream()
        hasher1.update(data)
        digest1 = hasher1.digest()

        # Multiple updates
        hasher2 = stream()
        hasher2.update(b"Hello, ")
        hasher2.update(b"World!")
        digest2 = hasher2.digest()

        assert digest1.formatted == digest2.formatted

    def test_many_small_chunks(self):
        """Test many small chunks."""
        data = b"Hello, World!"

        # All at once
        hasher1 = stream()
        hasher1.update(data)
        digest1 = hasher1.digest()

        # One byte at a time
        hasher2 = stream()
        for byte in data:
            hasher2.update(bytes([byte]))
        digest2 = hasher2.digest()

        assert digest1.formatted == digest2.formatted

    def test_empty_updates(self):
        """Test that empty updates don't affect result."""
        hasher1 = stream()
        hasher1.update(b"Hello, World!")
        digest1 = hasher1.digest()

        hasher2 = stream()
        hasher2.update(b"")
        hasher2.update(b"Hello, ")
        hasher2.update(b"")
        hasher2.update(b"World!")
        hasher2.update(b"")
        digest2 = hasher2.digest()

        assert digest1.formatted == digest2.formatted


class TestStreamingReset:
    """Test reset functionality."""

    def test_reset_clears_state(self):
        """Test reset() clears accumulated data."""
        hasher = stream()
        hasher.update(b"First data")
        first_digest = hasher.digest()

        # Reset and compute new hash
        hasher.reset()
        hasher.update(b"Second data")
        second_digest = hasher.digest()

        # Should be different
        assert first_digest.formatted != second_digest.formatted

    def test_reset_allows_reuse(self):
        """Test hasher can be reused after reset."""
        hasher = stream()

        # First use
        hasher.update(b"Hello, World!")
        digest1 = hasher.digest()

        # Reset and second use
        hasher.reset()
        hasher.update(b"Hello, World!")
        digest2 = hasher.digest()

        # Should be identical (same data)
        assert digest1.formatted == digest2.formatted

    def test_reset_with_chaining(self):
        """Test reset with method chaining."""
        hasher = stream()

        hasher.update(b"ignored")
        digest = hasher.reset().update(b"Hello, World!").digest()

        assert digest.formatted == "xxh3-128:531df2844447dd5077db03842cd75395"


class TestStreamingEdgeCases:
    """Test edge cases."""

    def test_digest_does_not_reset(self):
        """Test digest() does not reset hasher."""
        hasher = stream()
        hasher.update(b"Hello")

        digest1 = hasher.digest()

        # Add more data
        hasher.update(b", World!")
        digest2 = hasher.digest()

        # Digests should be different (accumulated data)
        assert digest1.formatted != digest2.formatted
        assert digest2.formatted == "xxh3-128:531df2844447dd5077db03842cd75395"

    def test_empty_stream(self):
        """Test hashing with no updates (empty input)."""
        hasher = stream(Algorithm.XXH3_128)
        digest = hasher.digest()

        # Should match empty-input fixture
        empty_fixture = next(f for f in BLOCK_FIXTURES if f["name"] == "empty-input")
        assert digest.formatted == empty_fixture["xxh3_128"]

    def test_digest_multiple_calls(self):
        """Test calling digest() multiple times."""
        hasher = stream()
        hasher.update(b"Hello, World!")

        digest1 = hasher.digest()
        digest2 = hasher.digest()
        digest3 = hasher.digest()

        # All should be identical
        assert digest1.formatted == digest2.formatted == digest3.formatted


class TestStreamingAlgorithms:
    """Test algorithm selection."""

    def test_default_algorithm(self):
        """Test default algorithm is XXH3-128."""
        hasher = stream()
        assert hasher.algorithm == Algorithm.XXH3_128

    def test_explicit_algorithm(self):
        """Test explicit algorithm selection."""
        hasher_xxh3 = stream(Algorithm.XXH3_128)
        hasher_sha = stream(Algorithm.SHA256)

        hasher_xxh3.update(b"test")
        hasher_sha.update(b"test")

        digest_xxh3 = hasher_xxh3.digest()
        digest_sha = hasher_sha.digest()

        # Different algorithms produce different results
        assert digest_xxh3.algorithm == Algorithm.XXH3_128
        assert digest_sha.algorithm == Algorithm.SHA256
        assert digest_xxh3.formatted != digest_sha.formatted
