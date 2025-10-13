"""Tests for pyfulmen.version module."""

from pyfulmen.version import (
    get_version_info,
    read_version,
    validate_version_sync,
)


def test_read_version():
    """Test reading version from VERSION file."""
    version = read_version()
    assert version
    assert isinstance(version, str)
    assert len(version.split(".")) >= 2  # At least X.Y format


def test_get_version_info():
    """Test getting version info dictionary."""
    info = get_version_info()

    assert "version" in info
    assert "source" in info
    assert "valid" in info

    assert info["source"] == "VERSION"
    assert isinstance(info["valid"], bool)
    assert info["valid"] is True  # Should be valid format


def test_validate_version_sync():
    """Test version sync validation across files."""
    sync_info = validate_version_sync()

    assert "synced" in sync_info
    assert "version_file" in sync_info
    assert "pyproject_version" in sync_info
    assert "init_version" in sync_info
    assert "mismatches" in sync_info

    # All versions should match
    assert sync_info["synced"] is True, f"Version mismatch detected: {sync_info['mismatches']}"

    # All versions should be identical
    version_file = sync_info["version_file"]
    assert sync_info["pyproject_version"] == version_file
    assert sync_info["init_version"] == version_file


def test_version_format_semver():
    """Test that version follows SemVer format."""
    version = read_version()

    # Should be X.Y.Z or X.Y.Z-suffix
    parts = version.split("-")[0].split(".")
    assert len(parts) == 3, f"Expected SemVer format (X.Y.Z), got {version}"

    # Each part should be numeric
    major, minor, patch = parts
    assert major.isdigit()
    assert minor.isdigit()
    assert patch.isdigit()
