"""Tests for FulHash file hashing and convenience APIs.

Validates hash_file and hash() dispatcher with temp files, error handling,
and equivalence to block hashing.
"""

import pytest

from pyfulmen.fulhash import (
    Algorithm,
    hash,
    hash_bytes,
    hash_file,
    hash_string,
)


class TestHashFile:
    """Test hash_file() function."""

    def test_hash_file_with_path_object(self, tmp_path):
        """Test hashing file with Path object."""
        # Create temp file
        file_path = tmp_path / "test.txt"
        content = b"Hello, World!"
        file_path.write_bytes(content)

        # Hash file
        digest = hash_file(file_path)

        # Should match block hash
        expected = hash_bytes(content)
        assert digest.formatted == expected.formatted
        assert digest.hex == expected.hex

    def test_hash_file_with_string_path(self, tmp_path):
        """Test hashing file with string path."""
        # Create temp file
        file_path = tmp_path / "test.txt"
        content = b"Hello, World!"
        file_path.write_bytes(content)

        # Hash file using string path
        digest = hash_file(str(file_path))

        # Should match block hash
        expected = hash_bytes(content)
        assert digest.formatted == expected.formatted

    def test_hash_file_with_sha256(self, tmp_path):
        """Test hashing file with SHA-256."""
        file_path = tmp_path / "test.txt"
        content = b"Test data"
        file_path.write_bytes(content)

        digest = hash_file(file_path, Algorithm.SHA256)

        expected = hash_bytes(content, Algorithm.SHA256)
        assert digest.algorithm == Algorithm.SHA256
        assert digest.formatted == expected.formatted

    def test_hash_file_empty(self, tmp_path):
        """Test hashing empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_bytes(b"")

        digest = hash_file(file_path)

        # Should match empty-input fixture
        expected = hash_bytes(b"")
        assert digest.formatted == expected.formatted

    def test_hash_file_large_file(self, tmp_path):
        """Test hashing file larger than chunk size (64KB)."""
        file_path = tmp_path / "large.bin"

        # Create 1MB file (much larger than 64KB chunk)
        size = 1024 * 1024  # 1MB
        content = b"A" * size
        file_path.write_bytes(content)

        digest = hash_file(file_path)

        # Should match block hash
        expected = hash_bytes(content)
        assert digest.formatted == expected.formatted

    def test_hash_file_unicode_content(self, tmp_path):
        """Test hashing file with Unicode content."""
        file_path = tmp_path / "unicode.txt"
        text = "Hello 🔥 World"
        content = text.encode("utf-8")
        file_path.write_bytes(content)

        digest = hash_file(file_path)

        # Should match block hash
        expected = hash_bytes(content)
        assert digest.formatted == expected.formatted

    def test_hash_file_binary_data(self, tmp_path):
        """Test hashing file with binary data."""
        file_path = tmp_path / "binary.bin"
        content = bytes([0, 1, 2, 3, 255, 254, 253])
        file_path.write_bytes(content)

        digest = hash_file(file_path)

        expected = hash_bytes(content)
        assert digest.formatted == expected.formatted


class TestHashFileErrors:
    """Test hash_file() error handling."""

    def test_hash_file_not_found(self, tmp_path):
        """Test hashing nonexistent file raises FileNotFoundError."""
        nonexistent = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError, match="File not found"):
            hash_file(nonexistent)

    def test_hash_file_directory(self, tmp_path):
        """Test hashing directory raises IsADirectoryError."""
        directory = tmp_path / "dir"
        directory.mkdir()

        with pytest.raises(IsADirectoryError, match="directory, not a file"):
            hash_file(directory)

    def test_hash_file_permission_error(self, tmp_path):
        """Test hashing unreadable file raises PermissionError."""
        # This test may be skipped on some platforms
        file_path = tmp_path / "unreadable.txt"
        file_path.write_bytes(b"content")

        # Remove read permissions
        file_path.chmod(0o000)

        try:
            with pytest.raises(PermissionError, match="Permission denied"):
                hash_file(file_path)
        finally:
            # Restore permissions for cleanup
            file_path.chmod(0o644)


class TestHashDispatcher:
    """Test hash() dispatcher function."""

    def test_hash_bytes(self):
        """Test hash() with bytes."""
        data = b"Hello, World!"
        digest = hash(data)

        expected = hash_bytes(data)
        assert digest.formatted == expected.formatted

    def test_hash_string(self):
        """Test hash() with string."""
        text = "Hello, World!"
        digest = hash(text)

        expected = hash_string(text)
        assert digest.formatted == expected.formatted

    def test_hash_path(self, tmp_path):
        """Test hash() with Path object."""
        file_path = tmp_path / "test.txt"
        content = b"Hello, World!"
        file_path.write_bytes(content)

        digest = hash(file_path)

        expected = hash_bytes(content)
        assert digest.formatted == expected.formatted

    def test_hash_with_algorithm(self):
        """Test hash() with explicit algorithm."""
        data = b"test"
        digest = hash(data, Algorithm.SHA256)

        assert digest.algorithm == Algorithm.SHA256
        expected = hash_bytes(data, Algorithm.SHA256)
        assert digest.formatted == expected.formatted

    def test_hash_string_unicode(self):
        """Test hash() with Unicode string."""
        text = "Hello 🔥 World"
        digest = hash(text)

        expected = hash_string(text)
        assert digest.formatted == expected.formatted

    def test_hash_unsupported_type(self):
        """Test hash() with unsupported type raises TypeError."""
        with pytest.raises(TypeError, match="Unsupported data type"):
            hash(123)  # int not supported

        with pytest.raises(TypeError, match="Unsupported data type"):
            hash([1, 2, 3])  # list not supported


class TestDispatcherEquivalence:
    """Test hash() dispatcher produces identical results to specific functions."""

    def test_bytes_equivalence(self):
        """Test hash(bytes) == hash_bytes(bytes)."""
        data = b"Test data"

        dispatcher_result = hash(data)
        direct_result = hash_bytes(data)

        assert dispatcher_result.formatted == direct_result.formatted
        assert dispatcher_result.hex == direct_result.hex
        assert dispatcher_result.bytes == direct_result.bytes

    def test_string_equivalence(self):
        """Test hash(str) == hash_string(str)."""
        text = "Test string"

        dispatcher_result = hash(text)
        direct_result = hash_string(text)

        assert dispatcher_result.formatted == direct_result.formatted
        assert dispatcher_result.hex == direct_result.hex

    def test_file_equivalence(self, tmp_path):
        """Test hash(Path) == hash_file(Path)."""
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(b"File content")

        dispatcher_result = hash(file_path)
        direct_result = hash_file(file_path)

        assert dispatcher_result.formatted == direct_result.formatted
        assert dispatcher_result.hex == direct_result.hex

    def test_all_types_same_data(self, tmp_path):
        """Test hash() produces same result for same data via different types."""
        data = b"Hello, World!"
        text = data.decode("utf-8")

        # Create file with same content
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(data)

        digest_bytes = hash(data)
        digest_string = hash(text)
        digest_file = hash(file_path)

        # All should produce identical results
        assert digest_bytes.formatted == digest_string.formatted
        assert digest_string.formatted == digest_file.formatted


class TestFileHashingChunks:
    """Test file hashing with various chunk sizes."""

    def test_file_smaller_than_chunk(self, tmp_path):
        """Test file smaller than chunk size (64KB)."""
        file_path = tmp_path / "small.txt"
        content = b"Small file content"
        file_path.write_bytes(content)

        digest = hash_file(file_path)
        expected = hash_bytes(content)
        assert digest.formatted == expected.formatted

    def test_file_exactly_one_chunk(self, tmp_path):
        """Test file exactly one chunk size (64KB)."""
        file_path = tmp_path / "one_chunk.bin"
        content = b"X" * (64 * 1024)  # Exactly 64KB
        file_path.write_bytes(content)

        digest = hash_file(file_path)
        expected = hash_bytes(content)
        assert digest.formatted == expected.formatted

    def test_file_multiple_chunks(self, tmp_path):
        """Test file spanning multiple chunks."""
        file_path = tmp_path / "multi_chunk.bin"
        # 3 chunks + 1KB
        content = b"M" * (64 * 1024 * 3 + 1024)
        file_path.write_bytes(content)

        digest = hash_file(file_path)
        expected = hash_bytes(content)
        assert digest.formatted == expected.formatted

    def test_file_large_10mb(self, tmp_path):
        """Test large file (10MB) as specified in plan."""
        file_path = tmp_path / "large_10mb.bin"

        # Create 10MB file
        size = 10 * 1024 * 1024  # 10MB
        content = b"L" * size
        file_path.write_bytes(content)

        digest = hash_file(file_path)
        expected = hash_bytes(content)
        assert digest.formatted == expected.formatted


class TestFileHashingIntegration:
    """Test integration scenarios."""

    def test_hash_file_then_compare(self, tmp_path):
        """Test hashing two files and comparing."""
        from pyfulmen.fulhash import compare_digests

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file3 = tmp_path / "file3.txt"

        file1.write_bytes(b"Same content")
        file2.write_bytes(b"Same content")
        file3.write_bytes(b"Different content")

        digest1 = hash_file(file1)
        digest2 = hash_file(file2)
        digest3 = hash_file(file3)

        # Same content should match
        assert compare_digests(digest1, digest2)

        # Different content should not match
        assert not compare_digests(digest1, digest3)

    def test_hash_file_format_parse(self, tmp_path):
        """Test hashing file and parsing formatted string."""
        from pyfulmen.fulhash import parse_checksum

        file_path = tmp_path / "test.txt"
        file_path.write_bytes(b"Test content")

        digest = hash_file(file_path)
        formatted = digest.formatted

        # Parse the formatted string
        algo, hex_digest = parse_checksum(formatted)

        assert algo == digest.algorithm.value
        assert hex_digest == digest.hex

    def test_multiple_algorithms_same_file(self, tmp_path):
        """Test hashing same file with different algorithms."""
        file_path = tmp_path / "test.txt"
        content = b"Multi-algorithm test"
        file_path.write_bytes(content)

        digest_xxh3 = hash_file(file_path, Algorithm.XXH3_128)
        digest_sha = hash_file(file_path, Algorithm.SHA256)

        # Different algorithms should produce different results
        assert digest_xxh3.algorithm == Algorithm.XXH3_128
        assert digest_sha.algorithm == Algorithm.SHA256
        assert digest_xxh3.formatted != digest_sha.formatted

        # But both should be valid
        from pyfulmen.fulhash import validate_checksum_string

        assert validate_checksum_string(digest_xxh3.formatted)
        assert validate_checksum_string(digest_sha.formatted)
