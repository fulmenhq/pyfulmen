"""Data models for Crucible asset metadata and version information.

Provides dataclasses for representing Crucible asset metadata and version
information used by the bridge API for unified asset access.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssetMetadata:
    """Metadata for a Crucible asset (schema, doc, or config file).

    Used by the bridge API to provide rich information about discovered assets.

    Attributes:
        id: Stable asset identifier (e.g., 'observability/logging/v1.0.0/logger-config')
        category: Asset category ('schemas', 'docs', or 'config')
        path: Absolute path to asset file
        description: Human-readable description (optional)
        checksum: SHA256 checksum (optional, computed on-demand if None)

    Example:
        >>> asset = AssetMetadata(
        ...     id='observability/logging/v1.0.0/logger-config',
        ...     category='schemas',
        ...     path=Path('/path/to/schema.json'),
        ...     description='Logger configuration schema'
        ... )
        >>> print(asset.id)
        observability/logging/v1.0.0/logger-config
    """

    id: str
    category: str
    path: Path
    description: str | None = None
    checksum: str | None = None


@dataclass(frozen=True)
class CrucibleVersion:
    """Version metadata for embedded Crucible assets.

    Provides information about the version of Crucible assets embedded in
    PyFulmen, including sync date and commit information when available.

    Attributes:
        version: Semantic or CalVer version string (e.g., '2025.10.0')
        sync_date: ISO 8601 date of last sync (optional)
        commit: Git commit SHA of synced Crucible version (optional)

    Example:
        >>> version = CrucibleVersion(
        ...     version='2025.10.0',
        ...     sync_date='2025-10-20T15:30:00Z',
        ...     commit='abc123def456'
        ... )
        >>> print(f"Crucible v{version.version}")
        Crucible v2025.10.0
    """

    version: str
    sync_date: str | None = None
    commit: str | None = None


__all__ = [
    "AssetMetadata",
    "CrucibleVersion",
]
