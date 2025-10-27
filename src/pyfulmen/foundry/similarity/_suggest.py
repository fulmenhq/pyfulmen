"""
Suggestion ranking and filtering for fuzzy matching.

Provides ranked suggestions based on similarity scores with configurable
thresholds and result limits, supporting multiple similarity metrics and
normalization presets.
"""

from ._distance import MetricType, score, substring_match
from ._normalize import NormalizationPreset, apply_normalization_preset, normalize
from .models import Suggestion


def suggest(
    input: str,
    candidates: list[str],
    *,
    min_score: float = 0.6,
    max_suggestions: int = 3,
    normalize_text: bool = True,
    metric: MetricType = "levenshtein",
    normalize_preset: NormalizationPreset | None = None,
    prefer_prefix: bool = False,
    jaro_prefix_scale: float = 0.1,
    jaro_max_prefix: int = 4,
) -> list[Suggestion]:
    """Generate ranked suggestions from candidates based on similarity.

    Calculates similarity scores for each candidate using the specified metric,
    filters by minimum score, sorts by score (descending) then alphabetically
    for ties, and returns the top suggestions.

    Args:
        input: Input string to match against
        candidates: List of candidate strings to rank
        min_score: Minimum similarity score threshold (default: 0.6)
        max_suggestions: Maximum number of suggestions to return (default: 3)
        normalize_text: (Legacy) If True, normalize using default preset (default: True)
                       Ignored if normalize_preset is provided.
        metric: Distance metric to use (default: "levenshtein")
            - "levenshtein": Standard edit distance
            - "damerau_osa": Damerau-Levenshtein OSA (typo correction)
            - "damerau_unrestricted": Damerau-Levenshtein unrestricted
            - "jaro_winkler": Jaro-Winkler similarity (name matching)
            - "substring": Longest common substring
        normalize_preset: Normalization preset to apply (default: None)
            - None: Use legacy normalize_text behavior
            - "none": No normalization
            - "minimal": NFC + trim
            - "default": NFC + casefold + trim (recommended)
            - "aggressive": NFKD + casefold + strip accents + remove punctuation + trim
        prefer_prefix: If True, apply bonus for prefix matches (default: False)
        jaro_prefix_scale: Jaro-Winkler prefix scaling factor (default: 0.1)
        jaro_max_prefix: Jaro-Winkler max prefix length (default: 4)

    Returns:
        List of Suggestion objects sorted by score (desc), then value (asc)

    Sorting Behavior:
        Suggestions are sorted first by score (descending), then by value
        (ascending) for deterministic tie-breaking. This ensures consistent
        results when multiple candidates have the same similarity score.

    Enhanced Features (v2.0):
        - Multiple similarity metrics (Damerau-Levenshtein, Jaro-Winkler, substring)
        - Preset-based normalization (none, minimal, default, aggressive)
        - Optional prefix preference bonus
        - Metadata population (matched_range for substring, normalized_value)

    Examples:
        >>> # Basic usage (v1.0 compatibility)
        >>> suggestions = suggest("docscrib", ["docscribe", "crucible-shim"])
        >>> suggestions[0].value
        'docscribe'
        >>> suggestions[0].score > 0.8
        True

        >>> # Using Damerau-Levenshtein for typo correction
        >>> suggestions = suggest("tset", ["test", "rest"], metric="damerau_osa")
        >>> suggestions[0].value
        'test'

        >>> # Using Jaro-Winkler for name matching
        >>> suggestions = suggest("Jon", ["John", "Jane"], metric="jaro_winkler")
        >>> suggestions[0].value
        'John'

        >>> # Using aggressive normalization
        >>> suggestions = suggest("café", ["Cafe", "cache"], normalize_preset="aggressive")
        >>> suggestions[0].value
        'Cafe'

        >>> # Case-insensitive matching (normalize=True by default)
        >>> suggestions = suggest("DOCSCRIBE", ["docscribe", "Docscribe"])
        >>> len(suggestions)
        2
        >>> suggestions[0].score
        1.0

        >>> # No matches above threshold
        >>> suggestions = suggest("xyz", ["abc", "def"], min_score=0.6)
        >>> len(suggestions)
        0

    Note:
        Empty input or empty candidates list returns empty list.
        When normalize_preset is provided, it takes precedence over normalize_text.
        Legacy normalize_text parameter is maintained for backward compatibility.
    """
    if not input or not candidates:
        return []

    if normalize_preset is not None:
        normalized_input = apply_normalization_preset(input, normalize_preset)
    elif normalize_text:
        normalized_input = normalize(input)
    else:
        normalized_input = input

    scored_candidates: list[Suggestion] = []

    for candidate in candidates:
        if normalize_preset is not None:
            normalized_candidate = apply_normalization_preset(candidate, normalize_preset)
        elif normalize_text:
            normalized_candidate = normalize(candidate)
        else:
            normalized_candidate = candidate

        if metric == "substring":
            matched_range, similarity_score = substring_match(
                normalized_input, normalized_candidate
            )
            if similarity_score >= min_score:
                norm_val = normalized_candidate if normalize_preset or normalize_text else None
                suggestion = Suggestion(
                    score=similarity_score,
                    value=candidate,
                    matched_range=matched_range,
                    normalized_value=norm_val,
                )
                scored_candidates.append(suggestion)
        else:
            similarity_score = score(
                normalized_input,
                normalized_candidate,
                metric=metric,
                jaro_prefix_scale=jaro_prefix_scale,
                jaro_max_prefix=jaro_max_prefix,
            )

            if similarity_score >= min_score:
                norm_val = normalized_candidate if normalize_preset or normalize_text else None
                is_prefix = normalized_candidate.startswith(normalized_input)
                suggestion = Suggestion(
                    score=similarity_score,
                    value=candidate,
                    normalized_value=norm_val,
                    reason="prefix_match" if (prefer_prefix and is_prefix) else None,
                )
                scored_candidates.append(suggestion)

    if prefer_prefix:
        scored_candidates.sort(
            key=lambda s: (
                -s.score,
                0 if s.reason == "prefix_match" else 1,
                s.value.lower(),
                sum(1 for c in s.value if c.isupper()),
                s.value,
            )
        )
    else:
        scored_candidates.sort(
            key=lambda s: (
                -s.score,
                s.value.lower(),
                sum(1 for c in s.value if c.isupper()),
                s.value,
            )
        )

    return scored_candidates[:max_suggestions]
