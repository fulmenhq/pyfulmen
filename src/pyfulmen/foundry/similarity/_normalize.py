"""
Text normalization utilities for Unicode-aware string processing.

Provides case folding, accent stripping, and preset-based normalization pipelines
following the Foundry text similarity standard v2.0.0.

Normalization Presets:
    - none: No changes (returns input unchanged)
    - minimal: NFC normalization + trim whitespace
    - default: NFC + casefold + trim (recommended for most use cases)
    - aggressive: NFKD + casefold + strip accents + remove punctuation + trim
"""

import re
import unicodedata
from typing import Literal

NormalizationPreset = Literal["none", "minimal", "default", "aggressive"]


def casefold(value: str, locale: str = "") -> str:
    """Apply Unicode case folding with optional locale support.

    Converts text to lowercase using Unicode-aware case folding rules.
    Supports Turkish locale special-casing for dotted/dotless i handling.

    Args:
        value: String to casefold
        locale: Locale code for special-case handling (default: "" for simple casefold)
                Currently supports "tr" for Turkish locale.

    Returns:
        Casefolded string

    Locale Handling:
        - Default (locale=""): Uses Python's str.casefold() (Unicode-aware)
        - Turkish (locale="tr"): Handles İ→i and I→ı correctly
        - Invalid locale: Falls back to simple casefold (no error raised)

    Examples:
        >>> casefold("Hello World")
        'hello world'
        >>> casefold("CAFÉ")
        'café'
        >>> casefold("İstanbul", locale="tr")
        'istanbul'
        >>> casefold("ISTANBUL", locale="tr")
        'ıstanbul'

    Note:
        Turkish locale handling is "best-effort" - implements common cases
        but may not cover all edge cases. For production Turkish text
        processing, consider dedicated locale libraries.
    """
    if not value:
        return value

    if locale == "tr":
        result = ""
        for char in value:
            if char == "İ":
                result += "i"
            elif char == "I":
                result += "ı"
            elif char == "i":
                result += "i"
            elif char == "ı":
                result += "ı"
            else:
                result += char.lower()
        return result

    return value.casefold()


def strip_accents(value: str) -> str:
    """Remove diacritical marks (accents) from text.

    Uses Unicode NFD normalization to decompose characters, then filters
    out combining marks (Unicode category Mn - Nonspacing_Mark), and
    recomposes to NFC form.

    Args:
        value: String to process

    Returns:
        String with accents removed

    Algorithm:
        1. Normalize to NFD (decompose combining characters)
        2. Filter out category Mn (Nonspacing_Mark)
        3. Recompose to NFC for standard form

    Examples:
        >>> strip_accents("café")
        'cafe'
        >>> strip_accents("naïve")
        'naive'
        >>> strip_accents("Zürich")
        'Zurich'
        >>> strip_accents("résumé")
        'resume'

    Note:
        Only removes combining marks (Mn category). Does not handle
        precomposed characters that are fundamentally different letters
        (e.g., Æ, Œ, ß remain unchanged).
    """
    if not value:
        return value

    nfd = unicodedata.normalize("NFD", value)

    without_accents = "".join(char for char in nfd if unicodedata.category(char) != "Mn")

    return unicodedata.normalize("NFC", without_accents)


def apply_normalization_preset(text: str, preset: NormalizationPreset) -> str:
    """Apply normalization preset to text.

    Presets provide standard normalization pipelines for common use cases,
    following Foundry Similarity v2.0.0 standard.

    Args:
        text: String to normalize
        preset: Normalization level:
            - "none": No changes (returns input unchanged)
            - "minimal": NFC normalization + trim whitespace
            - "default": NFC + casefold + trim (recommended)
            - "aggressive": NFKD + casefold + strip accents + remove punctuation + trim

    Returns:
        Normalized string according to preset

    Raises:
        ValueError: If preset is not one of the valid options

    Examples:
        >>> apply_normalization_preset("  Hello  ", "none")
        '  Hello  '
        >>> apply_normalization_preset("  Café-Zürich!  ", "minimal")
        'Café-Zürich!'
        >>> apply_normalization_preset("  Café-Zürich!  ", "default")
        'café-zürich!'
        >>> apply_normalization_preset("  Café-Zürich!  ", "aggressive")
        'cafezurich'

    Preset Details:
        - none: Identity function, preserves input exactly
        - minimal: Unicode NFC + trim (preserves case and accents)
        - default: NFC + casefold + trim (case-insensitive, keeps accents)
        - aggressive: NFKD + casefold + strip accents + remove punctuation + trim
          (maximum normalization for fuzzy matching)

    Note:
        Newlines and internal whitespace are preserved in all presets.
        Only leading/trailing whitespace is trimmed.
    """
    if preset == "none":
        return text

    if preset == "minimal":
        normalized = unicodedata.normalize("NFC", text)
        return normalized.strip()

    if preset == "default":
        normalized = unicodedata.normalize("NFC", text)
        normalized = normalized.strip()
        normalized = casefold(normalized, locale="")
        return normalized

    if preset == "aggressive":
        normalized = unicodedata.normalize("NFKD", text)
        normalized = normalized.strip()
        normalized = casefold(normalized, locale="")
        normalized = strip_accents(normalized)
        normalized = re.sub(r"[^\w\s\r\n]", "", normalized)
        return normalized

    raise ValueError(
        f"Invalid normalization preset: {preset!r}. "
        f"Valid options: 'none', 'minimal', 'default', 'aggressive'"
    )


def normalize(
    value: str,
    *,
    preset: NormalizationPreset | None = None,
    strip_accents_flag: bool = False,
    locale: str = "",
) -> str:
    """Normalize text through trim, casefold, and optional accent stripping.

    Applies a normalization pipeline suitable for fuzzy matching and
    case-insensitive comparison. Supports both preset-based and legacy
    parameter-based normalization.

    Args:
        value: String to normalize
        preset: Normalization preset (v2.0.0+):
            - "none": No changes
            - "minimal": NFC + trim
            - "default": NFC + casefold + trim
            - "aggressive": NFKD + casefold + strip accents + remove punctuation + trim
            If None, uses legacy parameter-based normalization.
        strip_accents_flag: (Legacy) If True, remove diacritical marks (default: False)
        locale: (Legacy) Locale code for case folding (default: "" for simple casefold)

    Returns:
        Normalized string

    Examples:
        # Preset-based normalization (v2.0.0+)
        >>> normalize("  Hello World  ", preset="default")
        'hello world'
        >>> normalize("  Café-Zürich!  ", preset="aggressive")
        'cafezurich'

        # Legacy parameter-based normalization
        >>> normalize("  Hello World  ")
        'hello world'
        >>> normalize("  Café  ", strip_accents_flag=True)
        'cafe'
        >>> normalize("İSTANBUL", locale="tr")
        'istanbul'

    Note:
        If preset is provided, it takes precedence over strip_accents_flag and locale.
        For backward compatibility, when preset=None, uses legacy pipeline:
        1. Trim leading/trailing whitespace
        2. Apply Unicode case folding (with optional locale)
        3. Optionally strip accents
    """
    if not value:
        return value

    if preset is not None:
        return apply_normalization_preset(value, preset)

    result = value.strip()
    result = casefold(result, locale=locale)

    if strip_accents_flag:
        result = strip_accents(result)

    return result


def equals_ignore_case(a: str, b: str, *, strip_accents_flag: bool = False) -> bool:
    """Compare strings for equality with normalization.

    Normalizes both strings and compares for exact equality. Useful for
    case-insensitive matching and optional accent-insensitive matching.

    Args:
        a: First string
        b: Second string
        strip_accents_flag: If True, ignore accents in comparison (default: False)

    Returns:
        True if normalized strings are equal, False otherwise

    Examples:
        >>> equals_ignore_case("Hello", "hello")
        True
        >>> equals_ignore_case("Café", "cafe", strip_accents_flag=True)
        True
        >>> equals_ignore_case("Café", "cafe", strip_accents_flag=False)
        False
        >>> equals_ignore_case("  WORLD  ", "world")
        True

    Note:
        Uses default (empty) locale for case folding. For locale-specific
        comparisons, use normalize() directly with locale parameter.
    """
    normalized_a = normalize(a, strip_accents_flag=strip_accents_flag, locale="")
    normalized_b = normalize(b, strip_accents_flag=strip_accents_flag, locale="")
    return normalized_a == normalized_b
