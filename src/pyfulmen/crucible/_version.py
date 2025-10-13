"""Crucible version information.

Note: Legacy .crucible-version file support removed. Crucible version tracking
will be reimplemented in goneat v0.3.x with multi-SSOT tracking support.

For now, version information can be inferred from .crucible/metadata/ directory.
"""

from pathlib import Path

from . import _paths


def get_crucible_metadata_path() -> Path:
    """Get path to Crucible metadata directory.

    Returns:
        Path to .crucible/metadata/ directory
    """
    return _paths.get_crucible_metadata_dir()


def get_crucible_info() -> dict[str, str]:
    """Get Crucible asset information.

    Returns:
        Dictionary with Crucible metadata:
        - schemas_dir: Path to schemas directory
        - docs_dir: Path to docs directory
        - config_dir: Path to config directory
        - metadata_dir: Path to sync metadata directory

    Note: Version tracking will be added in future goneat releases.
    """
    return {
        "schemas_dir": str(_paths.get_schemas_dir()),
        "docs_dir": str(_paths.get_docs_dir()),
        "config_dir": str(_paths.get_config_dir()),
        "metadata_dir": str(_paths.get_crucible_metadata_dir()),
    }


__all__ = [
    "get_crucible_metadata_path",
    "get_crucible_info",
]
