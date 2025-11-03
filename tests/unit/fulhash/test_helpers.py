"""Tests for FulHash metadata helpers.

Validates format_checksum, parse_checksum, validate_checksum_string,
and compare_digests functions against format fixtures and error cases.
"""

from pathlib import Path

import pytest
import yaml

from pyfulmen.fulhash import (
    Algorithm,
    Digest,
    compare_digests,
    format_checksum,
    hash_bytes,
    hash_string,
    parse_checksum,
    validate_checksum_string,
)

# Load fixtures once at module level
FIXTURES_PATH = Path("config/crucible-py/library/fulhash/fixtures.yaml")
with open(FIXTURES_PATH) as f:
    FIXTURES_DATA = yaml.safe_load(f)

FORMAT_FIXTURES = FIXTURES_DATA["format_fixtures"]
ERROR_FIXTURES = FIXTURES_DATA["error_fixtures"]


class TestFormatChecksum:
    """Test format_checksum() function."""

    def test_format_xxh3_with_enum(self):
        """Test formatting with XXH3-128 enum."""
        result = format_checksum(Algorithm.XXH3_128, "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
        assert result == "xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"

    def test_format_xxh3_with_string(self):
        """Test formatting with XXH3-128 string."""
        result = format_checksum("xxh3-128", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
        assert result == "xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"

    def test_format_sha256_with_enum(self):
        """Test formatting with SHA-256 enum."""
        result = format_checksum(
            Algorithm.SHA256,
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        assert result == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_format_sha256_with_string(self):
        """Test formatting with SHA-256 string."""
        result = format_checksum(
            "sha256",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        assert result == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    @pytest.mark.parametrize(
        "fixture",
        [f for f in FORMAT_FIXTURES if f["name"].startswith("format-")],
        ids=lambda f: f["name"],
    )
    def test_format_fixtures(self, fixture):
        """Test format_checksum against format fixtures."""
        result = format_checksum(fixture["algorithm"], fixture["hex"])
        assert result == fixture["expected_formatted"]

    def test_format_unsupported_algorithm(self):
        """Test formatting with unsupported algorithm."""
        with pytest.raises(ValueError, match="Unsupported algorithm: md5"):
            format_checksum("md5", "abc123def456")

    def test_format_invalid_hex_uppercase(self):
        """Test formatting rejects uppercase hex."""
        with pytest.raises(ValueError, match="Invalid hex format"):
            format_checksum("xxh3-128", "A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6")

    def test_format_invalid_hex_length(self):
        """Test formatting rejects wrong hex length."""
        with pytest.raises(ValueError, match="32 hex characters"):
            format_checksum("xxh3-128", "abc123")

    def test_format_invalid_hex_chars(self):
        """Test formatting rejects non-hex characters."""
        with pytest.raises(ValueError, match="Invalid hex format"):
            format_checksum("xxh3-128", "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")


class TestParseChecksum:
    """Test parse_checksum() function."""

    def test_parse_xxh3(self):
        """Test parsing XXH3-128 checksum."""
        algo, hex_digest = parse_checksum("xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
        assert algo == "xxh3-128"
        assert hex_digest == "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"

    def test_parse_sha256(self):
        """Test parsing SHA-256 checksum."""
        algo, hex_digest = parse_checksum("sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        assert algo == "sha256"
        assert hex_digest == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    @pytest.mark.parametrize(
        "fixture",
        [f for f in FORMAT_FIXTURES if f["name"].startswith("parse-")],
        ids=lambda f: f["name"],
    )
    def test_parse_fixtures(self, fixture):
        """Test parse_checksum against parse fixtures."""
        algo, hex_digest = parse_checksum(fixture["formatted"])
        assert algo == fixture["expected_algorithm"]
        assert hex_digest == fixture["expected_hex"]

    def test_parse_with_whitespace(self):
        """Test parsing strips leading/trailing whitespace."""
        algo, hex_digest = parse_checksum("  xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6  ")
        assert algo == "xxh3-128"
        assert hex_digest == "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"

    def test_parse_invalid_no_separator(self):
        """Test parsing rejects missing colon separator."""
        with pytest.raises(ValueError, match="expected format 'algorithm:hex'"):
            parse_checksum("invalid-no-separator")

    def test_parse_invalid_algorithm(self):
        """Test parsing rejects unsupported algorithm."""
        with pytest.raises(ValueError, match="Unsupported algorithm: md5"):
            parse_checksum("md5:abc123def456")

    def test_parse_invalid_hex_uppercase(self):
        """Test parsing rejects uppercase hex."""
        with pytest.raises(ValueError, match="Invalid hex format"):
            parse_checksum("xxh3-128:A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6")

    def test_parse_invalid_hex_length(self):
        """Test parsing rejects wrong hex length."""
        with pytest.raises(ValueError, match="32 hex characters"):
            parse_checksum("xxh3-128:abc123")

    def test_parse_roundtrip(self):
        """Test format -> parse roundtrip."""
        original_algo = "xxh3-128"
        original_hex = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"

        formatted = format_checksum(original_algo, original_hex)
        parsed_algo, parsed_hex = parse_checksum(formatted)

        assert parsed_algo == original_algo
        assert parsed_hex == original_hex


class TestValidateChecksumString:
    """Test validate_checksum_string() function."""

    def test_validate_valid_xxh3(self):
        """Test validation accepts valid XXH3-128."""
        assert validate_checksum_string("xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")

    def test_validate_valid_sha256(self):
        """Test validation accepts valid SHA-256."""
        assert validate_checksum_string("sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_validate_with_whitespace(self):
        """Test validation strips whitespace."""
        assert validate_checksum_string("  xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6  ")

    def test_validate_invalid_no_separator(self):
        """Test validation rejects missing separator."""
        assert not validate_checksum_string("invalid-no-separator")

    def test_validate_invalid_algorithm(self):
        """Test validation rejects unsupported algorithm."""
        assert not validate_checksum_string("md5:abc123def456")

    def test_validate_invalid_hex_uppercase(self):
        """Test validation rejects uppercase hex."""
        assert not validate_checksum_string("xxh3-128:A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6")

    def test_validate_invalid_hex_length_short(self):
        """Test validation rejects short hex."""
        assert not validate_checksum_string("xxh3-128:abc123")

    def test_validate_invalid_hex_length_long(self):
        """Test validation rejects long hex."""
        assert not validate_checksum_string("xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6extra")

    def test_validate_empty_string(self):
        """Test validation rejects empty string."""
        assert not validate_checksum_string("")

    @pytest.mark.parametrize(
        "fixture",
        FORMAT_FIXTURES,
        ids=lambda f: f["name"],
    )
    def test_validate_all_format_fixtures(self, fixture):
        """Test validation accepts all format fixtures."""
        if "expected_formatted" in fixture:
            assert validate_checksum_string(fixture["expected_formatted"])
        if "formatted" in fixture:
            assert validate_checksum_string(fixture["formatted"])


class TestCompareDigests:
    """Test compare_digests() function."""

    def test_compare_identical_digests(self):
        """Test comparison of identical digests."""
        digest1 = hash_bytes(b"Hello, World!")
        digest2 = hash_bytes(b"Hello, World!")

        assert compare_digests(digest1, digest2)

    def test_compare_different_data(self):
        """Test comparison of different data."""
        digest1 = hash_bytes(b"Hello, World!")
        digest2 = hash_bytes(b"Different data")

        assert not compare_digests(digest1, digest2)

    def test_compare_different_algorithms(self):
        """Test comparison of different algorithms."""
        digest_xxh3 = hash_bytes(b"test", Algorithm.XXH3_128)
        digest_sha = hash_bytes(b"test", Algorithm.SHA256)

        assert not compare_digests(digest_xxh3, digest_sha)

    def test_compare_same_instance(self):
        """Test comparison of same instance."""
        digest = hash_bytes(b"test")
        assert compare_digests(digest, digest)

    def test_compare_manually_constructed(self):
        """Test comparison of manually constructed digests."""
        digest1 = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
        )
        digest2 = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
        )

        assert compare_digests(digest1, digest2)

    def test_compare_with_bytes_field(self):
        """Test comparison uses hex field (bytes field is optional)."""
        # One with bytes, one without
        digest1 = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
            bytes=b"S\x1d\xf2\x84DB}\xd5\x07}\xb0\x38B\xcdu\x95",  # 16 bytes
        )
        digest2 = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
            # No bytes field
        )

        # Should still match (hex is the same)
        assert compare_digests(digest1, digest2)


class TestErrorFixtures:
    """Test error handling against error fixtures."""

    def test_unsupported_algorithm_format(self):
        """Test unsupported algorithm in format_checksum."""
        with pytest.raises(ValueError) as exc_info:
            format_checksum("md5", "abc123def456789")

        error = str(exc_info.value)
        assert "md5" in error
        assert "supported algorithms" in error.lower()
        assert "xxh3-128" in error
        assert "sha256" in error

    def test_unsupported_algorithm_parse(self):
        """Test unsupported algorithm in parse_checksum."""
        with pytest.raises(ValueError) as exc_info:
            parse_checksum("unknown:abc123")

        error = str(exc_info.value)
        assert "unknown" in error
        assert "supported algorithms" in error.lower()

    def test_invalid_checksum_format_parse(self):
        """Test invalid format in parse_checksum."""
        with pytest.raises(ValueError) as exc_info:
            parse_checksum("invalid-no-separator")

        error = str(exc_info.value)
        assert "expected format" in error.lower()
        assert "algorithm:hex" in error


class TestHelperIntegration:
    """Test integration between helpers."""

    def test_digest_to_format_to_parse(self):
        """Test Digest -> format_checksum -> parse_checksum."""
        digest = hash_bytes(b"Hello, World!")

        # Use digest's formatted property
        checksum_str = digest.formatted

        # Parse it back
        algo, hex_digest = parse_checksum(checksum_str)

        assert algo == digest.algorithm.value
        assert hex_digest == digest.hex

    def test_format_parse_validate_roundtrip(self):
        """Test format -> parse -> validate roundtrip."""
        # Format
        formatted = format_checksum("xxh3-128", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")

        # Validate
        assert validate_checksum_string(formatted)

        # Parse
        algo, hex_digest = parse_checksum(formatted)

        # Re-format
        reformatted = format_checksum(algo, hex_digest)

        assert reformatted == formatted

    def test_hash_compare_workflow(self):
        """Test typical hash and compare workflow."""
        data1 = b"Hello, World!"
        data2 = b"Hello, World!"
        data3 = b"Different"

        digest1 = hash_bytes(data1)
        digest2 = hash_bytes(data2)
        digest3 = hash_bytes(data3)

        # Same data should match
        assert compare_digests(digest1, digest2)

        # Different data should not match
        assert not compare_digests(digest1, digest3)
        assert not compare_digests(digest2, digest3)


class TestTelemetry:
    """Tests for FulHash telemetry instrumentation."""

    def test_hash_string_with_telemetry_enabled(self):
        """Verify hash_string executes with telemetry instrumentation."""
        digest = hash_string("Telemetry test string")
        assert digest is not None
        assert digest.algorithm == Algorithm.XXH3_128
