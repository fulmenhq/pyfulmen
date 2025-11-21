"""ZIP format handler using Python stdlib zipfile."""

import logging
import zipfile
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


class ZipHandler:
    """Handler for ZIP archives."""

    def __init__(self, format: ArchiveFormat = ArchiveFormat.ZIP):
        """Initialize handler.

        Args:
            format: Must be ArchiveFormat.ZIP
        """
        if format != ArchiveFormat.ZIP:
            raise InvalidFormatError(
                f"ZipHandler only supports ZIP, got {format}",
                context={"format": format.value},
                code="FULPACK_INVALID_FORMAT",
            )
        self.format = format

    def create(self, source: list[str], output: str, options: CreateOptions) -> ArchiveInfo:
        """Create archive from source files."""
        entry_count = 0
        total_size = 0

        compresslevel = cast(int, options.get("compression_level", 6))
        # map 0 to stored, 1-9 to deflated (default)
        compression = zipfile.ZIP_STORED if compresslevel == 0 else zipfile.ZIP_DEFLATED

        with zipfile.ZipFile(
            output,
            "w",
            compression=compression,
            compresslevel=compresslevel if compression != zipfile.ZIP_STORED else None,
        ) as zf:
            for source_path in source:
                path = Path(source_path)
                if not path.exists():
                    logger.warning(f"Source not found: {source_path}")
                    continue

                # Walk directory or add file
                if path.is_dir():
                    for file_path in path.rglob("*"):
                        # Calculate arcname relative to source parent (standard behavior)
                        # If source is "foo/bar", we want "bar/..." in archive usually,
                        # or preserve full structure.
                        # TarHandler uses tar.add(path, arcname=path.name) which puts it at root.
                        # We'll do similar: calculate relative path from source's parent.
                        rel_path = file_path.relative_to(path.parent)
                        zf.write(file_path, arcname=str(rel_path))
                        entry_count += 1
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                else:
                    zf.write(path, arcname=path.name)
                    entry_count += 1
                    total_size += path.stat().st_size

        # Compute metadata
        archive_path = Path(output)
        compressed_size = archive_path.stat().st_size
        compression_ratio = total_size / compressed_size if compressed_size > 0 else 1.0

        checksum_algo = cast(str, options.get("checksum_algorithm", "sha256"))
        _checksum = compute_checksum(output, checksum_algo)

        return ArchiveInfo(
            format=cast(Any, self.format.value),
            entry_count=entry_count,
            total_size=total_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            has_checksums=True,  # ZIP has CRC32 built-in, but we compute whole-file checksum
            checksum_algorithm=cast(Any, checksum_algo),
            created=datetime.now(UTC).isoformat(),
        )

    def extract(self, archive: str, destination: str, options: ExtractOptions) -> ExtractResult:
        """Extract archive to destination."""
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)

        extracted_count = 0
        skipped_count = 0
        errors: list[dict[str, Any]] = []

        max_size = cast(int, options.get("max_size", 1_000_000_000))
        max_entries = cast(int, options.get("max_entries", 10_000))
        total_extracted = 0

        with zipfile.ZipFile(archive, "r") as zf:
            for member in zf.infolist():
                # Check limits
                if extracted_count >= max_entries:
                    break

                # Validate path
                try:
                    validate_path_traversal(member.filename, destination)
                except Exception as e:
                    errors.append({"code": "PATH_TRAVERSAL", "message": str(e), "path": member.filename})
                    skipped_count += 1
                    continue

                # Check bomb
                try:
                    check_decompression_bomb(
                        entry_size=member.file_size,
                        compressed_size=member.compress_size,
                        total_size=total_extracted,
                        entry_count=extracted_count,
                        max_entry_size=max_size,
                        max_total_size=max_size * 10,
                        max_entries=max_entries,
                    )
                except Exception as e:
                    errors.append({"code": "DECOMPRESSION_BOMB", "message": str(e)})
                    break

                # Extract
                try:
                    zf.extract(member, path=destination)
                    extracted_count += 1
                    total_extracted += member.file_size
                except Exception as e:
                    errors.append({"code": "EXTRACT_ERROR", "message": str(e), "path": member.filename})
                    skipped_count += 1

        error_messages = [f"{e.get('code', 'ERROR')}: {e['message']}" for e in errors] if errors else None

        return ExtractResult(
            extracted_count=extracted_count,
            skipped_count=skipped_count,
            error_count=len(errors),
            errors=error_messages,
        )

    def scan(self, archive: str, options: ScanOptions) -> list[ArchiveEntry]:
        """Scan archive entries without extraction."""
        entries: list[ArchiveEntry] = []
        max_entries = cast(int, options.get("max_entries", 100_000))

        with zipfile.ZipFile(archive, "r") as zf:
            for member in zf.infolist():
                if len(entries) >= max_entries:
                    break

                # Determine type
                entry_type = EntryType.DIRECTORY if member.is_dir() else EntryType.FILE
                # Simple detection, ZIP doesn't support symlinks consistently standardly

                entries.append(
                    ArchiveEntry(
                        path=normalize_path(member.filename),
                        type=cast(Any, entry_type.value),
                        size=member.file_size,
                        compressed_size=member.compress_size,
                        modified=datetime(*member.date_time, tzinfo=UTC).isoformat(),
                        checksum=str(member.CRC),  # ZIP stores CRC32
                        mode=None,  # ZIP external_attr is complex
                        symlink_target=None,
                    )
                )

        return entries

    def info(self, archive: str) -> ArchiveInfo:
        """Get archive metadata."""
        entry_count = 0
        total_size = 0
        compressed_size_sum = 0

        with zipfile.ZipFile(archive, "r") as zf:
            for member in zf.infolist():
                entry_count += 1
                total_size += member.file_size
                compressed_size_sum += member.compress_size

        archive_path = Path(archive)
        actual_file_size = archive_path.stat().st_size
        compression_ratio = total_size / actual_file_size if actual_file_size > 0 else 1.0

        return ArchiveInfo(
            format=cast(Any, self.format.value),
            entry_count=entry_count,
            total_size=total_size,
            compressed_size=actual_file_size,
            compression_ratio=compression_ratio,
            has_checksums=True,  # Has CRC
            checksum_algorithm=cast(Any, "crc32"),
            created=None,
        )

    def verify(self, archive: str) -> ValidationResult:
        """Verify archive integrity."""
        errors: list[str] = []
        warnings: list[str] = []
        entry_count = 0
        checksums_verified = 0

        try:
            with zipfile.ZipFile(archive, "r") as zf:
                # Testzip checks CRCs
                bad_file = zf.testzip()
                if bad_file:
                    errors.append(f"CRC check failed for {bad_file}")

                for member in zf.infolist():
                    entry_count += 1
                    checksums_verified += 1  # Implicitly verified by testzip/open

                    # Check path traversal
                    try:
                        validate_path_traversal(member.filename, "/tmp/validation")
                    except Exception:
                        errors.append(f"Path traversal: {member.filename}")

        except zipfile.BadZipFile as e:
            errors.append(f"Invalid archive: {e}")
        except Exception as e:
            errors.append(f"Verification error: {e}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            entry_count=entry_count,
            checksums_verified=checksums_verified,
            checks_performed=cast(Any, ["structure_valid", "checksums_verified", "no_path_traversal"]),
        )
