"""Tests for FulHash models (Algorithm enum and Digest)."""

import json

import pytest
from pydantic import ValidationError

from pyfulmen.fulhash import Algorithm, Digest
from pyfulmen.schema.validator import validate_against_schema


class TestAlgorithm:
    """Test Algorithm enum."""

    def test_algorithm_values(self):
        """Test algorithm string values."""
        assert Algorithm.XXH3_128.value == "xxh3-128"
        assert Algorithm.SHA256.value == "sha256"

    def test_algorithm_from_string(self):
        """Test creating algorithm from string."""
        assert Algorithm("xxh3-128") == Algorithm.XXH3_128
        assert Algorithm("sha256") == Algorithm.SHA256

    def test_invalid_algorithm(self):
        """Test invalid algorithm raises error."""
        with pytest.raises(ValueError, match="not a valid Algorithm"):
            Algorithm("md5")


class TestDigestBasics:
    """Test basic Digest model functionality."""

    def test_digest_xxh3_valid(self):
        """Test valid xxh3-128 digest."""
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
        )
        assert digest.algorithm == Algorithm.XXH3_128
        assert digest.hex == "531df2844447dd5077db03842cd75395"
        assert digest.bytes is None
        assert digest.formatted == "xxh3-128:531df2844447dd5077db03842cd75395"

    def test_digest_sha256_valid(self):
        """Test valid sha256 digest."""
        digest = Digest(
            algorithm=Algorithm.SHA256,
            hex="dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f",
        )
        assert digest.algorithm == Algorithm.SHA256
        assert digest.hex == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert digest.bytes is None
        assert digest.formatted == "sha256:dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

    def test_digest_with_bytes(self):
        """Test digest with bytes field."""
        raw_bytes = b"S\x1d\xf2\x84DB}\xd5\x07}\xb0\x38B\xcdu\x95"
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
            bytes=raw_bytes,
        )
        assert digest.bytes == raw_bytes
        assert len(digest.bytes) == 16


class TestDigestValidation:
    """Test Digest validation logic."""

    def test_hex_length_xxh3_invalid(self):
        """Test xxh3-128 with wrong hex length."""
        with pytest.raises(ValidationError, match="32 hex characters"):
            Digest(
                algorithm=Algorithm.XXH3_128,
                hex="abc123",  # Too short
            )

    def test_hex_length_sha256_invalid(self):
        """Test sha256 with wrong hex length."""
        with pytest.raises(ValidationError, match="64 hex characters"):
            Digest(
                algorithm=Algorithm.SHA256,
                hex="531df2844447dd5077db03842cd75395",  # 32 chars, need 64
            )

    def test_hex_uppercase_invalid(self):
        """Test hex with uppercase letters (must be lowercase)."""
        with pytest.raises(ValidationError, match="pattern"):
            Digest(
                algorithm=Algorithm.XXH3_128,
                hex="531DF2844447DD5077DB03842CD75395",  # Uppercase
            )

    def test_hex_non_hex_chars(self):
        """Test hex with non-hexadecimal characters."""
        with pytest.raises(ValidationError, match="pattern"):
            Digest(
                algorithm=Algorithm.XXH3_128,
                hex="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            )

    def test_bytes_length_xxh3_invalid(self):
        """Test xxh3-128 with wrong bytes length."""
        with pytest.raises(ValidationError, match="16 bytes"):
            Digest(
                algorithm=Algorithm.XXH3_128,
                hex="531df2844447dd5077db03842cd75395",
                bytes=b"tooshort",  # 8 bytes, need 16
            )

    def test_bytes_length_sha256_invalid(self):
        """Test sha256 with wrong bytes length."""
        with pytest.raises(ValidationError, match="32 bytes"):
            Digest(
                algorithm=Algorithm.SHA256,
                hex="dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f",
                bytes=b"S\x1d\xf2\x84DB}\xd5\x07}\xb0\x38B\xcdu\x95",  # 16 bytes, need 32
            )


class TestDigestImmutability:
    """Test Digest immutability."""

    def test_digest_is_frozen(self):
        """Test digest cannot be modified after creation."""
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
        )
        with pytest.raises(ValidationError, match="frozen"):
            digest.hex = "000000000000000000000000000000000"

    def test_digest_hash(self):
        """Test digest is hashable (frozen)."""
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
        )
        # Should be hashable
        assert hash(digest) is not None

        # Can be used in sets/dicts
        digest_set = {digest}
        assert digest in digest_set


class TestDigestFormatted:
    """Test formatted property."""

    def test_formatted_xxh3(self):
        """Test formatted string for xxh3-128."""
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
        )
        assert digest.formatted == "xxh3-128:531df2844447dd5077db03842cd75395"

    def test_formatted_sha256(self):
        """Test formatted string for sha256."""
        digest = Digest(
            algorithm=Algorithm.SHA256,
            hex="dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f",
        )
        assert digest.formatted == "sha256:dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

    def test_formatted_matches_schema_pattern(self):
        """Test formatted matches checksum-string.schema.json pattern."""
        import re

        # Pattern from checksum-string.schema.json
        pattern = r"^(xxh3-128:[0-9a-f]{32}|sha256:[0-9a-f]{64})$"

        xxh3_digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
        )
        assert re.match(pattern, xxh3_digest.formatted)

        sha256_digest = Digest(
            algorithm=Algorithm.SHA256,
            hex="dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f",
        )
        assert re.match(pattern, sha256_digest.formatted)


class TestDigestSerialization:
    """Test Digest JSON serialization."""

    def test_model_dump_json(self):
        """Test Digest can be dumped to JSON."""
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
        )
        data = digest.model_dump(mode="json")

        assert data["algorithm"] == "xxh3-128"
        assert data["hex"] == "531df2844447dd5077db03842cd75395"
        assert data["formatted"] == "xxh3-128:531df2844447dd5077db03842cd75395"
        # None bytes is omitted entirely in JSON mode (never null)
        assert "bytes" not in data

    def test_model_dump_json_with_bytes(self):
        """Test JSON mode serializes bytes as list[int]."""
        raw_bytes = b"S\x1d\xf2\x84DB}\xd5\x07}\xb0\x38B\xcdu\x95"
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
            bytes=raw_bytes,
        )
        data = digest.model_dump(mode="json")

        assert data["bytes"] == list(raw_bytes)
        assert all(isinstance(b, int) for b in data["bytes"])

    def test_model_dump_json_string(self):
        """Test model_dump_json() does not crash on non-UTF-8 digest bytes."""
        raw_bytes = b"S\x1d\xf2\x84DB}\xd5\x07}\xb0\x38B\xcdu\x95"
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
            bytes=raw_bytes,
        )
        data = json.loads(digest.model_dump_json())

        assert data["bytes"] == list(raw_bytes)

    def test_model_dump_python_mode(self):
        """Test Digest Python serialization (not JSON mode)."""
        raw_bytes = b"S\x1d\xf2\x84DB}\xd5\x07}\xb0\x38B\xcdu\x95"
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
            bytes=raw_bytes,
        )
        data = digest.model_dump(mode="python")

        # Bytes preserved in python mode
        assert data["bytes"] == raw_bytes

    def test_validate_bytes_from_list_of_ints(self):
        """Test list[int] (JSON form) coerces to bytes on validation."""
        raw_bytes = b"S\x1d\xf2\x84DB}\xd5\x07}\xb0\x38B\xcdu\x95"
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
            bytes=list(raw_bytes),
        )
        assert digest.bytes == raw_bytes

    def test_validate_bytes_from_invalid_list(self):
        """Test out-of-range list items raise ValidationError."""
        with pytest.raises(ValidationError, match="invalid byte array"):
            Digest(
                algorithm=Algorithm.XXH3_128,
                hex="531df2844447dd5077db03842cd75395",
                bytes=[256] * 16,
            )

    def test_validate_bytes_rejects_boolean_elements(self):
        """Test boolean list items raise ValidationError (bool is not a byte)."""
        with pytest.raises(ValidationError, match="invalid byte array"):
            Digest(
                algorithm=Algorithm.XXH3_128,
                hex="531df2844447dd5077db03842cd75395",
                bytes=[True] * 16,
            )

    def test_serialization_json_schema_not_collapsed(self):
        """Test the wrap serializer does not erase the serialization schema.

        A declared dict return annotation on a model_serializer collapses
        model_json_schema(mode="serialization") to a bare object schema.
        """
        schema = Digest.model_json_schema(mode="serialization")
        assert "properties" in schema
        assert "bytes" in schema["properties"]
        assert "algorithm" in schema["properties"]


class TestDigestSchemaRoundTrip:
    """Test JSON serialization round-trips against digest.schema.json."""

    def test_round_trip_with_bytes(self):
        """Test digest with bytes: JSON validates against schema and parses back equal."""
        raw_bytes = b"S\x1d\xf2\x84DB}\xd5\x07}\xb0\x38B\xcdu\x95"
        digest = Digest(
            algorithm=Algorithm.XXH3_128,
            hex="531df2844447dd5077db03842cd75395",
            bytes=raw_bytes,
        )
        json_str = digest.model_dump_json()
        data = json.loads(json_str)

        # Serialized output conforms to digest.schema.json
        validate_against_schema(data, "library/fulhash", "v1.0.0", "digest")

        # Parses back to an equal digest
        parsed = Digest.model_validate_json(json_str)
        assert parsed == digest
        assert parsed.bytes == raw_bytes

    def test_round_trip_without_bytes(self):
        """Test digest without bytes: JSON omits the key, validates, and parses."""
        digest = Digest(
            algorithm=Algorithm.SHA256,
            hex="dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f",
        )
        json_str = digest.model_dump_json()
        data = json.loads(json_str)

        # bytes key omitted entirely (schema does not allow null)
        assert "bytes" not in data

        # Serialized output conforms to digest.schema.json
        validate_against_schema(data, "library/fulhash", "v1.0.0", "digest")

        # Parses back to an equal digest
        parsed = Digest.model_validate_json(json_str)
        assert parsed == digest
        assert parsed.bytes is None
