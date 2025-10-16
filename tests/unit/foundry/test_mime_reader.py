"""Tests for MIME detection from streams and files.

Tests for reader-based and file-based detection with gofulmen parity.
"""

import io

import pytest

from pyfulmen.foundry.mime_detection import (
    detect_mime_type_from_file,
    detect_mime_type_from_reader,
)


class TestDetectMimeTypeFromReader:
    """Streaming detection tests (gofulmen parity)."""

    def test_json_detection_from_stream(self):
        data = b'{"key": "value"}'
        reader = io.BytesIO(data)

        mime, new_reader = detect_mime_type_from_reader(reader, 512)

        assert mime is not None
        assert mime.id == "json"

        # Verify reader preservation: read all data back
        read_data = new_reader.read()
        assert read_data == data

    def test_short_reader_less_than_max_bytes(self):
        data = b'{"short":"json"}'
        reader = io.BytesIO(data)

        mime, new_reader = detect_mime_type_from_reader(reader, 512)

        assert mime.id == "json"
        assert new_reader.read() == data

    def test_large_reader_preserves_all_data(self):
        # Create input larger than detection buffer
        header = b'{"large": "json", "data": ['
        large_data = b"x" * 1000
        footer = b"]}"
        data = header + large_data + footer

        reader = io.BytesIO(data)

        mime, new_reader = detect_mime_type_from_reader(reader, 100)

        assert mime.id == "json"
        # Verify ALL data preserved
        assert new_reader.read() == data

    def test_empty_reader(self):
        reader = io.BytesIO(b"")

        mime, new_reader = detect_mime_type_from_reader(reader, 512)

        assert mime is None
        assert new_reader.read() == b""

    def test_default_max_bytes(self):
        data = b'{"key": "value"}'
        reader = io.BytesIO(data)

        # Pass 0 to use default (512)
        mime, new_reader = detect_mime_type_from_reader(reader, 0)

        assert mime.id == "json"
        assert new_reader.read() == data

    def test_xml_from_stream(self):
        data = b'<?xml version="1.0"?><root><item>data</item></root>'
        reader = io.BytesIO(data)

        mime, new_reader = detect_mime_type_from_reader(reader, 512)

        assert mime.id == "xml"
        assert new_reader.read() == data

    def test_yaml_from_stream(self):
        data = b"name: John Doe\nage: 30\ncity: New York\n"
        reader = io.BytesIO(data)

        mime, new_reader = detect_mime_type_from_reader(reader, 512)

        assert mime.id == "yaml"
        assert new_reader.read() == data

    def test_csv_from_stream(self):
        data = b"name,age,city\nJohn,30,NYC\nJane,25,LA\n"
        reader = io.BytesIO(data)

        mime, new_reader = detect_mime_type_from_reader(reader, 512)

        assert mime.id == "csv"
        assert new_reader.read() == data

    def test_plain_text_from_stream(self):
        data = b"This is plain text content without any special formatting."
        reader = io.BytesIO(data)

        mime, new_reader = detect_mime_type_from_reader(reader, 512)

        assert mime.id == "plain-text"
        assert new_reader.read() == data


class TestDetectMimeTypeFromFile:
    """File detection tests (gofulmen parity)."""

    def test_json_file(self, tmp_path):
        file = tmp_path / "test.json"
        file.write_bytes(b'{"key": "value"}')

        mime = detect_mime_type_from_file(file)

        assert mime is not None
        assert mime.id == "json"

    def test_xml_file(self, tmp_path):
        file = tmp_path / "test.xml"
        file.write_bytes(b'<?xml version="1.0"?><root/>')

        mime = detect_mime_type_from_file(file)
        assert mime.id == "xml"

    def test_yaml_file(self, tmp_path):
        file = tmp_path / "test.yaml"
        file.write_bytes(b"name: test\nvalue: 123\n")

        mime = detect_mime_type_from_file(file)
        assert mime.id == "yaml"

    def test_csv_file(self, tmp_path):
        file = tmp_path / "test.csv"
        file.write_bytes(b"col1,col2,col3\nval1,val2,val3\n")

        mime = detect_mime_type_from_file(file)
        assert mime.id == "csv"

    def test_plain_text_file(self, tmp_path):
        file = tmp_path / "test.txt"
        file.write_bytes(b"This is plain text.")

        mime = detect_mime_type_from_file(file)
        assert mime.id == "plain-text"

    def test_empty_file(self, tmp_path):
        file = tmp_path / "empty.txt"
        file.write_bytes(b"")

        mime = detect_mime_type_from_file(file)
        assert mime is None  # Empty file, not an error

    def test_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            detect_mime_type_from_file("/nonexistent/file.txt")

    def test_large_file(self, tmp_path):
        file = tmp_path / "large.json"
        header = b'{"large": "file", "data": ['
        large_data = b"x" * 10000  # 10KB
        footer = b"]}"
        file.write_bytes(header + large_data + footer)

        mime = detect_mime_type_from_file(file)
        assert mime.id == "json"

    def test_file_with_bom(self, tmp_path):
        file = tmp_path / "bom.json"
        file.write_bytes(b'\xef\xbb\xbf{"key": "value"}')

        mime = detect_mime_type_from_file(file)
        assert mime.id == "json"

    def test_string_path(self, tmp_path):
        file = tmp_path / "test.json"
        file.write_bytes(b'{"key": "value"}')

        # Test with string path (not Path object)
        mime = detect_mime_type_from_file(str(file))
        assert mime.id == "json"
