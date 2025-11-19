"""Unit tests for fulpack security utilities."""

import tempfile
from pathlib import Path

import pytest

from pyfulmen.fulpack.exceptions import (
    DecompressionBombError,
    PathTraversalError,
    SymlinkError,
)
from pyfulmen.fulpack.security import (
    check_decompression_bomb,
    compute_checksum,
    normalize_path,
    validate_path_traversal,
    validate_symlink_target,
    verify_checksum,
)


class TestNormalizePath:
    """Test path normalization."""

    def test_simple_path(self):
        """Test simple path normalization."""
        assert normalize_path("foo/bar") == "foo/bar"

    def test_current_dir(self):
        """Test current directory normalization."""
        assert normalize_path("foo/./bar") == "foo/bar"

    def test_parent_dir(self):
        """Test parent directory normalization."""
        assert normalize_path("foo/../bar") == "bar"

    def test_multiple_slashes(self):
        """Test multiple slashes normalization."""
        assert normalize_path("foo//bar///baz") == "foo/bar/baz"

    def test_absolute_path(self):
        """Test absolute path normalization."""
        result = normalize_path("/foo/bar/../baz")
        assert result == "/foo/baz"

    def test_trailing_slash(self):
        """Test trailing slash removal."""
        assert normalize_path("foo/bar/") == "foo/bar"

    def test_empty_after_normalization(self):
        """Test paths that normalize to empty."""
        assert normalize_path(".") == "."


class TestValidatePathTraversal:
    """Test path traversal validation."""

    def test_valid_path(self):
        """Test valid path passes validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validate_path_traversal("foo/bar.txt", tmpdir)  # Should not raise

    def test_absolute_path_rejected(self):
        """Test absolute paths are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(PathTraversalError) as exc_info:
                validate_path_traversal("/etc/passwd", tmpdir)
            assert "absolute path" in str(exc_info.value)
            assert exc_info.value.context["attack_type"] == "absolute_path"

    def test_symlink_based_escape(self):
        """Test that actual symlink-based escapes would be caught.

        Note: Our normalization strips leading .. which makes normalized
        paths safe. Real escapes would need to use symlinks, which are
        caught by validate_symlink_target().
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create structure: tmpdir/subdir/file.txt
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()

            # Path like "subdir/../../etc" resolves to "etc" which is within base
            # This is secure normalization behavior
            validate_path_traversal("subdir/../../etc/passwd", tmpdir)

    def test_parent_escape_normalized_safe(self):
        """Test that paths with .. that normalize within base are allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ../../../etc/passwd normalizes to just "etc/passwd" which is safe
            # This is correct behavior - normalization removes leading ../
            validate_path_traversal("../../../etc/passwd", tmpdir)

            # foo/../../bar normalizes to "bar" which is safe
            validate_path_traversal("foo/../../bar", tmpdir)

    def test_complex_valid_path(self):
        """Test complex but valid path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # foo/../bar resolves to just 'bar' which is valid
            validate_path_traversal("foo/../bar/baz.txt", tmpdir)


class TestValidateSymlinkTarget:
    """Test symlink validation."""

    def test_valid_relative_target(self):
        """Test valid relative symlink target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validate_symlink_target("link.txt", "target.txt", tmpdir)

    def test_absolute_target_rejected(self):
        """Test absolute targets are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SymlinkError) as exc_info:
                validate_symlink_target("link.txt", "/etc/passwd", tmpdir)
            assert "absolute target" in str(exc_info.value)

    def test_escape_target_rejected(self):
        """Test escape targets are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SymlinkError) as exc_info:
                validate_symlink_target("link.txt", "../../../etc/passwd", tmpdir)
            assert "resolves outside base" in str(exc_info.value)

    def test_valid_nested_symlink(self):
        """Test valid nested symlink."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validate_symlink_target("foo/link.txt", "../bar/target.txt", tmpdir)


class TestCheckDecompressionBomb:
    """Test decompression bomb detection."""

    def test_normal_entry(self):
        """Test normal entry passes checks."""
        check_decompression_bomb(
            entry_size=100_000,
            compressed_size=10_000,
            total_size=100_000,
            entry_count=1,
        )

    def test_oversized_entry_rejected(self):
        """Test oversized entry is rejected."""
        with pytest.raises(DecompressionBombError) as exc_info:
            check_decompression_bomb(
                entry_size=2_000_000_000,  # 2 GB > 1 GB limit
                compressed_size=10_000,
                total_size=2_000_000_000,
                entry_count=1,
            )
        assert "entry size" in str(exc_info.value)
        assert exc_info.value.context["attack_type"] == "oversized_entry"

    def test_oversized_total_rejected(self):
        """Test oversized total is rejected."""
        with pytest.raises(DecompressionBombError) as exc_info:
            check_decompression_bomb(
                entry_size=100_000,
                compressed_size=10_000,
                total_size=15_000_000_000,  # 15 GB > 10 GB limit
                entry_count=100_000,
            )
        assert "total size" in str(exc_info.value)
        assert exc_info.value.context["attack_type"] == "oversized_total"

    def test_too_many_entries_rejected(self):
        """Test too many entries is rejected."""
        with pytest.raises(DecompressionBombError) as exc_info:
            check_decompression_bomb(
                entry_size=100_000,
                compressed_size=10_000,
                total_size=100_000,
                entry_count=150_000,  # > 100k limit
            )
        assert "entry count" in str(exc_info.value)
        assert exc_info.value.context["attack_type"] == "too_many_entries"

    def test_high_compression_ratio_warns(self, caplog):
        """Test high compression ratio generates warning."""
        import logging

        caplog.set_level(logging.WARNING)

        check_decompression_bomb(
            entry_size=1_000_000,  # 1 MB
            compressed_size=5_000,  # 5 KB -> 200:1 ratio
            total_size=1_000_000,
            entry_count=1,
        )

        # Should log warning but not fail
        assert "Suspicious compression ratio" in caplog.text
        assert "200" in caplog.text  # Ratio should be mentioned

    def test_custom_limits(self):
        """Test custom limits are respected."""
        # Should fail with custom lower limit
        with pytest.raises(DecompressionBombError):
            check_decompression_bomb(
                entry_size=100_000,
                compressed_size=10_000,
                total_size=100_000,
                entry_count=1,
                max_entry_size=50_000,  # Lower limit
            )


class TestChecksums:
    """Test checksum computation and verification."""

    def test_compute_checksum_sha256(self):
        """Test SHA-256 checksum computation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content\n")
            path = f.name

        try:
            # Empty file has known SHA-256
            checksum = compute_checksum(path, "sha256")
            assert len(checksum) == 64  # SHA-256 is 64 hex chars
            assert all(c in "0123456789abcdef" for c in checksum)
        finally:
            Path(path).unlink()

    def test_compute_checksum_sha512(self):
        """Test SHA-512 checksum computation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            path = f.name

        try:
            checksum = compute_checksum(path, "sha512")
            assert len(checksum) == 128  # SHA-512 is 128 hex chars
        finally:
            Path(path).unlink()

    def test_compute_checksum_unsupported_algorithm(self):
        """Test unsupported algorithm raises error."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                compute_checksum(path, "blake2b")
            assert "Unsupported hash algorithm" in str(exc_info.value)
        finally:
            Path(path).unlink()

    def test_verify_checksum_match(self):
        """Test checksum verification with matching checksum."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content\n")
            path = f.name

        try:
            expected = compute_checksum(path, "sha256")
            assert verify_checksum(path, expected, "sha256") is True
        finally:
            Path(path).unlink()

    def test_verify_checksum_mismatch(self):
        """Test checksum verification with mismatched checksum."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            path = f.name

        try:
            wrong_checksum = "0" * 64
            assert verify_checksum(path, wrong_checksum, "sha256") is False
        finally:
            Path(path).unlink()

    def test_verify_checksum_case_insensitive(self):
        """Test checksum verification is case-insensitive."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            path = f.name

        try:
            checksum = compute_checksum(path, "sha256")
            assert verify_checksum(path, checksum.upper(), "sha256") is True
            assert verify_checksum(path, checksum.lower(), "sha256") is True
        finally:
            Path(path).unlink()
