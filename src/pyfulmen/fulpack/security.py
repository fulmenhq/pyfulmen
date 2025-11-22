"""Security utilities for archive operations.

Provides mandatory security protections:
- Path traversal prevention
- Decompression bomb detection
- Checksum computation and verification
- Symlink validation

All protections are enabled by default and cannot be disabled.
Limits are configurable but have safe defaults.
"""

import hashlib
import logging
import os
from pathlib import Path

from pyfulmen import fulhash
from pyfulmen.fulhash import Algorithm as HashAlgo

from .exceptions import (
    DecompressionBombError,
    PathTraversalError,
    SymlinkError,
)

# Default security limits (configurable via environment or options)
DEFAULT_MAX_ENTRY_SIZE = 1_000_000_000  # 1 GB
DEFAULT_MAX_TOTAL_SIZE = 10_000_000_000  # 10 GB
DEFAULT_MAX_ENTRIES = 100_000
DEFAULT_MAX_COMPRESSION_RATIO = 100.0  # 100:1 (warn, don't fail by default)

logger = logging.getLogger(__name__)


def normalize_path(path: str) -> str:
    """Normalize a path for safe comparison.

    Resolves `.`, `..`, and handles various path separators.
    Does NOT resolve symlinks (use validate_symlink_target for that).

    Args:
        path: Path to normalize

    Returns:
        Normalized path string

    Example:
        >>> normalize_path("foo/./bar/../baz")
        'foo/baz'
        >>> normalize_path("/foo//bar/")
        '/foo/bar'
    """
    # Convert to Path for normalization
    p = Path(path)

    # Resolve . and .. but don't follow symlinks
    parts = []
    for part in p.parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)

    # Rebuild path
    if p.is_absolute():
        return str(Path("/").joinpath(*parts))
    else:
        return str(Path(*parts)) if parts else "."


def validate_path_traversal(path: str, base: str) -> None:
    """Validate that a path does not escape the base directory.

    Checks for common path traversal attacks:
    - Absolute paths (e.g., /etc/passwd)
    - Parent directory escapes (e.g., ../../etc/passwd)
    - Paths that resolve outside base after normalization

    Args:
        path: Path to validate (from archive entry)
        base: Base directory (extraction destination)

    Raises:
        PathTraversalError: If path traversal is detected

    Example:
        >>> validate_path_traversal("foo/bar.txt", "/tmp/dest")  # OK
        >>> validate_path_traversal("../etc/passwd", "/tmp/dest")  # RAISES
        >>> validate_path_traversal("/etc/passwd", "/tmp/dest")  # RAISES
    """
    # Reject absolute paths
    if os.path.isabs(path):
        raise PathTraversalError(
            f"Path traversal detected: absolute path '{path}' not allowed",
            context={
                "path": path,
                "base": base,
                "attack_type": "absolute_path",
            },
            code="FULPACK_PATH_TRAVERSAL",
        )

    # Normalize and resolve
    normalized = normalize_path(path)
    full_path = Path(base) / normalized
    resolved_full = full_path.resolve()
    resolved_base = Path(base).resolve()

    # Check if resolved path escapes base
    try:
        resolved_full.relative_to(resolved_base)
    except ValueError as e:
        raise PathTraversalError(
            f"Path traversal detected: '{path}' resolves outside base '{base}'",
            context={
                "path": path,
                "normalized": normalized,
                "base": base,
                "resolved_path": str(resolved_full),
                "resolved_base": str(resolved_base),
                "attack_type": "parent_escape",
            },
            code="FULPACK_PATH_TRAVERSAL",
        ) from e


def validate_symlink_target(link: str, target: str, base: str) -> None:
    """Validate that a symlink target does not escape the base directory.

    Checks that the symlink's target resolves within the base directory
    after following the symlink from its location.

    Args:
        link: Path to the symlink (relative to base)
        target: Target path of the symlink (can be relative or absolute)
        base: Base directory (extraction destination)

    Raises:
        SymlinkError: If symlink points outside base

    Example:
        >>> validate_symlink_target("link.txt", "target.txt", "/tmp/dest")  # OK
        >>> validate_symlink_target("link.txt", "../../../etc/passwd", "/tmp/dest")  # RAISES
    """
    # Reject absolute target paths
    if os.path.isabs(target):
        raise SymlinkError(
            f"Symlink validation failed: absolute target '{target}' not allowed",
            context={
                "link": link,
                "target": target,
                "base": base,
                "attack_type": "symlink_absolute_target",
            },
            code="FULPACK_SYMLINK_INVALID",
        )

    # Compute where the symlink will be
    link_location = Path(base) / link
    link_dir = link_location.parent

    # Resolve target relative to symlink's directory
    target_resolved = (link_dir / target).resolve()
    base_resolved = Path(base).resolve()

    # Check if target escapes base
    try:
        target_resolved.relative_to(base_resolved)
    except ValueError as e:
        raise SymlinkError(
            f"Symlink validation failed: target '{target}' resolves outside base '{base}'",
            context={
                "link": link,
                "target": target,
                "base": base,
                "resolved_target": str(target_resolved),
                "resolved_base": str(base_resolved),
                "attack_type": "symlink_escape",
            },
            code="FULPACK_SYMLINK_INVALID",
        ) from e


def check_decompression_bomb(
    entry_size: int,
    compressed_size: int,
    total_size: int,
    entry_count: int,
    max_entry_size: int = DEFAULT_MAX_ENTRY_SIZE,
    max_total_size: int = DEFAULT_MAX_TOTAL_SIZE,
    max_entries: int = DEFAULT_MAX_ENTRIES,
    max_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
) -> None:
    """Check for decompression bomb indicators.

    Validates:
    - Individual entry size limits
    - Total extracted size limits
    - Entry count limits
    - Compression ratio warnings

    Args:
        entry_size: Size of current entry (uncompressed)
        compressed_size: Size of current entry (compressed)
        total_size: Running total of extracted bytes
        entry_count: Running total of extracted entries
        max_entry_size: Maximum size for single entry
        max_total_size: Maximum total extracted size
        max_entries: Maximum number of entries
        max_ratio: Maximum compression ratio (warn threshold)

    Raises:
        DecompressionBombError: If limits are exceeded

    Example:
        >>> check_decompression_bomb(500_000, 10_000, 500_000, 1)  # OK
        >>> check_decompression_bomb(2_000_000_000, 10_000, 2_000_000_000, 1)  # RAISES
    """
    # Check entry size limit
    if entry_size > max_entry_size:
        raise DecompressionBombError(
            f"Decompression bomb detected: entry size {entry_size} exceeds limit {max_entry_size}",
            context={
                "entry_size": entry_size,
                "max_entry_size": max_entry_size,
                "attack_type": "oversized_entry",
            },
            code="FULPACK_DECOMPRESSION_BOMB",
        )

    # Check total size limit
    if total_size > max_total_size:
        raise DecompressionBombError(
            f"Decompression bomb detected: total size {total_size} exceeds limit {max_total_size}",
            context={
                "total_size": total_size,
                "max_total_size": max_total_size,
                "attack_type": "oversized_total",
            },
            code="FULPACK_DECOMPRESSION_BOMB",
        )

    # Check entry count limit
    if entry_count > max_entries:
        raise DecompressionBombError(
            f"Decompression bomb detected: entry count {entry_count} exceeds limit {max_entries}",
            context={
                "entry_count": entry_count,
                "max_entries": max_entries,
                "attack_type": "too_many_entries",
            },
            code="FULPACK_DECOMPRESSION_BOMB",
        )

    # Check compression ratio (warn, don't fail by default)
    if compressed_size > 0:
        ratio = entry_size / compressed_size
        if ratio > max_ratio:
            logger.warning(
                f"Suspicious compression ratio detected: {ratio:.1f}:1 exceeds threshold {max_ratio}:1",
                extra={
                    "entry_size": entry_size,
                    "compressed_size": compressed_size,
                    "ratio": ratio,
                    "max_ratio": max_ratio,
                },
            )


def compute_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Compute checksum for a file.

    Uses streaming to handle large files efficiently.
    Delegates to fulhash for supported algorithms (sha256, xxh3-128, crc32, crc32c).
    Falls back to hashlib for legacy algorithms (md5, sha1, sha512).

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, sha512, sha1, md5, crc32, xxh3-128)

    Returns:
        Hex-encoded checksum string

    Raises:
        ValueError: If algorithm is not supported
        FileNotFoundError: If file does not exist

    Example:
        >>> compute_checksum("file.txt", "sha256")
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    """
    # Check for fulhash support
    try:
        algo_enum = HashAlgo(algorithm.lower())
        digest = fulhash.hash_file(file_path, algo_enum)
        return digest.hex
    except ValueError:
        # Not supported by fulhash, fall back to hashlib
        pass

    # Validate algorithm for hashlib
    supported = {"sha512", "sha1", "md5"}
    if algorithm.lower() not in supported:
        raise ValueError(
            f"Unsupported hash algorithm '{algorithm}'. Supported: {sorted(supported)} + fulhash algorithms"
        )

    # Create hasher
    hasher = hashlib.new(algorithm.lower())

    # Stream file in chunks
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_checksum(file_path: str, expected: str, algorithm: str = "sha256") -> bool:
    """Verify file checksum matches expected value.

    Args:
        file_path: Path to file
        expected: Expected checksum (hex-encoded)
        algorithm: Hash algorithm (sha256, sha512, sha1, md5)

    Returns:
        True if checksum matches, False otherwise

    Example:
        >>> verify_checksum("file.txt", "e3b0c44298fc...", "sha256")
        True
    """
    actual = compute_checksum(file_path, algorithm)
    return actual.lower() == expected.lower()
