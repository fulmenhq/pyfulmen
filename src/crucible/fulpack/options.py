"""Fulpack Options - Generated from Crucible schemas.

This file is AUTO-GENERATED from the Fulpack module specification.
DO NOT EDIT MANUALLY - changes will be overwritten.

Schema Version: v1.0.0
Last Reviewed: 2025-11-12
Source: schemas/library/fulpack/v1.0.0/

See: https://github.com/fulmenhq/crucible/blob/main/docs/standards/library/modules/fulpack.md
"""

from typing import Literal, TypedDict


class CreateOptions(TypedDict, total=False):
    """Options for archive creation operation

    Generated from: schemas/library/fulpack/v1.0.0/create-options.schema.json

    All fields are optional. Use as **kwargs when calling functions.
    """

    compression_level: int  # Compression level (1=fastest, 9=best compression, format-dependent)

    include_patterns: list[str]  # Glob patterns for files to include (e.g., ['**/*.py', '**/*.md'])

    exclude_patterns: list[str]  # Glob patterns for files to exclude (e.g., ['**/__pycache__', '**/.git'])

    checksum_algorithm: Literal["sha256", "sha512", "sha1", "md5"]  # Checksum algorithm for entry verification

    preserve_permissions: bool  # Preserve Unix file permissions in archive

    follow_symlinks: bool  # Follow symbolic links and archive their targets


class ExtractOptions(TypedDict, total=False):
    """Options for archive extraction operation

    Generated from: schemas/library/fulpack/v1.0.0/extract-options.schema.json

    All fields are optional. Use as **kwargs when calling functions.
    """

    overwrite: Literal[
        "error", "skip", "overwrite"
    ]  # How to handle existing files (error=fail, skip=keep existing, overwrite=replace)

    verify_checksums: bool  # Verify checksums during extraction if available

    preserve_permissions: bool  # Preserve Unix file permissions from archive

    include_patterns: list[str]  # Glob patterns for entries to extract (e.g., ['**/*.csv'])

    max_size: int  # Maximum total decompressed size in bytes (decompression bomb protection)

    max_entries: int  # Maximum number of entries to extract (decompression bomb protection)


class ScanOptions(TypedDict, total=False):
    """Options for archive scanning operation (for Pathfinder integration)

    Generated from: schemas/library/fulpack/v1.0.0/scan-options.schema.json

    All fields are optional. Use as **kwargs when calling functions.
    """

    include_metadata: bool  # Include metadata (size, checksum, modified timestamp) in results

    entry_types: list[Literal["file", "directory", "symlink"]]  # Filter entries by type (from entry-types taxonomy)

    max_depth: int | None  # Maximum depth for directory traversal (null = unlimited)

    max_entries: int  # Safety limit for maximum entries to return
