"""Config path utilities for PyFulmen.

Implements the Fulmen Config Path Standard with platform-aware helpers for
config/data/cache discovery, vendor/app namespace handling, and optional
directory creation. Functions accept identifiers in the form
`<app>` or `<vendor>/<app>` and normalise names to kebab-case.

Example:
    >>> from pyfulmen.config import paths
    >>> paths.get_fulmen_config_dir()
    PosixPath('/Users/you/.config/fulmen')
    >>> paths.get_app_config_dir('fulmenhq/myapp')
    PosixPath('/Users/you/.config/fulmenhq/myapp')
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from ._platform import Platform, detect_platform

# Defaults align with Fulmen naming conventions
DEFAULT_VENDOR = "fulmenhq"
DEFAULT_APP_NAMESPACE = "fulmen"


def _normalise_segment(value: str) -> str:
    """Convert vendor/app segment to kebab-case."""
    return value.strip().replace(" ", "-").replace("_", "-").lower()


def _split_app_identifier(app: str, vendor: str | None = None) -> tuple[str, str]:
    """Resolve vendor/app tuple from identifier."""
    app = app.strip()
    if "/" in app:
        potential_vendor, app_name = app.split("/", 1)
        vendor = vendor or potential_vendor
    else:
        app_name = app

    vendor_segment = _normalise_segment(vendor or DEFAULT_VENDOR)
    app_segment = _normalise_segment(app_name or DEFAULT_APP_NAMESPACE)
    return vendor_segment, app_segment


def _apply_fulmen_override(kind: str, default: Path) -> Path:
    """Apply FULMEN_* environment overrides for config/data/cache roots."""
    env_var = {
        "config": "FULMEN_CONFIG_HOME",
        "data": "FULMEN_DATA_HOME",
        "cache": "FULMEN_CACHE_HOME",
    }[kind]
    override = os.getenv(env_var)
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_absolute():
            return candidate
    return default


def get_xdg_base_dirs() -> dict[str, Path]:
    """Get XDG base directories with platform-specific defaults."""
    platform_type = detect_platform()
    home = Path.home()

    if platform_type == Platform.LINUX:
        config_default = home / ".config"
        data_default = home / ".local" / "share"
        cache_default = home / ".cache"
    elif platform_type == Platform.MACOS:
        config_default = home / "Library" / "Application Support"
        data_default = home / "Library" / "Application Support"
        cache_default = home / "Library" / "Caches"
    elif platform_type == Platform.WINDOWS:
        appdata = os.getenv("APPDATA", str(home / "AppData" / "Roaming"))
        localappdata = os.getenv("LOCALAPPDATA", str(home / "AppData" / "Local"))
        config_default = Path(appdata)
        data_default = Path(appdata)
        cache_default = Path(localappdata)
    else:
        config_default = home / ".config"
        data_default = home / ".local" / "share"
        cache_default = home / ".cache"

    config_home = os.getenv("XDG_CONFIG_HOME")
    data_home = os.getenv("XDG_DATA_HOME")
    cache_home = os.getenv("XDG_CACHE_HOME")

    base_dirs = {
        "config": Path(config_home).expanduser() if config_home else config_default,
        "data": Path(data_home).expanduser() if data_home else data_default,
        "cache": Path(cache_home).expanduser() if cache_home else cache_default,
    }

    for kind in ("config", "data", "cache"):
        base_dirs[kind] = _apply_fulmen_override(kind, base_dirs[kind])

    return base_dirs


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating parents if needed."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_app_config_dir(
    app: str,
    *,
    vendor: str | None = None,
    ensure: bool = False,
) -> Path:
    """Return config directory for vendor/app."""
    base_dirs = get_xdg_base_dirs()
    vendor_segment, app_segment = _split_app_identifier(app, vendor=vendor)
    config_path = base_dirs["config"] / vendor_segment / app_segment
    return ensure_dir(config_path) if ensure else config_path


def get_app_data_dir(
    app: str,
    *,
    vendor: str | None = None,
    ensure: bool = False,
) -> Path:
    """Return data directory for vendor/app."""
    base_dirs = get_xdg_base_dirs()
    vendor_segment, app_segment = _split_app_identifier(app, vendor=vendor)
    data_path = base_dirs["data"] / vendor_segment / app_segment
    return ensure_dir(data_path) if ensure else data_path


def get_app_cache_dir(
    app: str,
    *,
    vendor: str | None = None,
    ensure: bool = False,
) -> Path:
    """Return cache directory for vendor/app."""
    base_dirs = get_xdg_base_dirs()
    vendor_segment, app_segment = _split_app_identifier(app, vendor=vendor)
    cache_root = base_dirs["cache"] / vendor_segment / app_segment
    if detect_platform() == Platform.WINDOWS:
        cache_root = cache_root / "Cache"
    return ensure_dir(cache_root) if ensure else cache_root


def get_app_config_paths(
    app: str,
    legacy_names: Iterable[str] | None = None,
    *,
    vendor: str | None = None,
) -> list[Path]:
    """Return ordered list of config search paths for vendor/app and legacy names."""
    paths = [get_app_config_dir(app, vendor=vendor)]
    if legacy_names:
        for legacy in legacy_names:
            paths.append(get_app_config_dir(legacy, vendor=vendor))
    return paths


def get_config_search_paths(app: str, *, vendor: str | None = None) -> list[Path]:
    """Alias matching Config Path API standard."""
    return get_app_config_paths(app, vendor=vendor)


def get_fulmen_config_dir(*, ensure: bool = False) -> Path:
    """Return Fulmen ecosystem config directory."""
    override = os.getenv("FULMEN_CONFIG_HOME")
    if override:
        override_path = Path(override).expanduser()
        return ensure_dir(override_path) if ensure else override_path
    path = get_app_config_dir(DEFAULT_APP_NAMESPACE, vendor=DEFAULT_VENDOR)
    return ensure_dir(path) if ensure else path


def get_fulmen_data_dir(*, ensure: bool = False) -> Path:
    """Return Fulmen ecosystem data directory."""
    override = os.getenv("FULMEN_DATA_HOME")
    if override:
        override_path = Path(override).expanduser()
        return ensure_dir(override_path) if ensure else override_path
    path = get_app_data_dir(DEFAULT_APP_NAMESPACE, vendor=DEFAULT_VENDOR)
    return ensure_dir(path) if ensure else path


def get_fulmen_cache_dir(*, ensure: bool = False) -> Path:
    """Return Fulmen ecosystem cache directory."""
    override = os.getenv("FULMEN_CACHE_HOME")
    if override:
        override_path = Path(override).expanduser()
        return ensure_dir(override_path) if ensure else override_path
    path = get_app_cache_dir(DEFAULT_APP_NAMESPACE, vendor=DEFAULT_VENDOR)
    return ensure_dir(path) if ensure else path


def get_org_config_dir(*, ensure: bool = False) -> Path:
    """Return organization-level config directory.

    Defaults to /opt/fulmen but can be overridden via FULMEN_ORG_PATH
    environment variable for multi-tenant deployments.

    Returns:
        Path to organization config directory

    Example:
        >>> get_org_config_dir()
        PosixPath('/opt/fulmen')
        >>> os.environ['FULMEN_ORG_PATH'] = '/shared/acme/fulmen'
        >>> get_org_config_dir()
        PosixPath('/shared/acme/fulmen')
    """
    override = os.getenv("FULMEN_ORG_PATH")
    if override:
        org_path = Path(override).expanduser()
        return ensure_dir(org_path) if ensure else org_path

    default_org_path = Path("/opt/fulmen")
    return ensure_dir(default_org_path) if ensure else default_org_path


def ensure_fulmen_config_dir() -> Path:
    """Ensure Fulmen config directory exists."""
    return ensure_dir(get_fulmen_config_dir())


def ensure_fulmen_data_dir() -> Path:
    """Ensure Fulmen data directory exists."""
    return ensure_dir(get_fulmen_data_dir())


def ensure_fulmen_cache_dir() -> Path:
    """Ensure Fulmen cache directory exists."""
    return ensure_dir(get_fulmen_cache_dir())


__all__ = [
    "get_xdg_base_dirs",
    "get_app_config_dir",
    "get_app_data_dir",
    "get_app_cache_dir",
    "get_app_config_paths",
    "get_config_search_paths",
    "get_fulmen_config_dir",
    "get_fulmen_data_dir",
    "get_fulmen_cache_dir",
    "get_org_config_dir",
    "ensure_dir",
    "ensure_fulmen_config_dir",
    "ensure_fulmen_data_dir",
    "ensure_fulmen_cache_dir",
]
