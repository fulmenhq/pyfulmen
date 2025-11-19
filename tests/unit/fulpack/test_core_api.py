"""Unit tests for core fulpack API."""

from pyfulmen import fulpack
from pyfulmen.fulpack import ArchiveFormat


class TestCoreAPI:
    """Test core fulpack public API functions."""

    def test_create_and_info(self, tmp_path):
        """Test create() and info() functions."""
        # Create test files
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("Hello")
        (source_dir / "file2.txt").write_text("World")

        # Create archive using public API
        archive_path = tmp_path / "test.tar.gz"
        info = fulpack.create(
            source=str(source_dir),
            output=str(archive_path),
            format=ArchiveFormat.TAR_GZ,
        )

        assert archive_path.exists()
        assert info.entry_count >= 2
        assert info.format == "tar.gz"
        assert info.compression_ratio > 0

        # Get info using public API
        info2 = fulpack.info(str(archive_path))
        assert info2.entry_count == info.entry_count
        assert info2.format == "tar.gz"

    def test_extract(self, tmp_path):
        """Test extract() function."""
        # Create test archive
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("content")

        archive_path = tmp_path / "test.tar.gz"
        fulpack.create([str(source_dir)], str(archive_path), ArchiveFormat.TAR_GZ)

        # Extract using public API
        dest_dir = tmp_path / "dest"
        result = fulpack.extract(str(archive_path), str(dest_dir))

        assert result.extracted_count >= 1
        assert result.error_count == 0
        assert (dest_dir / "source" / "test.txt").exists()

    def test_scan(self, tmp_path):
        """Test scan() function."""
        # Create test archive
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("a")
        (source_dir / "file2.txt").write_text("b")

        archive_path = tmp_path / "test.tar.gz"
        fulpack.create([str(source_dir)], str(archive_path), ArchiveFormat.TAR_GZ)

        # Scan using public API
        entries = fulpack.scan(str(archive_path))

        assert len(entries) >= 2
        entry_names = [e.path for e in entries]
        assert any("file1.txt" in name for name in entry_names)
        assert any("file2.txt" in name for name in entry_names)

    def test_verify(self, tmp_path):
        """Test verify() function."""
        # Create test archive
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("content")

        archive_path = tmp_path / "test.tar.gz"
        fulpack.create([str(source_dir)], str(archive_path), ArchiveFormat.TAR_GZ)

        # Verify using public API
        result = fulpack.verify(str(archive_path))

        assert result.valid is True
        assert result.entry_count >= 1

    def test_create_with_list_of_sources(self, tmp_path):
        """Test create() with list of source paths."""
        # Create multiple source directories
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "file1.txt").write_text("content1")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "file2.txt").write_text("content2")

        # Create archive from multiple sources
        archive_path = tmp_path / "multi.tar.gz"
        info = fulpack.create(
            source=[str(dir1), str(dir2)],
            output=str(archive_path),
            format=ArchiveFormat.TAR_GZ,
        )

        assert archive_path.exists()
        assert info.entry_count >= 2

        # Verify both directories are in archive
        entries = fulpack.scan(str(archive_path))
        entry_names = [e.path for e in entries]
        assert any("dir1" in name or "file1.txt" in name for name in entry_names)
        assert any("dir2" in name or "file2.txt" in name for name in entry_names)

    def test_format_detection(self, tmp_path):
        """Test automatic format detection in extract/scan/verify/info."""
        # Create tar.gz archive
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("content")

        archive_path = tmp_path / "test.tar.gz"
        fulpack.create([str(source_dir)], str(archive_path), ArchiveFormat.TAR_GZ)

        # Test that these functions auto-detect format
        info = fulpack.info(str(archive_path))
        assert info.format == "tar.gz"

        entries = fulpack.scan(str(archive_path))
        assert len(entries) >= 1

        result = fulpack.verify(str(archive_path))
        assert result.valid is True

        # Extract should also work with auto-detection
        dest_dir = tmp_path / "extracted"
        extract_result = fulpack.extract(str(archive_path), str(dest_dir))
        assert extract_result.extracted_count >= 1

    def test_create_with_options(self, tmp_path):
        """Test create() with compression level option."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("x" * 10000)  # Some compressible content

        # Create with max compression
        archive_path = tmp_path / "compressed.tar.gz"
        info = fulpack.create(
            source=str(source_dir),
            output=str(archive_path),
            format=ArchiveFormat.TAR_GZ,
            options={"compression_level": 9},
        )

        assert archive_path.exists()
        assert info.compression_ratio > 1.0  # Should be compressed
