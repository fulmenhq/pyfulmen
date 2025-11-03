"""Unit tests for schema export functionality."""

import json

import pytest

from pyfulmen.schema import export_schema
from pyfulmen.schema.validator import SchemaValidationError


class TestExportSchema:
    """Unit tests for export_schema function."""

    def test_export_json_success(self, tmp_path):
        """Test successful JSON export."""
        out_file = tmp_path / "test-schema.json"

        result = export_schema(
            "observability/logging/v1.0.0/logger-config",
            out_file
        )

        assert result == out_file.absolute()
        assert out_file.exists()

        # Verify valid JSON
        with open(out_file) as f:
            data = json.load(f)

        assert "$schema" in data
        assert "$comment" in data  # Provenance
        assert "x-crucible-source" in data["$comment"]

    def test_export_yaml_success(self, tmp_path):
        """Test successful YAML export."""
        pytest.importorskip("yaml")  # Skip if PyYAML not available

        import yaml

        out_file = tmp_path / "test-schema.yaml"

        result = export_schema(
            "observability/logging/v1.0.0/logger-config",
            out_file
        )

        assert result == out_file.absolute()
        assert out_file.exists()

        # Verify valid YAML
        with open(out_file) as f:
            data = yaml.safe_load(f)

        assert "$schema" in data

    def test_export_no_provenance(self, tmp_path):
        """Test export without provenance metadata."""
        out_file = tmp_path / "test-schema.json"

        export_schema(
            "observability/logging/v1.0.0/logger-config",
            out_file,
            include_provenance=False
        )

        with open(out_file) as f:
            data = json.load(f)

        assert "$comment" not in data

    def test_export_file_exists_no_overwrite(self, tmp_path):
        """Test that export refuses to overwrite without flag."""
        out_file = tmp_path / "existing.json"
        out_file.write_text("{}")

        with pytest.raises(FileExistsError, match="already exists"):
            export_schema(
                "observability/logging/v1.0.0/logger-config",
                out_file,
                overwrite=False
            )

    def test_export_file_exists_with_overwrite(self, tmp_path):
        """Test that export overwrites with flag."""
        out_file = tmp_path / "existing.json"
        out_file.write_text("{}")

        result = export_schema(
            "observability/logging/v1.0.0/logger-config",
            out_file,
            overwrite=True
        )

        assert result == out_file.absolute()
        assert out_file.exists()

        # Verify new content (not just "{}")
        with open(out_file) as f:
            data = json.load(f)
        assert "$schema" in data

    def test_export_invalid_schema_id(self, tmp_path):
        """Test export with invalid schema identifier."""
        out_file = tmp_path / "test.json"

        with pytest.raises(ValueError, match="Invalid schema_id"):
            export_schema("invalid-id", out_file)

    def test_export_validation_failure(self, tmp_path, monkeypatch):
        """Test export fails when schema is invalid and validation enabled."""

        def bad_schema_loader(*_, **__):
            return {"type": "object", "properties": {"bad": {"type": "unknown"}}}

        monkeypatch.setattr("pyfulmen.crucible.schemas.load_schema", bad_schema_loader)

        out_file = tmp_path / "test.json"

        with pytest.raises(SchemaValidationError):
            export_schema(
                "observability/logging/v1.0.0/logger-config",
                out_file,
                validate=True,
            )

    def test_export_schema_not_found(self, tmp_path):
        """Test export with non-existent schema."""
        out_file = tmp_path / "test.json"

        with pytest.raises(FileNotFoundError, match="Schema not found"):
            export_schema(
                "nonexistent/v1.0.0/schema",
                out_file
            )

    def test_export_creates_parent_directories(self, tmp_path):
        """Test that export creates parent directories."""
        out_file = tmp_path / "nested" / "path" / "schema.json"

        result = export_schema(
            "observability/logging/v1.0.0/logger-config",
            out_file
        )

        assert result.exists()
        assert result.parent.exists()

    def test_export_provenance_content(self, tmp_path):
        """Test provenance metadata structure."""
        out_file = tmp_path / "test-schema.json"

        export_schema(
            "observability/logging/v1.0.0/logger-config",
            out_file
        )

        with open(out_file) as f:
            data = json.load(f)

        provenance = data["$comment"]["x-crucible-source"]

        assert "schema_id" in provenance
        assert provenance["schema_id"] == "observability/logging/v1.0.0/logger-config"
        assert "crucible_version" in provenance
        assert "pyfulmen_version" in provenance
        assert "exported_at" in provenance
        # revision may be None in test environment

    def test_export_json_deterministic(self, tmp_path):
        """Test that JSON export is deterministic (sorted keys, consistent formatting)."""
        out_file1 = tmp_path / "test1.json"
        out_file2 = tmp_path / "test2.json"

        export_schema(
            "observability/logging/v1.0.0/logger-config",
            out_file1,
            include_provenance=False
        )

        export_schema(
            "observability/logging/v1.0.0/logger-config",
            out_file2,
            include_provenance=False
        )

        # Compare byte-for-byte (except timestamp would differ with provenance)
        content1 = out_file1.read_bytes()
        content2 = out_file2.read_bytes()
        assert content1 == content2

    def test_export_mixed_case_extensions(self, tmp_path):
        """Test that mixed-case extensions are handled correctly."""
        # Test uppercase .JSON
        out_file_json = tmp_path / "test.JSON"
        export_schema("observability/logging/v1.0.0/logger-config", out_file_json)

        with open(out_file_json) as f:
            data = json.load(f)
        assert "$comment" in data  # Should have provenance

        # Test uppercase .YAML
        pytest.importorskip("yaml")
        out_file_yaml = tmp_path / "test.YAML"
        export_schema("observability/logging/v1.0.0/logger-config", out_file_yaml)

        content = out_file_yaml.read_text()
        assert "# Crucible Schema Export Provenance" in content

    def test_export_unknown_extension_defaults_to_json(self, tmp_path):
        """Test that unknown extensions default to JSON format."""
        out_file = tmp_path / "test.unknown"

        export_schema("observability/logging/v1.0.0/logger-config", out_file)

        # Should be valid JSON
        with open(out_file) as f:
            data = json.load(f)
        assert "$schema" in data
        # Should have provenance (either as $comment or _crucible_provenance)
        assert ("$comment" in data and "x-crucible-source" in data["$comment"]) or "_crucible_provenance" in data

    def test_export_comment_collision_merge(self, tmp_path, monkeypatch):
        """Test that existing $comment is preserved and provenance added separately."""

        def mock_load_schema(*_, **__):
            return {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$comment": "existing comment",
                "type": "object"
            }

        monkeypatch.setattr("pyfulmen.crucible.schemas.load_schema", mock_load_schema)

        out_file = tmp_path / "test.json"
        export_schema("test/schema/v1.0.0/test", out_file)

        with open(out_file) as f:
            data = json.load(f)

        # Existing $comment should be preserved
        assert data["$comment"] == "existing comment"
        # Provenance should be added as separate field
        assert "_crucible_provenance" in data
        assert "schema_id" in data["_crucible_provenance"]