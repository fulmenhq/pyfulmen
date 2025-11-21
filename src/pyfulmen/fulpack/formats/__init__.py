"""Format handlers and registry for archive operations.

Provides:
- FormatHandler protocol for pluggable format implementations
- Format registry for runtime handler registration
- Format detection by extension and magic bytes

Example:
    >>> from pyfulmen.fulpack.formats import get_handler, detect_format
    >>> from crucible.fulpack import ArchiveFormat
    >>>
    >>> # Detect format
    >>> format = detect_format("archive.tar.gz")
    >>> # Get handler
    >>> handler = get_handler(format)
    >>> # Use handler
    >>> info = handler.info("archive.tar.gz")
"""

from pathlib import Path
from typing import Protocol

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

from ..exceptions import InvalidFormatError


class FormatHandler(Protocol):
    """Protocol for archive format handlers.

    All format handlers must implement this protocol to be registered
    in the format registry. Handlers provide the five canonical operations:
    create, extract, scan, verify, and info.

    This protocol enables pluggable architecture for future extensions
    (e.g., fulpack-formats specialized module).
    """

    def create(
        self,
        source: list[str],
        output: str,
        options: CreateOptions,
    ) -> ArchiveInfo:
        """Create archive from source files/directories.

        Args:
            source: List of paths to archive
            output: Output archive file path
            options: Creation options

        Returns:
            ArchiveInfo with metadata
        """
        ...

    def extract(
        self,
        archive: str,
        destination: str,
        options: ExtractOptions,
    ) -> ExtractResult:
        """Extract archive contents to destination.

        Args:
            archive: Archive file path
            destination: Target directory
            options: Extraction options

        Returns:
            ExtractResult with counts and errors
        """
        ...

    def scan(
        self,
        archive: str,
        options: ScanOptions,
    ) -> list[ArchiveEntry]:
        """Scan archive entries without extraction.

        Args:
            archive: Archive file path
            options: Scan options

        Returns:
            List of ArchiveEntry objects
        """
        ...

    def info(self, archive: str) -> ArchiveInfo:
        """Get archive metadata without extraction.

        Args:
            archive: Archive file path

        Returns:
            ArchiveInfo with format, sizes, entry count
        """
        ...

    def verify(self, archive: str) -> ValidationResult:
        """Verify archive integrity and security.

        Args:
            archive: Archive file path

        Returns:
            ValidationResult with validity status
        """
        ...


# Global registry for format handlers
_FORMAT_HANDLERS: dict[ArchiveFormat, FormatHandler] = {}


def _register_builtin_handlers() -> None:
    """Register stdlib-based format handlers."""
    from .gzip import GzipHandler
    from .tar import TarHandler
    from .zip import ZipHandler

    # Register TAR and TAR.GZ handlers
    _FORMAT_HANDLERS[ArchiveFormat.TAR] = TarHandler(ArchiveFormat.TAR)
    _FORMAT_HANDLERS[ArchiveFormat.TAR_GZ] = TarHandler(ArchiveFormat.TAR_GZ)

    # Register ZIP handler
    _FORMAT_HANDLERS[ArchiveFormat.ZIP] = ZipHandler(ArchiveFormat.ZIP)

    # Register GZIP handler
    _FORMAT_HANDLERS[ArchiveFormat.GZIP] = GzipHandler(ArchiveFormat.GZIP)


# Auto-register built-in handlers on module import
_register_builtin_handlers()


def register_format(format: ArchiveFormat, handler: FormatHandler) -> None:
    """Register a format handler.

    Allows runtime registration of format handlers for extensibility.
    Used by built-in handlers and future extension modules.

    Args:
        format: Archive format enum value
        handler: Handler implementing FormatHandler protocol

    Example:
        >>> from .tar import TarGzHandler
        >>> register_format(ArchiveFormat.TAR_GZ, TarGzHandler())
    """
    _FORMAT_HANDLERS[format] = handler


def get_handler(format: ArchiveFormat) -> FormatHandler:
    """Get handler for format.

    Args:
        format: Archive format

    Returns:
        Format handler

    Raises:
        InvalidFormatError: If format is not supported

    Example:
        >>> handler = get_handler(ArchiveFormat.TAR_GZ)
        >>> info = handler.info("archive.tar.gz")
    """
    if format not in _FORMAT_HANDLERS:
        supported = sorted([f.value for f in _FORMAT_HANDLERS])
        raise InvalidFormatError(
            f"Unsupported format: {format.value}. Supported formats: {', '.join(supported)}",
            context={
                "format": format.value,
                "supported_formats": supported,
            },
            code="FULPACK_INVALID_FORMAT",
        )
    return _FORMAT_HANDLERS[format]


def detect_format(archive_path: str) -> ArchiveFormat:
    """Detect archive format from file extension.

    Uses file extension to determine format. Future versions may add
    magic byte detection as fallback.

    Args:
        archive_path: Path to archive file

    Returns:
        Detected ArchiveFormat

    Raises:
        InvalidFormatError: If format cannot be detected

    Example:
        >>> detect_format("archive.tar.gz")
        <ArchiveFormat.TAR_GZ: 'tar.gz'>
        >>> detect_format("archive.zip")
        <ArchiveFormat.ZIP: 'zip'>
    """
    path = Path(archive_path)

    # Check for double extensions first (tar.gz, tar.bz2, etc.)
    if path.suffix == ".gz" and path.stem.endswith(".tar"):
        return ArchiveFormat.TAR_GZ

    # Single extensions
    extension_map = {
        ".tar": ArchiveFormat.TAR,
        ".tgz": ArchiveFormat.TAR_GZ,
        ".tar.gz": ArchiveFormat.TAR_GZ,
        ".zip": ArchiveFormat.ZIP,
        ".gz": ArchiveFormat.GZIP,
    }

    # Try full suffix first (handles .tar.gz)
    full_suffix = "".join(path.suffixes)
    if full_suffix in extension_map:
        return extension_map[full_suffix]

    # Try single suffix
    if path.suffix in extension_map:
        return extension_map[path.suffix]

    raise InvalidFormatError(
        f"Cannot detect format for '{archive_path}': unknown extension",
        context={
            "path": archive_path,
            "extension": path.suffix,
            "supported_extensions": sorted(extension_map.keys()),
        },
        code="FULPACK_UNKNOWN_FORMAT",
    )
