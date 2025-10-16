"""Golden fixture tests for MIME detection.

These tests validate MIME detection against golden fixture files
to ensure cross-language behavioral parity per Crucible standards.
"""

from pathlib import Path

from pyfulmen.foundry import detect_mime_type_from_file

# Golden fixture directory
FIXTURE_DIR = Path(__file__).parent.parent.parent / "fixtures" / "foundry" / "mime"


class TestMimeDetectionGoldenFixtures:
    """Golden fixture tests for cross-language parity."""

    def test_fixture_directory_exists(self):
        """Ensure fixture directory is present."""
        assert FIXTURE_DIR.exists(), f"Fixture directory not found: {FIXTURE_DIR}"
        assert FIXTURE_DIR.is_dir()

    def test_valid_json_object_fixture(self):
        """Test JSON object detection from golden fixture."""
        fixture = FIXTURE_DIR / "valid-json-object.json"
        assert fixture.exists(), f"Fixture missing: {fixture}"

        mime = detect_mime_type_from_file(fixture)
        assert mime is not None, "JSON detection failed"
        assert mime.id == "json"
        assert mime.mime == "application/json"

    def test_valid_json_array_fixture(self):
        """Test JSON array detection from golden fixture."""
        fixture = FIXTURE_DIR / "valid-json-array.json"
        assert fixture.exists(), f"Fixture missing: {fixture}"

        mime = detect_mime_type_from_file(fixture)
        assert mime is not None
        assert mime.id == "json"

    def test_valid_xml_fixture(self):
        """Test XML detection from golden fixture."""
        fixture = FIXTURE_DIR / "valid-xml.xml"
        assert fixture.exists(), f"Fixture missing: {fixture}"

        mime = detect_mime_type_from_file(fixture)
        assert mime is not None
        assert mime.id == "xml"
        assert mime.mime == "application/xml"

    def test_valid_yaml_fixture(self):
        """Test YAML detection from golden fixture."""
        fixture = FIXTURE_DIR / "valid-yaml.yaml"
        assert fixture.exists(), f"Fixture missing: {fixture}"

        mime = detect_mime_type_from_file(fixture)
        assert mime is not None
        assert mime.id == "yaml"
        assert mime.mime == "application/yaml"

    def test_valid_csv_fixture(self):
        """Test CSV detection from golden fixture."""
        fixture = FIXTURE_DIR / "valid-csv.csv"
        assert fixture.exists(), f"Fixture missing: {fixture}"

        mime = detect_mime_type_from_file(fixture)
        assert mime is not None
        assert mime.id == "csv"
        assert mime.mime == "text/csv"

    def test_valid_text_fixture(self):
        """Test plain text detection from golden fixture."""
        fixture = FIXTURE_DIR / "valid-text.txt"
        assert fixture.exists(), f"Fixture missing: {fixture}"

        mime = detect_mime_type_from_file(fixture)
        assert mime is not None
        assert mime.id == "plain-text"
        assert mime.mime == "text/plain"

    def test_binary_unknown_fixture(self):
        """Test binary/unknown returns None from golden fixture."""
        fixture = FIXTURE_DIR / "binary-unknown.bin"
        assert fixture.exists(), f"Fixture missing: {fixture}"

        mime = detect_mime_type_from_file(fixture)
        # Binary should not be detected (returns None)
        assert mime is None

    def test_json_with_utf8_bom_fixture(self):
        """Test JSON with UTF-8 BOM detection from golden fixture."""
        fixture = FIXTURE_DIR / "json-with-utf8-bom.json"
        assert fixture.exists(), f"Fixture missing: {fixture}"

        mime = detect_mime_type_from_file(fixture)
        assert mime is not None
        assert mime.id == "json"
