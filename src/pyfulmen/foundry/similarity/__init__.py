"""
Text similarity and normalization utilities for PyFulmen.

This module provides Levenshtein distance calculation, normalized similarity
scoring, suggestion ranking, and Unicode-aware text normalization following
the Foundry text similarity standard.

Public API:
    distance(a, b) -> int - Calculate Levenshtein edit distance
    score(a, b) -> float - Calculate normalized similarity score (0.0-1.0)
    suggest(input, candidates, ...) -> list[Suggestion] - Rank suggestions by similarity
    normalize(value, ...) -> str - Normalize text (trim, casefold, strip accents)
    casefold(value, locale) -> str - Unicode casefold with locale support
    equals_ignore_case(a, b, ...) -> bool - Case-insensitive equality
    strip_accents(value) -> str - Remove combining accent marks

    Suggestion - Data model for ranked suggestions

Example:
    >>> from pyfulmen.foundry import similarity
    >>>
    >>> # Calculate edit distance
    >>> similarity.distance("kitten", "sitting")
    3
    >>>
    >>> # Calculate normalized similarity score
    >>> similarity.score("hello", "helo")
    0.8
    >>>
    >>> # Get ranked suggestions
    >>> suggestions = similarity.suggest(
    ...     "cofnig",
    ...     ["config", "configure", "confirm"],
    ...     min_score=0.6,
    ...     max_suggestions=3
    ... )
    >>> suggestions[0].value
    'config'
    >>> suggestions[0].score
    0.8333333333333334
    >>>
    >>> # Normalize text
    >>> similarity.normalize("  Café  ", strip_accents=True)
    'cafe'

References:
    - Standard: docs/crucible-py/standards/library/foundry/similarity.md
    - Fixtures: config/crucible-py/library/foundry/similarity-fixtures.yaml
    - Schema: schemas/crucible-py/library/foundry/v2.0.0/similarity.schema.json
"""

from ._distance import distance, score, substring_match
from ._normalize import (
    apply_normalization_preset,
    casefold,
    equals_ignore_case,
    normalize,
    strip_accents,
)
from ._suggest import suggest
from .models import Suggestion

__all__ = [
    "Suggestion",
    "distance",
    "score",
    "substring_match",
    "suggest",
    "apply_normalization_preset",
    "casefold",
    "normalize",
    "strip_accents",
    "equals_ignore_case",
]
