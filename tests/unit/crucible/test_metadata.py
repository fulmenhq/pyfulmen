"""Tests for Crucible metadata computation utilities."""

from datetime import datetime
from pathlib import Path

import pytest

from pyfulmen.crucible._metadata import (
    compute_checksum,
    get_file_format,
    get_file_size,
    get_modified_time,
)


class TestComputeChecksum:
    """Tests for compute_checksum function."""

    def test_compute_checksum_basic(self, tmp_path):
        """Compute checksum for simple file."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        checksum = compute_checksum(test_file)

        assert isinstance(checksum, str)
        assert len(checksum) == 64

    def test_compute_checksum_deterministic(self, tmp_path):
        """Same content produces same checksum."""
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"

        content = '{"test": "data", "value": 123}'
        file1.write_text(content)
        file2.write_text(content)

        checksum1 = compute_checksum(file1)
        checksum2 = compute_checksum(file2)

        assert checksum1 == checksum2

    def test_compute_checksum_different_content(self, tmp_path):
        """Different content produces different checksum."""
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"

        file1.write_text('{"test": "data1"}')
        file2.write_text('{"test": "data2"}')

        checksum1 = compute_checksum(file1)
        checksum2 = compute_checksum(file2)

        assert checksum1 != checksum2

    def test_compute_checksum_large_file(self, tmp_path):
        """Handle large files with buffered reads."""
        large_file = tmp_path / "large.bin"

        with large_file.open("wb") as f:
            f.write(b"x" * (128 * 1024))

        checksum = compute_checksum(large_file)

        assert isinstance(checksum, str)
        assert len(checksum) == 64

    def test_compute_checksum_missing_file(self, tmp_path):
        """Raise FileNotFoundError for missing file."""
        missing_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            compute_checksum(missing_file)

    def test_compute_checksum_custom_buffer(self, tmp_path):
        """Use custom buffer size."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        checksum = compute_checksum(test_file, buffer_size=1024)

        assert isinstance(checksum, str)
        assert len(checksum) == 64


class TestGetFileSize:
    """Tests for get_file_size function."""

    def test_get_file_size_basic(self, tmp_path):
        """Get size of simple file."""
        test_file = tmp_path / "test.json"
        content = '{"test": "data"}'
        test_file.write_text(content)

        size = get_file_size(test_file)

        assert size == len(content.encode())

    def test_get_file_size_empty_file(self, tmp_path):
        """Get size of empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        size = get_file_size(empty_file)

        assert size == 0

    def test_get_file_size_large_file(self, tmp_path):
        """Get size of large file."""
        large_file = tmp_path / "large.bin"
        expected_size = 100 * 1024

        with large_file.open("wb") as f:
            f.write(b"x" * expected_size)

        size = get_file_size(large_file)

        assert size == expected_size

    def test_get_file_size_missing_file(self, tmp_path):
        """Raise FileNotFoundError for missing file."""
        missing_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            get_file_size(missing_file)


class TestGetFileFormat:
    """Tests for get_file_format function."""

    def test_get_file_format_json(self):
        """Extract 'json' format from .json file."""
        path = Path("/path/to/schema.json")
        assert get_file_format(path) == "json"

    def test_get_file_format_yaml(self):
        """Extract 'yaml' format from .yaml file."""
        path = Path("/path/to/config.yaml")
        assert get_file_format(path) == "yaml"

    def test_get_file_format_yml(self):
        """Extract 'yml' format from .yml file."""
        path = Path("/path/to/config.yml")
        assert get_file_format(path) == "yml"

    def test_get_file_format_md(self):
        """Extract 'md' format from .md file."""
        path = Path("/path/to/doc.md")
        assert get_file_format(path) == "md"

    def test_get_file_format_multiple_dots(self):
        """Handle filename with multiple dots."""
        path = Path("/path/to/schema.v1.0.0.json")
        assert get_file_format(path) == "json"

    def test_get_file_format_no_extension(self):
        """Return 'unknown' for file without extension."""
        path = Path("/path/to/README")
        assert get_file_format(path) == "unknown"

    def test_get_file_format_dot_file(self):
        """Handle dot files (hidden files) without extension."""
        path = Path("/path/to/.gitignore")
        assert get_file_format(path) == "unknown"


class TestGetModifiedTime:
    """Tests for get_modified_time function."""

    def test_get_modified_time_from_sync_metadata(self, tmp_path):
        """Prefer sync metadata timestamp over file mtime."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        sync_metadata = {"syncedAt": "2025-10-20T18:42:11Z"}
        modified = get_modified_time(test_file, sync_metadata)

        assert modified == "2025-10-20T18:42:11Z"

    def test_get_modified_time_from_file_mtime(self, tmp_path):
        """Fall back to file mtime when no sync metadata."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        modified = get_modified_time(test_file)

        assert modified is not None
        assert isinstance(modified, str)
        assert "T" in modified
        assert modified.endswith("Z")

    def test_get_modified_time_empty_sync_metadata(self, tmp_path):
        """Fall back to file mtime with empty sync metadata."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        sync_metadata = {}
        modified = get_modified_time(test_file, sync_metadata)

        assert modified is not None
        assert isinstance(modified, str)

    def test_get_modified_time_iso8601_format(self, tmp_path):
        """Modified time is ISO-8601 formatted with Z suffix."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        modified = get_modified_time(test_file)

        assert modified is not None
        dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
        assert dt.tzinfo is not None

    def test_get_modified_time_missing_file(self, tmp_path):
        """Return None for missing file."""
        missing_file = tmp_path / "nonexistent.json"

        modified = get_modified_time(missing_file)

        assert modified is None

    def test_get_modified_time_sync_metadata_priority(self, tmp_path):
        """Sync metadata takes precedence over file mtime."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}')

        sync_time = "2020-01-01T00:00:00Z"
        sync_metadata = {"syncedAt": sync_time}

        modified = get_modified_time(test_file, sync_metadata)

        assert modified == sync_time
