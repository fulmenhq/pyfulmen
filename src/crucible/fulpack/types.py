"""Fulpack Types - Generated from Crucible schemas.

This file is AUTO-GENERATED from the Fulpack module specification.
DO NOT EDIT MANUALLY - changes will be overwritten.

Schema Version: v1.0.0
Last Reviewed: 2025-11-12
Source: schemas/library/fulpack/v1.0.0/

See: https://github.com/fulmenhq/crucible/blob/main/docs/standards/library/modules/fulpack.md
"""

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class ArchiveInfo:
    """Metadata about an archive file

    Generated from: schemas/library/fulpack/v1.0.0/archive-info.schema.json
    """

    format: Literal["tar.gz", "zip", "gzip"]  # Archive format from archive-formats taxonomy

    entry_count: int  # Total number of entries in the archive

    total_size: int  # Total uncompressed size in bytes

    compressed_size: int  # Compressed archive file size in bytes

    compression: Literal["gzip", "deflate", "none"] | None = None  # Compression algorithm used

    compression_ratio: float | None = None  # Compression ratio (total_size / compressed_size)

    has_checksums: bool | None = None  # Whether the archive contains checksums

    checksum_algorithm: Literal["sha256", "sha512", "sha1", "md5"] | None = (
        None  # Checksum algorithm used (if has_checksums is true)
    )

    created: str | None = None  # Archive creation timestamp (ISO 8601 format)


@dataclass
class ArchiveEntry:
    """Metadata for a single archive entry (returned by scan operation)

    Generated from: schemas/library/fulpack/v1.0.0/archive-entry.schema.json
    """

    path: str  # Normalized entry path within archive

    type: Literal["file", "directory", "symlink"]  # Entry type from entry-types taxonomy

    size: int  # Uncompressed size in bytes

    compressed_size: int | None = None  # Compressed size in bytes (if available)

    modified: str | None = None  # Modification timestamp (ISO 8601 format)

    checksum: str | None = None  # SHA-256 checksum (64 hex characters)

    mode: str | None = None  # Unix file permissions (octal string, e.g., '0644')

    symlink_target: str | None = None  # Target path if type is symlink, null otherwise


@dataclass
class ArchiveManifest:
    """Complete archive table of contents (for large archives and caching)

    Generated from: schemas/library/fulpack/v1.0.0/archive-manifest.schema.json
    """

    format: Literal["tar.gz", "zip", "gzip"]  # Archive format from archive-formats taxonomy

    version: str  # Manifest schema version (semantic versioning)

    generated: str  # Manifest generation timestamp (ISO 8601 format)

    entry_count: int  # Total number of entries in manifest

    entries: list[Any]  # Array of archive entries

    total_size: int | None = None  # Total uncompressed size in bytes

    compressed_size: int | None = None  # Compressed archive file size in bytes

    index: dict[str, Any] | None = None  # Optional searchable index for fast lookups


@dataclass
class ValidationResult:
    """Result of archive integrity verification (from verify operation)

    Generated from: schemas/library/fulpack/v1.0.0/validation-result.schema.json
    """

    valid: bool  # Whether the archive is valid and intact

    errors: list[str]  # Array of validation errors (empty if valid)

    warnings: list[str]  # Array of non-critical warnings (e.g., missing checksums)

    entry_count: int  # Number of entries validated

    checksums_verified: int | None = None  # Number of checksums successfully verified

    checks_performed: (
        list[
            Literal[
                "structure_valid", "checksums_verified", "no_path_traversal", "no_decompression_bomb", "symlinks_safe"
            ]
        ]
        | None
    ) = None  # List of security and integrity checks performed


@dataclass
class ExtractResult:
    """Result of archive extraction operation

    Generated from: schemas/library/fulpack/v1.0.0/extract-result.schema.json
    """

    extracted_count: int  # Number of entries successfully extracted

    skipped_count: int  # Number of entries skipped (e.g., already exists)

    error_count: int  # Number of entries that failed to extract

    errors: list[str] | None = None  # Array of error messages for failed extractions

    warnings: list[str] | None = None  # Array of warning messages (e.g., skipped files)

    checksums_verified: int | None = None  # Number of checksums successfully verified during extraction

    total_bytes: int | None = None  # Total bytes extracted
