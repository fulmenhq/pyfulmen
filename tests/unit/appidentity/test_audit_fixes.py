"""
Tests for audit fixes to ensure Crucible v0.2.4 compliance.

This test file verifies that all audit notes have been addressed:
1. Python metadata parsing from metadata.python block
2. Telemetry namespace default fallback to binary_name
3. Provenance timestamp using UTC ISO format
4. Fixtures and examples alignment with schema
"""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from pyfulmen.appidentity import load_from_path


class TestAuditFixes:
    """Test that all audit fixes are working correctly."""

    def test_python_metadata_parsing(self):
        """Test that Python metadata is parsed from metadata.python block."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "app-identity" / "valid" / "library.yaml"

        identity = load_from_path(fixture_path)

        # Should read from metadata.python.distribution_name
        assert identity.python_distribution == "pyfulmen"
        # Should read from metadata.python.package_name
        assert identity.python_package == "pyfulmen"
        # Should read from metadata.python.console_scripts
        assert identity.console_scripts is not None
        assert len(identity.console_scripts) == 1
        assert identity.console_scripts[0]["name"] == "pyfulmen"

    def test_telemetry_default_fallback(self):
        """Test that telemetry_namespace falls back to binary_name when omitted."""
        # Create test config without telemetry_namespace
        test_data = {
            "app": {
                "binary_name": "test-binary",
                "vendor": "testvendor",
                "env_prefix": "TEST_",
                "config_name": "test-config",
                "description": "Test application",
            },
            "metadata": {},
        }

        import tempfile

        import yaml

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(test_data, f)
            temp_path = f.name

        try:
            identity = load_from_path(Path(temp_path))

            # Should fallback to binary_name
            assert identity.telemetry_namespace == "test-binary"

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_telemetry_explicit_value(self):
        """Test that explicit telemetry_namespace is preserved."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "app-identity" / "valid" / "library.yaml"

        identity = load_from_path(fixture_path)

        # Should use explicit value when provided
        assert identity.telemetry_namespace == "fulmenhq_pyfulmen"

    def test_provenance_timestamp_format(self):
        """Test that provenance timestamp uses UTC ISO format."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "app-identity" / "valid" / "minimal.yaml"

        identity = load_from_path(fixture_path)

        # Get provenance
        provenance = getattr(identity, "_provenance", {})
        assert "loaded_at" in provenance

        # Should be ISO format with UTC timezone
        timestamp_str = provenance["loaded_at"]

        # Parse to verify format
        try:
            # Should parse as ISO format with Z or +00:00 timezone
            parsed_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            # Should be in UTC (within reasonable test window)
            now_utc = datetime.now(ZoneInfo("UTC"))
            time_diff = abs((now_utc - parsed_time).total_seconds())
            assert time_diff < 60  # Within 1 minute

        except ValueError as e:
            pytest.fail(f"Invalid timestamp format: {timestamp_str}, error: {e}")

    def test_missing_python_metadata_handling(self):
        """Test that missing metadata.python block is handled gracefully."""
        # Create test config without python metadata
        test_data = {
            "app": {
                "binary_name": "test-app",
                "vendor": "testvendor",
                "env_prefix": "TEST_",
                "config_name": "test-config",
                "description": "Test application",
            },
            "metadata": {
                "project_url": "https://example.com"
                # No python block
            },
        }

        import tempfile

        import yaml

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(test_data, f)
            temp_path = f.name

        try:
            identity = load_from_path(Path(temp_path))

            # Should handle missing python metadata gracefully
            assert identity.python_distribution is None
            assert identity.python_package is None
            assert identity.console_scripts is None
            # Other metadata should still work
            assert identity.project_url == "https://example.com"

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_examples_alignment(self):
        """Test that examples use correct metadata.python structure."""
        # This is verified by the examples running successfully
        # but we can also check the example config structure
        import tempfile

        import yaml

        # Example structure from appidentity_usage.py
        example_data = {
            "app": {
                "binary_name": "example-app",
                "vendor": "examplevendor",
                "env_prefix": "EXAMPLE_",
                "config_name": "example-config",
                "description": "Example application for demonstration",
            },
            "metadata": {
                "project_url": "https://github.com/example/example-app",
                "support_email": "support@example.com",
                "license": "MIT",
                "repository_category": "cli",
                "python": {
                    "distribution_name": "example-app",
                    "package_name": "example_app",
                    "console_scripts": [{"name": "example", "entry_point": "example_app.cli:main"}],
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(example_data, f)
            temp_path = f.name

        try:
            identity = load_from_path(Path(temp_path))

            # Should parse python metadata correctly
            assert identity.python_distribution == "example-app"
            assert identity.python_package == "example_app"
            assert identity.console_scripts is not None
            assert len(identity.console_scripts) == 1
            assert identity.console_scripts[0]["name"] == "example"

            # Should parse other metadata correctly
            assert identity.project_url == "https://github.com/example/example-app"
            assert identity.support_email == "support@example.com"
            assert identity.license == "MIT"
            assert identity.repository_category == "cli"

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_main_config_alignment(self):
        """Test that main .fulmen/app.yaml uses correct structure."""
        main_config_path = Path(__file__).parent.parent.parent.parent / ".fulmen" / "app.yaml"

        if main_config_path.exists():
            identity = load_from_path(main_config_path)

            # Should have python metadata in correct structure
            assert identity.binary_name == "pyfulmen"
            assert identity.vendor == "fulmenhq"
            assert identity.python_distribution == "pyfulmen"
            assert identity.python_package == "pyfulmen"

            # Should have telemetry default (since not explicitly set)
            assert identity.telemetry_namespace == "pyfulmen"
