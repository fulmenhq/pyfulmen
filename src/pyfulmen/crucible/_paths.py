"""Internal path utilities for Crucible shim package.

This module provides internal helpers for locating Crucible assets.
Not part of the public API.
"""

from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent.parent

SCHEMAS_DIR = _REPO_ROOT / "schemas" / "crucible-py"
DOCS_DIR = _REPO_ROOT / "docs" / "crucible-py"
CONFIG_DIR = _REPO_ROOT / "config" / "crucible-py"


def get_repo_root() -> Path:
    """Get repository root directory."""
    return _REPO_ROOT


def get_schemas_dir() -> Path:
    """Get schemas directory path."""
    return SCHEMAS_DIR


def get_docs_dir() -> Path:
    """Get docs directory path."""
    return DOCS_DIR


def get_config_dir() -> Path:
    """Get config directory path."""
    return CONFIG_DIR


def get_crucible_metadata_dir() -> Path:
    """Get .crucible/metadata directory path.
    
    Contains sync metadata from goneat ssot sync.
    Future versions will include multi-SSOT tracking here.
    """
    return _REPO_ROOT / ".crucible" / "metadata"


__all__ = [
    "get_docs_dir",
    "get_schemas_dir",
    "get_config_dir",
    "get_crucible_metadata_dir",
]
