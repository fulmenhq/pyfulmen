"""Config defaults access utilities for Crucible assets.

This module provides helpers to discover and load configuration defaults
from the synced Crucible repository.

Example:
    >>> from pyfulmen.crucible import config
    >>> config.list_config_categories()
    ['sync', 'terminal']
    >>> defaults = config.load_config_defaults('terminal', 'v1.0.0', 'terminal-overrides-defaults')
"""

from pathlib import Path
from typing import Any

import yaml

from . import _paths


def list_config_categories() -> list[str]:
    """List available config categories.

    Returns:
        List of config category names

    Example:
        >>> list_config_categories()
        ['sync', 'terminal']
    """
    config_dir = _paths.get_config_dir()

    if not config_dir.exists():
        return []

    categories = [d.name for d in config_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]

    return sorted(categories)


def list_config_versions(category: str) -> list[str]:
    """List available versions for a config category.

    Args:
        category: Config category (e.g., 'terminal')

    Returns:
        List of version directories (e.g., ['v1.0.0'])

    Example:
        >>> list_config_versions('terminal')
        ['v1.0.0']
    """
    config_dir = _paths.get_config_dir()
    category_path = config_dir / category

    if not category_path.exists():
        return []

    versions = [
        d.name for d in category_path.iterdir() if d.is_dir() and not d.name.startswith(".")
    ]

    return sorted(versions)


def get_config_path(category: str, version: str, name: str) -> Path:
    """Get path to a config file.

    Args:
        category: Config category (e.g., 'terminal')
        version: Config version (e.g., 'v1.0.0')
        name: Config name without extension (e.g., 'terminal-overrides-defaults')

    Returns:
        Path to config file

    Raises:
        FileNotFoundError: If config file doesn't exist

    Example:
        >>> get_config_path('terminal', 'v1.0.0', 'terminal-overrides-defaults')
        PosixPath('.../config/crucible-py/terminal/v1.0.0/terminal-overrides-defaults.yaml')
    """
    config_dir = _paths.get_config_dir()

    # Try both .yaml and .yml extensions
    for ext in [".yaml", ".yml"]:
        config_path = config_dir / category / version / f"{name}{ext}"
        if config_path.exists():
            return config_path

    # Not found - raise with helpful message
    raise FileNotFoundError(
        f"Config not found: {category}/{version}/{name}\n"
        f"Searched in: {config_dir / category / version}\n"
        "Run 'make sync-crucible' to sync Crucible assets."
    )


def load_config_defaults(category: str, version: str, name: str) -> dict[str, Any]:
    """Load config defaults from Crucible.

    Args:
        category: Config category (e.g., 'terminal')
        version: Config version (e.g., 'v1.0.0')
        name: Config name without extension (e.g., 'terminal-overrides-defaults')

    Returns:
        Parsed config as dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file cannot be parsed

    Example:
        >>> defaults = load_config_defaults('terminal', 'v1.0.0', 'terminal-overrides-defaults')
        >>> 'ghostty' in defaults
        True
    """
    config_path = get_config_path(category, version, name)

    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse config {config_path}: {e}") from e


__all__ = [
    "list_config_categories",
    "list_config_versions",
    "get_config_path",
    "load_config_defaults",
]
