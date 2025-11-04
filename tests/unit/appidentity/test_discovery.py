"""
Unit tests for app identity discovery and loading.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from pyfulmen.appidentity._loader import (
    _discover_identity_path,
    _load_identity_from_path,
    load,
    load_from_path,
)
from pyfulmen.appidentity.errors import (
    AppIdentityLoadError,
    AppIdentityNotFoundError,
    AppIdentityValidationError,
)


class TestDiscovery:
    """Test identity file discovery."""

    def test_discovery_env_override(self):
        """Test environment variable override."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.yaml"
            test_file.write_text("test: content")

            # Set environment variable
            with patch.dict(os.environ, {"FULMEN_APP_IDENTITY_PATH": str(test_file)}):
                result = _discover_identity_path()
                assert result == test_file.resolve()

    def test_discovery_ancestor_search(self):
        """Test ancestor search for .fulmen/app.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create nested directory structure
            nested_dir = tmpdir / "a" / "b" / "c"
            nested_dir.mkdir(parents=True)

            # Create .fulmen/app.yaml in parent
            fulmen_dir = tmpdir / ".fulmen"
            fulmen_dir.mkdir()
            app_file = fulmen_dir / "app.yaml"
            app_file.write_text("test: content")

            # Change to nested directory and search
            with patch("pathlib.Path.cwd", return_value=nested_dir):
                result = _discover_identity_path()
                # Compare paths without resolving (macOS path differences)
                assert result.name == app_file.name
                assert result.parent.name == app_file.parent.name

    def test_discovery_not_found(self):
        """Test discovery when no file found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Start from empty directory
            empty_dir = Path(tmpdir)

            with patch("pathlib.Path.cwd", return_value=empty_dir):
                with pytest.raises(AppIdentityNotFoundError) as exc_info:
                    _discover_identity_path()

                # Should have searched current directory .fulmen/app.yaml
                searched = exc_info.value.searched_paths
                assert len(searched) >= 1
                assert any(path.name == "app.yaml" for path in searched)

    def test_discovery_env_override_nonexistent(self):
        """Test environment override with nonexistent file."""
        nonexistent = Path("/nonexistent/path.yaml")

        with patch.dict(os.environ, {"FULMEN_APP_IDENTITY_PATH": str(nonexistent)}):
            with pytest.raises(AppIdentityNotFoundError) as exc_info:
                _discover_identity_path()

            searched = exc_info.value.searched_paths
            assert nonexistent.resolve() in searched


class TestLoading:
    """Test identity file loading."""

    def test_load_valid_file(self):
        """Test loading a valid identity file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "valid.yaml"

            # Write valid identity data
            data = {
                "app": {
                    "binary_name": "testapp",
                    "vendor": "testvendor",
                    "env_prefix": "TEST_",
                    "config_name": "testapp",
                    "description": "Test application",
                }
            }
            test_file.write_text(yaml.dump(data))

            result = _load_identity_from_path(test_file)
            assert result == data

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file."""
        nonexistent = Path("/nonexistent/file.yaml")

        with pytest.raises(AppIdentityLoadError) as exc_info:
            load_from_path(nonexistent)

        assert "not found" in str(exc_info.value).lower()

    def test_load_empty_file(self):
        """Test loading empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_file = Path(tmpdir) / "empty.yaml"
            empty_file.write_text("")

            with pytest.raises(AppIdentityLoadError) as exc_info:
                _load_identity_from_path(empty_file)

            assert "empty" in str(exc_info.value).lower()

    def test_load_invalid_yaml(self):
        """Test loading file with invalid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_file = Path(tmpdir) / "invalid.yaml"
            invalid_file.write_text("invalid: yaml: content: [")

            with pytest.raises(AppIdentityLoadError):
                _load_identity_from_path(invalid_file)

    def test_load_non_dict_yaml(self):
        """Test loading YAML that's not a dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            list_file = Path(tmpdir) / "list.yaml"
            list_file.write_text("- item1\n- item2")

            with pytest.raises(AppIdentityLoadError) as exc_info:
                _load_identity_from_path(list_file)

            assert "Expected dictionary" in str(exc_info.value)

    def test_load_file_too_large(self):
        """Test loading file that exceeds size limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            large_file = Path(tmpdir) / "large.yaml"

            # Write file larger than 10KB
            large_content = "data: " + "x" * (11 * 1024)  # > 10KB
            large_file.write_text(large_content)

            with pytest.raises(AppIdentityLoadError) as exc_info:
                _load_identity_from_path(large_file)

            assert "too large" in str(exc_info.value).lower()


class TestLoadFromPath:
    """Test load_from_path function."""

    def test_load_from_path_valid(self):
        """Test loading valid identity from path."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "app-identity" / "valid" / "library.yaml"

        identity = load_from_path(fixture_path)

        assert identity.binary_name == "pyfulmen"
        assert identity.vendor == "fulmenhq"
        assert identity.env_prefix == "FULMEN_"
        assert identity.config_name == "pyfulmen"
        assert identity.description == "Python Fulmen libraries"
        assert identity.project_url == "https://github.com/fulmenhq/pyfulmen"
        assert identity.support_email == "dev@3leaps.net"

    def test_load_from_path_invalid_schema(self):
        """Test loading file with schema validation errors."""
        fixture_path = (
            Path(__file__).parent.parent.parent / "fixtures" / "app-identity" / "invalid" / "bad_env_prefix.yaml"
        )

        with pytest.raises(AppIdentityValidationError) as exc_info:
            load_from_path(fixture_path)

        # Should have validation error about env_prefix
        errors = " ".join(exc_info.value.validation_errors)
        assert "env_prefix" in errors.lower()

    def test_load_from_path_populates_provenance(self):
        """Test that loading populates provenance information."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "app-identity" / "valid" / "minimal.yaml"

        identity = load_from_path(fixture_path)

        # Check internal provenance field
        assert hasattr(identity, "_provenance")
        provenance = object.__getattribute__(identity, "_provenance")
        assert "source_path" in provenance
        assert "loaded_at" in provenance
        assert str(fixture_path.resolve()) in provenance["source_path"]

    def test_load_from_path_populates_raw_metadata(self):
        """Test that loading preserves raw metadata."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "app-identity" / "valid" / "minimal.yaml"

        identity = load_from_path(fixture_path)

        # Check internal raw metadata field
        assert hasattr(identity, "_raw_metadata")
        raw_metadata = object.__getattribute__(identity, "_raw_metadata")
        assert isinstance(raw_metadata, dict)
        assert "app" in raw_metadata
        assert raw_metadata["app"]["binary_name"] == "testapp"


class TestLoad:
    """Test load function with discovery."""

    def test_load_with_discovery(self):
        """Test loading using discovery algorithm."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "app-identity" / ".fulmen" / "app.yaml"

        # Change to fixture directory and load
        fixture_dir = fixture_path.parent.parent
        with patch("pathlib.Path.cwd", return_value=fixture_dir):
            identity = load()

            assert identity.binary_name == "testapp"
            assert identity.vendor == "testvendor"
            assert identity.env_prefix == "TEST_"

    def test_load_no_file_found(self):
        """Test load when no identity file found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir)

            with patch("pathlib.Path.cwd", return_value=empty_dir), pytest.raises(AppIdentityNotFoundError):
                load()
