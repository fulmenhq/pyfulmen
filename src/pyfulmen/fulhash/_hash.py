"""Block hashing implementation for FulHash.

Provides one-shot hashing functions for bytes and strings using
xxh3-128 (default, fast) and sha256 (cryptographic) algorithms.
"""

import hashlib

import xxhash

from pyfulmen.telemetry import MetricRegistry

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
    if algorithm == Algorithm.XXH3_128:
        hasher = xxhash.xxh3_128(data)
        digest_bytes = hasher.digest()
        hex_digest = hasher.hexdigest()
    elif algorithm == Algorithm.SHA256:
        hasher = hashlib.sha256(data)
        digest_bytes = hasher.digest()
        hex_digest = hasher.hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

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
    registry = MetricRegistry()
    registry.counter("fulhash_hash_string_count").inc()

    data = text.encode(encoding)
    return hash_bytes(data, algorithm)


__all__ = ["hash_bytes", "hash_string"]
