"""FulHash data models.

Implements the Digest type and Algorithm enum according to:
- schemas/crucible-py/library/fulhash/v1.0.0/digest.schema.json
- schemas/crucible-py/library/fulhash/v1.0.0/checksum-string.schema.json
- docs/crucible-py/standards/library/modules/fulhash.md
"""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class Algorithm(str, Enum):
    """Supported hash algorithms.

    Attributes:
        XXH3_128: Fast non-cryptographic 128-bit hash (default)
        SHA256: Cryptographic 256-bit hash
    """

    XXH3_128 = "xxh3-128"
    SHA256 = "sha256"


class Digest(BaseModel):
    """Hash digest with metadata.

    Represents a computed hash digest with algorithm metadata,
    conforming to digest.schema.json.

    Attributes:
        algorithm: Hash algorithm used
        hex: Lowercase hexadecimal digest representation
        bytes: Optional raw digest bytes
        formatted: Computed checksum string (algorithm:hex)

    Examples:
        >>> from pyfulmen.fulhash import Digest, Algorithm
        >>> digest = Digest(
        ...     algorithm=Algorithm.XXH3_128,
        ...     hex="531df2844447dd5077db03842cd75395",
        ...     bytes=b"S\\x1d\\xf2\\x84DB}\\xd5\\x07}\\xb0\\x38B\\xcdu\\x95"
        ... )
        >>> digest.formatted
        'xxh3-128:531df2844447dd5077db03842cd75395'

        >>> # SHA-256 example
        >>> sha_digest = Digest(
        ...     algorithm=Algorithm.SHA256,
        ...     hex="dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        ... )
        >>> sha_digest.formatted
        'sha256:dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
    """

    model_config = ConfigDict(
        frozen=True,  # Immutable after creation
        str_strip_whitespace=True,
    )

    algorithm: Algorithm = Field(
        ...,
        description="Hash algorithm identifier",
    )

    hex: str = Field(
        ...,
        description="Lowercase hexadecimal digest representation",
        pattern=r"^[0-9a-f]+$",
    )

    bytes: Annotated[
        bytes | None,
        Field(
            default=None,
            description="Raw digest bytes",
            repr=False,  # Don't include in repr (can be long)
        ),
    ]

    @field_validator("hex")
    @classmethod
    def validate_hex_length(cls, v: str, info) -> str:
        """Validate hex length matches algorithm requirements.

        Per digest.schema.json:
        - xxh3-128: 32 hex characters (16 bytes)
        - sha256: 64 hex characters (32 bytes)
        """
        algorithm = info.data.get("algorithm")
        if algorithm is None:
            return v

        expected_length = {
            Algorithm.XXH3_128: 32,
            Algorithm.SHA256: 64,
        }[algorithm]

        if len(v) != expected_length:
            raise ValueError(
                f"{algorithm.value} requires {expected_length} hex characters, got {len(v)}"
            )

        return v

    @field_validator("bytes")
    @classmethod
    def validate_bytes_length(cls, v: bytes | None, info) -> bytes | None:
        """Validate bytes length matches algorithm requirements.

        Per digest.schema.json:
        - xxh3-128: 16 bytes
        - sha256: 32 bytes
        """
        if v is None:
            return v

        algorithm = info.data.get("algorithm")
        if algorithm is None:
            return v

        expected_length = {
            Algorithm.XXH3_128: 16,
            Algorithm.SHA256: 32,
        }[algorithm]

        if len(v) != expected_length:
            raise ValueError(f"{algorithm.value} requires {expected_length} bytes, got {len(v)}")

        return v

    @computed_field  # type: ignore[misc]
    @property
    def formatted(self) -> str:
        """Canonical checksum string representation.

        Returns checksum in format: algorithm:hex

        Conforms to checksum-string.schema.json pattern:
        ^(xxh3-128:[0-9a-f]{32}|sha256:[0-9a-f]{64})$
        """
        return f"{self.algorithm.value}:{self.hex}"


__all__ = ["Algorithm", "Digest"]
