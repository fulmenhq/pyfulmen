"""Unit tests for TAR handler."""

from crucible.fulpack import ArchiveFormat
from pyfulmen.fulpack.formats.tar import TarHandler


class TestTarHandler:
    """Test TAR and TAR.GZ format handler."""

    def test_tar_gz_create_and_info(self, tmp_path):
        """Test creating and inspecting a tar.gz archive."""
        handler = TarHandler(ArchiveFormat.TAR_GZ)

        # Create test files
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("Hello")
        (source_dir / "file2.txt").write_text("World")

        # Create archive
        archive_path = tmp_path / "test.tar.gz"
        info = handler.create(
            source=[str(source_dir)],
            output=str(archive_path),
            options={},
        )

        assert archive_path.exists()
        assert info.entry_count >= 2  # At least 2 files
        assert info.format == "tar.gz"
        assert info.compression_ratio > 0

        # Get info
        info2 = handler.info(str(archive_path))
        assert info2.entry_count == info.entry_count
        assert info2.format == "tar.gz"

    def test_tar_uncompressed(self, tmp_path):
        """Test uncompressed TAR format."""
        handler = TarHandler(ArchiveFormat.TAR)

        # Create test file
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("content")

        # Create archive
        archive_path = tmp_path / "test.tar"
        info = handler.create(
            source=[str(source_dir)],
            output=str(archive_path),
            options={},
        )

        assert archive_path.exists()
        assert info.format == "tar"
        # TAR has block padding so compressed_size > total_size for small files
        # Compression ratio = total_size / compressed_size, so it will be < 1 for small files
        assert info.compression_ratio > 0

    def test_extract(self, tmp_path):
        """Test extracting an archive."""
        handler = TarHandler(ArchiveFormat.TAR_GZ)

        # Create archive
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("content")

        archive_path = tmp_path / "test.tar.gz"
        handler.create([str(source_dir)], str(archive_path), {})

        # Extract
        dest_dir = tmp_path / "dest"
        result = handler.extract(str(archive_path), str(dest_dir), {})

        assert result.extracted_count >= 1
        assert result.error_count == 0
        assert (dest_dir / "source" / "test.txt").exists()

    def test_scan(self, tmp_path):
        """Test scanning archive entries."""
        handler = TarHandler(ArchiveFormat.TAR_GZ)

        # Create archive with multiple files
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("a")
        (source_dir / "file2.txt").write_text("b")

        archive_path = tmp_path / "test.tar.gz"
        handler.create([str(source_dir)], str(archive_path), {})

        # Scan
        entries = handler.scan(str(archive_path), {})

        assert len(entries) >= 2
        entry_names = [e.path for e in entries]
        assert any("file1.txt" in name for name in entry_names)
        assert any("file2.txt" in name for name in entry_names)

    def test_verify(self, tmp_path):
        """Test archive verification."""
        handler = TarHandler(ArchiveFormat.TAR_GZ)

        # Create valid archive
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("content")

        archive_path = tmp_path / "test.tar.gz"
        handler.create([str(source_dir)], str(archive_path), {})

        # Verify
        result = handler.verify(str(archive_path))

        assert result.valid is True
        assert result.entry_count >= 1
        assert "structure_valid" in result.checks_performed
