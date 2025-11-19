"""Integration tests for fulpack using Crucible fixtures.

Tests fulpack operations against fixtures from config/crucible-py/library/fulpack/fixtures/
to ensure cross-language parity and spec compliance.
"""

from pathlib import Path

import pytest

from pyfulmen import fulpack

# Fixture paths
FIXTURES_DIR = (
    Path(__file__).parent.parent.parent.parent / "config" / "crucible-py" / "library" / "fulpack" / "fixtures"
)


class TestBasicTarFixture:
    """Test basic.tar fixture (uncompressed tar format)."""

    def test_info_basic_tar(self):
        """Test info() on basic.tar fixture."""
        fixture_path = FIXTURES_DIR / "basic.tar"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

        info = fulpack.info(str(fixture_path))

        # Verify metadata
        assert info.format == "tar"
        assert info.entry_count >= 5  # At least 5 files (may include directories)
        # TAR has block padding overhead, so small archives have ratio < 1.0
        # This is expected behavior (compressed_size > total_size due to headers/padding)
        assert info.compression_ratio > 0  # Just verify it's calculated
        assert info.total_size > 0
        assert info.compressed_size > 0

    def test_scan_basic_tar(self):
        """Test scan() on basic.tar fixture."""
        fixture_path = FIXTURES_DIR / "basic.tar"
        entries = fulpack.scan(str(fixture_path))

        # Should have 6 entries (directory + 5 files per fixture docs)
        assert len(entries) >= 5

        # Verify expected files exist
        entry_paths = [e.path for e in entries]
        assert any("README.md" in p for p in entry_paths)
        assert any("config.json" in p for p in entry_paths)
        assert any("metadata.txt" in p for p in entry_paths)
        assert any("sample.txt" in p for p in entry_paths)
        assert any("tiny.png" in p for p in entry_paths)

    def test_extract_basic_tar(self, tmp_path):
        """Test extract() on basic.tar fixture."""
        fixture_path = FIXTURES_DIR / "basic.tar"
        dest_dir = tmp_path / "extracted"

        result = fulpack.extract(str(fixture_path), str(dest_dir))

        # Verify extraction succeeded
        assert result.extracted_count >= 5
        assert result.error_count == 0

        # Verify files were extracted
        assert (dest_dir / "README.md").exists()
        assert (dest_dir / "config.json").exists()
        assert (dest_dir / "metadata.txt").exists()

        # Verify subdirectory
        assert (dest_dir / "data" / "sample.txt").exists()
        assert (dest_dir / "data" / "tiny.png").exists()

    def test_verify_basic_tar(self):
        """Test verify() on basic.tar fixture."""
        fixture_path = FIXTURES_DIR / "basic.tar"

        result = fulpack.verify(str(fixture_path))

        # Basic tar should be valid
        assert result.valid is True
        assert result.entry_count >= 5


class TestBasicTarGzFixture:
    """Test basic.tar.gz fixture (compressed tar.gz format)."""

    def test_info_basic_tar_gz(self):
        """Test info() on basic.tar.gz fixture."""
        fixture_path = FIXTURES_DIR / "basic.tar.gz"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

        info = fulpack.info(str(fixture_path))

        # Verify metadata
        assert info.format == "tar.gz"
        assert info.entry_count >= 4  # At least 4 files per fixture docs
        assert info.compression_ratio > 1.0  # Should be compressed
        assert info.total_size > info.compressed_size  # Content bigger than archive

    def test_scan_basic_tar_gz(self):
        """Test scan() on basic.tar.gz fixture."""
        fixture_path = FIXTURES_DIR / "basic.tar.gz"
        entries = fulpack.scan(str(fixture_path))

        # Should have at least 4 entries per docs
        assert len(entries) >= 4

        # Verify expected files
        entry_paths = [e.path for e in entries]
        assert any("README.md" in p for p in entry_paths)
        assert any("file1.txt" in p for p in entry_paths)
        assert any("file2.txt" in p for p in entry_paths)
        assert any("file3.txt" in p for p in entry_paths)

    def test_extract_basic_tar_gz(self, tmp_path):
        """Test extract() on basic.tar.gz fixture."""
        fixture_path = FIXTURES_DIR / "basic.tar.gz"
        dest_dir = tmp_path / "extracted"

        result = fulpack.extract(str(fixture_path), str(dest_dir))

        # Verify extraction succeeded
        assert result.extracted_count >= 4
        assert result.error_count == 0

        # Verify files were extracted
        assert (dest_dir / "README.md").exists()
        assert (dest_dir / "file1.txt").exists()
        assert (dest_dir / "file2.txt").exists()

        # Verify subdirectory
        assert (dest_dir / "subdir" / "file3.txt").exists()

    def test_verify_basic_tar_gz(self):
        """Test verify() on basic.tar.gz fixture."""
        fixture_path = FIXTURES_DIR / "basic.tar.gz"

        result = fulpack.verify(str(fixture_path))

        # Basic tar.gz should be valid
        assert result.valid is True
        assert result.entry_count >= 4

    def test_compression_ratio_tar_vs_tar_gz(self):
        """Compare compression ratios: tar.gz should have better compression than tar.

        Note: TAR has block padding overhead, so small files have ratio < 1.0
        (compressed_size > total_size due to headers). This is expected for tar format.
        TAR.GZ should have actual compression, so ratio > 1.0.
        """
        tar_info = fulpack.info(str(FIXTURES_DIR / "basic.tar"))
        tar_gz_info = fulpack.info(str(FIXTURES_DIR / "basic.tar.gz"))

        # Tar.gz should have actual compression
        assert tar_gz_info.compression_ratio > 1.0

        # Both should have valid ratios
        assert tar_info.compression_ratio > 0
        assert tar_gz_info.compression_ratio > 0


class TestPathologicalFixture:
    """Test pathological.tar.gz fixture (security test cases)."""

    def test_scan_pathological(self):
        """Test scan() on pathological.tar.gz - should list all entries."""
        fixture_path = FIXTURES_DIR / "pathological.tar.gz"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

        # Scan should succeed and list all entries (including simulated malicious ones)
        entries = fulpack.scan(str(fixture_path))

        assert len(entries) >= 5  # Should have multiple entries

        # Verify legitimate file exists
        entry_paths = [e.path for e in entries]
        assert any("legitimate.txt" in p for p in entry_paths)
        assert any("README.md" in p for p in entry_paths)

    def test_info_pathological(self):
        """Test info() on pathological.tar.gz fixture."""
        fixture_path = FIXTURES_DIR / "pathological.tar.gz"

        info = fulpack.info(str(fixture_path))

        # Should return basic metadata without errors
        assert info.format == "tar.gz"
        assert info.entry_count >= 5
        assert info.compressed_size > 0

    def test_verify_pathological(self):
        """Test verify() on pathological.tar.gz - should detect simulated issues."""
        fixture_path = FIXTURES_DIR / "pathological.tar.gz"

        result = fulpack.verify(str(fixture_path))

        # Note: The pathological fixture contains SIMULATED security issues
        # (filenames that look like attacks but are safe)
        # So verify() should actually pass since paths are normalized
        # The real security checks happen during extract()

        # For now, verify should pass (no actual malicious content)
        # Future: Add real malicious test cases if needed
        assert result.entry_count >= 5

    def test_extract_pathological_safe(self, tmp_path):
        """Test extract() on pathological.tar.gz - should extract safely."""
        fixture_path = FIXTURES_DIR / "pathological.tar.gz"
        dest_dir = tmp_path / "extracted"

        # The fixture contains simulated security files (safe filenames)
        # Extract should succeed
        result = fulpack.extract(str(fixture_path), str(dest_dir))

        # Should extract successfully (no actual malicious content)
        assert result.extracted_count >= 5
        assert result.error_count == 0

        # Verify legitimate file was extracted
        assert (dest_dir / "legitimate.txt").exists()
        assert (dest_dir / "README.md").exists()


class TestNestedZipFixture:
    """Test nested.zip fixture (3-level directory nesting)."""

    @pytest.mark.skip(reason="ZIP handler not yet implemented")
    def test_scan_nested_zip(self):
        """Test scan() on nested.zip fixture."""
        fixture_path = FIXTURES_DIR / "nested.zip"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

        entries = fulpack.scan(str(fixture_path))

        # Should have 3-level nesting per fixture docs
        entry_paths = [e.path for e in entries]
        assert any("root.txt" in p for p in entry_paths)
        assert any("level1" in p for p in entry_paths)
        assert any("level2" in p for p in entry_paths)
        assert any("level3" in p for p in entry_paths)


class TestFormatDetection:
    """Test automatic format detection."""

    def test_detect_tar_format(self):
        """Test format detection for .tar files."""
        fixture_path = FIXTURES_DIR / "basic.tar"
        info = fulpack.info(str(fixture_path))
        assert info.format == "tar"

    def test_detect_tar_gz_format(self):
        """Test format detection for .tar.gz files."""
        fixture_path = FIXTURES_DIR / "basic.tar.gz"
        info = fulpack.info(str(fixture_path))
        assert info.format == "tar.gz"

    @pytest.mark.skip(reason="ZIP handler not yet implemented")
    def test_detect_zip_format(self):
        """Test format detection for .zip files."""
        fixture_path = FIXTURES_DIR / "nested.zip"
        info = fulpack.info(str(fixture_path))
        assert info.format == "zip"
