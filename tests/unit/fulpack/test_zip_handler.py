"""Unit tests for ZIP handler."""

from crucible.fulpack import ArchiveFormat
from pyfulmen.fulpack.formats.zip import ZipHandler


class TestZipHandler:
    """Test ZIP format handler."""

    def test_zip_create_and_info(self, tmp_path):
        """Test creating and inspecting a zip archive."""
        handler = ZipHandler(ArchiveFormat.ZIP)

        # Create test files
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("Hello")
        (source_dir / "file2.txt").write_text("World")

        # Create archive
        archive_path = tmp_path / "test.zip"
        info = handler.create(
            source=[str(source_dir)],
            output=str(archive_path),
            options={},
        )

        assert archive_path.exists()
        assert info.entry_count >= 2  # At least 2 files
        assert info.format == "zip"
        assert info.compression_ratio is not None and info.compression_ratio > 0

        # Get info
        info2 = handler.info(str(archive_path))
        assert info2.entry_count == info.entry_count
        assert info2.format == "zip"

    def test_zip_extract(self, tmp_path):
        """Test extracting a zip archive."""
        handler = ZipHandler(ArchiveFormat.ZIP)

        # Create archive
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("content")

        archive_path = tmp_path / "test.zip"
        handler.create([str(source_dir)], str(archive_path), {})

        # Extract
        dest_dir = tmp_path / "dest"
        result = handler.extract(str(archive_path), str(dest_dir), {})

        assert result.extracted_count >= 1
        assert result.error_count == 0
        assert (dest_dir / "source" / "test.txt").exists()

    def test_zip_scan(self, tmp_path):
        """Test scanning zip archive entries."""
        handler = ZipHandler(ArchiveFormat.ZIP)

        # Create archive with multiple files
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("a")
        (source_dir / "file2.txt").write_text("b")

        archive_path = tmp_path / "test.zip"
        handler.create([str(source_dir)], str(archive_path), {})

        # Scan
        entries = handler.scan(str(archive_path), {})

        assert len(entries) >= 2
        entry_names = [e.path for e in entries]
        assert any("file1.txt" in name for name in entry_names)
        assert any("file2.txt" in name for name in entry_names)

    def test_zip_verify(self, tmp_path):
        """Test zip archive verification."""
        handler = ZipHandler(ArchiveFormat.ZIP)

        # Create valid archive
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("content")

        archive_path = tmp_path / "test.zip"
        handler.create([str(source_dir)], str(archive_path), {})

        # Verify
        result = handler.verify(str(archive_path))

        assert result.valid is True
        assert result.entry_count >= 1
        assert result.checks_performed is not None
        assert "structure_valid" in result.checks_performed
        assert "checksums_verified" in result.checks_performed
