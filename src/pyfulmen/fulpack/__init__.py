"""Fulpack - Enterprise-grade archive operations for PyFulmen.

Common-tier module providing secure, validated archive handling with:
- tar.gz, zip, gzip format support (stdlib only)
- Security-by-default protections (path traversal, decompression bombs)
- Pathfinder integration for archive-aware file discovery
- Pluggable architecture for future extensions

Quick Start:
    >>> from pyfulmen import fulpack
    >>> from pyfulmen.fulpack import ArchiveFormat
    >>>
    >>> # Create archive
    >>> info = fulpack.create(
    ...     source=["src/", "docs/"],
    ...     output="release.tar.gz",
    ...     format=ArchiveFormat.TAR_GZ
    ... )
    >>>
    >>> # Extract with security checks
    >>> result = fulpack.extract(
    ...     archive="release.tar.gz",
    ...     destination="/tmp/extracted"
    ... )
    >>>
    >>> # Scan without extraction
    >>> entries = fulpack.scan("release.tar.gz")
    >>> csv_files = [e for e in entries if e.path.endswith(".csv")]

Security:
    All operations enforce:
    - Path traversal protection (mandatory)
    - Decompression bomb detection (configurable limits)
    - Checksum verification (opt-out, not opt-in)
    - Symlink validation (reject by default)

See Also:
    - Module docs: docs/modules/fulpack.md
    - Crucible spec: docs/crucible-py/standards/library/modules/fulpack.md
    - Examples: examples/fulpack_usage.py
"""

# Re-export Crucible-generated types for user convenience
from crucible.fulpack import (
    # Data structures
    ArchiveEntry,
    # Enums
    ArchiveFormat,
    ArchiveInfo,
    ArchiveManifest,
    # Options
    CreateOptions,
    EntryType,
    ExtractOptions,
    ExtractResult,
    Operation,
    ScanOptions,
    ValidationResult,
)

# Public API functions
from .core import create, extract, info, scan, verify

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
    # API functions
    "create",
    "extract",
    "scan",
    "verify",
    "info",
]

__version__ = "0.1.11"
