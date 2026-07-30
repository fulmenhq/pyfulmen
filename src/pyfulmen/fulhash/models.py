"""FulHash data models.

Implements the Digest type and Algorithm enum according to:
- schemas/crucible-py/library/fulhash/v1.0.0/digest.schema.json
- schemas/crucible-py/library/fulhash/v1.0.0/checksum-string.schema.json
- docs/crucible-py/standards/library/modules/fulhash.md
"""

from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    computed_field,
    field_serializer,
    field_validator,
    model_serializer,
)

import crucible.fulhash as _crucible_fulhash

# SSOT re-export: the Algorithm enum is generated from crucible
# (src/crucible/fulhash/types.py). Member names/values and the StrEnum base
# are byte-identical to the previous local definition, so this is a drop-in
# replacement. Keep `pyfulmen.fulhash.models.Algorithm` importable — external
# code and tests import it from this path.
from crucible.fulhash import Algorithm

from .errors import (
    SUPPORTED_ALGORITHMS_TEXT,
    InvalidChecksumError,
    UnsupportedAlgorithmError,
)


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

    @field_validator("bytes", mode="before")
    @classmethod
    def coerce_bytes_from_list(cls, v: Any) -> Any:
        """Coerce a JSON ``list[int]`` payload back into ``bytes``.

        Per digest.schema.json, the ``bytes`` property is serialized as an
        array of integers (0-255) in JSON; accept that form on validation so
        JSON round-trips work.
        """
        if isinstance(v, list):
            if any(not isinstance(item, int) or isinstance(item, bool) for item in v):
                raise ValueError("invalid byte array: elements must be integers 0-255")
            try:
                return bytes(v)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid byte array: {exc}") from exc
        return v

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

        if algorithm == Algorithm.XXH3_128:
            expected_length = 32
        elif algorithm == Algorithm.SHA256:
            expected_length = 64
        elif algorithm == Algorithm.CRC32 or algorithm == Algorithm.CRC32C:
            expected_length = 8
        else:
            return v

        if len(v) != expected_length:
            raise ValueError(f"{algorithm.value} requires {expected_length} hex characters, got {len(v)}")

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

        if algorithm == Algorithm.XXH3_128:
            expected_length = 16
        elif algorithm == Algorithm.SHA256:
            expected_length = 32
        elif algorithm == Algorithm.CRC32 or algorithm == Algorithm.CRC32C:
            expected_length = 4
        else:
            return v

        if len(v) != expected_length:
            raise ValueError(f"{algorithm.value} requires {expected_length} bytes, got {len(v)}")

        return v

    @field_serializer("bytes", when_used="json-unless-none")
    def serialize_bytes_as_list(self, v: bytes) -> list[int]:
        """Serialize raw digest bytes as ``list[int]`` in JSON mode.

        Per digest.schema.json, ``bytes`` is an array of integers (0-255).
        Python mode (``model_dump()``) is unaffected and keeps ``bytes``.
        """
        return list(v)

    # No return annotation: a declared dict[str, Any] would replace the
    # model's serialization JSON schema with a bare object schema.
    @model_serializer(mode="wrap", when_used="json")
    def omit_none_bytes_in_json(self, handler: SerializerFunctionWrapHandler):
        """Omit the ``bytes`` key entirely in JSON output when unset.

        digest.schema.json marks ``bytes`` as optional; ``null`` is not a
        valid value for it, so the key must be absent rather than ``None``.
        """
        data = handler(self)
        if data.get("bytes") is None:
            data.pop("bytes", None)
        return data

    @computed_field  # type: ignore[misc]
    @property
    def formatted(self) -> str:
        """Canonical checksum string representation.

        Returns checksum in format: algorithm:hex

        Conforms to checksum-string.schema.json pattern:
        ^(xxh3-128:[0-9a-f]{32}|sha256:[0-9a-f]{64}|crc32:[0-9a-f]{8}|crc32c:[0-9a-f]{8})$
        """
        return f"{self.algorithm.value}:{self.hex}"

    def to_crucible(self) -> _crucible_fulhash.Digest:
        """Convert to the generated crucible Digest TypedDict.

        Copies algorithm/hex/formatted; ``bytes`` is included as ``list[int]``
        only when set (the schema marks it optional and null is not valid).
        """
        result: _crucible_fulhash.Digest = {
            "algorithm": self.algorithm.value,
            "hex": self.hex,
            "formatted": self.formatted,
        }
        if self.bytes is not None:
            result["bytes"] = list(self.bytes)
        return result

    @classmethod
    def from_crucible(cls, crucible_digest: _crucible_fulhash.Digest) -> "Digest":
        """Build a Digest from the generated crucible Digest TypedDict.

        Mirrors gofulmen ``FromCrucible``: validates the algorithm, takes raw
        bytes from the ``bytes`` field when present, otherwise decodes them
        from ``hex``; errors if both are missing. ``formatted`` is recomputed
        rather than trusted from the payload.

        Note: uses defensive ``.get()`` access throughout because the
        generated TypedDict is currently ``total=False`` (known codegen
        defect — filed upstream against crucible).

        Raises:
            UnsupportedAlgorithmError: If the algorithm is not supported.
            InvalidChecksumError: If both ``bytes`` and ``hex`` are missing.
        """
        algo_value = crucible_digest.get("algorithm")
        try:
            algorithm = Algorithm(algo_value)
        except ValueError as exc:
            raise UnsupportedAlgorithmError(
                f"Unsupported algorithm: {algo_value}. Supported algorithms: {SUPPORTED_ALGORITHMS_TEXT}"
            ) from exc

        raw_bytes = crucible_digest.get("bytes")
        hex_digest = crucible_digest.get("hex")

        if raw_bytes:
            # Non-empty bytes are authoritative (gofulmen parity): hex is
            # always derived from them, never trusted from the payload.
            digest_bytes = bytes(raw_bytes)
            hex_digest = digest_bytes.hex()
        elif hex_digest:
            try:
                digest_bytes = bytes.fromhex(hex_digest)
            except ValueError as exc:
                raise InvalidChecksumError(f"Invalid hex in crucible digest: {hex_digest!r}") from exc
        else:
            raise InvalidChecksumError("crucible digest missing both bytes and hex fields")

        return cls(algorithm=algorithm, hex=hex_digest, bytes=digest_bytes)


__all__ = ["Algorithm", "Digest"]
