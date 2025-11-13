"""Fulpack - Archive operations module for Crucible.

This file is AUTO-GENERATED from the Fulpack module specification.
DO NOT EDIT MANUALLY - changes will be overwritten.

Schema Version: v1.0.0
Last Reviewed: 2025-11-12

Common-tier archive operations with security-by-default protections
and mandatory Pathfinder integration.

Supported formats:
- tar.gz (POSIX tar with gzip compression)
- zip (ZIP with deflate compression)
- gzip (Single file compression)

See: https://github.com/fulmenhq/crucible/blob/main/docs/standards/library/modules/fulpack.md
"""

# Enums
from .enums import (
    ArchiveFormat,
    EntryType,
    Operation,
)

# Options (TypedDicts)
from .options import (
    CreateOptions,
    ExtractOptions,
    ScanOptions,
)

# Data structures
from .types import (
    ArchiveEntry,
    ArchiveInfo,
    ArchiveManifest,
    ExtractResult,
    ValidationResult,
)

__all__ = [
    # Enums
    "ArchiveFormat",
    "EntryType",
    "Operation",
    # Data structures
    "ArchiveInfo",
    "ArchiveEntry",
    "ArchiveManifest",
    "ValidationResult",
    "ExtractResult",
    # Options
    "CreateOptions",
    "ExtractOptions",
    "ScanOptions",
]

# Module version for compatibility checks
__version__ = "v1.0.0"
