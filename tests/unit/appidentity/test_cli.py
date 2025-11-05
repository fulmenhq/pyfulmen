"""Tests for AppIdentity CLI module."""

import subprocess
import sys
from pathlib import Path

import pytest

from pyfulmen.appidentity import cli
from pyfulmen.appidentity.errors import AppIdentityNotFoundError, AppIdentityValidationError


class TestBuildParser:
    """Test CLI argument parser construction."""

    def test_build_parser_returns_parser(self):
        """Test that build_parser returns a valid ArgumentParser."""
        parser = cli.build_parser()
        assert parser is not None
        assert "PyFulmen AppIdentity CLI" in parser.description

    def test_show_command_parsing(self):
        """Test show command argument parsing."""
        parser = cli.build_parser()

        # Default arguments
        args = parser.parse_args(["show"])
        assert args.command == "show"
        assert args.format == "text"
        assert args.path is None

        # With format
        args = parser.parse_args(["show", "--format", "json"])
        assert args.format == "json"

        # With path
        test_path = Path("/test/app.yaml")
        args = parser.parse_args(["show", "--path", str(test_path)])
        assert args.path == test_path

    def test_validate_command_parsing(self):
        """Test validate command argument parsing."""
        parser = cli.build_parser()

        test_path = Path("/test/app.yaml")
        args = parser.parse_args(["validate", str(test_path)])
        assert args.command == "validate"
        assert args.path == test_path


class TestFormatIdentityText:
    """Test identity text formatting."""

    def test_format_minimal_identity(self):
        """Test formatting minimal identity."""
        from pyfulmen.appidentity.models import AppIdentity

        identity = AppIdentity(
            binary_name="test", vendor="testvendor", env_prefix="TEST_", config_name="test", description="Test app"
        )

        result = cli.format_identity_text(identity)
        lines = result.split("\n")

        assert "Application Identity: test" in lines
        assert "Vendor: testvendor" in lines
        assert "Environment Prefix: TEST_" in lines
        assert "Config Directory: test" in lines
        assert "Description: Test app" in lines

    def test_format_full_identity(self):
        """Test formatting full identity with all optional fields."""
        from pyfulmen.appidentity.models import AppIdentity

        identity = AppIdentity(
            binary_name="test",
            vendor="testvendor",
            env_prefix="TEST_",
            config_name="test",
            description="Test app",
            project_url="https://example.com",
            support_email="support@example.com",
            license="MIT",
            repository_category="library",
            telemetry_namespace="test_telemetry",
            python_distribution="test-dist",
            python_package="test_package",
            console_scripts=[{"name": "test_script"}],
        )

        result = cli.format_identity_text(identity)
        lines = result.split("\n")

        assert "Project URL: https://example.com" in lines
        assert "Support Email: support@example.com" in lines
        assert "License: MIT" in lines
        assert "Repository Category: library" in lines
        assert "Telemetry Namespace: test_telemetry" in lines
        assert "Python Distribution: test-dist" in lines
        assert "Python Package: test_package" in lines
        assert "Console Scripts:" in lines
        assert "  - test_script" in lines

    def test_format_identity_with_provenance(self):
        """Test formatting identity with provenance data."""
        from pyfulmen.appidentity.models import AppIdentity

        identity = AppIdentity(
            binary_name="test", vendor="testvendor", env_prefix="TEST_", config_name="test", description="Test app"
        )
        # Add provenance via object.__setattr__ to bypass frozen dataclass
        object.__setattr__(identity, "_provenance", {"source_path": "/test/path", "loaded_at": "2025-01-01T00:00:00Z"})

        result = cli.format_identity_text(identity)
        lines = result.split("\n")

        assert "Provenance:" in lines
        assert "  source_path: /test/path" in lines
        assert "  loaded_at: 2025-01-01T00:00:00Z" in lines


class TestCommands:
    """Test CLI command functions."""

    def test_cmd_show_success(self, monkeypatch):
        """Test successful show command."""
        from pyfulmen.appidentity.models import AppIdentity

        # Mock get_identity
        mock_identity = AppIdentity(
            binary_name="test", vendor="testvendor", env_prefix="TEST_", config_name="test", description="Test app"
        )

        def mock_get_identity():
            return mock_identity

        monkeypatch.setattr("pyfulmen.appidentity.cli.get_identity", mock_get_identity)

        # Create mock args
        args = type("Args", (), {"path": None, "format": "text"})()

        result = cli.cmd_show(args)
        assert result == 0  # Success exit code

    def test_cmd_show_success_json(self, monkeypatch):
        """Test successful show command with JSON format."""
        from pyfulmen.appidentity.models import AppIdentity

        mock_identity = AppIdentity(
            binary_name="test", vendor="testvendor", env_prefix="TEST_", config_name="test", description="Test app"
        )

        def mock_get_identity():
            return mock_identity

        monkeypatch.setattr("pyfulmen.appidentity.cli.get_identity", mock_get_identity)

        args = type("Args", (), {"path": None, "format": "json"})()

        result = cli.cmd_show(args)
        assert result == 0

    def test_cmd_show_not_found(self, monkeypatch):
        """Test show command when identity not found."""

        def mock_get_identity():
            raise AppIdentityNotFoundError("Not found")

        monkeypatch.setattr("pyfulmen.appidentity.cli.get_identity", mock_get_identity)

        args = type("Args", (), {"path": None, "format": "text"})()

        result = cli.cmd_show(args)
        from pyfulmen.foundry import ExitCode

        assert result == ExitCode.EXIT_FILE_NOT_FOUND.value

    def test_cmd_show_validation_error(self, monkeypatch):
        """Test show command with validation error."""

        def mock_get_identity():
            raise AppIdentityValidationError("Invalid data", [])

        monkeypatch.setattr("pyfulmen.appidentity.cli.get_identity", mock_get_identity)

        args = type("Args", (), {"path": None, "format": "text"})()

        result = cli.cmd_show(args)
        from pyfulmen.foundry import ExitCode

        assert result == ExitCode.EXIT_DATA_INVALID.value

    def test_cmd_validate_success(self, monkeypatch):
        """Test successful validate command."""
        from pyfulmen.appidentity.models import AppIdentity

        mock_identity = AppIdentity(
            binary_name="test", vendor="testvendor", env_prefix="TEST_", config_name="test", description="Test app"
        )

        def mock_load_from_path(path):
            return mock_identity

        monkeypatch.setattr("pyfulmen.appidentity.cli.load_from_path", mock_load_from_path)

        args = type("Args", (), {"path": Path("/test/app.yaml")})()

        result = cli.cmd_validate(args)
        assert result == 0

    def test_cmd_validate_not_found(self, monkeypatch):
        """Test validate command when file not found."""

        def mock_load_from_path(path):
            raise AppIdentityNotFoundError("Not found")

        monkeypatch.setattr("pyfulmen.appidentity.cli.load_from_path", mock_load_from_path)

        args = type("Args", (), {"path": Path("/test/app.yaml")})()

        result = cli.cmd_validate(args)
        from pyfulmen.foundry import ExitCode

        assert result == ExitCode.EXIT_FILE_NOT_FOUND.value

    def test_cmd_validate_validation_error(self, monkeypatch):
        """Test validate command with validation errors."""
        from pyfulmen.appidentity.errors import AppIdentityValidationError

        def mock_load_from_path(path):
            error = AppIdentityValidationError("Invalid data", ["Error 1", "Error 2"])
            raise error

        monkeypatch.setattr("pyfulmen.appidentity.cli.load_from_path", mock_load_from_path)

        args = type("Args", (), {"path": Path("/test/app.yaml")})()

        result = cli.cmd_validate(args)
        from pyfulmen.foundry import ExitCode

        assert result == ExitCode.EXIT_DATA_INVALID.value


class TestMainFunction:
    """Test main CLI entry point."""

    def test_main_show_command(self, monkeypatch):
        """Test main function with show command."""

        def mock_cmd_show(args):
            return 0

        monkeypatch.setattr("pyfulmen.appidentity.cli.cmd_show", mock_cmd_show)

        result = cli.main(["show"])
        assert result == 0

    def test_main_validate_command(self, monkeypatch):
        """Test main function with validate command."""

        def mock_cmd_validate(args):
            return 0

        monkeypatch.setattr("pyfulmen.appidentity.cli.cmd_validate", mock_cmd_validate)

        result = cli.main(["validate", "/test/app.yaml"])
        assert result == 0

    def test_main_unknown_command(self):
        """Test main function with unknown command."""
        # Test that parser.error is called for unknown command
        # This will raise SystemExit, which we catch
        with pytest.raises(SystemExit) as exc_info:
            cli.main(["unknown"])
        assert exc_info.value.code == 2


class TestCLIIntegration:
    """Test CLI integration with subprocess."""

    def test_cli_show_help(self):
        """Test CLI show help via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "pyfulmen.appidentity", "show", "--help"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "--format" in result.stdout
        assert "--path" in result.stdout

    def test_cli_validate_help(self):
        """Test CLI validate help via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "pyfulmen.appidentity", "validate", "--help"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "path" in result.stdout

    def test_cli_main_help(self):
        """Test CLI main help via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "pyfulmen.appidentity", "--help"], capture_output=True, text=True
        )
        assert result.returncode == 0
        assert "show" in result.stdout
        assert "validate" in result.stdout
