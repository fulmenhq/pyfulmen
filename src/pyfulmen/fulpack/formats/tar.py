"""TAR and TAR.GZ format handler using Python stdlib tarfile."""

import logging
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from crucible.fulpack import (
    ArchiveEntry,
    ArchiveFormat,
    ArchiveInfo,
    CreateOptions,
    EntryType,
    ExtractOptions,
    ExtractResult,
    ScanOptions,
    ValidationResult,
)

from ..exceptions import InvalidFormatError
from ..security import (
    check_decompression_bomb,
    compute_checksum,
    normalize_path,
    validate_path_traversal,
)

logger = logging.getLogger(__name__)


class TarHandler:
    """Handler for TAR and TAR.GZ archives."""

    def __init__(self, format: ArchiveFormat):
        """Initialize handler.

        Args:
            format: ArchiveFormat.TAR_GZ or ArchiveFormat.TAR
        """
        if format not in (ArchiveFormat.TAR_GZ, ArchiveFormat.TAR):
            raise InvalidFormatError(
                f"TarHandler only supports TAR and TAR_GZ, got {format}",
                context={"format": format.value},
                code="FULPACK_INVALID_FORMAT",
            )
        self.format = format

    def _get_mode(self, operation: str) -> str:
        """Get tarfile mode for operation.

        Returns 'w:gz'/'r:gz' for tar.gz, 'w:'/'r:' for uncompressed tar.
        """
        if self.format == ArchiveFormat.TAR_GZ:
            return f"{operation}:gz"
        return f"{operation}:"

    def create(self, source: list[str], output: str, options: CreateOptions) -> ArchiveInfo:
        """Create archive from source files."""
        mode = self._get_mode("w")

        entry_count = 0
        total_size = 0

        # Open archive for writing with appropriate context manager
        if self.format == ArchiveFormat.TAR_GZ:
            compresslevel = cast(int, options.get("compression_level", 6))
            with tarfile.open(output, mode=mode, compresslevel=compresslevel) as tar:  # type: ignore[call-overload]
                for source_path in source:
                    path = Path(source_path)
                    if not path.exists():
                        logger.warning(f"Source not found: {source_path}")
                        continue

                    # Add path to archive
                    tar.add(str(path), arcname=path.name, recursive=True)
        else:
            # Uncompressed TAR doesn't support compresslevel parameter
            with tarfile.open(output, mode=mode) as tar:  # type: ignore[call-overload]
                for source_path in source:
                    path = Path(source_path)
                    if not path.exists():
                        logger.warning(f"Source not found: {source_path}")
                        continue

                    # Add path to archive
                    tar.add(str(path), arcname=path.name, recursive=True)

        # Count entries by re-reading the archive (ensures accurate count)
        with tarfile.open(output, mode=self._get_mode("r")) as tar:  # type: ignore[call-overload]
            for member in tar:
                entry_count += 1
                if member.isfile():
                    total_size += member.size

        # Compute metadata
        archive_path = Path(output)
        compressed_size = archive_path.stat().st_size
        compression_ratio = total_size / compressed_size if compressed_size > 0 else 1.0

        checksum_algo = cast(str, options.get("checksum_algorithm", "sha256"))
        _checksum = compute_checksum(output, checksum_algo)  # Computed but not currently stored

        return ArchiveInfo(
            format=cast(Any, self.format.value),
            entry_count=entry_count,
            total_size=total_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            has_checksums=True,
            checksum_algorithm=cast(Any, checksum_algo),
            created=datetime.now(UTC).isoformat(),
        )

    def extract(self, archive: str, destination: str, options: ExtractOptions) -> ExtractResult:
        """Extract archive to destination."""
        mode = self._get_mode("r")
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)

        extracted_count = 0
        skipped_count = 0
        errors: list[dict[str, Any]] = []

        max_size = cast(int, options.get("max_size", 1_000_000_000))
        max_entries = cast(int, options.get("max_entries", 10_000))
        total_extracted = 0

        with tarfile.open(archive, mode=mode) as tar:  # type: ignore[call-overload]
            for member in tar:
                # Check limits
                if extracted_count >= max_entries:
                    break

                # Validate path
                try:
                    validate_path_traversal(member.name, destination)
                except Exception as e:
                    errors.append({"code": "PATH_TRAVERSAL", "message": str(e), "path": member.name})
                    skipped_count += 1
                    continue

                # Check bomb
                try:
                    check_decompression_bomb(
                        entry_size=member.size,
                        compressed_size=0,
                        total_size=total_extracted,
                        entry_count=extracted_count,
                        max_entry_size=max_size,
                        max_total_size=max_size * 10,
                        max_entries=max_entries,
                    )
                except Exception as e:
                    errors.append({"code": "DECOMPRESSION_BOMB", "message": str(e)})
                    break

                # Extract with filter for Python 3.14+ compatibility
                # Use data filter to prevent security issues while allowing extraction
                tar.extract(member, path=destination, filter="data")
                extracted_count += 1
                total_extracted += member.size

        # Convert dict errors to strings for schema compliance
        error_messages = [f"{e.get('code', 'ERROR')}: {e['message']}" for e in errors] if errors else None

        return ExtractResult(
            extracted_count=extracted_count,
            skipped_count=skipped_count,
            error_count=len(errors),
            errors=error_messages,
        )

    def scan(self, archive: str, options: ScanOptions) -> list[ArchiveEntry]:
        """Scan archive entries without extraction."""
        mode = self._get_mode("r")
        entries: list[ArchiveEntry] = []

        max_entries = cast(int, options.get("max_entries", 100_000))

        with tarfile.open(archive, mode=mode) as tar:  # type: ignore[call-overload]
            for member in tar:
                if len(entries) >= max_entries:
                    break

                # Determine type
                if member.isfile():
                    entry_type = EntryType.FILE
                elif member.isdir():
                    entry_type = EntryType.DIRECTORY
                elif member.issym() or member.islnk():
                    entry_type = EntryType.SYMLINK
                else:
                    continue

                entries.append(
                    ArchiveEntry(
                        path=normalize_path(member.name),
                        type=cast(Any, entry_type.value),
                        size=member.size,
                        compressed_size=None,
                        modified=datetime.fromtimestamp(member.mtime, UTC).isoformat(),
                        checksum=None,
                        mode=member.mode,
                        symlink_target=member.linkname if entry_type == EntryType.SYMLINK else None,
                    )
                )

        return entries

    def info(self, archive: str) -> ArchiveInfo:
        """Get archive metadata."""
        mode = self._get_mode("r")

        entry_count = 0
        total_size = 0

        with tarfile.open(archive, mode=mode) as tar:  # type: ignore[call-overload]
            for member in tar:
                entry_count += 1
                if member.isfile():
                    total_size += member.size

        archive_path = Path(archive)
        compressed_size = archive_path.stat().st_size
        compression_ratio = total_size / compressed_size if compressed_size > 0 else 1.0

        return ArchiveInfo(
            format=cast(Any, self.format.value),
            entry_count=entry_count,
            total_size=total_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            has_checksums=False,
            checksum_algorithm=None,
            created=None,
        )

    def verify(self, archive: str) -> ValidationResult:
        """Verify archive integrity."""
        errors: list[str] = []
        warnings: list[str] = []
        entry_count = 0

        mode = self._get_mode("r")

        try:
            with tarfile.open(archive, mode=mode) as tar:  # type: ignore[call-overload]
                for member in tar:
                    entry_count += 1

                    # Check path traversal
                    try:
                        validate_path_traversal(member.name, "/tmp/validation")
                    except Exception:
                        errors.append(f"Path traversal: {member.name}")

        except tarfile.TarError as e:
            errors.append(f"Invalid archive: {e}")

        warnings.append("Checksums not available in TAR format")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            entry_count=entry_count,
            checksums_verified=0,
            checks_performed=["structure_valid", "no_path_traversal"],
        )
