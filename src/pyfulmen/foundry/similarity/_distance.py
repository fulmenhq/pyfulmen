"""
Text similarity distance and scoring with multiple metrics.

Implements multiple string distance algorithms:
- Levenshtein (default): insertions, deletions, substitutions
- Damerau-Levenshtein OSA: adds adjacent transpositions (Optimal String Alignment)
- Damerau-Levenshtein Unrestricted: unrestricted transpositions
- Jaro-Winkler: similarity for short strings with common prefixes
- Substring: longest common substring matching

References:
    - Levenshtein: Wagner-Fischer dynamic programming algorithm
    - Damerau-Levenshtein: OSA and unrestricted variants
    - Jaro-Winkler: Similarity metric for short strings
    - Substring: Longest common substring via dynamic programming
"""

from typing import Literal

MetricType = Literal[
    "levenshtein",
    "damerau_osa",
    "damerau_unrestricted",
    "jaro_winkler",
    "substring",
]


def distance(a: str, b: str, metric: MetricType = "levenshtein") -> int:
    """Calculate edit distance between two strings using specified metric.

    Computes the minimum number of single-character edits required to transform
    string a into string b. Supported metrics include Levenshtein (default),
    Damerau-Levenshtein variants (OSA and unrestricted), and substring matching.

    Args:
        a: First string
        b: Second string
        metric: Distance metric to use (default: "levenshtein")
            - "levenshtein": insertions, deletions, substitutions
            - "damerau_osa": adds adjacent transpositions (Optimal String Alignment)
            - "damerau_unrestricted": unrestricted transpositions
            - "jaro_winkler": raises ValueError (use score() for similarity)
            - "substring": raises ValueError (use substring_match() for LCS)

    Returns:
        Edit distance as non-negative integer

    Raises:
        ValueError: If metric is invalid or not applicable for distance calculation

    Algorithm:
        Levenshtein: Wagner-Fischer dynamic programming with two-row optimization.
        Damerau OSA: Extended DP with transposition tracking.
        Damerau Unrestricted: Full DP matrix with unrestricted edits.
        Time complexity: O(m×n) where m, n are string lengths.
        Space complexity: O(min(m,n)) for Levenshtein, O(m×n) for Damerau variants.

    Examples:
        >>> distance("kitten", "sitting")
        3
        >>> distance("abcd", "abdc", metric="damerau_osa")
        1
        >>> distance("CA", "ABC", metric="damerau_osa")
        3
        >>> distance("CA", "ABC", metric="damerau_unrestricted")
        2

    Note:
        This is case-sensitive. Use normalize() before calling if you need
        case-insensitive comparison.
    """
    if metric == "jaro_winkler":
        raise ValueError(
            "jaro_winkler metric produces similarity scores, not distances. "
            "Use score(a, b, metric='jaro_winkler') instead."
        )
    if metric == "substring":
        raise ValueError("substring metric does not produce distances. Use substring_match(needle, haystack) instead.")

    if metric == "levenshtein":
        return _levenshtein_distance(a, b)
    elif metric == "damerau_osa":
        return _damerau_osa_distance(a, b)
    elif metric == "damerau_unrestricted":
        return _damerau_unrestricted_distance(a, b)
    else:
        raise ValueError(
            f"Invalid metric: {metric!r}. Valid options: 'levenshtein', 'damerau_osa', 'damerau_unrestricted'"
        )


def _levenshtein_distance(a: str, b: str) -> int:
    """Calculate Levenshtein edit distance using Wagner-Fischer algorithm.

    Internal implementation for Levenshtein distance calculation.
    """
    len_a = len(a)
    len_b = len(b)

    if len_a == 0:
        return len_b
    if len_b == 0:
        return len_a

    if len_a > len_b:
        a, b = b, a
        len_a, len_b = len_b, len_a

    previous_row = list(range(len_a + 1))
    current_row = [0] * (len_a + 1)

    for j in range(1, len_b + 1):
        current_row[0] = j

        for i in range(1, len_a + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1

            current_row[i] = min(previous_row[i] + 1, current_row[i - 1] + 1, previous_row[i - 1] + cost)

        previous_row, current_row = current_row, previous_row

    return previous_row[len_a]


def _damerau_osa_distance(a: str, b: str) -> int:
    """Calculate Damerau-Levenshtein distance using OSA algorithm.

    OSA (Optimal String Alignment) variant that allows transpositions
    but cannot edit the same substring more than once.

    Uses rapidfuzz for reference implementation.
    """
    from rapidfuzz.distance import OSA

    return OSA.distance(a, b)


def _damerau_unrestricted_distance(a: str, b: str) -> int:
    """Calculate unrestricted Damerau-Levenshtein distance.

    Unrestricted variant allows transpositions without OSA restrictions.

    Uses rapidfuzz for reference implementation.
    """
    from rapidfuzz.distance import DamerauLevenshtein

    return DamerauLevenshtein.distance(a, b)


def score(
    a: str,
    b: str,
    metric: MetricType = "levenshtein",
    jaro_prefix_scale: float = 0.1,
    jaro_max_prefix: int = 4,
) -> float:
    """Calculate normalized similarity score between two strings.

    Returns a similarity score in range [0.0, 1.0] where:
    - 0.0 = completely different
    - 1.0 = identical

    Formula (distance-based metrics):
        1.0 - distance(a, b) / max(len(a), len(b))

    Formula (similarity-based metrics):
        Direct similarity calculation (Jaro-Winkler, substring)

    Args:
        a: First string
        b: Second string
        metric: Similarity metric to use (default: "levenshtein")
            - "levenshtein": insertions, deletions, substitutions
            - "damerau_osa": adds adjacent transpositions (OSA)
            - "damerau_unrestricted": unrestricted transpositions
            - "jaro_winkler": similarity for short strings with common prefixes
            - "substring": longest common substring ratio
        jaro_prefix_scale: Jaro-Winkler prefix scaling factor (default: 0.1)
        jaro_max_prefix: Maximum prefix length for Jaro-Winkler (default: 4)

    Returns:
        Similarity score from 0.0 (no match) to 1.0 (perfect match)

    Examples:
        >>> score("kitten", "sitting")
        0.5714285714285714
        >>> score("abcd", "abdc", metric="damerau_osa")
        0.75
        >>> score("martha", "marhta", metric="jaro_winkler")
        0.9611111111111111
        >>> score("hello", "hello world", metric="substring")
        0.4545454545454545

    Note:
        Empty strings are considered identical (score = 1.0).
        This is case-sensitive. Use normalize() before calling if needed.
    """
    len_a = len(a)
    len_b = len(b)

    if len_a == 0 and len_b == 0:
        return 1.0

    if metric == "jaro_winkler":
        return _jaro_winkler_similarity(a, b, jaro_prefix_scale, jaro_max_prefix)
    elif metric == "substring":
        _, substring_score = substring_match(a, b)
        return substring_score

    max_len = max(len_a, len_b)

    if max_len == 0:
        return 1.0

    edit_distance = distance(a, b, metric=metric)

    return 1.0 - (edit_distance / max_len)


def _jaro_winkler_similarity(a: str, b: str, prefix_scale: float = 0.1, max_prefix: int = 4) -> float:
    """Calculate Jaro-Winkler similarity score.

    Internal implementation using rapidfuzz.

    Args:
        a: First string
        b: Second string
        prefix_scale: Prefix scaling factor (default: 0.1)
        max_prefix: Maximum prefix length (default: 4)

    Returns:
        Similarity score from 0.0 to 1.0
    """
    from rapidfuzz.distance import JaroWinkler

    return JaroWinkler.similarity(a, b, prefix_weight=prefix_scale, processor=None)


def substring_match(needle: str, haystack: str) -> tuple[tuple[int, int] | None, float]:
    """Find longest common substring and calculate similarity score.

    Computes the longest common substring (LCS) between needle and haystack,
    returning both the matched range in the haystack and a normalized score.

    Args:
        needle: String to search for (or compare against)
        haystack: String to search within (or compare against)

    Returns:
        Tuple of (matched_range, score) where:
        - matched_range: (start, end) indices in haystack, or None if no match
        - score: lcs_length / max(len(needle), len(haystack))

    Examples:
        >>> substring_match("hello", "hello world")
        ((0, 5), 0.4545454545454545)
        >>> substring_match("world", "hello world")
        ((6, 11), 0.4545454545454545)
        >>> substring_match("xyz", "abcdef")
        (None, 0.0)

    Algorithm:
        Dynamic programming to find longest common substring.
        Time complexity: O(m×n) where m=len(needle), n=len(haystack).
        Space complexity: O(m×n) for DP table.
    """
    len_needle = len(needle)
    len_haystack = len(haystack)

    if len_needle == 0 or len_haystack == 0:
        return (None, 0.0)

    max_len = max(len_needle, len_haystack)

    dp = [[0] * (len_haystack + 1) for _ in range(len_needle + 1)]
    lcs_length = 0
    lcs_end_pos = 0

    for i in range(1, len_needle + 1):
        for j in range(1, len_haystack + 1):
            if needle[i - 1] == haystack[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > lcs_length:
                    lcs_length = dp[i][j]
                    lcs_end_pos = j

    if lcs_length == 0:
        return (None, 0.0)

    start = lcs_end_pos - lcs_length
    end = lcs_end_pos
    score = lcs_length / max_len

    return ((start, end), score)
