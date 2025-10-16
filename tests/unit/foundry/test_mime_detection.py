"""Tests for MIME type detection from byte signatures.

Comprehensive test coverage for magic number detection with gofulmen parity.
"""

from pyfulmen.foundry.mime_detection import (
    _detect_csv,
    _detect_json,
    _detect_xml,
    _detect_yaml,
    _is_text_content,
    _trim_bom_and_whitespace,
    detect_mime_type,
)


class TestTrimBOMAndWhitespace:
    """Tests for BOM and whitespace trimming helper."""

    def test_utf8_bom_removed(self):
        data = b'\xef\xbb\xbf{"test": true}'
        result = _trim_bom_and_whitespace(data)
        assert result == b'{"test": true}'

    def test_utf16_le_bom_removed(self):
        data = b'\xff\xfe{"test": true}'
        result = _trim_bom_and_whitespace(data)
        assert result == b'{"test": true}'

    def test_utf16_be_bom_removed(self):
        data = b'\xfe\xff{"test": true}'
        result = _trim_bom_and_whitespace(data)
        assert result == b'{"test": true}'

    def test_leading_whitespace_removed(self):
        data = b'  \n\t{"test": true}'
        result = _trim_bom_and_whitespace(data)
        assert result == b'{"test": true}'

    def test_bom_and_whitespace_combined(self):
        data = b'\xef\xbb\xbf  \n{"test": true}'
        result = _trim_bom_and_whitespace(data)
        assert result == b'{"test": true}'

    def test_empty_data(self):
        result = _trim_bom_and_whitespace(b"")
        assert result == b""

    def test_no_bom_or_whitespace(self):
        data = b'{"test": true}'
        result = _trim_bom_and_whitespace(data)
        assert result == data


class TestIsTextContent:
    """Tests for text content detection heuristic."""

    def test_plain_text_detected(self):
        data = b"This is plain text content."
        assert _is_text_content(data) is True

    def test_multiline_text_detected(self):
        data = b"Line 1\nLine 2\nLine 3"
        assert _is_text_content(data) is True

    def test_text_with_tabs_detected(self):
        data = b"Column1\tColumn2\tColumn3"
        assert _is_text_content(data) is True

    def test_utf8_text_detected(self):
        data = "Hello 世界! Привет мир!".encode()
        assert _is_text_content(data) is True

    def test_binary_not_detected(self):
        data = b"\x00\x01\x02\x03\x04\xff\xfe\xfd"
        assert _is_text_content(data) is False

    def test_mostly_binary_not_detected(self):
        # 30% text, 70% binary (below 80% threshold)
        data = b"txt" + b"\x00" * 7
        assert _is_text_content(data) is False

    def test_empty_data(self):
        assert _is_text_content(b"") is False


class TestDetectJSON:
    """Tests for JSON detection heuristic."""

    def test_json_object_detected(self):
        data = b'{"key": "value"}'
        assert _detect_json(data) is True

    def test_json_array_detected(self):
        data = b'["item1", "item2"]'
        assert _detect_json(data) is True

    def test_json_with_nested_structure(self):
        data = b'{"outer": {"inner": "value"}}'
        assert _detect_json(data) is True

    def test_json_with_minimal_structure(self):
        data = b"{}"
        assert _detect_json(data) is True

    def test_not_json_text(self):
        data = b"This is plain text"
        assert _detect_json(data) is False

    def test_not_json_xml(self):
        data = b'<?xml version="1.0"?>'
        assert _detect_json(data) is False

    def test_empty_data(self):
        assert _detect_json(b"") is False


class TestDetectXML:
    """Tests for XML detection heuristic."""

    def test_xml_with_declaration_detected(self):
        data = b'<?xml version="1.0"?><root></root>'
        assert _detect_xml(data) is True

    def test_xml_with_encoding_detected(self):
        data = b'<?xml version="1.0" encoding="UTF-8"?><root/>'
        assert _detect_xml(data) is True

    def test_xml_minimal(self):
        data = b"<?xml"
        assert _detect_xml(data) is True

    def test_not_xml_html(self):
        # HTML without XML declaration
        data = b"<html><body></body></html>"
        assert _detect_xml(data) is False

    def test_not_xml_json(self):
        data = b'{"key": "value"}'
        assert _detect_xml(data) is False

    def test_too_short(self):
        data = b"<?xm"
        assert _detect_xml(data) is False


class TestDetectYAML:
    """Tests for YAML detection heuristic."""

    def test_yaml_simple_detected(self):
        data = b"key: value\nanother: data"
        assert _detect_yaml(data) is True

    def test_yaml_nested_detected(self):
        data = b"parent:\n  child: value"
        assert _detect_yaml(data) is True

    def test_yaml_with_array(self):
        data = b"items:\n  - first\n  - second"
        assert _detect_yaml(data) is True

    def test_yaml_multiline(self):
        data = b"name: test\nage: 30\ncity: NYC"
        assert _detect_yaml(data) is True

    def test_not_yaml_json_object(self):
        data = b'{"key": "value"}'
        assert _detect_yaml(data) is False

    def test_not_yaml_json_array(self):
        data = b'["item"]'
        assert _detect_yaml(data) is False

    def test_not_yaml_xml(self):
        data = b'<?xml version="1.0"?>'
        assert _detect_yaml(data) is False

    def test_not_yaml_plain_text(self):
        # Plain text without key: value pattern
        data = b"This is just plain text."
        assert _detect_yaml(data) is False


class TestDetectCSV:
    """Tests for CSV detection heuristic."""

    def test_csv_with_header_detected(self):
        data = b"name,age,city\nJohn,30,NYC"
        assert _detect_csv(data) is True

    def test_csv_multiple_rows(self):
        data = b"col1,col2,col3\nval1,val2,val3\nval4,val5,val6"
        assert _detect_csv(data) is True

    def test_csv_minimal(self):
        data = b"a,b,c"
        assert _detect_csv(data) is True

    def test_csv_with_quotes(self):
        data = b'"name","age","city"\n"John","30","NYC"'
        assert _detect_csv(data) is True

    def test_not_csv_single_comma(self):
        # Needs at least 2 commas
        data = b"key,value"
        assert _detect_csv(data) is False

    def test_not_csv_no_commas(self):
        data = b"This is plain text"
        assert _detect_csv(data) is False

    def test_not_csv_json(self):
        # JSON may have commas but not in first "line"
        data = b'{"key": "value"}'
        assert _detect_csv(data) is False


class TestDetectMimeType:
    """Core MIME detection tests (gofulmen parity)."""

    def test_json_object(self):
        data = b'{"key": "value"}'
        mime = detect_mime_type(data)
        assert mime is not None
        assert mime.mime == "application/json"

    def test_json_array(self):
        data = b'["item1", "item2"]'
        mime = detect_mime_type(data)
        assert mime.mime == "application/json"

    def test_xml_with_declaration(self):
        data = b'<?xml version="1.0"?><root></root>'
        mime = detect_mime_type(data)
        assert mime.mime == "application/xml"

    def test_yaml_document(self):
        data = b"key: value\nanother: data\n"
        mime = detect_mime_type(data)
        assert mime.mime == "application/yaml"

    def test_csv_data(self):
        data = b"name,age,city\nJohn,30,NYC\nJane,25,LA\n"
        mime = detect_mime_type(data)
        assert mime.mime == "text/csv"

    def test_plain_text(self):
        data = b"This is just plain text without special formatting."
        mime = detect_mime_type(data)
        assert mime.mime == "text/plain"

    def test_empty_input(self):
        data = b""
        mime = detect_mime_type(data)
        assert mime is None

    def test_binary_data(self):
        data = b"\x00\x01\x02\x03\xff\xfe"
        mime = detect_mime_type(data)
        assert mime is None  # Unknown, not an error

    def test_json_with_bom(self):
        data = b'\xef\xbb\xbf{"key": "value"}'
        mime = detect_mime_type(data)
        assert mime.mime == "application/json"

    def test_json_with_whitespace(self):
        data = b'  \n\t{"key": "value"}'
        mime = detect_mime_type(data)
        assert mime.mime == "application/json"
