"""Tests for pyfulmen.config.paths module."""

import os
from pathlib import Path
from unittest.mock import patch

from pyfulmen.config import paths
from pyfulmen.config._platform import Platform


def test_get_xdg_base_dirs():
    """Test getting XDG base directories."""
    base_dirs = paths.get_xdg_base_dirs()

    assert "config" in base_dirs
    assert "data" in base_dirs
    assert "cache" in base_dirs

    # All should be Path objects
    assert isinstance(base_dirs["config"], Path)
    assert isinstance(base_dirs["data"], Path)
    assert isinstance(base_dirs["cache"], Path)


def test_get_xdg_base_dirs_with_env_override():
    """Test XDG base dirs with environment variable overrides."""
    with patch.dict(
        os.environ,
        {
            "XDG_CONFIG_HOME": "/custom/config",
            "XDG_DATA_HOME": "/custom/data",
            "XDG_CACHE_HOME": "/custom/cache",
        },
    ):
        base_dirs = paths.get_xdg_base_dirs()

        assert base_dirs["config"] == Path("/custom/config")
        assert base_dirs["data"] == Path("/custom/data")
        assert base_dirs["cache"] == Path("/custom/cache")


def test_get_app_config_dir():
    """Test getting app config directory."""
    config_dir = paths.get_app_config_dir("fulmenhq/myapp")

    assert isinstance(config_dir, Path)
    assert "fulmenhq" in str(config_dir)
    assert "myapp" in str(config_dir)


def test_get_app_data_dir():
    """Test getting app data directory."""
    data_dir = paths.get_app_data_dir("fulmenhq/myapp")

    assert isinstance(data_dir, Path)
    assert "myapp" in str(data_dir).lower()


def test_get_app_cache_dir():
    """Test getting app cache directory."""
    cache_dir = paths.get_app_cache_dir("fulmenhq/myapp")

    assert isinstance(cache_dir, Path)
    assert "myapp" in str(cache_dir).lower()


def test_get_app_config_paths_no_legacy():
    """Test getting app config paths without legacy names."""
    config_paths = paths.get_app_config_paths("myapp")

    assert isinstance(config_paths, list)
    assert len(config_paths) == 1
    assert "myapp" in str(config_paths[0]).lower()


def test_get_app_config_paths_with_legacy():
    """Test getting app config paths with legacy names."""
    config_paths = paths.get_app_config_paths(
        "fulmenhq/myapp", legacy_names=["fulmenhq/oldapp", "fulmenhq/ancientapp"]
    )

    assert isinstance(config_paths, list)
    assert len(config_paths) == 3

    # First should be current name
    assert "myapp" in str(config_paths[0])
    # Rest should be legacy names in order
    assert "oldapp" in str(config_paths[1])
    assert "ancientapp" in str(config_paths[2])


def test_get_fulmen_config_dir():
    """Test getting Fulmen config directory."""
    fulmen_config = paths.get_fulmen_config_dir()

    assert isinstance(fulmen_config, Path)
    assert "fulmen" in str(fulmen_config)


def test_get_fulmen_data_dir():
    """Test getting Fulmen data directory."""
    fulmen_data = paths.get_fulmen_data_dir()

    assert isinstance(fulmen_data, Path)
    assert "fulmen" in str(fulmen_data)


def test_get_fulmen_cache_dir():
    """Test getting Fulmen cache directory."""
    fulmen_cache = paths.get_fulmen_cache_dir()

    assert isinstance(fulmen_cache, Path)
    assert "fulmen" in str(fulmen_cache)


@patch("pyfulmen.config.paths.detect_platform")
def test_macos_paths(mock_detect):
    """Test path generation on macOS."""
    mock_detect.return_value = Platform.MACOS

    base_dirs = paths.get_xdg_base_dirs()

    # macOS should use Library/Application Support
    assert "Library" in str(base_dirs["config"])
    assert "Application Support" in str(base_dirs["config"])


@patch("pyfulmen.config.paths.detect_platform")
def test_linux_paths(mock_detect):
    """Test path generation on Linux."""
    mock_detect.return_value = Platform.LINUX

    base_dirs = paths.get_xdg_base_dirs()

    # Linux should use .config, .local/share, .cache
    assert ".config" in str(base_dirs["config"])
    assert ".local" in str(base_dirs["data"]) and "share" in str(base_dirs["data"])
    assert ".cache" in str(base_dirs["cache"])


@patch("pyfulmen.config.paths.detect_platform")
def test_windows_paths(mock_detect):
    """Test path generation on Windows."""
    mock_detect.return_value = Platform.WINDOWS

    cache_dir = paths.get_app_cache_dir("myapp")

    # Windows cache should include Cache subdirectory
    assert "Cache" in str(cache_dir)


def test_fulmen_env_overrides(tmp_path, monkeypatch):
    """FULMEN_* environment overrides should take precedence."""
    monkeypatch.setenv("FULMEN_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("FULMEN_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("FULMEN_CACHE_HOME", str(tmp_path / "cache"))

    assert paths.get_fulmen_config_dir() == tmp_path / "cfg"
    assert paths.get_fulmen_data_dir() == tmp_path / "data"
    assert paths.get_fulmen_cache_dir() == tmp_path / "cache"


def test_ensure_dir(tmp_path):
    """ensure_dir should create directories."""
    target = tmp_path / "nested" / "dir"
    assert not target.exists()
    paths.ensure_dir(target)
    assert target.exists()


def test_config_search_paths_alias():
    """get_config_search_paths should match get_app_config_paths."""
    assert paths.get_config_search_paths(
        "fulmenhq/myapp", vendor="fulmenhq"
    ) == paths.get_app_config_paths("fulmenhq/myapp", vendor="fulmenhq")
