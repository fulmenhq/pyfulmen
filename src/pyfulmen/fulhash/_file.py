"""File hashing and convenience APIs for FulHash.

Provides hash_file for hashing file contents and a universal hash()
dispatcher that works with bytes, strings, and file paths.
"""

from pathlib import Path

from pyfulmen.telemetry import MetricRegistry

from ._hash import hash_bytes, hash_string
from ._stream import stream
from .models import Algorithm, Digest

# Chunk size for streaming file reads (64KB)
CHUNK_SIZE = 64 * 1024


def hash_file(path: Path | str, algorithm: Algorithm = Algorithm.XXH3_128) -> Digest:
    """Compute hash digest for file contents.

    Reads file in binary mode using streaming hasher with 64KB chunks
    for memory efficiency. Works with files of any size.

    Args:
        path: Path to file (Path object or string)
        algorithm: Hash algorithm to use (default: XXH3_128)

    Returns:
        Digest with algorithm, hex, bytes, and formatted fields

    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
        IsADirectoryError: If path is a directory

    Telemetry:
        - Emits fulhash_hash_file_count counter (hash operations)
        - Emits fulhash_errors_count counter (file I/O errors)

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
    registry = MetricRegistry()
    registry.counter("fulhash_hash_file_count").inc()

    # Convert str to Path
    if isinstance(path, str):
        path = Path(path)

    # Create streaming hasher
    hasher = stream(algorithm)

    # Read file in chunks
    try:
        with open(path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hasher.update(chunk)
    except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
        registry.counter("fulhash_errors_count").inc()
        if isinstance(e, FileNotFoundError):
            raise FileNotFoundError(f"File not found: {path}") from e
        elif isinstance(e, IsADirectoryError):
            raise IsADirectoryError(f"Path is a directory, not a file: {path}") from e
        else:
            raise PermissionError(f"Permission denied reading file: {path}") from e

    return hasher.digest()


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
        raise TypeError(
            f"Unsupported data type: {type(data).__name__}. Expected bytes, str, or Path."
        )


__all__ = ["hash_file", "hash"]
