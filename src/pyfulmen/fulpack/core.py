"""Core API functions for fulpack archive operations.

Provides high-level API for creating, extracting, scanning, verifying, and
inspecting archives with security-by-default protections.

Quick Start:
    >>> from pyfulmen.fulpack import create, extract, scan, ArchiveFormat
    >>>
    >>> # Create archive
    >>> info = create(["src/", "docs/"], "release.tar.gz", ArchiveFormat.TAR_GZ)
    >>>
    >>> # Extract with security checks
    >>> result = extract("release.tar.gz", "/tmp/extracted")
    >>>
    >>> # Scan without extraction
    >>> entries = scan("release.tar.gz")

Security:
    All operations enforce mandatory security protections:
    - Path traversal prevention
    - Decompression bomb detection
    - Checksum verification (when available)
    - Symlink validation
"""

import logging

from crucible.fulpack import (
    ArchiveEntry,
    ArchiveFormat,
    ArchiveInfo,
    CreateOptions,
    ExtractOptions,
    ExtractResult,
    ScanOptions,
    ValidationResult,
)

from .exceptions import FulpackError
from .formats import detect_format, get_handler

logger = logging.getLogger(__name__)


def create(
    source: str | list[str],
    output: str,
    format: ArchiveFormat,
    options: CreateOptions | None = None,
) -> ArchiveInfo:
    """Create an archive from source files/directories.

    Args:
        source: Single path or list of paths to archive
        output: Output archive file path
        format: Archive format (TAR_GZ, ZIP, GZIP)
        options: Optional creation options (compression_level, patterns, checksums)

    Returns:
        ArchiveInfo with metadata (entry count, sizes, checksums)

    Raises:
        FulpackError: On creation failure
        InvalidFormatError: On unsupported format
        SecurityError: On path validation failure

    Example:
        >>> info = create(
        ...     source=["src/", "docs/"],
        ...     output="release.tar.gz",
        ...     format=ArchiveFormat.TAR_GZ,
        ...     options={"compression_level": 9}
        ... )
        >>> print(f"Created archive with {info.entry_count} entries")
    """
    # Normalize source to list
    source_list = [source] if isinstance(source, str) else source

    # Get handler and delegate
    handler = get_handler(format)
    logger.info(f"Creating {format.value} archive: {output} from {len(source_list)} source(s)")

    try:
        result = handler.create(source_list, output, options or {})
        logger.info(
            f"Created archive: {result.entry_count} entries, "
            f"{result.total_size} bytes → {result.compressed_size} bytes "
            f"(ratio: {result.compression_ratio:.2f})"
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create archive: {e}")
        if isinstance(e, FulpackError):
            raise
        raise FulpackError(
            f"Failed to create archive: {e}",
            context={"output": output, "format": format.value, "source_count": len(source_list)},
            code="FULPACK_CREATE_FAILED",
        ) from e


def extract(
    archive: str,
    destination: str,
    options: ExtractOptions | None = None,
) -> ExtractResult:
    """Extract archive contents to destination.

    Args:
        archive: Archive file path
        destination: Target directory (must be explicit, no implicit CWD)
        options: Optional extraction options (overwrite, verify, max_size, max_entries)

    Returns:
        ExtractResult with counts (extracted, skipped, errors)

    Raises:
        FulpackError: On extraction failure
        SecurityError: On path traversal or bomb detection
        InvalidFormatError: On format detection failure

    Example:
        >>> result = extract(
        ...     archive="release.tar.gz",
        ...     destination="/tmp/extracted",
        ...     options={"max_size": 1_000_000_000}  # 1GB limit
        ... )
        >>> print(f"Extracted {result.extracted_count} files")
    """
    # Detect format automatically
    format = detect_format(archive)
    handler = get_handler(format)

    logger.info(f"Extracting {format.value} archive: {archive} → {destination}")

    try:
        result = handler.extract(archive, destination, options or {})
        logger.info(
            f"Extraction complete: {result.extracted_count} extracted, "
            f"{result.skipped_count} skipped, {result.error_count} errors"
        )
        if result.errors:
            logger.warning(f"Extraction had {result.error_count} errors: {result.errors[:3]}")
        return result
    except Exception as e:
        logger.error(f"Failed to extract archive: {e}")
        if isinstance(e, FulpackError):
            raise
        raise FulpackError(
            f"Failed to extract archive: {e}",
            context={"archive": archive, "destination": destination, "format": format.value},
            code="FULPACK_EXTRACT_FAILED",
        ) from e


def scan(
    archive: str,
    options: ScanOptions | None = None,
) -> list[ArchiveEntry]:
    """Scan archive entries without extraction.

    Provides fast TOC (table of contents) reading for inspecting archive
    contents without extracting files to disk.

    Args:
        archive: Archive file path
        options: Optional scan options (include_metadata, entry_types, max_depth)

    Returns:
        List of ArchiveEntry objects

    Raises:
        FulpackError: On scan failure
        InvalidFormatError: On format detection failure

    Example:
        >>> entries = scan("data.tar.gz")
        >>> csv_files = [e for e in entries if e.path.endswith(".csv")]
        >>> print(f"Found {len(csv_files)} CSV files")
    """
    format = detect_format(archive)
    handler = get_handler(format)

    logger.debug(f"Scanning {format.value} archive: {archive}")

    try:
        entries = handler.scan(archive, options or {})
        logger.debug(f"Scan complete: {len(entries)} entries found")
        return entries
    except Exception as e:
        logger.error(f"Failed to scan archive: {e}")
        if isinstance(e, FulpackError):
            raise
        raise FulpackError(
            f"Failed to scan archive: {e}",
            context={"archive": archive, "format": format.value},
            code="FULPACK_SCAN_FAILED",
        ) from e


def verify(archive: str) -> ValidationResult:
    """Verify archive integrity and security.

    Performs comprehensive validation including:
    - Archive structure integrity
    - Path traversal detection
    - Decompression bomb detection
    - Checksum verification (if available)
    - Symlink safety checks

    Args:
        archive: Archive file path

    Returns:
        ValidationResult with validity status, errors, warnings

    Raises:
        FulpackError: On verification failure
        InvalidFormatError: On format detection failure

    Example:
        >>> result = verify("suspicious.tar.gz")
        >>> if not result.valid:
        ...     print(f"Validation failed: {result.errors}")
        >>> if result.warnings:
        ...     print(f"Warnings: {result.warnings}")
    """
    format = detect_format(archive)
    handler = get_handler(format)

    logger.info(f"Verifying {format.value} archive: {archive}")

    try:
        result = handler.verify(archive)
        if result.valid:
            logger.info(
                f"Verification passed: {result.entry_count} entries, {result.checksums_verified} checksums verified"
            )
        else:
            logger.warning(f"Verification failed with {len(result.errors or [])} errors")
        return result
    except Exception as e:
        logger.error(f"Failed to verify archive: {e}")
        if isinstance(e, FulpackError):
            raise
        raise FulpackError(
            f"Failed to verify archive: {e}",
            context={"archive": archive, "format": format.value},
            code="FULPACK_VERIFY_FAILED",
        ) from e


def info(archive: str) -> ArchiveInfo:
    """Get archive metadata without extraction.

    Provides quick access to archive metadata including format, entry count,
    sizes, and compression ratio. Does not extract or validate file contents.

    Args:
        archive: Archive file path

    Returns:
        ArchiveInfo with format, sizes, entry count

    Raises:
        FulpackError: On info extraction failure
        InvalidFormatError: On format detection failure

    Example:
        >>> info_data = info("release.tar.gz")
        >>> print(f"Format: {info_data.format}")
        >>> print(f"Entries: {info_data.entry_count}")
        >>> print(f"Compression: {info_data.compression_ratio:.1f}x")
    """
    format = detect_format(archive)
    handler = get_handler(format)

    logger.debug(f"Getting info for {format.value} archive: {archive}")

    try:
        result = handler.info(archive)
        logger.debug(
            f"Info retrieved: {result.entry_count} entries, "
            f"{result.compressed_size} bytes, ratio {result.compression_ratio:.2f}"
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get archive info: {e}")
        if isinstance(e, FulpackError):
            raise
        raise FulpackError(
            f"Failed to get archive info: {e}",
            context={"archive": archive, "format": format.value},
            code="FULPACK_INFO_FAILED",
        ) from e


__all__ = [
    "create",
    "extract",
    "scan",
    "verify",
    "info",
]
