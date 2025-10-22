"""
Suggestion ranking and filtering for fuzzy matching.

Provides ranked suggestions based on similarity scores with configurable
thresholds and result limits.
"""

from ._distance import score
from ._normalize import normalize
from .models import Suggestion


def suggest(
    input: str,
    candidates: list[str],
    *,
    min_score: float = 0.6,
    max_suggestions: int = 3,
    normalize_text: bool = True,
) -> list[Suggestion]:
    """Generate ranked suggestions from candidates based on similarity.

    Calculates similarity scores for each candidate, filters by minimum score,
    sorts by score (descending) then alphabetically for ties, and returns the
    top suggestions.

    Args:
        input: Input string to match against
        candidates: List of candidate strings to rank
        min_score: Minimum similarity score threshold (default: 0.6)
        max_suggestions: Maximum number of suggestions to return (default: 3)
        normalize_text: If True, normalize input and candidates before comparison
                       (default: True)

    Returns:
        List of Suggestion objects sorted by score (desc), then value (asc)

    Sorting Behavior:
        Suggestions are sorted first by score (descending), then by value
        (ascending) for deterministic tie-breaking. This ensures consistent
        results when multiple candidates have the same similarity score.

    Examples:
        >>> suggestions = suggest("docscrib", ["docscribe", "crucible-shim"])
        >>> suggestions[0].value
        'docscribe'
        >>> suggestions[0].score > 0.8
        True

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

        >>> # Tie-breaking by alphabetical order
        >>> suggestions = suggest("tset", ["test", "set", "rest"])
        >>> # Both "test" and "set" have same score, sorted alphabetically
        >>> [s.value for s in suggestions if s.score == 0.75]
        ['set', 'test']

    Note:
        Empty input or empty candidates list returns empty list.
        Normalization uses default locale (no Turkish special-casing).
    """
    if not input or not candidates:
        return []

    normalized_input = normalize(input) if normalize_text else input

    scored_candidates: list[Suggestion] = []

    for candidate in candidates:
        normalized_candidate = normalize(candidate) if normalize_text else candidate

        similarity_score = score(normalized_input, normalized_candidate)

        if similarity_score >= min_score:
            scored_candidates.append(Suggestion(score=similarity_score, value=candidate))

    scored_candidates.sort(
        key=lambda s: (-s.score, s.value.lower(), sum(1 for c in s.value if c.isupper()), s.value)
    )

    return scored_candidates[:max_suggestions]
