"""
Data models for text similarity operations.

This module provides immutable data structures for similarity calculations,
following FulmenHQ foundry standards for text matching and suggestions.
"""

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Suggestion:
    """A ranked suggestion with similarity score and optional metadata.

    Represents a candidate string matched against input text with a normalized
    similarity score. Used for "Did you mean...?" prompts, fuzzy search results,
    and error correction suggestions.

    Attributes:
        score: Similarity score from 0.0 (no match) to 1.0 (perfect match)
        value: The suggested string
        matched_range: Optional (start, end) tuple for substring matches
        reason: Optional reason code (e.g., "prefix_match", "typo_correction")
        normalized_value: Optional normalized form of the value (when normalization applied)

    Note:
        Instances are ordered by score descending, then value ascending for
        deterministic sorting when scores are equal. This is achieved by
        defining score first in the dataclass (with order=True).

        The optional fields (matched_range, reason, normalized_value) default to None
        and are excluded from ordering comparisons.

    Example:
        >>> # Basic suggestion (v1.0 compatibility)
        >>> suggestion = Suggestion(score=0.85, value="example")
        >>> suggestion.value
        'example'
        >>> suggestion.score
        0.85

        >>> # Enhanced suggestion with metadata (v2.0)
        >>> suggestion = Suggestion(
        ...     score=0.95,
        ...     value="docscribe",
        ...     reason="typo_correction",
        ...     normalized_value="docscribe"
        ... )
        >>> suggestion.reason
        'typo_correction'

        >>> # Substring match with range
        >>> suggestion = Suggestion(
        ...     score=0.8,
        ...     value="hello world",
        ...     matched_range=(0, 5)
        ... )
        >>> suggestion.matched_range
        (0, 5)

        >>> # Sorting behavior
        >>> suggestions = [
        ...     Suggestion(score=0.7, value="zebra"),
        ...     Suggestion(score=0.9, value="alpha"),
        ...     Suggestion(score=0.7, value="alpha"),
        ... ]
        >>> sorted(suggestions, reverse=True)
        [Suggestion(score=0.9, value='alpha', ...),
         Suggestion(score=0.7, value='alpha', ...),
         Suggestion(score=0.7, value='zebra', ...)]
    """

    score: float
    value: str
    matched_range: tuple[int, int] | None = None
    reason: str | None = None
    normalized_value: str | None = None
