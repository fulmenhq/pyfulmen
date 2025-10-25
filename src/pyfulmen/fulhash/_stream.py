"""Streaming hashing implementation for FulHash.

Provides incremental hashing for large data or data arriving in chunks,
using xxh3-128 (default, fast) and sha256 (cryptographic) algorithms.
"""

import hashlib
from typing import Self

import xxhash

from pyfulmen.telemetry import MetricRegistry

from .models import Algorithm, Digest


class StreamHasher:
    """Incremental hash computation for streaming data.

    Allows computing hashes over data that arrives in chunks or is too
    large to fit in memory at once.

    Attributes:
        algorithm: Hash algorithm in use

    Examples:
        >>> from pyfulmen.fulhash import stream, Algorithm
        >>> hasher = stream(Algorithm.XXH3_128)
        >>> hasher.update(b"Hello, ")
        >>> hasher.update(b"World!")
        >>> digest = hasher.digest()
        >>> digest.formatted
        'xxh3-128:531df2844447dd5077db03842cd75395'

        >>> # Streaming produces same result as block hashing
        >>> from pyfulmen.fulhash import hash_bytes
        >>> block_digest = hash_bytes(b"Hello, World!")
        >>> block_digest == digest
        True
    """

    def __init__(self, algorithm: Algorithm = Algorithm.XXH3_128) -> None:
        """Initialize streaming hasher.

        Args:
            algorithm: Hash algorithm to use (default: XXH3_128)
        """
        self._algorithm = algorithm
        self._reset_hasher()

    def _reset_hasher(self) -> None:
        """Reset internal hasher state."""
        if self._algorithm == Algorithm.XXH3_128:
            self._hasher = xxhash.xxh3_128()
        elif self._algorithm == Algorithm.SHA256:
            self._hasher = hashlib.sha256()
        else:
            raise ValueError(f"Unsupported algorithm: {self._algorithm}")

    @property
    def algorithm(self) -> Algorithm:
        """Hash algorithm in use."""
        return self._algorithm

    def update(self, data: bytes) -> Self:
        """Add data to hash computation.

        Args:
            data: Bytes to add to the hash

        Returns:
            Self for method chaining

        Examples:
            >>> hasher = stream()
            >>> hasher.update(b"Hello").update(b", ").update(b"World!")
            >>> digest = hasher.digest()
        """
        self._hasher.update(data)
        return self

    def digest(self) -> Digest:
        """Compute final hash digest.

        Returns:
            Digest with algorithm, hex, bytes, and formatted fields

        Note:
            This does NOT reset the hasher. You can continue calling
            update() to add more data, or call reset() to start fresh.

        Examples:
            >>> hasher = stream()
            >>> hasher.update(b"Hello")
            >>> intermediate = hasher.digest()
            >>> hasher.update(b", World!")
            >>> final = hasher.digest()
            >>> # intermediate != final (different data)
        """
        digest_bytes = self._hasher.digest()
        hex_digest = self._hasher.hexdigest()

        return Digest(
            algorithm=self._algorithm,
            hex=hex_digest,
            bytes=digest_bytes,
        )

    def reset(self) -> Self:
        """Reset hasher to initial state.

        Clears all accumulated data and allows reusing the hasher
        for a new computation.

        Returns:
            Self for method chaining

        Examples:
            >>> hasher = stream()
            >>> hasher.update(b"First computation")
            >>> first = hasher.digest()
            >>> hasher.reset().update(b"Second computation")
            >>> second = hasher.digest()
            >>> # first != second (different data)
        """
        self._reset_hasher()
        return self


def stream(algorithm: Algorithm = Algorithm.XXH3_128) -> StreamHasher:
    """Create a new streaming hasher.

    Convenience factory function for creating StreamHasher instances.

    Args:
        algorithm: Hash algorithm to use (default: XXH3_128)

    Returns:
        StreamHasher instance ready to accept data

    Telemetry:
        - Emits fulhash_stream_created_count counter (streamer creation)

    Examples:
        >>> from pyfulmen.fulhash import stream, Algorithm
        >>> hasher = stream(Algorithm.SHA256)
        >>> hasher.update(b"Hello, World!")
        >>> digest = hasher.digest()
        >>> digest.formatted
        'sha256:dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
    """
    registry = MetricRegistry()
    registry.counter("fulhash_stream_created_count").inc()

    return StreamHasher(algorithm)


__all__ = ["StreamHasher", "stream"]
