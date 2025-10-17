"""
Tests for pyfulmen.pathfinder.safety module.

Tests path validation and safety checks for preventing traversal attacks.
"""

import pytest

from pyfulmen.pathfinder.safety import (
    InvalidPathError,
    PathTraversalError,
    is_safe_path,
    validate_path,
)


class TestValidatePath:
    """Test path validation function."""

    def test_valid_relative_path(self):
        """Valid relative paths should pass validation."""
        validate_path("valid/path/to/file.txt")
        validate_path("single_file.txt")
        validate_path("path/with/multiple/components")

    def test_valid_nested_path(self):
        """Nested paths without traversal should be valid."""
        validate_path("foo/bar/baz/file.txt")
        validate_path("a/b/c/d/e/f")

    def test_path_traversal_raises(self):
        """Path traversal attempts should raise PathTraversalError."""
        with pytest.raises(PathTraversalError):
            validate_path("../escape")

        with pytest.raises(PathTraversalError):
            validate_path("path/../escape")

        with pytest.raises(PathTraversalError):
            validate_path("../../double_escape")

    def test_empty_path_raises(self):
        """Empty paths should raise InvalidPathError."""
        with pytest.raises(InvalidPathError):
            validate_path("")

    def test_current_directory_raises(self):
        """Current directory path should raise InvalidPathError."""
        with pytest.raises(InvalidPathError):
            validate_path(".")

    def test_root_path_raises(self):
        """Root paths should raise InvalidPathError (too broad)."""
        with pytest.raises(InvalidPathError):
            validate_path("/")

        with pytest.raises(InvalidPathError):
            validate_path("\\")

    def test_normalized_traversal_caught(self):
        """Normalized paths with traversal should be caught."""
        # os.path.normpath will normalize these, but we still catch ".."
        with pytest.raises(PathTraversalError):
            validate_path("foo/../bar")


class TestIsSafePath:
    """Test convenience function for safe path checking."""

    def test_safe_paths_return_true(self):
        """Safe paths should return True."""
        assert is_safe_path("valid/path")
        assert is_safe_path("file.txt")
        assert is_safe_path("nested/deep/path/file")

    def test_unsafe_paths_return_false(self):
        """Unsafe paths should return False."""
        assert not is_safe_path("../escape")
        assert not is_safe_path("")
        assert not is_safe_path(".")
        assert not is_safe_path("/")
        assert not is_safe_path("path/../traversal")

    def test_no_exception_raised(self):
        """is_safe_path should never raise exceptions."""
        # Should not raise, just return False
        result = is_safe_path("../bad")
        assert result is False

        result = is_safe_path("")
        assert result is False


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_path_with_spaces(self):
        """Paths with spaces should be valid if no traversal."""
        validate_path("path with spaces/file.txt")
        assert is_safe_path("path with spaces")

    def test_path_with_dots_in_filename(self):
        """Filenames with dots (not ..) should be valid."""
        validate_path("path/to/file.tar.gz")
        validate_path("hidden/.dotfile")
        assert is_safe_path("config.yaml")

    def test_path_with_special_chars(self):
        """Paths with special characters should be validated."""
        validate_path("path/with-dash/file_underscore.txt")
        assert is_safe_path("file@special#chars.txt")

    def test_windows_style_paths(self):
        """Windows-style paths should be validated correctly."""
        # Note: os.path.normpath handles platform differences
        validate_path("path\\to\\file.txt")
        assert is_safe_path("windows\\path")
