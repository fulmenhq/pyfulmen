"""Config path utilities for PyFulmen.

Provides platform-aware config, data, and cache path resolution following
the XDG Base Directory Specification and Fulmen Config Path Standard.

Example:
    >>> from pyfulmen.config import paths
    >>> paths.get_fulmen_config_dir()
    PosixPath('/Users/you/.config/fulmen')
    >>> paths.get_app_config_dir('myapp')
    PosixPath('/Users/you/.config/myapp')
"""

import os
from pathlib import Path

from ._platform import Platform, detect_platform


def get_xdg_base_dirs() -> dict[str, Path]:
    """Get XDG base directories with platform-specific defaults.

    Respects XDG_CONFIG_HOME, XDG_DATA_HOME, and XDG_CACHE_HOME environment
    variables. Falls back to platform-specific defaults if not set.

    Returns:
        Dictionary with 'config', 'data', and 'cache' paths

    Example:
        >>> get_xdg_base_dirs()
        {'config': PosixPath('/Users/you/.config'),
         'data': PosixPath('/Users/you/.local/share'),
         'cache': PosixPath('/Users/you/.cache')}
    """
    platform_type = detect_platform()
    home = Path.home()

    # Linux/Unix defaults
    if platform_type == Platform.LINUX:
        config_default = home / ".config"
        data_default = home / ".local" / "share"
        cache_default = home / ".cache"

    # macOS defaults
    elif platform_type == Platform.MACOS:
        config_default = home / "Library" / "Application Support"
        data_default = home / "Library" / "Application Support"
        cache_default = home / "Library" / "Caches"

    # Windows defaults
    elif platform_type == Platform.WINDOWS:
        appdata = os.getenv("APPDATA", str(home / "AppData" / "Roaming"))
        localappdata = os.getenv("LOCALAPPDATA", str(home / "AppData" / "Local"))
        config_default = Path(appdata)
        data_default = Path(appdata)
        cache_default = Path(localappdata)

    # Unknown platform - use Unix-like defaults
    else:
        config_default = home / ".config"
        data_default = home / ".local" / "share"
        cache_default = home / ".cache"

    # Respect XDG environment overrides
    config_home = os.getenv("XDG_CONFIG_HOME")
    data_home = os.getenv("XDG_DATA_HOME")
    cache_home = os.getenv("XDG_CACHE_HOME")

    return {
        "config": Path(config_home) if config_home else config_default,
        "data": Path(data_home) if data_home else data_default,
        "cache": Path(cache_home) if cache_home else cache_default,
    }


def get_app_config_dir(app_name: str) -> Path:
    """Get configuration directory for an application.

    Args:
        app_name: Application name (e.g., 'myapp', 'fulmen')

    Returns:
        Path to app config directory

    Example:
        >>> get_app_config_dir('myapp')
        PosixPath('/Users/you/.config/myapp')
    """
    base_dirs = get_xdg_base_dirs()
    platform_type = detect_platform()

    # macOS/Windows: Use capitalized app name
    if platform_type in (Platform.MACOS, Platform.WINDOWS):
        app_name = app_name.capitalize()

    return base_dirs["config"] / app_name


def get_app_data_dir(app_name: str) -> Path:
    """Get data directory for an application.

    Args:
        app_name: Application name (e.g., 'myapp', 'fulmen')

    Returns:
        Path to app data directory

    Example:
        >>> get_app_data_dir('myapp')
        PosixPath('/Users/you/.local/share/myapp')
    """
    base_dirs = get_xdg_base_dirs()
    platform_type = detect_platform()

    # macOS/Windows: Use capitalized app name
    if platform_type in (Platform.MACOS, Platform.WINDOWS):
        app_name = app_name.capitalize()

    return base_dirs["data"] / app_name


def get_app_cache_dir(app_name: str) -> Path:
    """Get cache directory for an application.

    Args:
        app_name: Application name (e.g., 'myapp', 'fulmen')

    Returns:
        Path to app cache directory

    Example:
        >>> get_app_cache_dir('myapp')
        PosixPath('/Users/you/.cache/myapp')
    """
    base_dirs = get_xdg_base_dirs()
    platform_type = detect_platform()

    # macOS/Windows: Use capitalized app name
    if platform_type in (Platform.MACOS, Platform.WINDOWS):
        app_name = app_name.capitalize()

    # Windows: Add Cache subdirectory
    if platform_type == Platform.WINDOWS:
        return base_dirs["cache"] / app_name / "Cache"

    return base_dirs["cache"] / app_name


def get_app_config_paths(app_name: str, legacy_names: list[str] | None = None) -> list[Path]:
    """Get ordered list of config search paths for an application.

    Returns paths in priority order: current name first, then legacy names.

    Args:
        app_name: Current application name
        legacy_names: Optional list of legacy app names to check

    Returns:
        List of paths to search (ordered by priority)

    Example:
        >>> get_app_config_paths('myapp', legacy_names=['oldapp'])
        [PosixPath('/Users/you/.config/myapp'),
         PosixPath('/Users/you/.config/oldapp')]
    """
    paths = [get_app_config_dir(app_name)]

    if legacy_names:
        for legacy_name in legacy_names:
            paths.append(get_app_config_dir(legacy_name))

    return paths


def get_fulmen_config_dir() -> Path:
    """Get Fulmen ecosystem configuration directory.

    Returns:
        Path to fulmen config directory

    Example:
        >>> get_fulmen_config_dir()
        PosixPath('/Users/you/.config/fulmen')  # Linux
        PosixPath('/Users/you/Library/Application Support/Fulmen')  # macOS
    """
    return get_app_config_dir("fulmen")


def get_fulmen_data_dir() -> Path:
    """Get Fulmen ecosystem data directory.

    Returns:
        Path to fulmen data directory

    Example:
        >>> get_fulmen_data_dir()
        PosixPath('/Users/you/.local/share/fulmen')  # Linux
        PosixPath('/Users/you/Library/Application Support/Fulmen')  # macOS
    """
    return get_app_data_dir("fulmen")


def get_fulmen_cache_dir() -> Path:
    """Get Fulmen ecosystem cache directory.

    Returns:
        Path to fulmen cache directory

    Example:
        >>> get_fulmen_cache_dir()
        PosixPath('/Users/you/.cache/fulmen')  # Linux
        PosixPath('/Users/you/Library/Caches/Fulmen')  # macOS
    """
    return get_app_cache_dir("fulmen")


__all__ = [
    "get_xdg_base_dirs",
    "get_app_config_dir",
    "get_app_data_dir",
    "get_app_cache_dir",
    "get_app_config_paths",
    "get_fulmen_config_dir",
    "get_fulmen_data_dir",
    "get_fulmen_cache_dir",
]
