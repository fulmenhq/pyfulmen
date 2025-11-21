"""GZIP format handler using Python stdlib gzip."""

import gzip
import logging
import shutil
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

from ..exceptions import FulpackError, InvalidFormatError
from ..security import (
    check_decompression_bomb,
    compute_checksum,
)

logger = logging.getLogger(__name__)


class GzipHandler:
    """Handler for GZIP archives (single file compression)."""

    def __init__(self, format: ArchiveFormat = ArchiveFormat.GZIP):
        """Initialize handler.

        Args:
            format: Must be ArchiveFormat.GZIP
        """
        if format != ArchiveFormat.GZIP:
            raise InvalidFormatError(
                f"GzipHandler only supports GZIP, got {format}",
                context={"format": format.value},
                code="FULPACK_INVALID_FORMAT",
            )
        self.format = format

    def create(self, source: list[str], output: str, options: CreateOptions) -> ArchiveInfo:
        """Create archive from source file."""
        if len(source) != 1:
            raise FulpackError(
                "GZIP format only supports single file compression",
                context={"source_count": len(source)},
                code="FULPACK_GZIP_MULTIPLE_SOURCES",
            )

        source_path = Path(source[0])
        if not source_path.exists():
            raise FulpackError(
                f"Source not found: {source[0]}",
                context={"path": source[0]},
                code="FULPACK_SOURCE_NOT_FOUND",
            )
        if source_path.is_dir():
            raise FulpackError(
                "GZIP format cannot compress directories",
                context={"path": source[0]},
                code="FULPACK_GZIP_DIRECTORY",
            )

        compresslevel = cast(int, options.get("compression_level", 9))

        with open(source_path, "rb") as f_in, gzip.open(output, "wb", compresslevel=compresslevel) as f_out:
            shutil.copyfileobj(f_in, f_out)

        # Compute metadata
        entry_count = 1
        total_size = source_path.stat().st_size

        archive_path = Path(output)
        compressed_size = archive_path.stat().st_size
        compression_ratio = total_size / compressed_size if compressed_size > 0 else 1.0

        checksum_algo = cast(str, options.get("checksum_algorithm", "sha256"))
        # Note: We are computing checksum of the ARCHIVE (compressed file),
        # but for GZIP create, usually we care about the uncompressed content?
        # The standard create signature implies the ArchiveInfo describes the resulting archive.
        # compute_checksum computes checksum of the file at `output`.
        _checksum = compute_checksum(output, checksum_algo)

        return ArchiveInfo(
            format=cast(Any, self.format.value),
            entry_count=entry_count,
            total_size=total_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            has_checksums=True,  # GZIP has CRC32
            checksum_algorithm=cast(Any, checksum_algo),
            created=datetime.now(UTC).isoformat(),
        )

    def extract(self, archive: str, destination: str, options: ExtractOptions) -> ExtractResult:
        """Extract archive to destination."""
        dest_path = Path(destination)

        # Determine output filename
        # If destination is a dir, we need to infer filename.
        # If destination doesn't exist, is it a dir or a file?
        # Convention: extract(archive, destination) -> destination is the target directory.
        # So we must infer filename.

        archive_path = Path(archive)
        output_filename = archive_path.stem  # Remove .gz suffix
        # If archive is "foo", stem is "foo". If "foo.tar.gz", stem is "foo.tar".
        # For GZIP handler, we expect just .gz usually.

        # If archive doesn't end in .gz, what do we do? Just append nothing?
        # archive_path.stem handles "file.txt.gz" -> "file.txt".

        target_file = dest_path / output_filename

        # Ensure destination directory exists
        dest_path.mkdir(parents=True, exist_ok=True)

        extracted_count = 0
        skipped_count = 0
        errors: list[dict[str, Any]] = []

        max_size = cast(int, options.get("max_size", 1_000_000_000))
        total_extracted = 0

        try:
            with gzip.open(archive, "rb") as f_in, open(target_file, "wb") as f_out:
                # We must stream to check for bombs
                chunk_size = 1024 * 1024  # 1MB
                while True:
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break

                    total_extracted += len(chunk)

                    # Check bomb
                    # GZIP doesn't give us total size easily upfront without reading.
                    # We check running total vs compressed size
                    compressed_size = archive_path.stat().st_size
                    try:
                        check_decompression_bomb(
                            entry_size=total_extracted,  # Current extracted size
                            compressed_size=compressed_size,
                            total_size=total_extracted,
                            entry_count=0,  # Single file
                            max_entry_size=max_size,
                            max_total_size=max_size * 10,
                            max_entries=1,
                        )
                    except Exception as e:
                        raise FulpackError(str(e), code="DECOMPRESSION_BOMB") from e

                    f_out.write(chunk)

            extracted_count = 1

        except Exception as e:
            errors.append({"code": "EXTRACT_ERROR", "message": str(e), "path": archive})
            # Cleanup partial file
            if target_file.exists():
                target_file.unlink()

        error_messages = [f"{e.get('code', 'ERROR')}: {e['message']}" for e in errors] if errors else None

        return ExtractResult(
            extracted_count=extracted_count,
            skipped_count=skipped_count,
            error_count=len(errors),
            errors=error_messages,
        )

    def scan(self, archive: str, options: ScanOptions) -> list[ArchiveEntry]:
        """Scan archive entries without extraction."""
        archive_path = Path(archive)

        # GZIP doesn't store filename reliably.
        # We return an entry representing the uncompressed content.
        # Name: inferred from archive name.

        entry_path = archive_path.stem  # Remove .gz

        # Estimate size? GZIP stores ISIZE (original size mod 2^32) in last 4 bytes.
        # We can read it.
        uncompressed_size = 0
        try:
            with open(archive, "rb") as f:
                f.seek(-4, 2)
                import struct

                isize = struct.unpack("<I", f.read(4))[0]
                uncompressed_size = isize
                # Note: This is wrong for files > 4GB.
        except Exception:
            pass  # Ignore if empty or too small

        return [
            ArchiveEntry(
                path=entry_path,
                type=cast(Any, EntryType.FILE.value),
                size=uncompressed_size,
                compressed_size=archive_path.stat().st_size,
                modified=datetime.fromtimestamp(archive_path.stat().st_mtime, UTC).isoformat(),
                checksum=None,  # CRC32 is in header but not easily accessible via gzip module without reading
                mode=None,
                symlink_target=None,
            )
        ]

    def info(self, archive: str) -> ArchiveInfo:
        """Get archive metadata."""
        archive_path = Path(archive)
        compressed_size = archive_path.stat().st_size

        # Read ISIZE for estimate
        total_size = 0
        try:
            with open(archive, "rb") as f:
                f.seek(-4, 2)
                import struct

                total_size = struct.unpack("<I", f.read(4))[0]
        except Exception:
            pass

        compression_ratio = total_size / compressed_size if compressed_size > 0 else 1.0

        return ArchiveInfo(
            format=cast(Any, self.format.value),
            entry_count=1,
            total_size=total_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            has_checksums=True,
            checksum_algorithm=cast(Any, "crc32"),
            created=None,
        )

    def verify(self, archive: str) -> ValidationResult:
        """Verify archive integrity."""
        errors: list[str] = []
        warnings: list[str] = []

        try:
            with gzip.open(archive, "rb") as f:
                # Read whole file to verify checksum (gzip module checks CRC32 automatically on read)
                while f.read(1024 * 1024):
                    pass
        except Exception as e:
            errors.append(f"Verification error: {e}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            entry_count=1,
            checksums_verified=1,
            checks_performed=cast(Any, ["structure_valid", "checksums_verified"]),
        )
