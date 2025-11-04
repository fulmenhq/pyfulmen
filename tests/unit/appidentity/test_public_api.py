"""
Tests for the public API of appidentity module.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from pyfulmen.appidentity import (
    clear_identity_cache,
    get_identity,
    load,
    load_from_path,
    override_identity_for_testing,
    reload_identity,
)
from pyfulmen.appidentity.errors import AppIdentityNotFoundError
from pyfulmen.appidentity.models import AppIdentity


class TestPublicAPI:
    """Test the public API functions."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_identity_cache()

    def test_get_identity_caching(self):
        """Test that get_identity caches results."""
        # Clear cache first
        clear_identity_cache()

        # Mock load to track calls
        with patch("pyfulmen.appidentity.load") as mock_load:
            test_identity = AppIdentity(
                binary_name="test-app",
                vendor="testvendor",
                env_prefix="TEST_",
                config_name="test-config",
                description="Test application",
            )
            mock_load.return_value = test_identity

            # First call should load
            identity1 = get_identity()
            assert identity1 is test_identity
            assert mock_load.call_count == 1

            # Second call should use cache
            identity2 = get_identity()
            assert identity2 is test_identity
            assert mock_load.call_count == 1  # No additional calls

    def test_get_identity_with_override(self):
        """Test that get_identity respects test overrides."""
        # Clear cache first
        clear_identity_cache()

        # Mock load to track calls
        with patch("pyfulmen.appidentity.load") as mock_load:
            test_identity = AppIdentity(
                binary_name="test-app",
                vendor="testvendor",
                env_prefix="TEST_",
                config_name="test-config",
                description="Test application",
            )
            mock_load.return_value = test_identity

            override_identity = AppIdentity(
                binary_name="override-app",
                vendor="overridevendor",
                env_prefix="OVERRIDE_",
                config_name="override-config",
                description="Override application",
            )

            # Should use override, not load
            with override_identity_for_testing(override_identity):
                identity = get_identity()
                assert identity is override_identity
                assert mock_load.call_count == 0  # No load calls

    def test_reload_identity(self):
        """Test that reload_identity forces fresh load."""
        # Clear cache first
        clear_identity_cache()

        with patch("pyfulmen.appidentity.load") as mock_load:
            test_identity1 = AppIdentity(
                binary_name="test-app-1",
                vendor="testvendor",
                env_prefix="TEST_",
                config_name="test-config",
                description="Test application 1",
            )
            test_identity2 = AppIdentity(
                binary_name="test-app-2",
                vendor="testvendor",
                env_prefix="TEST_",
                config_name="test-config",
                description="Test application 2",
            )

            # First load
            mock_load.return_value = test_identity1
            identity1 = get_identity()
            assert identity1 is test_identity1
            assert mock_load.call_count == 1

            # Reload should call load again
            mock_load.return_value = test_identity2
            identity2 = reload_identity()
            assert identity2 is test_identity2
            assert mock_load.call_count == 2

            # Subsequent get should use reloaded value
            identity3 = get_identity()
            assert identity3 is test_identity2
            assert mock_load.call_count == 2

    def test_clear_identity_cache(self):
        """Test that clear_identity_cache clears cache."""
        with patch("pyfulmen.appidentity.load") as mock_load:
            test_identity = AppIdentity(
                binary_name="test-app",
                vendor="testvendor",
                env_prefix="TEST_",
                config_name="test-config",
                description="Test application",
            )
            mock_load.return_value = test_identity

            # Load and cache
            identity1 = get_identity()
            assert identity1.binary_name == test_identity.binary_name
            assert mock_load.call_count == 1

            # Clear cache
            clear_identity_cache()

            # Next call should reload
            identity2 = get_identity()
            assert identity2.binary_name == test_identity.binary_name
            assert mock_load.call_count == 2

    def test_get_identity_propagates_errors(self):
        """Test that get_identity properly propagates loading errors."""
        # Clear cache first
        clear_identity_cache()

        with patch("pyfulmen.appidentity.load") as mock_load:
            mock_load.side_effect = AppIdentityNotFoundError(["/test/path"])

            with pytest.raises(AppIdentityNotFoundError):
                get_identity()

    def test_reload_identity_propagates_errors(self):
        """Test that reload_identity properly propagates loading errors."""
        with patch("pyfulmen.appidentity.load") as mock_load:
            mock_load.side_effect = AppIdentityNotFoundError(["/test/path"])

            with pytest.raises(AppIdentityNotFoundError):
                reload_identity()


class TestAPIIntegration:
    """Test integration between public API functions."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_identity_cache()

    def test_load_and_get_identity_consistency(self):
        """Test that load() and get_identity() return consistent results."""
        # Clear cache first
        clear_identity_cache()

        with patch("pyfulmen.appidentity._loader._discover_identity_path") as mock_discover:
            # Create a test fixture
            import tempfile

            import yaml

            test_data = {
                "app": {
                    "binary_name": "consistency-test",
                    "vendor": "testvendor",
                    "env_prefix": "TEST_",
                    "config_name": "test-config",
                    "description": "Consistency test application",
                }
            }

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                yaml.dump(test_data, f)
                temp_path = f.name

            try:
                mock_discover.return_value = Path(temp_path)

                # Both should return the same result for the first call
                loaded = load()
                gotten = get_identity()

                # Should have the same data (cached)
                assert loaded.binary_name == gotten.binary_name
                assert loaded.vendor == gotten.vendor
                assert loaded.env_prefix == gotten.env_prefix
            finally:
                import os

                os.unlink(temp_path)

    def test_load_from_path_bypasses_cache(self):
        """Test that load_from_path() bypasses cache."""
        # Clear cache first
        clear_identity_cache()

        # Create a test fixture
        import os
        import tempfile

        import yaml

        test_data = {
            "app": {
                "binary_name": "path-test",
                "vendor": "testvendor",
                "env_prefix": "TEST_",
                "config_name": "test-config",
                "description": "Path test application",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(test_data, f)
            temp_path = f.name

        try:
            # Load from path should not affect cache
            path_identity = load_from_path(Path(temp_path))

            # get_identity should still do discovery (and potentially fail)
            with patch("pyfulmen.appidentity.load") as mock_load:
                mock_load.side_effect = AppIdentityNotFoundError("Not found")

                with pytest.raises(AppIdentityNotFoundError):
                    get_identity()

            # But load_from_path should work
            assert path_identity.binary_name == "path-test"

        finally:
            os.unlink(temp_path)

    def test_override_context_isolation(self):
        """Test that override context properly isolates from normal operation."""
        # Clear cache first
        clear_identity_cache()

        with patch("pyfulmen.appidentity.load") as mock_load:
            normal_identity = AppIdentity(
                binary_name="normal-app",
                vendor="normalvendor",
                env_prefix="NORMAL_",
                config_name="normal-config",
                description="Normal application",
            )
            override_identity = AppIdentity(
                binary_name="override-app",
                vendor="overridevendor",
                env_prefix="OVERRIDE_",
                config_name="override-config",
                description="Override application",
            )

            mock_load.return_value = normal_identity

            # Normal operation
            assert get_identity().binary_name == "normal-app"
            assert mock_load.call_count == 1

            # Override context
            with override_identity_for_testing(override_identity):
                assert get_identity().binary_name == "override-app"
                assert mock_load.call_count == 1  # No additional load

            # Back to normal
            assert get_identity().binary_name == "normal-app"
            assert mock_load.call_count == 1  # Still using cache
