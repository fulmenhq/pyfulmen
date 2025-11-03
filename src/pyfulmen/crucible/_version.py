"""Crucible version information.

Note: Legacy .crucible-version file support removed. Crucible version tracking
will be reimplemented in goneat v0.3.x with multi-SSOT tracking support.

For now, version information can be inferred from .crucible/metadata/ directory.
"""

from pathlib import Path

import yaml

from . import _paths
from .errors import CrucibleVersionError
from .models import CrucibleVersion


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


def get_crucible_version() -> CrucibleVersion:
    """Get version metadata for embedded Crucible assets.

    Reads version information from .crucible/metadata/sync-keys.yaml if available.
    Extracts version, commit (defaults to "unknown"), and syncedAt (defaults to None).

    Expected sync-keys.yaml structure:
        version: "2025.10.0"
        commit: "abc123def456"      # optional
        syncedAt: "2025-10-20T18:42:11Z"  # optional
        keys: [...]

    Returns:
        CrucibleVersion instance with version, commit, and synced_at

    Raises:
        CrucibleVersionError: If version metadata cannot be determined

    Example:
        >>> version = get_crucible_version()
        >>> print(f"Crucible v{version.version} (commit: {version.commit})")
        Crucible v2025.10.0 (commit: unknown)
    """
    metadata_dir = _paths.get_crucible_metadata_dir()
    sync_keys_path = metadata_dir / "sync-keys.yaml"

    if not sync_keys_path.exists():
        raise CrucibleVersionError(
            f"Crucible metadata not found at {sync_keys_path}. Run 'make sync-crucible' to sync Crucible assets."
        )

    try:
        with sync_keys_path.open() as f:
            data = yaml.safe_load(f)

        version = data.get("version")
        if not version:
            raise CrucibleVersionError(f"Version field not found in {sync_keys_path}")

        commit = data.get("commit", "unknown")
        synced_at = data.get("syncedAt")

        return CrucibleVersion(
            version=str(version),
            commit=str(commit) if commit else "unknown",
            synced_at=str(synced_at) if synced_at else None,
        )

    except yaml.YAMLError as e:
        raise CrucibleVersionError(f"Failed to parse {sync_keys_path}: {e}") from e
    except Exception as e:
        raise CrucibleVersionError(f"Failed to read Crucible version metadata: {e}") from e


__all__ = [
    "get_crucible_metadata_path",
    "get_crucible_info",
    "get_crucible_version",
]
