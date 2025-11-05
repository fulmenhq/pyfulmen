"""Tests for Crucible v0.2.4 alignment features."""

from pathlib import Path

import pytest

from pyfulmen.appidentity.errors import (
    AppIdentityLoadError,
    AppIdentityNotFoundError,
    AppIdentityValidationError,
)
from pyfulmen.appidentity.models import AppIdentity


class TestAncestorSearchGuard:
    """Test ancestor search is capped at 20 levels."""

    def test_ancestor_search_stops_at_max_levels(self, monkeypatch, tmp_path):
        """Test that ancestor search stops after 20 levels."""
        from pyfulmen.appidentity._loader import _discover_identity_path

        # Create a deep directory structure (25 levels)
        deep_dir = tmp_path
        for i in range(25):
            deep_dir = deep_dir / f"level_{i}"
            deep_dir.mkdir()

        # Change to the deep directory
        monkeypatch.chdir(deep_dir)

        # Should not find anything and should not scan infinitely
        with pytest.raises(AppIdentityNotFoundError) as exc_info:
            _discover_identity_path()

        # Should have searched exactly 20 levels (max depth reached)
        assert exc_info.value.searched_paths is not None
        assert len(exc_info.value.searched_paths) == 20, f"Expected 20 paths, got {len(exc_info.value.searched_paths)}"

        # Verify we hit the max depth by checking that we didn't search the starting directory's parent
        # beyond the 20-level limit. The deepest searched path should be 20 levels up from start.
        deepest_path = exc_info.value.searched_paths[-1]
        # The path should contain .fulmen/app.yaml and be within the search bounds
        assert ".fulmen/app.yaml" in str(deepest_path)
        print(f"Deepest searched path: {deepest_path}")


class TestEnvPrefixRegex:
    """Test env_prefix validation matches schema pattern."""

    def test_valid_env_prefixes(self):
        """Test env prefixes that should be valid."""
        valid_prefixes = [
            "APP_",
            "MY_APP_",
            "TEST_123_",
            "A_1_",
            "MY_APP_NAME_1_",
            "X_",
        ]

        for prefix in valid_prefixes:
            identity = AppIdentity(
                binary_name="test", vendor="test", env_prefix=prefix, config_name="test", description="Test"
            )
            assert identity.env_prefix == prefix

    def test_invalid_env_prefixes(self):
        """Test env prefixes that should be invalid."""
        invalid_prefixes = [
            "invalid",  # No underscore, lowercase
            "INVALID",  # No underscore
            "invalid_",  # Lowercase start
            "APP",  # No underscore
            "_APP_",  # Starts with underscore
            "123_",  # Starts with digit
        ]

        for prefix in invalid_prefixes:
            with pytest.raises(ValueError, match="must start with uppercase letter"):
                AppIdentity(
                    binary_name="test", vendor="test", env_prefix=prefix, config_name="test", description="Test"
                )


class TestErrorGuidance:
    """Test error messages include documentation links and guidance."""

    def test_not_found_error_includes_guidance(self):
        """Test AppIdentityNotFoundError includes guidance."""
        error = AppIdentityNotFoundError([Path("/test/path")])
        msg = str(error)

        assert "docs.fulmenhq.com" in msg
        assert "Create a .fulmen/app.yaml" in msg
        assert "FULMEN_APP_IDENTITY_PATH" in msg

    def test_validation_error_includes_guidance(self):
        """Test AppIdentityValidationError includes guidance."""
        error = AppIdentityValidationError(Path("/test/app.yaml"), ["Field 'binary_name' is required"])
        msg = str(error)

        assert "docs.fulmenhq.com" in msg
        assert "schema reference" in msg

    def test_load_error_includes_guidance(self):
        """Test AppIdentityLoadError includes guidance."""
        cause = Exception("Permission denied")
        error = AppIdentityLoadError(Path("/test/app.yaml"), cause)
        msg = str(error)

        assert "docs.fulmenhq.com" in msg
        assert "Check file format and permissions" in msg


class TestPublicProperties:
    """Test new public properties for provenance and metadata."""

    def test_provenance_property(self):
        """Test provenance property returns copy of internal data."""
        identity = AppIdentity(
            binary_name="test", vendor="test", env_prefix="TEST_", config_name="test", description="Test"
        )

        # Add some provenance data
        object.__setattr__(identity, "_provenance", {"source_path": "/test/path", "loaded_at": "2025-01-01T00:00:00Z"})

        # Test property returns copy
        provenance = identity.provenance
        assert provenance == identity._provenance
        assert provenance is not identity._provenance  # Should be copy

        # Test modification doesn't affect original
        provenance["test"] = "value"
        assert "test" not in identity.provenance

    def test_raw_metadata_property(self):
        """Test raw_metadata property returns copy of internal data."""
        identity = AppIdentity(
            binary_name="test", vendor="test", env_prefix="TEST_", config_name="test", description="Test"
        )

        # Add some raw metadata
        object.__setattr__(identity, "_raw_metadata", {"extra_field": "extra_value", "nested": {"key": "value"}})

        # Test property returns copy
        metadata = identity.raw_metadata
        assert metadata == identity._raw_metadata
        assert metadata is not identity._raw_metadata  # Should be copy

        # Test modification doesn't affect original
        metadata["test"] = "value"
        assert "test" not in identity.raw_metadata

    def test_properties_return_empty_dicts_when_unset(self):
        """Test properties return empty dicts when internal data is unset."""
        identity = AppIdentity(
            binary_name="test", vendor="test", env_prefix="TEST_", config_name="test", description="Test"
        )

        # Should return empty dicts, not None
        assert identity.provenance == {}
        assert identity.raw_metadata == {}

        # Should be different objects (copies)
        assert identity.provenance is not identity._provenance
        assert identity.raw_metadata is not identity._raw_metadata
