"""
Text normalization utilities for Unicode-aware string processing.

Provides case folding, accent stripping, and combined normalization pipelines
following the Foundry text similarity standard.
"""

import unicodedata


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


def normalize(value: str, *, strip_accents_flag: bool = False, locale: str = "") -> str:
    """Normalize text through trim, casefold, and optional accent stripping.

    Applies a normalization pipeline suitable for fuzzy matching and
    case-insensitive comparison.

    Args:
        value: String to normalize
        strip_accents_flag: If True, remove diacritical marks (default: False)
        locale: Locale code for case folding (default: "" for simple casefold)

    Returns:
        Normalized string

    Pipeline:
        1. Trim leading/trailing whitespace
        2. Apply Unicode case folding (with optional locale)
        3. Optionally strip accents

    Examples:
        >>> normalize("  Hello World  ")
        'hello world'
        >>> normalize("  Café  ", strip_accents_flag=True)
        'cafe'
        >>> normalize("İSTANBUL", locale="tr")
        'istanbul'
        >>> normalize("  RÉSUMÉ  ", strip_accents_flag=True)
        'resume'

    Note:
        Parameter name is strip_accents_flag (not strip_accents) to avoid
        naming conflict with the strip_accents() function.
    """
    if not value:
        return value

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
