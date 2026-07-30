"""FulHash error hierarchy.

Mirrors the tsfulmen/gofulmen error trees:
    FulHashError
    ├── UnsupportedAlgorithmError
    └── InvalidChecksumError
        └── InvalidChecksumFormatError

Compatibility note: ``UnsupportedAlgorithmError`` and ``InvalidChecksumError``
(and therefore ``InvalidChecksumFormatError``) also subclass ``ValueError``.
This is load-bearing — existing callers dispatch on ``except ValueError``
(e.g. ``fulpack.security.compute_checksum`` uses it as the hashlib-fallback
dispatch, and ``pathfinder.finder`` catches it for algorithm normalization).
Do not remove the ``ValueError`` base.
"""

SUPPORTED_ALGORITHMS_TEXT = "xxh3-128, sha256, crc32, crc32c"


class FulHashError(Exception):
    """Base class for all FulHash errors."""


class UnsupportedAlgorithmError(FulHashError, ValueError):
    """Raised when an algorithm is not supported by FulHash."""


class InvalidChecksumError(FulHashError, ValueError):
    """Raised when a checksum or digest payload is invalid."""


class InvalidChecksumFormatError(InvalidChecksumError):
    """Raised when a checksum string does not match 'algorithm:hex' format."""


__all__ = [
    "FulHashError",
    "UnsupportedAlgorithmError",
    "InvalidChecksumError",
    "InvalidChecksumFormatError",
]
