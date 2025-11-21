"""Unit tests for GZIP handler."""

import pytest

from crucible.fulpack import ArchiveFormat
from pyfulmen.fulpack.exceptions import FulpackError
from pyfulmen.fulpack.formats.gzip import GzipHandler


class TestGzipHandler:
    """Test GZIP format handler."""

    def test_gzip_create_and_info(self, tmp_path):
        """Test creating and inspecting a gzip archive."""
        handler = GzipHandler(ArchiveFormat.GZIP)

        # Create test file
        source_file = tmp_path / "file.txt"
        source_file.write_text("Hello World")

        # Create archive
        archive_path = tmp_path / "file.txt.gz"
        info = handler.create(
            source=[str(source_file)],
            output=str(archive_path),
            options={},
        )

        assert archive_path.exists()
        assert info.entry_count == 1
        assert info.format == "gzip"
        assert info.compression_ratio is not None and info.compression_ratio > 0

        # Get info
        info2 = handler.info(str(archive_path))
        assert info2.entry_count == 1
        assert info2.format == "gzip"

    def test_gzip_create_fail_multiple(self, tmp_path):
        """Test that creating gzip from multiple files fails."""
        handler = GzipHandler(ArchiveFormat.GZIP)

        f1 = tmp_path / "f1"
        f1.touch()
        f2 = tmp_path / "f2"
        f2.touch()

        with pytest.raises(FulpackError, match="single file"):
            handler.create([str(f1), str(f2)], str(tmp_path / "out.gz"), {})

    def test_gzip_create_fail_directory(self, tmp_path):
        """Test that creating gzip from directory fails."""
        handler = GzipHandler(ArchiveFormat.GZIP)

        d = tmp_path / "dir"
        d.mkdir()

        with pytest.raises(FulpackError, match="directories"):
            handler.create([str(d)], str(tmp_path / "out.gz"), {})

    def test_gzip_extract(self, tmp_path):
        """Test extracting a gzip archive."""
        handler = GzipHandler(ArchiveFormat.GZIP)

        # Create archive
        source_file = tmp_path / "test.txt"
        source_file.write_text("content")

        archive_path = tmp_path / "test.txt.gz"
        handler.create([str(source_file)], str(archive_path), {})

        # Extract
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        result = handler.extract(str(archive_path), str(dest_dir), {})

        assert result.extracted_count == 1
        assert result.error_count == 0
        assert (dest_dir / "test.txt").exists()
        assert (dest_dir / "test.txt").read_text() == "content"

    def test_gzip_scan(self, tmp_path):
        """Test scanning gzip archive."""
        handler = GzipHandler(ArchiveFormat.GZIP)

        # Create archive
        source_file = tmp_path / "data.csv"
        source_file.write_text("a,b,c")

        archive_path = tmp_path / "data.csv.gz"
        handler.create([str(source_file)], str(archive_path), {})

        # Scan
        entries = handler.scan(str(archive_path), {})

        assert len(entries) == 1
        assert entries[0].path == "data.csv"
        assert entries[0].size > 0

    def test_gzip_verify(self, tmp_path):
        """Test gzip verification."""
        handler = GzipHandler(ArchiveFormat.GZIP)

        # Create archive
        source_file = tmp_path / "test.txt"
        source_file.write_text("content")
        archive_path = tmp_path / "test.txt.gz"
        handler.create([str(source_file)], str(archive_path), {})

        # Verify
        result = handler.verify(str(archive_path))

        assert result.valid is True
        assert result.checksums_verified == 1
