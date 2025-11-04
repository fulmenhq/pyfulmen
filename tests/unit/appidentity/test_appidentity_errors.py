"""
Unit tests for app identity exceptions.
"""

from pathlib import Path

import pytest

from pyfulmen.appidentity.errors import (
    AppIdentityError,
    AppIdentityLoadError,
    AppIdentityNotFoundError,
    AppIdentityValidationError,
)


class TestAppIdentityError:
    """Test base exception."""

    def test_base_exception(self):
        """Test base exception can be raised."""
        with pytest.raises(AppIdentityError, match="Test error"):
            raise AppIdentityError("Test error")


class TestAppIdentityNotFoundError:
    """Test not found exception."""

    def test_not_found_with_paths(self):
        """Test exception with searched paths."""
        paths = [Path("/path1"), Path("/path2")]

        with pytest.raises(AppIdentityNotFoundError) as exc_info:
            raise AppIdentityNotFoundError(paths)

        assert exc_info.value.searched_paths == paths
        assert "path1" in str(exc_info.value)
        assert "path2" in str(exc_info.value)

    def test_not_found_empty_paths(self):
        """Test exception with empty paths list."""
        with pytest.raises(AppIdentityNotFoundError) as exc_info:
            raise AppIdentityNotFoundError([])

        assert exc_info.value.searched_paths == []


class TestAppIdentityValidationError:
    """Test validation error exception."""

    def test_validation_with_errors(self):
        """Test exception with validation errors."""
        path = Path("/test/app.yaml")
        errors = ["Missing field: binary_name", "Invalid env prefix"]

        with pytest.raises(AppIdentityValidationError) as exc_info:
            raise AppIdentityValidationError(path, errors)

        assert exc_info.value.path == path
        assert exc_info.value.validation_errors == errors
        assert str(path) in str(exc_info.value)
        assert "Missing field" in str(exc_info.value)

    def test_validation_empty_errors(self):
        """Test exception with empty errors list."""
        path = Path("/test/app.yaml")

        with pytest.raises(AppIdentityValidationError) as exc_info:
            raise AppIdentityValidationError(path, [])

        assert exc_info.value.validation_errors == []


class TestAppIdentityLoadError:
    """Test load error exception."""

    def test_load_with_cause(self):
        """Test exception with cause."""
        path = Path("/test/app.yaml")
        cause = OSError("Permission denied")

        with pytest.raises(AppIdentityLoadError) as exc_info:
            raise AppIdentityLoadError(path, cause)

        assert exc_info.value.path == path
        assert exc_info.value.cause == cause
        assert str(path) in str(exc_info.value)
        assert "Permission denied" in str(exc_info.value)
