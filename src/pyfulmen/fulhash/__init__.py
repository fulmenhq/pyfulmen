"""FulHash - Fast, consistent hashing for the Fulmen ecosystem.

Provides block and streaming hashing with xxh3-128 (default, fast) and
sha256 (cryptographic) algorithms.

Standard: docs/crucible-py/standards/library/modules/fulhash.md
Schemas: schemas/crucible-py/library/fulhash/v1.0.0/

Examples:
    Block hashing:
        >>> from pyfulmen.fulhash import hash_bytes, Algorithm
        >>> digest = hash_bytes(b"Hello, World!", Algorithm.SHA256)
        >>> digest.formatted
        'sha256:dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'

    Streaming:
        >>> from pyfulmen.fulhash import stream, Algorithm
        >>> hasher = stream(Algorithm.XXH3_128)
        >>> hasher.update(b"Hello, ")
        >>> hasher.update(b"World!")
        >>> digest = hasher.digest()
        >>> digest.formatted
        'xxh3-128:531df2844447dd5077db03842cd75395'
"""

from ._file import hash, hash_file
from ._hash import hash_bytes, hash_string
from ._helpers import (
    compare_digests,
    format_checksum,
    parse_checksum,
    validate_checksum_string,
)
from ._stream import StreamHasher, stream
from .models import Algorithm, Digest

__all__ = [
    "Algorithm",
    "Digest",
    "hash",
    "hash_bytes",
    "hash_string",
    "hash_file",
    "stream",
    "StreamHasher",
    "format_checksum",
    "parse_checksum",
    "validate_checksum_string",
    "compare_digests",
]

__version__ = "0.1.6"
