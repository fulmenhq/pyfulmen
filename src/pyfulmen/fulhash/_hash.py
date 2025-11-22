"""Block hashing implementation for FulHash.

Provides one-shot hashing functions for bytes and strings using
xxh3-128 (default, fast) and sha256 (cryptographic) algorithms.
"""

import hashlib
import time
import zlib

import google_crc32c
import xxhash

from pyfulmen.telemetry import counter, histogram

from .models import Algorithm, Digest


def hash_bytes(data: bytes, algorithm: Algorithm = Algorithm.XXH3_128) -> Digest:
    """Compute hash digest for byte data.

    Args:
        data: Bytes to hash
        algorithm: Hash algorithm to use (default: XXH3_128)

    Returns:
        Digest with algorithm, hex, bytes, and formatted fields

    Examples:
        >>> from pyfulmen.fulhash import hash_bytes, Algorithm
        >>> digest = hash_bytes(b"Hello, World!", Algorithm.SHA256)
        >>> digest.formatted
        'sha256:dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'

        >>> # Default algorithm (XXH3-128)
        >>> digest = hash_bytes(b"Hello, World!")
        >>> digest.formatted
        'xxh3-128:531df2844447dd5077db03842cd75395'
    """
    start_time = time.perf_counter()

    if algorithm == Algorithm.XXH3_128:
        hasher = xxhash.xxh3_128(data)
        digest_bytes = hasher.digest()
        hex_digest = hasher.hexdigest()
        counter("fulhash_operations_total_xxh3_128").inc()
    elif algorithm == Algorithm.SHA256:
        hasher = hashlib.sha256(data)
        digest_bytes = hasher.digest()
        hex_digest = hasher.hexdigest()
        counter("fulhash_operations_total_sha256").inc()
    elif algorithm == Algorithm.CRC32:
        value = zlib.crc32(data) & 0xFFFFFFFF
        digest_bytes = value.to_bytes(4, byteorder="big")
        hex_digest = f"{value:08x}"
        counter("fulhash_operations_total_crc32").inc()
    elif algorithm == Algorithm.CRC32C:
        value = google_crc32c.value(data) & 0xFFFFFFFF
        digest_bytes = value.to_bytes(4, byteorder="big")
        hex_digest = f"{value:08x}"
        counter("fulhash_operations_total_crc32c").inc()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    # Record telemetry
    counter("fulhash_bytes_hashed_total").inc(len(data))
    duration_ms = (time.perf_counter() - start_time) * 1000
    histogram("fulhash_operation_ms").observe(duration_ms)

    return Digest(
        algorithm=algorithm,
        hex=hex_digest,
        bytes=digest_bytes,
    )


def hash_string(
    text: str,
    algorithm: Algorithm = Algorithm.XXH3_128,
    encoding: str = "utf-8",
) -> Digest:
    """Compute hash digest for string data.

    Args:
        text: String to hash
        algorithm: Hash algorithm to use (default: XXH3_128)
        encoding: Text encoding (default: utf-8)

    Returns:
        Digest with algorithm, hex, bytes, and formatted fields

    Telemetry:
        - Emits fulhash_hash_string_count counter (hash operations)

    Examples:
        >>> from pyfulmen.fulhash import hash_string, Algorithm
        >>> digest = hash_string("Hello, World!", Algorithm.SHA256)
        >>> digest.formatted
        'sha256:dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'

        >>> # Unicode support
        >>> digest = hash_string("Hello =% World")
        >>> digest.algorithm
        <Algorithm.XXH3_128: 'xxh3-128'>
    """
    counter("fulhash_hash_string_total").inc()

    data = text.encode(encoding)
    return hash_bytes(data, algorithm)


__all__ = ["hash_bytes", "hash_string"]
