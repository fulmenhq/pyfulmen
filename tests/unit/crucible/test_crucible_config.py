"""Tests for pyfulmen.crucible.config module."""

import pytest

from pyfulmen.crucible import config


def test_list_config_categories():
    """Test listing config categories."""
    categories = config.list_config_categories()

    assert isinstance(categories, list)
    # May be empty or contain categories like 'terminal', 'sync'
    if len(categories) > 0:
        assert all(isinstance(c, str) for c in categories)


def test_list_config_versions():
    """Test listing config versions for a category."""
    # Test with terminal if it exists
    versions = config.list_config_versions("terminal")

    assert isinstance(versions, list)
    if len(versions) > 0:
        # Versions should follow vX.Y.Z format
        assert versions[0].startswith("v")


def test_get_config_path():
    """Test getting path to a config file."""
    # Test with known config from sync
    path = config.get_config_path("terminal", "v1.0.0", "terminal-overrides-defaults")

    assert path.exists()
    assert path.suffix in [".yaml", ".yml"]
    assert "terminal-overrides-defaults" in path.name


def test_get_config_path_not_found():
    """Test getting path to non-existent config."""
    with pytest.raises(FileNotFoundError):
        config.get_config_path("invalid", "v1.0.0", "nonexistent")


def test_load_config_defaults():
    """Test loading config defaults."""
    defaults = config.load_config_defaults("terminal", "v1.0.0", "terminal-overrides-defaults")

    assert isinstance(defaults, dict)
    # Should contain terminal-related config
    assert len(defaults) > 0
