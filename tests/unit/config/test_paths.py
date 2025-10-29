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


def test_macos_paths_on_real_macos():
    """Test macOS path generation - only runs on actual macOS.

    No mocking, no complexity - just validate the actual behavior on macOS.
    This test is skipped on Linux/Windows runners.
    """
    import sys

    if sys.platform != "darwin":
        import pytest

        pytest.skip("macOS-specific test, skipping on non-macOS platform")

    base_dirs = paths.get_xdg_base_dirs()

    # On real macOS, should use Library/Application Support
    assert "Library" in str(base_dirs["config"])
    assert "Application Support" in str(base_dirs["config"])


def test_linux_paths_on_real_linux():
    """Test Linux path generation - only runs on actual Linux.

    No mocking, no complexity - just validate the actual behavior on Linux.
    This test is skipped on macOS/Windows runners.
    """
    import sys

    if sys.platform != "linux":
        import pytest

        pytest.skip("Linux-specific test, skipping on non-Linux platform")

    base_dirs = paths.get_xdg_base_dirs()

    # On real Linux, should use .config, .local/share, .cache
    assert ".config" in str(base_dirs["config"])
    assert ".local" in str(base_dirs["data"]) and "share" in str(base_dirs["data"])
    assert ".cache" in str(base_dirs["cache"])


def test_windows_paths_on_real_windows():
    """Test Windows path generation - only runs on actual Windows.

    No mocking, no complexity - just validate the actual behavior on Windows.
    This test is skipped on Linux/macOS runners.
    """
    import sys

    if sys.platform != "win32":
        import pytest

        pytest.skip("Windows-specific test, skipping on non-Windows platform")

    cache_dir = paths.get_app_cache_dir("myapp")

    # On real Windows, cache should include Cache subdirectory
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


def test_platform_paths_via_xdg_env_vars(monkeypatch, tmp_path):
    """Test platform path logic using XDG env vars instead of mocking Path.home().

    This reality-check test avoids the nightmare of mocking classmethods and
    import-time bindings. Instead, it uses the environment variable override
    mechanism that the code already supports, which is how real applications
    would customize paths anyway.
    """
    import pyfulmen.config.paths as paths_module

    # Create test directories
    test_config = tmp_path / "config"
    test_data = tmp_path / "data"
    test_cache = tmp_path / "cache"

    # Use XDG environment variables (real mechanism, not mocks)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(test_config))
    monkeypatch.setenv("XDG_DATA_HOME", str(test_data))
    monkeypatch.setenv("XDG_CACHE_HOME", str(test_cache))

    # Test Linux behavior with env vars
    monkeypatch.setattr(paths_module, "detect_platform", lambda: Platform.LINUX)
    result = paths.get_xdg_base_dirs()
    assert result["config"] == test_config
    assert result["data"] == test_data
    assert result["cache"] == test_cache

    # Test macOS behavior (should still respect XDG overrides)
    monkeypatch.setattr(paths_module, "detect_platform", lambda: Platform.MACOS)
    result = paths.get_xdg_base_dirs()
    assert result["config"] == test_config
    assert result["data"] == test_data
    assert result["cache"] == test_cache


def test_actual_platform_detection_in_ci():
    """Validate paths work correctly on actual CI runner without mocks.

    This test ensures the code works in the REAL CI environment. It validates
    actual behavior rather than testing our ability to mock things correctly.
    This should pass on any platform (Linux CI, macOS CI, local dev).
    """
    import sys

    base_dirs = paths.get_xdg_base_dirs()

    # Should return valid absolute paths regardless of platform
    assert base_dirs["config"].is_absolute()
    assert base_dirs["data"].is_absolute()
    assert base_dirs["cache"].is_absolute()

    # Validate platform-specific expectations on REAL platform
    if sys.platform == "linux":
        # On Linux (GitHub Actions runners), paths should contain .config or /home/
        config_str = str(base_dirs["config"])
        assert ".config" in config_str or "/home/" in config_str
    elif sys.platform == "darwin":
        # On macOS, paths should contain Library
        assert "Library" in str(base_dirs["config"])
    # Windows would check for AppData, but we're not testing on Windows yet
