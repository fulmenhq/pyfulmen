"""Metadata helpers for FulHash checksums.

Provides utilities for formatting, parsing, validating, and comparing
checksum strings according to the checksum-string.schema.json specification.
"""

import hmac
import io
import re
import warnings
from pathlib import Path
from typing import BinaryIO

from ._file import DEFAULT_CHUNK_SIZE, _validate_chunk_size, hash_file, hash_reader
from ._hash import hash_bytes, hash_string
from ._stream import stream
from .errors import (
    InvalidChecksumError,
    InvalidChecksumFormatError,
    UnsupportedAlgorithmError,
)
from .models import Algorithm, Digest

# Checksum string pattern from checksum-string.schema.json
CHECKSUM_PATTERN = re.compile(r"^(xxh3-128:[0-9a-f]{32}|sha256:[0-9a-f]{64}|crc32:[0-9a-f]{8}|crc32c:[0-9a-f]{8})$")

# Algorithm to expected hex length mapping
ALGORITHM_HEX_LENGTHS = {
    "xxh3-128": 32,
    "sha256": 64,
    "crc32": 8,
    "crc32c": 8,
}


def format_checksum(algorithm: str | Algorithm, hex_digest: str) -> str:
    """Format algorithm and hex digest into checksum string.

    Args:
        algorithm: Hash algorithm identifier (enum or string)
        hex_digest: Lowercase hexadecimal digest

    Returns:
        Formatted checksum string in format "algorithm:hex"

    Raises:
        UnsupportedAlgorithmError: If algorithm is unsupported (ValueError subclass)
        InvalidChecksumError: If hex is invalid (ValueError subclass)

    Examples:
        >>> from pyfulmen.fulhash import format_checksum, Algorithm
        >>> format_checksum(Algorithm.XXH3_128, "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
        'xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6'

        >>> format_checksum(
        ...     "sha256",
        ...     "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ... )
        'sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    """
    # Normalize algorithm to string
    algo_str = algorithm.value if isinstance(algorithm, Algorithm) else algorithm

    # Validate algorithm is supported
    if algo_str not in ALGORITHM_HEX_LENGTHS:
        raise UnsupportedAlgorithmError(
            f"Unsupported algorithm: {algo_str}. Supported algorithms: {', '.join(ALGORITHM_HEX_LENGTHS.keys())}"
        )

    # Validate hex format
    expected_length = ALGORITHM_HEX_LENGTHS[algo_str]
    if not re.match(r"^[0-9a-f]+$", hex_digest):
        raise InvalidChecksumError(f"Invalid hex format: must be lowercase hexadecimal, got: {hex_digest!r}")

    if len(hex_digest) != expected_length:
        raise InvalidChecksumError(f"{algo_str} requires {expected_length} hex characters, got {len(hex_digest)}")

    return f"{algo_str}:{hex_digest}"


def parse_checksum(checksum: str) -> tuple[str, str]:
    """Parse checksum string into algorithm and hex components.

    Args:
        checksum: Checksum string in format "algorithm:hex"

    Returns:
        Tuple of (algorithm, hex_digest)

    Raises:
        InvalidChecksumFormatError: If checksum format is invalid (ValueError subclass)
        UnsupportedAlgorithmError: If algorithm is unsupported (ValueError subclass)

    Examples:
        >>> from pyfulmen.fulhash import parse_checksum
        >>> parse_checksum("xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
        ('xxh3-128', 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6')

        >>> parse_checksum(
        ...     "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ... )
        ('sha256', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
    """
    # Strip whitespace
    checksum = checksum.strip()

    # Check for colon separator
    if ":" not in checksum:
        raise InvalidChecksumFormatError(f"Invalid checksum format: expected format 'algorithm:hex', got: {checksum!r}")

    # Split on first colon only
    parts = checksum.split(":", 1)
    if len(parts) != 2:
        raise InvalidChecksumFormatError(f"Invalid checksum format: expected format 'algorithm:hex', got: {checksum!r}")

    algorithm, hex_digest = parts

    # Validate algorithm is supported
    if algorithm not in ALGORITHM_HEX_LENGTHS:
        raise UnsupportedAlgorithmError(
            f"Unsupported algorithm: {algorithm}. Supported algorithms: {', '.join(ALGORITHM_HEX_LENGTHS.keys())}"
        )

    # Validate hex format
    expected_length = ALGORITHM_HEX_LENGTHS[algorithm]
    if not re.match(r"^[0-9a-f]+$", hex_digest):
        raise InvalidChecksumFormatError(f"Invalid hex format: must be lowercase hexadecimal, got: {hex_digest!r}")

    if len(hex_digest) != expected_length:
        raise InvalidChecksumFormatError(
            f"{algorithm} requires {expected_length} hex characters, got {len(hex_digest)}"
        )

    return algorithm, hex_digest


def parse_digest(checksum: str) -> Digest:
    """Parse checksum string into a Digest model.

    Composes parse_checksum with Digest construction; raw bytes are decoded
    from the hex component (gofulmen ParseDigest parity).

    Args:
        checksum: Checksum string in format "algorithm:hex"

    Returns:
        Digest with algorithm, hex, bytes, and formatted fields

    Raises:
        InvalidChecksumFormatError: If checksum format is invalid (ValueError subclass)
        UnsupportedAlgorithmError: If algorithm is unsupported (ValueError subclass)

    Examples:
        >>> from pyfulmen.fulhash import parse_digest
        >>> digest = parse_digest("xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
        >>> digest.formatted
        'xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6'
    """
    algo_str, hex_digest = parse_checksum(checksum)
    return Digest(
        algorithm=Algorithm(algo_str),
        hex=hex_digest,
        bytes=bytes.fromhex(hex_digest),
    )


def validate_checksum_string(checksum: str) -> bool:
    """Validate checksum string against schema pattern.

    Returns True if checksum matches the checksum-string.schema.json pattern,
    False otherwise. Does not raise exceptions.

    Args:
        checksum: Checksum string to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> from pyfulmen.fulhash import validate_checksum_string
        >>> validate_checksum_string("xxh3-128:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
        True

        >>> validate_checksum_string("invalid-format")
        False

        >>> validate_checksum_string("md5:abc123")
        False
    """
    # Strip whitespace and validate
    checksum = checksum.strip()
    return CHECKSUM_PATTERN.match(checksum) is not None


def compare_digests(a: Digest, b: Digest) -> bool:
    """Compare two digests for equality using constant-time comparison.

    Uses hmac.compare_digest() to prevent timing attacks. Compares both
    algorithm and hex values.

    Args:
        a: First digest
        b: Second digest

    Returns:
        True if digests are identical, False otherwise

    Examples:
        >>> from pyfulmen.fulhash import hash_bytes, compare_digests
        >>> digest1 = hash_bytes(b"Hello, World!")
        >>> digest2 = hash_bytes(b"Hello, World!")
        >>> compare_digests(digest1, digest2)
        True

        >>> digest3 = hash_bytes(b"Different data")
        >>> compare_digests(digest1, digest3)
        False
    """
    # First check algorithms match (not timing-sensitive)
    if a.algorithm != b.algorithm:
        return False

    # Use constant-time comparison for hex values
    return hmac.compare_digest(a.hex, b.hex)


def verify_bytes(data: bytes, expected: str) -> bool:
    """Verify byte data against an expected checksum.

    Parses expected via parse_checksum, hashes data with the parsed
    algorithm, and compares using constant-time hmac.compare_digest.

    Args:
        data: Bytes to verify
        expected: Expected checksum string ("algorithm:hex")

    Returns:
        True if hash matches, False otherwise

    Raises:
        InvalidChecksumFormatError: If checksum format is invalid
        UnsupportedAlgorithmError: If algorithm is unsupported

    Examples:
        >>> from pyfulmen.fulhash import hash_bytes, verify_bytes
        >>> verify_bytes(b"Hello", hash_bytes(b"Hello").formatted)
        True
    """
    algo_str, expected_hex = parse_checksum(expected)
    digest = hash_bytes(data, Algorithm(algo_str))
    return hmac.compare_digest(digest.hex, expected_hex)


def verify_text(text: str, expected: str, encoding: str = "utf-8") -> bool:
    """Verify text against an expected checksum.

    The text is encoded (default UTF-8) and hashed; it is never treated
    as a file path. Use verify_file for paths.

    Args:
        text: Text to verify
        expected: Expected checksum string ("algorithm:hex")
        encoding: Text encoding (default: utf-8)

    Returns:
        True if hash matches, False otherwise

    Raises:
        InvalidChecksumFormatError: If checksum format is invalid
        UnsupportedAlgorithmError: If algorithm is unsupported

    Examples:
        >>> from pyfulmen.fulhash import hash_string, verify_text
        >>> verify_text("Hello", hash_string("Hello").formatted)
        True
    """
    algo_str, expected_hex = parse_checksum(expected)
    digest = hash_string(text, Algorithm(algo_str), encoding)
    return hmac.compare_digest(digest.hex, expected_hex)


def verify_file(path: Path | str, expected: str, *, chunk_size: int = DEFAULT_CHUNK_SIZE) -> bool:
    """Verify file contents against an expected checksum.

    Delegates to hash_file (streaming, chunk_size blocks) and compares
    using constant-time hmac.compare_digest.

    Args:
        path: Path to file (Path object or string)
        expected: Expected checksum string ("algorithm:hex")
        chunk_size: Read block size in bytes, must be > 0 (default: 64 KiB)

    Returns:
        True if hash matches, False otherwise

    Raises:
        InvalidChecksumFormatError: If checksum format is invalid
        UnsupportedAlgorithmError: If algorithm is unsupported
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
        IsADirectoryError: If path is a directory
        ValueError: If chunk_size is not > 0

    Examples:
        >>> from pyfulmen.fulhash import verify_file
        >>> verify_file("data.txt", "xxh3-128:...")  # doctest: +SKIP
    """
    algo_str, expected_hex = parse_checksum(expected)
    digest = hash_file(path, Algorithm(algo_str), chunk_size=chunk_size)
    return hmac.compare_digest(digest.hex, expected_hex)


def verify_reader(reader: BinaryIO, expected: str, *, chunk_size: int = DEFAULT_CHUNK_SIZE) -> bool:
    """Verify a caller-supplied binary stream against an expected checksum.

    Delegates to hash_reader: reads from the CURRENT position to EOF in
    chunk_size blocks; never seeks; stream is NOT closed and position is
    NOT restored (at EOF on return). Non-seekable streams fully supported.
    Text-mode streams rejected with TypeError.

    Args:
        reader: Binary stream to read from (current position to EOF)
        expected: Expected checksum string ("algorithm:hex")
        chunk_size: Read block size in bytes, must be > 0 (default: 64 KiB)

    Returns:
        True if hash matches, False otherwise

    Raises:
        InvalidChecksumFormatError: If checksum format is invalid
        UnsupportedAlgorithmError: If algorithm is unsupported
        TypeError: If reader is a text-mode stream
        ValueError: If chunk_size is not > 0
        OSError: If the underlying stream read fails

    Examples:
        >>> import io
        >>> from pyfulmen.fulhash import hash_bytes, verify_reader
        >>> expected = hash_bytes(b"Hello").formatted
        >>> verify_reader(io.BytesIO(b"Hello"), expected)
        True
    """
    algo_str, expected_hex = parse_checksum(expected)
    digest = hash_reader(reader, Algorithm(algo_str), chunk_size=chunk_size)
    return hmac.compare_digest(digest.hex, expected_hex)


def verify(source: str | Path | bytes, expected_digest: str) -> bool:
    """Verify data against an expected checksum (type dispatcher).

    Dispatches on source type:
    - bytes → verify_bytes()
    - str → verify_text() (deprecated; see below)
    - Path → verify_file()

    .. deprecated:: 0.3.0
        Passing a str to fulhash.verify() is deprecated because it is
        ambiguous (the string is hashed as text, never treated as a path).
        Use verify_text(), verify_bytes(), or verify_file() instead.
        str support will be removed in v0.5.0.

    Args:
        source: Data to verify (bytes, string-as-text, or file path)
        expected_digest: Expected checksum string ("algorithm:hex")

    Returns:
        True if hash matches, False otherwise

    Raises:
        ValueError: If checksum format is invalid or algorithm unsupported
        TypeError: If source type is not supported
        OSError: If file read fails

    Examples:
        >>> from pyfulmen.fulhash import verify
        >>> verify(b"Hello", "xxh3-128:...")  # doctest: +SKIP
    """
    if isinstance(source, bytes):
        return verify_bytes(source, expected_digest)
    elif isinstance(source, str):
        warnings.warn(
            "Passing a str to fulhash.verify() is deprecated because it is "
            "ambiguous (the string is hashed as text, never treated as a path). "
            "Use verify_text(), verify_bytes(), or verify_file() instead. "
            "str support will be removed in v0.5.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return verify_text(source, expected_digest)
    elif isinstance(source, Path):
        return verify_file(source, expected_digest)
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")


def multi_hash_bytes(data: bytes, algorithms: list[Algorithm]) -> dict[Algorithm, Digest]:
    """Compute multiple digests of byte data in a single pass.

    Args:
        data: Bytes to hash
        algorithms: List of algorithms to compute

    Returns:
        Dictionary mapping Algorithm to Digest

    Examples:
        >>> from pyfulmen.fulhash import Algorithm, multi_hash_bytes
        >>> digests = multi_hash_bytes(b"Hello", [Algorithm.XXH3_128, Algorithm.SHA256])
        >>> sorted(d.value for d in digests)
        ['sha256', 'xxh3-128']
    """
    hashers = [stream(algo) for algo in algorithms]
    for h in hashers:
        h.update(data)
    return {h.algorithm: h.digest() for h in hashers}


def multi_hash_text(text: str, algorithms: list[Algorithm], encoding: str = "utf-8") -> dict[Algorithm, Digest]:
    """Compute multiple digests of text in a single pass.

    The text is encoded (default UTF-8) and hashed; it is never treated
    as a file path. Use multi_hash_file for paths.

    Args:
        text: Text to hash
        algorithms: List of algorithms to compute
        encoding: Text encoding (default: utf-8)

    Returns:
        Dictionary mapping Algorithm to Digest
    """
    return multi_hash_bytes(text.encode(encoding), algorithms)


def multi_hash_file(
    path: Path | str,
    algorithms: list[Algorithm],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict[Algorithm, Digest]:
    """Compute multiple digests of file contents in a single pass.

    Streams the file once in chunk_size blocks, feeding all hashers.

    Args:
        path: Path to file (Path object or string)
        algorithms: List of algorithms to compute
        chunk_size: Read block size in bytes, must be > 0 (default: 64 KiB)

    Returns:
        Dictionary mapping Algorithm to Digest

    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file cannot be read
        IsADirectoryError: If path is a directory
        ValueError: If chunk_size is not > 0
    """
    _validate_chunk_size(chunk_size)

    hashers = [stream(algo) for algo in algorithms]
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            for h in hashers:
                h.update(chunk)
    return {h.algorithm: h.digest() for h in hashers}


def multi_hash_reader(
    reader: BinaryIO,
    algorithms: list[Algorithm],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict[Algorithm, Digest]:
    """Compute multiple digests of a caller-supplied binary stream in a single pass.

    reader must be a binary stream (BinaryIO) opened by the caller.
    FulHash reads from the CURRENT position to EOF in chunk_size blocks;
    it never seeks — bytes before the position are not hashed. Stream is
    NOT closed, position NOT restored (at EOF on return; ownership stays
    with caller). Non-seekable streams (pipes, sockets, stdin.buffer)
    fully supported (no seek/tell ever called). Text-mode streams
    rejected with TypeError. chunk_size > 0 (default 64 KiB).

    Args:
        reader: Binary stream to read from (current position to EOF)
        algorithms: List of algorithms to compute
        chunk_size: Read block size in bytes, must be > 0 (default: 64 KiB)

    Returns:
        Dictionary mapping Algorithm to Digest

    Raises:
        TypeError: If reader is a text-mode stream
        ValueError: If chunk_size is not > 0
        OSError: If the underlying stream read fails
    """
    _validate_chunk_size(chunk_size)
    if isinstance(reader, io.TextIOBase):
        raise TypeError(
            "multi_hash_reader requires a binary stream (BinaryIO); got a text-mode stream. Open with 'rb'."
        )

    hashers = [stream(algo) for algo in algorithms]
    while chunk := reader.read(chunk_size):
        if isinstance(chunk, str):
            raise TypeError(
                "multi_hash_reader requires a binary stream (BinaryIO); reader.read() returned str. Open with 'rb'."
            )
        for h in hashers:
            h.update(chunk)
    return {h.algorithm: h.digest() for h in hashers}


def multi_hash(source: str | Path | bytes, algorithms: list[Algorithm]) -> dict[Algorithm, Digest]:
    """Compute multiple digests in a single pass (type dispatcher).

    Dispatches on source type:
    - bytes → multi_hash_bytes()
    - str → multi_hash_text() (deprecated; see below)
    - Path → multi_hash_file()

    .. deprecated:: 0.3.0
        Passing a str to fulhash.multi_hash() is deprecated because it is
        ambiguous (the string is hashed as text, never treated as a path).
        Use multi_hash_text(), multi_hash_bytes(), or multi_hash_file()
        instead. str support will be removed in v0.5.0.

    Args:
        source: Data to hash (bytes, string-as-text, or Path)
        algorithms: List of algorithms to compute

    Returns:
        Dictionary mapping Algorithm to Digest

    Raises:
        TypeError: If source type is not supported
        OSError: If file read fails
    """
    if isinstance(source, bytes):
        return multi_hash_bytes(source, algorithms)
    elif isinstance(source, str):
        warnings.warn(
            "Passing a str to fulhash.multi_hash() is deprecated because it is "
            "ambiguous (the string is hashed as text, never treated as a path). "
            "Use multi_hash_text(), multi_hash_bytes(), or multi_hash_file() "
            "instead. str support will be removed in v0.5.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return multi_hash_text(source, algorithms)
    elif isinstance(source, Path):
        return multi_hash_file(source, algorithms)
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")


__all__ = [
    "format_checksum",
    "parse_checksum",
    "parse_digest",
    "validate_checksum_string",
    "compare_digests",
    "verify",
    "verify_bytes",
    "verify_text",
    "verify_file",
    "verify_reader",
    "multi_hash",
    "multi_hash_bytes",
    "multi_hash_text",
    "multi_hash_file",
    "multi_hash_reader",
]
