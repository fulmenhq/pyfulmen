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
        format: File format/extension (e.g., 'json', 'yaml', 'md') (optional)
        size: File size in bytes (optional)
        modified: ISO-8601 timestamp of last modification (optional)
        checksum: SHA256 checksum (optional, computed on-demand if None)

    Example:
        >>> asset = AssetMetadata(
        ...     id='observability/logging/v1.0.0/logger-config',
        ...     category='schemas',
        ...     path=Path('/path/to/schema.json'),
        ...     description='Logger configuration schema',
        ...     format='json',
        ...     size=2048,
        ...     modified='2025-10-20T15:30:00Z',
        ...     checksum='abc123...'
        ... )
        >>> print(f"{asset.id} ({asset.format}, {asset.size} bytes)")
        observability/logging/v1.0.0/logger-config (json, 2048 bytes)
    """

    id: str
    category: str
    path: Path
    description: str | None = None
    format: str | None = None
    size: int | None = None
    modified: str | None = None
    checksum: str | None = None


@dataclass(frozen=True)
class CrucibleVersion:
    """Version metadata for embedded Crucible assets.

    Provides information about the version of Crucible assets embedded in
    PyFulmen, including sync timestamp and commit information when available.

    Attributes:
        version: Semantic or CalVer version string (e.g., '2025.10.0')
        commit: Git commit SHA of synced Crucible version (defaults to "unknown" if unavailable)
        synced_at: ISO-8601 timestamp of last sync (optional, None if unavailable)

    Example:
        >>> version = CrucibleVersion(
        ...     version='2025.10.0',
        ...     commit='abc123def456',
        ...     synced_at='2025-10-20T18:42:11Z'
        ... )
        >>> print(f"Crucible v{version.version} (commit: {version.commit})")
        Crucible v2025.10.0 (commit: abc123def456)
    """

    version: str
    commit: str | None = None
    synced_at: str | None = None


__all__ = [
    "AssetMetadata",
    "CrucibleVersion",
]
