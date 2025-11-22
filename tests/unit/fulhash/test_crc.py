"""Tests for CRC32 and CRC32C algorithms."""

import zlib

import pytest

from pyfulmen.fulhash import Algorithm, hash_bytes, multi_hash, stream, verify

try:
    import google_crc32c

    HAS_CRC32C = True
except ImportError:
    HAS_CRC32C = False


class TestCRCAlgorithms:
    """Test CRC32 and CRC32C hashing."""

    def test_crc32_block(self):
        """Test CRC32 block hashing."""
        data = b"123456789"
        # CRC32 of "123456789" is 0xCBF43926
        expected_hex = "cbf43926"

        digest = hash_bytes(data, Algorithm.CRC32)
        assert digest.algorithm == Algorithm.CRC32
        assert digest.hex == expected_hex
        assert digest.formatted == f"crc32:{expected_hex}"

        # Validate against zlib
        assert digest.hex == f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"

    def test_crc32_streaming(self):
        """Test CRC32 streaming hashing."""
        data = b"123456789"
        expected_hex = "cbf43926"

        hasher = stream(Algorithm.CRC32)
        hasher.update(data[:5])
        hasher.update(data[5:])

        digest = hasher.digest()
        assert digest.hex == expected_hex

    @pytest.mark.skipif(not HAS_CRC32C, reason="google-crc32c not installed")
    def test_crc32c_block(self):
        """Test CRC32C block hashing."""
        data = b"123456789"
        # CRC32C of "123456789" is 0xE3069283
        expected_hex = "e3069283"

        digest = hash_bytes(data, Algorithm.CRC32C)
        assert digest.algorithm == Algorithm.CRC32C
        assert digest.hex == expected_hex

        # Validate against google_crc32c
        assert digest.hex == f"{google_crc32c.value(data) & 0xFFFFFFFF:08x}"

    @pytest.mark.skipif(not HAS_CRC32C, reason="google-crc32c not installed")
    def test_crc32c_streaming(self):
        """Test CRC32C streaming hashing."""
        data = b"123456789"
        expected_hex = "e3069283"

        hasher = stream(Algorithm.CRC32C)
        hasher.update(data[:5])
        hasher.update(data[5:])

        digest = hasher.digest()
        assert digest.hex == expected_hex

    def test_verify_helper(self, tmp_path):
        """Test verify helper."""
        data = b"123456789"
        expected_crc32 = "crc32:cbf43926"

        # Verify bytes
        assert verify(data, expected_crc32) is True
        assert verify(b"wrong", expected_crc32) is False

        # Verify file
        f = tmp_path / "test.txt"
        f.write_bytes(data)
        assert verify(f, expected_crc32) is True

        # Verify string (as text)
        assert verify("123456789", expected_crc32) is True

    def test_multi_hash(self):
        """Test multi_hash helper."""
        data = b"123456789"
        algos = [Algorithm.CRC32, Algorithm.XXH3_128]

        digests = multi_hash(data, algos)

        assert len(digests) == 2
        assert digests[Algorithm.CRC32].hex == "cbf43926"
        assert digests[Algorithm.XXH3_128].algorithm == Algorithm.XXH3_128
