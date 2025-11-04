"""Integration tests for schema export CLI."""

import json

import pytest
from click.testing import CliRunner

from pyfulmen.schema.cli import cli


class TestSchemaExportCLI:
    """Integration tests for schema export CLI."""

    def test_cli_export_success(self, tmp_path):
        """Test successful CLI export."""
        out_file = tmp_path / "schema.json"

        runner = CliRunner()
        result = runner.invoke(cli, ["export", "observability/logging/v1.0.0/logger-config", "--out", str(out_file)])

        assert result.exit_code == 0
        assert out_file.exists()

        # Verify output path printed
        assert str(out_file) in result.output

    def test_cli_export_verbose(self, tmp_path):
        """Test CLI export with verbose output."""
        out_file = tmp_path / "schema.json"

        runner = CliRunner()
        result = runner.invoke(
            cli, ["export", "observability/logging/v1.0.0/logger-config", "--out", str(out_file), "--verbose"]
        )

        assert result.exit_code == 0
        assert "✅ Exported schema" in result.output
        assert "Provenance: included" in result.output
        assert "Validation: passed" in result.output

    def test_cli_export_no_provenance(self, tmp_path):
        """Test CLI export without provenance."""
        out_file = tmp_path / "schema.json"

        runner = CliRunner()
        result = runner.invoke(
            cli, ["export", "observability/logging/v1.0.0/logger-config", "--out", str(out_file), "--no-provenance"]
        )

        assert result.exit_code == 0

        with open(out_file) as f:
            data = json.load(f)

        assert "$comment" not in data
        assert "_crucible_provenance" not in data

    def test_cli_export_force_overwrite(self, tmp_path):
        """Test CLI export with force overwrite."""
        out_file = tmp_path / "schema.json"
        out_file.write_text("{}")

        runner = CliRunner()
        result = runner.invoke(
            cli, ["export", "observability/logging/v1.0.0/logger-config", "--out", str(out_file), "--force"]
        )

        assert result.exit_code == 0
        assert out_file.exists()

        # Verify overwritten
        with open(out_file) as f:
            data = json.load(f)
        assert "$schema" in data

    def test_cli_export_file_exists_no_force(self, tmp_path):
        """Test CLI export fails when file exists without --force."""
        out_file = tmp_path / "schema.json"
        out_file.write_text("{}")

        runner = CliRunner()
        result = runner.invoke(cli, ["export", "observability/logging/v1.0.0/logger-config", "--out", str(out_file)])

        assert result.exit_code != 0
        assert "File exists" in result.output or "already exists" in result.output

    def test_cli_export_invalid_schema(self, tmp_path):
        """Test CLI export with invalid schema ID."""
        out_file = tmp_path / "schema.json"

        runner = CliRunner()
        result = runner.invoke(cli, ["export", "nonexistent/v1.0.0/schema", "--out", str(out_file)])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_cli_export_yaml(self, tmp_path):
        """Test CLI export to YAML format."""
        pytest.importorskip("yaml")

        out_file = tmp_path / "schema.yaml"

        runner = CliRunner()
        result = runner.invoke(cli, ["export", "observability/logging/v1.0.0/logger-config", "--out", str(out_file)])

        assert result.exit_code == 0
        assert out_file.exists()

        # Verify it's YAML with provenance comments
        content = out_file.read_text()
        assert "# Crucible Schema Export Provenance" in content
        assert "$schema" in content

    def test_cli_export_no_validate(self, tmp_path):
        """Test CLI export with validation disabled."""
        out_file = tmp_path / "schema.json"

        runner = CliRunner()
        result = runner.invoke(
            cli, ["export", "observability/logging/v1.0.0/logger-config", "--out", str(out_file), "--no-validate"]
        )

        assert result.exit_code == 0
        assert out_file.exists()

        # Verify verbose output mentions validation was skipped
        result_verbose = runner.invoke(
            cli,
            [
                "export",
                "observability/logging/v1.0.0/logger-config",
                "--out",
                str(tmp_path / "schema2.json"),
                "--no-validate",
                "--verbose",
            ],
        )

        assert "Validation: skipped" in result_verbose.output

    def test_cli_export_mixed_case_extension(self, tmp_path):
        """Test CLI export with mixed-case file extension."""
        out_file = tmp_path / "schema.JSON"

        runner = CliRunner()
        result = runner.invoke(cli, ["export", "observability/logging/v1.0.0/logger-config", "--out", str(out_file)])

        assert result.exit_code == 0
        assert out_file.exists()

        # Verify it's valid JSON with provenance
        with open(out_file) as f:
            data = json.load(f)
        assert "$schema" in data
        assert ("$comment" in data and "x-crucible-source" in data["$comment"]) or "_crucible_provenance" in data
