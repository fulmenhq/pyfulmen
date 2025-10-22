"""
Data models for text similarity operations.

This module provides immutable data structures for similarity calculations,
following FulmenHQ foundry standards for text matching and suggestions.
"""

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Suggestion:
    """A ranked suggestion with similarity score.

    Represents a candidate string matched against input text with a normalized
    similarity score. Used for "Did you mean...?" prompts, fuzzy search results,
    and error correction suggestions.

    Attributes:
        score: Similarity score from 0.0 (no match) to 1.0 (perfect match)
        value: The suggested string

    Note:
        Instances are ordered by score descending, then value ascending for
        deterministic sorting when scores are equal. This is achieved by
        defining score first in the dataclass (with order=True).

    Example:
        >>> suggestion = Suggestion(score=0.85, value="example")
        >>> suggestion.value
        'example'
        >>> suggestion.score
        0.85

        >>> suggestions = [
        ...     Suggestion(score=0.7, value="zebra"),
        ...     Suggestion(score=0.9, value="alpha"),
        ...     Suggestion(score=0.7, value="alpha"),
        ... ]
        >>> sorted(suggestions, reverse=True)
        [Suggestion(score=0.9, value='alpha'),
         Suggestion(score=0.7, value='alpha'),
         Suggestion(score=0.7, value='zebra')]
    """

    score: float
    value: str
