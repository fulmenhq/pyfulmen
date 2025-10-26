#!/usr/bin/env python3
"""Validate similarity fixture values without modifying the file.

This script reads the similarity-fixtures.yaml file and validates that all
computed values match what rapidfuzz would produce, without overwriting the file.
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
    """Apply normalization preset to text."""
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
    """Compute Damerau-Levenshtein OSA distance and normalized score."""
    dist = distance.OSA.distance(input_a, input_b)
    max_len = max(len(input_a), len(input_b))
    score = 1.0 - (dist / max_len) if max_len > 0 else 1.0
    return {"distance": dist, "score": score}


def compute_damerau_unrestricted(input_a: str, input_b: str) -> dict[str, float]:
    """Compute unrestricted Damerau-Levenshtein distance and normalized score."""
    dist = distance.DamerauLevenshtein.distance(input_a, input_b)
    max_len = max(len(input_a), len(input_b))
    score = 1.0 - (dist / max_len) if max_len > 0 else 1.0
    return {"distance": dist, "score": score}


def compute_jaro_winkler(
    input_a: str, input_b: str, prefix_weight: float = 0.1
) -> float:
    """Compute Jaro-Winkler similarity score."""
    return distance.JaroWinkler.similarity(
        input_a, input_b, prefix_weight=prefix_weight
    )


def find_longest_common_substring(needle: str, haystack: str) -> tuple[int, int, int]:
    """Find longest common substring and return (start, end, length)."""
    if not needle or not haystack:
        return (-1, -1, 0)

    m, n = len(needle), len(haystack)
    max_len = 0
    end_pos = 0

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
    """Compute substring match score and range."""
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
    """Compute suggestion scores for a query against candidates."""
    normalized_query = apply_normalization_preset(query, normalize_preset)

    results = []
    for candidate in candidates:
        normalized_candidate = apply_normalization_preset(candidate, normalize_preset)

        if metric == "levenshtein":
            result = compute_levenshtein(normalized_query, normalized_candidate)
            score = result["score"]
        elif metric == "jaro_winkler":
            prefix_weight = 0.1 if prefer_prefix else 0.1
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

    results.sort(key=lambda x: (-x["score"], x["value"]))

    return results[:max_suggestions]


def validate_test_case(test_case: dict) -> list[str]:
    """Validate a single test case category and return list of errors."""
    category = test_case.get("category")
    errors = []

    if category == "levenshtein":
        for case in test_case.get("cases", []):
            input_a = case["input_a"]
            input_b = case["input_b"]
            result = compute_levenshtein(input_a, input_b)

            if case["expected_distance"] != result["distance"]:
                errors.append(
                    f"  ❌ {case['description']}: distance mismatch "
                    f"(expected {case['expected_distance']}, got {result['distance']})"
                )
            if abs(case["expected_score"] - result["score"]) > 1e-10:
                errors.append(
                    f"  ❌ {case['description']}: score mismatch "
                    f"(expected {case['expected_score']}, got {result['score']})"
                )

    elif category == "damerau_osa":
        for case in test_case.get("cases", []):
            input_a = case["input_a"]
            input_b = case["input_b"]
            result = compute_damerau_osa(input_a, input_b)

            if case["expected_distance"] != result["distance"]:
                errors.append(
                    f"  ❌ {case['description']}: distance mismatch "
                    f"(expected {case['expected_distance']}, got {result['distance']})"
                )
            if abs(case["expected_score"] - result["score"]) > 1e-10:
                errors.append(
                    f"  ❌ {case['description']}: score mismatch "
                    f"(expected {case['expected_score']}, got {result['score']})"
                )

    elif category == "damerau_unrestricted":
        for case in test_case.get("cases", []):
            input_a = case["input_a"]
            input_b = case["input_b"]
            result = compute_damerau_unrestricted(input_a, input_b)

            if case["expected_distance"] != result["distance"]:
                errors.append(
                    f"  ❌ {case['description']}: distance mismatch "
                    f"(expected {case['expected_distance']}, got {result['distance']})"
                )
            if abs(case["expected_score"] - result["score"]) > 1e-10:
                errors.append(
                    f"  ❌ {case['description']}: score mismatch "
                    f"(expected {case['expected_score']}, got {result['score']})"
                )

    elif category == "jaro_winkler":
        for case in test_case.get("cases", []):
            input_a = case["input_a"]
            input_b = case["input_b"]
            score = compute_jaro_winkler(input_a, input_b)

            if abs(case["expected_score"] - score) > 1e-10:
                errors.append(
                    f"  ❌ {case['description']}: score mismatch "
                    f"(expected {case['expected_score']}, got {score})"
                )

    elif category == "substring":
        for case in test_case.get("cases", []):
            needle = case["needle"]
            haystack = case["haystack"]
            result = compute_substring(needle, haystack)

            if abs(case["expected_score"] - result["score"]) > 1e-10:
                errors.append(
                    f"  ❌ {case['description']}: score mismatch "
                    f"(expected {case['expected_score']}, got {result['score']})"
                )

            if "expected_range" in case:
                if "range" not in result:
                    errors.append(
                        f"  ❌ {case['description']}: expected range but got none"
                    )
                elif (
                    case["expected_range"]["start"] != result["range"]["start"]
                    or case["expected_range"]["end"] != result["range"]["end"]
                ):
                    errors.append(
                        f"  ❌ {case['description']}: range mismatch "
                        f"(expected {case['expected_range']}, got {result['range']})"
                    )

    elif category == "normalization_presets":
        for case in test_case.get("cases", []):
            input_text = case["input"]
            preset = case["preset"]
            expected = apply_normalization_preset(input_text, preset)

            if case["expected"] != expected:
                errors.append(
                    f"  ❌ {case['description']}: normalization mismatch "
                    f"(expected '{case['expected']}', got '{expected}')"
                )

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

            expected = case["expected"]

            if len(suggestions) != len(expected):
                errors.append(
                    f"  ❌ {case['description']}: suggestion count mismatch "
                    f"(expected {len(expected)}, got {len(suggestions)})"
                )
            else:
                for i, (exp, got) in enumerate(zip(expected, suggestions)):
                    if exp["value"] != got["value"]:
                        errors.append(
                            f"  ❌ {case['description']}: suggestion[{i}] value mismatch "
                            f"(expected '{exp['value']}', got '{got['value']}')"
                        )
                    if abs(exp["score"] - got["score"]) > 1e-10:
                        errors.append(
                            f"  ❌ {case['description']}: suggestion[{i}] score mismatch "
                            f"(expected {exp['score']}, got {got['score']})"
                        )

    return errors


def main():
    """Validate similarity fixture values."""
    fixtures_path = Path("config/crucible-py/library/foundry/similarity-fixtures.yaml")
    print(f"🔍 Validating fixtures from: {fixtures_path}\n")

    with open(fixtures_path) as f:
        data = yaml.safe_load(f)

    all_errors = []
    total_cases = 0

    for test_case in data.get("test_cases", []):
        category = test_case.get("category", "unknown")
        num_cases = len(test_case.get("cases", []))
        total_cases += num_cases

        print(f"  • {category}: {num_cases} cases...", end=" ")

        errors = validate_test_case(test_case)

        if errors:
            print("❌")
            all_errors.extend(errors)
        else:
            print("✅")

    print("\n📋 Summary:")
    print(f"   - Test case categories: {len(data.get('test_cases', []))}")
    print(f"   - Total test cases: {total_cases}")

    if all_errors:
        print(f"\n❌ Found {len(all_errors)} validation error(s):\n")
        for error in all_errors:
            print(error)
        return 1
    else:
        print("\n✅ All fixture values are correct!")
        print("\n🎉 Ready to hand back to Crucible for SSOT sync")
        return 0


if __name__ == "__main__":
    exit(main())
