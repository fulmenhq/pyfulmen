"""
Levenshtein distance and similarity scoring for text comparison.

Implements Wagner-Fischer dynamic programming algorithm with two-row
optimization for memory efficiency.
"""


def distance(a: str, b: str) -> int:
    """Calculate Levenshtein edit distance between two strings.

    Uses dynamic programming to compute the minimum number of single-character
    edits (insertions, deletions, or substitutions) required to transform
    string a into string b.

    Args:
        a: First string
        b: Second string

    Returns:
        Edit distance as non-negative integer

    Algorithm:
        Wagner-Fischer dynamic programming with two-row optimization.
        Time complexity: O(m×n) where m, n are string lengths.
        Space complexity: O(min(m,n)) using two-row approach.

    Examples:
        >>> distance("kitten", "sitting")
        3
        >>> distance("saturday", "sunday")
        3
        >>> distance("", "")
        0
        >>> distance("test", "test")
        0
        >>> distance("", "hello")
        5

    Note:
        This is case-sensitive. Use normalize() before calling if you need
        case-insensitive comparison.
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

            current_row[i] = min(
                previous_row[i] + 1, current_row[i - 1] + 1, previous_row[i - 1] + cost
            )

        previous_row, current_row = current_row, previous_row

    return previous_row[len_a]


def score(a: str, b: str) -> float:
    """Calculate normalized similarity score between two strings.

    Returns a similarity score in range [0.0, 1.0] where:
    - 0.0 = completely different
    - 1.0 = identical

    Formula: 1.0 - distance(a, b) / max(len(a), len(b))

    Args:
        a: First string
        b: Second string

    Returns:
        Similarity score from 0.0 (no match) to 1.0 (perfect match)

    Examples:
        >>> score("kitten", "sitting")
        0.5714285714285714
        >>> score("test", "test")
        1.0
        >>> score("", "")
        1.0
        >>> score("hello", "helo")
        0.8

    Note:
        Empty strings are considered identical (score = 1.0).
        This is case-sensitive. Use normalize() before calling if needed.
    """
    len_a = len(a)
    len_b = len(b)

    if len_a == 0 and len_b == 0:
        return 1.0

    max_len = max(len_a, len_b)

    if max_len == 0:
        return 1.0

    edit_distance = distance(a, b)

    return 1.0 - (edit_distance / max_len)
