#!/usr/bin/env python3
"""Compute authoritative similarity scores for Foundry Similarity v2 fixtures.

⚠️  BOOTSTRAP ONLY - Use validate_similarity_fixtures.py for ongoing validation.

This script was used for INITIAL bootstrap to compute fixture values from placeholders.
It OVERWRITES the file with PyYAML formatting, which differs from Crucible's format.

Once Crucible owns the fixture file, use validate_similarity_fixtures.py instead,
which validates values WITHOUT modifying the file or changing its formatting.

This script reads the similarity-fixtures.yaml file, computes missing values
for Levenshtein, Damerau-Levenshtein (both OSA and unrestricted variants),
Jaro-Winkler, substring matching, normalization presets, and suggestions,
then outputs updated fixture values.

Damerau-Levenshtein Variants:
    - damerau_osa: Uses OSA (Optimal String Alignment) - cannot edit same substring twice
    - damerau_unrestricted: Uses unrestricted Damerau - allows full edit distance with transpositions

Dependencies:
    - rapidfuzz>=3.10.0 (provides distance.OSA and distance.DamerauLevenshtein)
    - pyyaml>=6.0.3

Usage:
    # For initial bootstrap (overwrites file):
    uv run python scripts/bootstrap/compute_similarity_fixtures.py

    # For validation (preserves formatting):
    uv run python scripts/bootstrap/validate_similarity_fixtures.py
"""

import re
import unicodedata
from pathlib import Path
from typing import Any, Literal

import yaml

try:
    from rapidfuzz import distance
except ImportError:
    print("ERROR: rapidfuzz not installed. Run: uv sync --all-extras")
    exit(1)


def normalize_unicode(
    text: str, form: Literal["NFC", "NFD", "NFKC", "NFKD"] = "NFC"
) -> str:
    """Normalize Unicode string using specified form (NFC, NFKD, etc.)."""
    return unicodedata.normalize(form, text)


def strip_accents(text: str) -> str:
    """Remove diacritical marks from text."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def remove_punctuation(text: str) -> str:
    """Remove punctuation and keep only alphanumeric and whitespace."""
    return re.sub(r"[^\w\s]", "", text)


def apply_normalization_preset(text: str, preset: str) -> str:
    """Apply normalization preset to text.

    Presets:
    - none: No normalization (unchanged)
    - minimal: NFC + trim
    - default: NFC + casefold + trim
    - aggressive: NFKD + casefold + strip accents + remove punctuation + trim
    """
    if preset == "none":
        return text
    elif preset == "minimal":
        return normalize_unicode(text, "NFC").strip()
    elif preset == "default":
        return normalize_unicode(text, "NFC").casefold().strip()
    elif preset == "aggressive":
        text = normalize_unicode(text, "NFKD")
        text = text.casefold()
        text = strip_accents(text)
        text = remove_punctuation(text)
        return text.strip()
    else:
        raise ValueError(f"Unknown normalization preset: {preset}")


def compute_levenshtein(input_a: str, input_b: str) -> dict[str, float]:
    """Compute Levenshtein distance and normalized score."""
    dist = distance.Levenshtein.distance(input_a, input_b)
    max_len = max(len(input_a), len(input_b))
    score = 1.0 - (dist / max_len) if max_len > 0 else 1.0
    return {"distance": dist, "score": score}


def compute_damerau_osa(input_a: str, input_b: str) -> dict[str, float]:
    """Compute Damerau-Levenshtein OSA (Optimal String Alignment) distance and normalized score.

    Uses OSA variant which does not allow the same substring to be edited more than once.
    This differs from unrestricted Damerau-Levenshtein on certain edge cases.
    """
    dist = distance.OSA.distance(input_a, input_b)
    max_len = max(len(input_a), len(input_b))
    score = 1.0 - (dist / max_len) if max_len > 0 else 1.0
    return {"distance": dist, "score": score}


def compute_damerau_unrestricted(input_a: str, input_b: str) -> dict[str, float]:
    """Compute unrestricted Damerau-Levenshtein distance and normalized score.

    Uses unrestricted variant which allows full edit distance with transpositions.
    No restriction on editing the same substring multiple times.
    """
    dist = distance.DamerauLevenshtein.distance(input_a, input_b)
    max_len = max(len(input_a), len(input_b))
    score = 1.0 - (dist / max_len) if max_len > 0 else 1.0
    return {"distance": dist, "score": score}


def compute_jaro_winkler(
    input_a: str, input_b: str, prefix_weight: float = 0.1
) -> float:
    """Compute Jaro-Winkler similarity score.

    Args:
        input_a: First string
        input_b: Second string
        prefix_weight: Prefix bonus weight (default 0.1 per Jaro-Winkler standard)

    Returns:
        Similarity score between 0.0 and 1.0
    """
    return distance.JaroWinkler.similarity(
        input_a, input_b, prefix_weight=prefix_weight
    )


def find_longest_common_substring(needle: str, haystack: str) -> tuple[int, int, int]:
    """Find longest common substring and return (start, end, length).

    Returns:
        Tuple of (start_index, end_index, length) in haystack, or (-1, -1, 0) if none found
    """
    if not needle or not haystack:
        return (-1, -1, 0)

    m, n = len(needle), len(haystack)
    max_len = 0
    end_pos = 0

    # Dynamic programming table for LCS
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if needle[i - 1] == haystack[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > max_len:
                    max_len = dp[i][j]
                    end_pos = j

    if max_len == 0:
        return (-1, -1, 0)

    start = end_pos - max_len
    return (start, end_pos, max_len)


def compute_substring(needle: str, haystack: str) -> dict[str, Any]:
    """Compute substring match score and range.

    Score is: length_of_match / max(len(needle), len(haystack))
    """
    start, end, length = find_longest_common_substring(needle, haystack)

    max_len = max(len(needle), len(haystack))
    score = length / max_len if max_len > 0 else 0.0

    result: dict[str, Any] = {"score": score}
    if length > 0:
        result["range"] = {"start": start, "end": end}

    return result


def compute_suggestion_scores(
    query: str,
    candidates: list[str],
    metric: str,
    normalize_preset: str = "default",
    min_score: float = 0.0,
    max_suggestions: int = 10,
    prefer_prefix: bool = False,
) -> list[dict[str, Any]]:
    """Compute suggestion scores for a query against candidates.

    Args:
        query: Search query
        candidates: List of candidate strings
        metric: Similarity metric ("levenshtein", "jaro_winkler", "substring")
        normalize_preset: Normalization preset to apply
        min_score: Minimum score threshold
        max_suggestions: Maximum number of suggestions to return
        prefer_prefix: Whether to prefer prefix matches (for jaro_winkler)

    Returns:
        List of suggestions with value and score, sorted by score descending
    """
    # Normalize query
    normalized_query = apply_normalization_preset(query, normalize_preset)

    results = []
    for candidate in candidates:
        # Normalize candidate
        normalized_candidate = apply_normalization_preset(candidate, normalize_preset)

        # Compute score based on metric
        if metric == "levenshtein":
            result = compute_levenshtein(normalized_query, normalized_candidate)
            score = result["score"]
        elif metric == "jaro_winkler":
            prefix_weight = 0.1 if prefer_prefix else 0.1  # Standard weight
            score = compute_jaro_winkler(
                normalized_query, normalized_candidate, prefix_weight
            )
        elif metric == "substring":
            result = compute_substring(normalized_query, normalized_candidate)
            score = result["score"]
        else:
            raise ValueError(f"Unknown metric: {metric}")

        if score >= min_score:
            results.append({"value": candidate, "score": score})

    # Sort by score descending, then alphabetically for ties
    results.sort(key=lambda x: (-x["score"], x["value"]))

    return results[:max_suggestions]


def process_test_case(test_case: dict) -> dict:
    """Process a single test case and compute missing values."""
    category = test_case.get("category")

    if category == "levenshtein":
        # Already complete in fixtures
        pass

    elif category == "damerau_osa":
        for case in test_case.get("cases", []):
            input_a = case["input_a"]
            input_b = case["input_b"]
            result = compute_damerau_osa(input_a, input_b)
            case["expected_distance"] = result["distance"]
            case["expected_score"] = result["score"]

    elif category == "damerau_unrestricted":
        for case in test_case.get("cases", []):
            input_a = case["input_a"]
            input_b = case["input_b"]
            result = compute_damerau_unrestricted(input_a, input_b)
            case["expected_distance"] = result["distance"]
            case["expected_score"] = result["score"]

    elif category == "jaro_winkler":
        for case in test_case.get("cases", []):
            input_a = case["input_a"]
            input_b = case["input_b"]
            score = compute_jaro_winkler(input_a, input_b)
            case["expected_score"] = score

    elif category == "substring":
        # Already complete in fixtures (manually computed)
        pass

    elif category == "normalization_presets":
        for case in test_case.get("cases", []):
            input_text = case["input"]
            preset = case["preset"]
            expected = apply_normalization_preset(input_text, preset)
            case["expected"] = expected

    elif category == "suggestions":
        for case in test_case.get("cases", []):
            query = case["input"]
            candidates = case["candidates"]
            options = case.get("options", {})

            suggestions = compute_suggestion_scores(
                query,
                candidates,
                metric=options.get("metric", "levenshtein"),
                normalize_preset=options.get("normalize_preset", "default"),
                min_score=options.get("min_score", 0.0),
                max_suggestions=options.get("max_suggestions", 10),
                prefer_prefix=options.get("prefer_prefix", False),
            )

            case["expected"] = suggestions

    return test_case


def main():
    """Compute similarity values for all fixtures.

    NOTE: This script is designed to COMPUTE values for initial bootstrap.
    Once Crucible owns the fixture format, use validate_similarity_fixtures.py
    to verify values without modifying the file.
    """
    # Load fixtures
    fixtures_path = Path("config/crucible-py/library/foundry/similarity-fixtures.yaml")
    print(f"Loading fixtures from: {fixtures_path}")
    print("\n⚠️  WARNING: This will overwrite the file with PyYAML formatting.")
    print(
        "    Use validate_similarity_fixtures.py instead to preserve Crucible formatting.\n"
    )

    with open(fixtures_path) as f:
        data = yaml.safe_load(f)

    print(f"📊 Processing {len(data.get('test_cases', []))} test case categories...")

    # Process each test case category
    for test_case in data.get("test_cases", []):
        category = test_case.get("category", "unknown")
        num_cases = len(test_case.get("cases", []))
        print(f"  • {category}: {num_cases} cases")
        process_test_case(test_case)

    # Update notes to indicate values are computed
    if "notes" in data:
        notes = data["notes"]
        notes = notes.replace(
            'PLACEHOLDER values below are marked with "# PYFULMEN_COMPUTE" comments.\n'
            "  These must be replaced with actual computed values before language implementations begin.",
            "Values computed using rapidfuzz 3.14.1 (Python reference implementation).",
        )
        data["notes"] = notes

    # Write updated fixtures
    output_path = fixtures_path
    print(f"\n✍️  Writing updated fixtures to: {output_path}")
    print("    (Note: YAML formatting will be changed by PyYAML dumper)")

    with open(output_path, "w") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=1000,  # Prevent line wrapping for long strings
        )

    print("\n✅ Done! All similarity values computed and updated.")
    print("\n📋 Summary:")
    print(f"   - Test case categories: {len(data.get('test_cases', []))}")
    total_cases = sum(len(tc.get("cases", [])) for tc in data.get("test_cases", []))
    print(f"   - Total test cases: {total_cases}")
    print("\n🔍 Next steps:")
    print(f"   1. Review the computed values in {fixtures_path}")
    print(
        "   2. If Crucible owns the format, use validate_similarity_fixtures.py instead"
    )
    print(
        "   3. Run: uv run pytest tests/unit/foundry/similarity (once tests are updated)"
    )
    print("   4. Report completion to EA Steward for Crucible sync")


if __name__ == "__main__":
    main()
