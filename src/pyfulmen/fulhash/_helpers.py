"""Metadata helpers for FulHash checksums.

Provides utilities for formatting, parsing, validating, and comparing
checksum strings according to the checksum-string.schema.json specification.
"""

import hmac
import re
from pathlib import Path

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
        ValueError: If algorithm is unsupported or hex is invalid

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
        raise ValueError(
            f"Unsupported algorithm: {algo_str}. Supported algorithms: {', '.join(ALGORITHM_HEX_LENGTHS.keys())}"
        )

    # Validate hex format
    expected_length = ALGORITHM_HEX_LENGTHS[algo_str]
    if not re.match(r"^[0-9a-f]+$", hex_digest):
        raise ValueError(f"Invalid hex format: must be lowercase hexadecimal, got: {hex_digest!r}")

    if len(hex_digest) != expected_length:
        raise ValueError(f"{algo_str} requires {expected_length} hex characters, got {len(hex_digest)}")

    return f"{algo_str}:{hex_digest}"


def parse_checksum(checksum: str) -> tuple[str, str]:
    """Parse checksum string into algorithm and hex components.

    Args:
        checksum: Checksum string in format "algorithm:hex"

    Returns:
        Tuple of (algorithm, hex_digest)

    Raises:
        ValueError: If checksum format is invalid

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
        raise ValueError(f"Invalid checksum format: expected format 'algorithm:hex', got: {checksum!r}")

    # Split on first colon only
    parts = checksum.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid checksum format: expected format 'algorithm:hex', got: {checksum!r}")

    algorithm, hex_digest = parts

    # Validate algorithm is supported
    if algorithm not in ALGORITHM_HEX_LENGTHS:
        raise ValueError(
            f"Unsupported algorithm: {algorithm}. Supported algorithms: {', '.join(ALGORITHM_HEX_LENGTHS.keys())}"
        )

    # Validate hex format
    expected_length = ALGORITHM_HEX_LENGTHS[algorithm]
    if not re.match(r"^[0-9a-f]+$", hex_digest):
        raise ValueError(f"Invalid hex format: must be lowercase hexadecimal, got: {hex_digest!r}")

    if len(hex_digest) != expected_length:
        raise ValueError(f"{algorithm} requires {expected_length} hex characters, got {len(hex_digest)}")

    return algorithm, hex_digest


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


def verify(source: str | Path | bytes, expected_digest: str) -> bool:
    """Verify data against an expected checksum.

    Computes hash of source and compares with expected digest.

    Args:
        source: Data to verify (string, bytes, or file path)
        expected_digest: Expected checksum string ("algorithm:hex")

    Returns:
        True if hash matches, False otherwise

    Raises:
        ValueError: If checksum format is invalid or algorithm unsupported
        OSError: If file read fails

    Examples:
        >>> from pyfulmen.fulhash import verify
        >>> verify(b"Hello", "xxh3-128:...")  # doctest: +SKIP
    """
    from ._hash import hash_bytes, hash_string
    from ._stream import stream

    algo_str, expected_hex = parse_checksum(expected_digest)
    algorithm = Algorithm(algo_str)

    # Compute actual digest
    if isinstance(source, bytes):
        digest = hash_bytes(source, algorithm)
    elif isinstance(source, str):
        digest = hash_string(source, algorithm)
    elif isinstance(source, Path):
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")
        hasher = stream(algorithm)
        with open(source, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        digest = hasher.digest()
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    return hmac.compare_digest(digest.hex, expected_hex)


def multi_hash(source: str | Path | bytes, algorithms: list[Algorithm]) -> dict[Algorithm, Digest]:
    """Compute multiple digests in a single pass.

    Optimized for streaming data once to multiple hashers.

    Args:
        source: Data to hash (bytes, string, or Path)
        algorithms: List of algorithms to compute

    Returns:
        Dictionary mapping Algorithm to Digest
    """
    from ._stream import stream

    hashers = [stream(algo) for algo in algorithms]

    if isinstance(source, bytes):
        for h in hashers:
            h.update(source)
    elif isinstance(source, str):
        # Treat as text
        data = source.encode("utf-8")
        for h in hashers:
            h.update(data)
    elif isinstance(source, Path):
        with open(source, "rb") as f:
            while chunk := f.read(65536):
                for h in hashers:
                    h.update(chunk)
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    return {h.algorithm: h.digest() for h in hashers}


__all__ = [
    "format_checksum",
    "parse_checksum",
    "validate_checksum_string",
    "compare_digests",
    "verify",
    "multi_hash",
]
