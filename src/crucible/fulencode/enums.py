"""Fulencode Enums - Generated from Crucible taxonomies.

This file is AUTO-GENERATED from the Fulencode taxonomy schemas.
DO NOT EDIT MANUALLY - changes will be overwritten.

Taxonomy Version: v1.0.0
Last Reviewed: 2025-11-13
Source: schemas/taxonomy/library/fulencode/

See: https://github.com/fulmenhq/crucible/blob/main/docs/standards/library/modules/fulencode.md
"""

from enum import Enum


class EncodingFormat(str, Enum):
    """EncodingFormat enum

    Generated from: schemas/taxonomy/library/fulencode/encoding-families/v1.0.0/families.yaml
    """

    BASE64 = "base64"

    BASE64URL = "base64url"

    BASE64_RAW = "base64_raw"

    BASE32 = "base32"

    BASE32HEX = "base32hex"

    HEX = "hex"

    UTF_8 = "utf-8"

    UTF_16LE = "utf-16le"

    UTF_16BE = "utf-16be"

    ISO_8859_1 = "iso-8859-1"

    CP1252 = "cp1252"

    ASCII = "ascii"


class NormalizationProfile(str, Enum):
    """NormalizationProfile enum

    Generated from: schemas/taxonomy/library/fulencode/normalization-profiles/v1.0.0/profiles.yaml
    """

    NFC = "nfc"

    NFD = "nfd"

    NFKC = "nfkc"

    NFKD = "nfkd"

    SAFE_IDENTIFIERS = "safe_identifiers"

    SEARCH_OPTIMIZED = "search_optimized"

    FILENAME_SAFE = "filename_safe"

    LEGACY_COMPATIBLE = "legacy_compatible"


class ConfidenceLevel(str, Enum):
    """ConfidenceLevel enum

    Generated from: schemas/taxonomy/library/fulencode/detection-confidence/v1.0.0/levels.yaml
    """

    HIGH = "high"

    MEDIUM = "medium"

    LOW = "low"
