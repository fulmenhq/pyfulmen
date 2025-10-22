"""Metadata computation utilities for Crucible assets.

Provides functions for computing checksums, file sizes, formats, and timestamps
for asset metadata population.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path


def compute_checksum(path: Path, buffer_size: int = 65536) -> str:
    """Compute SHA-256 checksum of a file.

    Args:
        path: Path to file
        buffer_size: Buffer size for reading (default 64KB)

    Returns:
        Hexadecimal SHA-256 digest string

    Raises:
        FileNotFoundError: If file doesn't exist
        OSError: If file cannot be read

    Example:
        >>> path = Path("/path/to/schema.json")
        >>> checksum = compute_checksum(path)
        >>> print(checksum)
        'a1b2c3d4e5f6...'
    """
    sha256 = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            sha256.update(data)

    return sha256.hexdigest()


def get_file_size(path: Path) -> int:
    """Get file size in bytes.

    Args:
        path: Path to file

    Returns:
        File size in bytes

    Raises:
        FileNotFoundError: If file doesn't exist

    Example:
        >>> path = Path("/path/to/schema.json")
        >>> size = get_file_size(path)
        >>> print(f"{size} bytes")
        2048 bytes
    """
    return path.stat().st_size


def get_file_format(path: Path) -> str:
    """Extract file format/extension without leading dot.

    Args:
        path: Path to file

    Returns:
        File extension without dot (e.g., 'json', 'yaml', 'md')
        Returns 'unknown' if no extension found

    Example:
        >>> get_file_format(Path("schema.json"))
        'json'
        >>> get_file_format(Path("config.yaml"))
        'yaml'
        >>> get_file_format(Path("doc.md"))
        'md'
    """
    suffix = path.suffix.lstrip(".")
    return suffix if suffix else "unknown"


def get_modified_time(path: Path, sync_metadata: dict | None = None) -> str | None:
    """Get last modified time as ISO-8601 timestamp.

    Prefers sync metadata timestamp if available, falls back to file mtime.

    Args:
        path: Path to file
        sync_metadata: Optional sync metadata dict containing 'syncedAt' field

    Returns:
        ISO-8601 timestamp string or None if unavailable

    Example:
        >>> path = Path("/path/to/schema.json")
        >>> get_modified_time(path)
        '2025-10-20T15:30:00Z'
        >>> get_modified_time(path, {"syncedAt": "2025-10-20T18:42:11Z"})
        '2025-10-20T18:42:11Z'
    """
    if sync_metadata and "syncedAt" in sync_metadata:
        return sync_metadata["syncedAt"]

    try:
        mtime = path.stat().st_mtime
        dt = datetime.fromtimestamp(mtime, tz=UTC)
        return dt.isoformat().replace("+00:00", "Z")
    except (OSError, ValueError):
        return None


__all__ = [
    "compute_checksum",
    "get_file_size",
    "get_file_format",
    "get_modified_time",
]
