"""File and reader hashing plus convenience APIs for FulHash.

Provides hash_file for hashing file contents, hash_reader for hashing
caller-supplied binary streams, and a universal hash() dispatcher that
works with bytes, strings, and file paths.
"""

import io
import sys
import time
from pathlib import Path
from typing import BinaryIO

from pyfulmen.telemetry import counter, histogram

from ._hash import hash_bytes, hash_string
from ._stream import stream
from .models import Algorithm, Digest

# Default chunk size for streaming reads (64 KiB) — single SSOT for all
# chunked FulHash APIs (hash_file, hash_reader, verify_*, multi_hash_*).
DEFAULT_CHUNK_SIZE = 64 * 1024

# Taxonomy-registered per-algorithm operation counters (metrics.yaml).
# crc32/crc32c intentionally have no operation counters (not registered).
_OPERATION_COUNTERS = {
    Algorithm.XXH3_128: "fulhash_operations_total_xxh3_128",
    Algorithm.SHA256: "fulhash_operations_total_sha256",
}


def _validate_chunk_size(chunk_size: int) -> None:
    """Raise ValueError unless chunk_size is a positive integer.

    Rejects bool (a subclass of int) and non-int types so invalid values
    fail here with a clear message instead of surfacing as incidental
    TypeError/OverflowError inside read().
    """
    if type(chunk_size) is not int:
        raise ValueError(f"chunk_size must be a positive integer, got {chunk_size!r}")
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be > 0, got {chunk_size}")
    if chunk_size > sys.maxsize:
        raise ValueError(f"chunk_size must be <= {sys.maxsize}, got {chunk_size}")


def _emit_operation_telemetry(algorithm: Algorithm, bytes_hashed: int, start_time: float) -> None:
    """Emit taxonomy-registered metrics on the global registry.

    Emits fulhash_operations_total_<algo> (xxh3-128/sha256 only),
    fulhash_bytes_hashed_total, and fulhash_operation_ms.
    """
    operation_counter = _OPERATION_COUNTERS.get(algorithm)
    if operation_counter is not None:
        counter(operation_counter).inc()
    counter("fulhash_bytes_hashed_total").inc(bytes_hashed)
    duration_ms = (time.perf_counter() - start_time) * 1000
    histogram("fulhash_operation_ms").observe(duration_ms)


def hash_file(
    path: Path | str,
    algorithm: Algorithm = Algorithm.XXH3_128,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Digest:
    """Compute hash digest for file contents.

    Reads file in binary mode using streaming hasher with chunk_size
    blocks for memory efficiency. Works with files of any size.

    Args:
        path: Path to file (Path object or string)
        algorithm: Hash algorithm to use (default: XXH3_128)
        chunk_size: Read block size in bytes, must be > 0 (default: 64 KiB)

    Returns:
        Digest with algorithm, hex, bytes, and formatted fields

    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
        IsADirectoryError: If path is a directory
        ValueError: If chunk_size is not > 0

    Telemetry:
        Emits on the global registry after completion:
        - fulhash_operations_total_xxh3_128 / fulhash_operations_total_sha256
          counter (per-algorithm operations; crc32/crc32c are unmetered)
        - fulhash_bytes_hashed_total counter (bytes read)
        - fulhash_operation_ms histogram (operation latency)

    Examples:
        >>> from pyfulmen.fulhash import hash_file, Algorithm
        >>> from pathlib import Path
        >>> digest = hash_file("data.txt")
        >>> digest.formatted
        'xxh3-128:...'

        >>> # Path object
        >>> digest = hash_file(Path("data.txt"), Algorithm.SHA256)
        >>> digest.algorithm
        <Algorithm.SHA256: 'sha256'>
    """
    _validate_chunk_size(chunk_size)
    start_time = time.perf_counter()

    # Convert str to Path
    if isinstance(path, str):
        path = Path(path)

    # Create streaming hasher
    hasher = stream(algorithm)
    bytes_read = 0

    # Read file in chunks
    try:
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
                bytes_read += len(chunk)
    except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
        if isinstance(e, FileNotFoundError):
            raise FileNotFoundError(f"File not found: {path}") from e
        elif isinstance(e, IsADirectoryError):
            raise IsADirectoryError(f"Path is a directory, not a file: {path}") from e
        else:
            raise PermissionError(f"Permission denied reading file: {path}") from e

    digest = hasher.digest()
    _emit_operation_telemetry(algorithm, bytes_read, start_time)
    return digest


def hash_reader(
    reader: BinaryIO,
    algorithm: Algorithm = Algorithm.XXH3_128,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Digest:
    """Compute hash digest for a caller-supplied binary stream.

    reader must be a binary stream (BinaryIO) opened by the caller.
    FulHash reads from the CURRENT position to EOF in chunk_size blocks;
    it never seeks — bytes before the position are not hashed. Stream is
    NOT closed, position NOT restored (at EOF on return; ownership stays
    with caller). Non-seekable streams (pipes, sockets, stdin.buffer)
    fully supported (no seek/tell ever called). Text-mode streams
    rejected with TypeError. chunk_size > 0 (default 64 KiB).

    Args:
        reader: Binary stream to read from (current position to EOF)
        algorithm: Hash algorithm to use (default: XXH3_128)
        chunk_size: Read block size in bytes, must be > 0 (default: 64 KiB)

    Returns:
        Digest with algorithm, hex, bytes, and formatted fields

    Raises:
        TypeError: If reader is a text-mode stream
        ValueError: If chunk_size is not > 0
        OSError: If the underlying stream read fails

    Telemetry:
        Emits on the global registry after completion:
        - fulhash_operations_total_xxh3_128 / fulhash_operations_total_sha256
          counter (per-algorithm operations; crc32/crc32c are unmetered)
        - fulhash_bytes_hashed_total counter (bytes read)
        - fulhash_operation_ms histogram (operation latency)

    Examples:
        >>> import io
        >>> from pyfulmen.fulhash import hash_reader
        >>> digest = hash_reader(io.BytesIO(b"Hello, World!"))
        >>> digest.formatted
        'xxh3-128:531df2844447dd5077db03842cd75395'
    """
    _validate_chunk_size(chunk_size)
    if isinstance(reader, io.TextIOBase):
        raise TypeError("hash_reader requires a binary stream (BinaryIO); got a text-mode stream. Open with 'rb'.")

    start_time = time.perf_counter()
    hasher = stream(algorithm)
    bytes_read = 0

    while chunk := reader.read(chunk_size):
        if isinstance(chunk, str):
            raise TypeError(
                "hash_reader requires a binary stream (BinaryIO); reader.read() returned str. Open with 'rb'."
            )
        hasher.update(chunk)
        bytes_read += len(chunk)

    digest = hasher.digest()
    _emit_operation_telemetry(algorithm, bytes_read, start_time)
    return digest


def hash(data: bytes | str | Path, algorithm: Algorithm = Algorithm.XXH3_128) -> Digest:
    """Universal hash function - dispatches based on data type.

    Convenience wrapper that automatically chooses the right hashing
    function based on input type:
    - bytes → hash_bytes()
    - str → hash_string() (UTF-8 encoding)
    - Path → hash_file()

    Args:
        data: Data to hash (bytes, string, or file path)
        algorithm: Hash algorithm to use (default: XXH3_128)

    Returns:
        Digest with algorithm, hex, bytes, and formatted fields

    Raises:
        FileNotFoundError: If path does not exist (when data is Path)
        TypeError: If data type is not supported

    Examples:
        >>> from pyfulmen.fulhash import hash, Algorithm
        >>> from pathlib import Path

        >>> # Hash bytes
        >>> hash(b"Hello, World!").formatted
        'xxh3-128:531df2844447dd5077db03842cd75395'

        >>> # Hash string
        >>> hash("Hello, World!").formatted
        'xxh3-128:531df2844447dd5077db03842cd75395'

        >>> # Hash file
        >>> hash(Path("data.txt")).formatted
        'xxh3-128:...'

        >>> # Different algorithm
        >>> hash(b"test", Algorithm.SHA256).algorithm
        <Algorithm.SHA256: 'sha256'>
    """
    if isinstance(data, bytes):
        return hash_bytes(data, algorithm)
    elif isinstance(data, str):
        return hash_string(data, algorithm)
    elif isinstance(data, Path):
        return hash_file(data, algorithm)
    else:
        raise TypeError(f"Unsupported data type: {type(data).__name__}. Expected bytes, str, or Path.")


__all__ = ["DEFAULT_CHUNK_SIZE", "hash_file", "hash_reader", "hash"]
