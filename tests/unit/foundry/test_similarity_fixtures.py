"""
Fixture-driven validation tests for similarity module.

Loads and validates against Crucible SSOT fixtures to ensure cross-language
parity and compliance with the Foundry similarity standard.
"""

import pytest
import yaml

from pyfulmen.foundry import similarity


def load_fixtures():
    """Load similarity fixtures from Crucible SSOT."""
    fixture_path = "config/crucible-py/library/foundry/similarity-fixtures.yaml"

    with open(fixture_path) as f:
        data = yaml.safe_load(f)

    return data["test_cases"]


@pytest.fixture(scope="module")
def fixture_data():
    """Provide fixture data to all tests."""
    return load_fixtures()


class TestDistanceFixtures:
    """Test distance and score calculations against fixtures."""

    def test_all_distance_fixtures(self, fixture_data):
        """Validate all distance fixture test cases (v2.0 - multiple metric categories)."""
        distance_categories = {
            "levenshtein": "levenshtein",
            "damerau_osa": "damerau_osa",
            "damerau_unrestricted": "damerau_unrestricted",
        }

        failures = []

        for category, metric in distance_categories.items():
            category_block = [tc for tc in fixture_data if tc["category"] == category]
            if not category_block:
                continue

            cases = category_block[0]["cases"]

            for case in cases:
                input_a = case["input_a"]
                input_b = case["input_b"]
                expected_distance = case["expected_distance"]
                expected_score = case["expected_score"]
                description = case.get("description", "no description")

                actual_distance = similarity.distance(input_a, input_b, metric=metric)  # type: ignore
                actual_score = similarity.score(input_a, input_b, metric=metric)  # type: ignore

                distance_match = actual_distance == expected_distance
                score_match = abs(actual_score - expected_score) < 1e-10

                if not distance_match:
                    failures.append(
                        f"[{category}] {description}: distance mismatch - "
                        f"expected {expected_distance}, got {actual_distance}"
                    )

                if not score_match:
                    failures.append(
                        f"[{category}] {description}: score mismatch - "
                        f"expected {expected_score:.16f}, got {actual_score:.16f}"
                    )

        if failures:
            pytest.fail("\n".join(failures))


class TestNormalizationFixtures:
    """Test normalization functions against fixtures."""

    def test_all_normalization_fixtures(self, fixture_data):
        """Validate all normalization fixture test cases (v2.0 - preset-based)."""
        norm_block = [tc for tc in fixture_data if tc["category"] == "normalization_presets"]
        if not norm_block:
            pytest.skip("No normalization_presets category in fixtures")

        norm_cases = norm_block[0]["cases"]

        failures = []

        for case in norm_cases:
            input_val = case["input"]
            preset = case["preset"]
            expected = case["expected"]
            description = case.get("description", "no description")

            actual = similarity.apply_normalization_preset(input_val, preset)  # type: ignore

            if actual != expected:
                failures.append(
                    f"{description}: normalization mismatch - "
                    f"expected {repr(expected)}, got {repr(actual)}"
                )

        if failures:
            pytest.fail("\n".join(failures))


class TestSuggestionFixtures:
    """Test suggestion API against fixtures."""

    def test_all_suggestion_fixtures(self, fixture_data):
        """Validate all suggestion fixture test cases (v2.0 - supports all metrics)."""
        suggest_block = [tc for tc in fixture_data if tc["category"] == "suggestions"]
        if not suggest_block:
            pytest.skip("No suggestions category in fixtures")

        suggest_cases = suggest_block[0]["cases"]

        failures = []

        for case in suggest_cases:
            input_val = case["input"]
            candidates = case["candidates"]
            options = case.get("options", {})
            expected = case["expected"]
            description = case.get("description", "no description")

            kwargs = {
                "min_score": options.get("min_score", 0.6),
                "max_suggestions": options.get("max_suggestions", 3),
            }

            if "metric" in options:
                kwargs["metric"] = options["metric"]  # type: ignore

            if "normalize_preset" in options:
                kwargs["normalize_preset"] = options["normalize_preset"]  # type: ignore
            elif "normalize" in options:
                kwargs["normalize_text"] = options["normalize"]

            if "prefer_prefix" in options:
                kwargs["prefer_prefix"] = options["prefer_prefix"]

            actual_suggestions = similarity.suggest(input_val, candidates, **kwargs)

            if len(actual_suggestions) != len(expected):
                failures.append(
                    f"{description}: suggestion count mismatch - "
                    f"expected {len(expected)}, got {len(actual_suggestions)}"
                )
                continue

            for i, (actual, exp) in enumerate(zip(actual_suggestions, expected, strict=False)):
                if actual.value != exp["value"]:
                    failures.append(
                        f"{description} [#{i}]: value mismatch - "
                        f"expected {repr(exp['value'])}, got {repr(actual.value)}"
                    )

                if abs(actual.score - exp["score"]) >= 1e-10:
                    failures.append(
                        f"{description} [#{i}]: score mismatch - "
                        f"expected {exp['score']:.16f}, got {actual.score:.16f}"
                    )

        if failures:
            pytest.fail("\n".join(failures))


class TestFixtureMetadata:
    """Test fixture file metadata and structure."""

    def test_fixture_version(self, fixture_data):
        """Verify fixture version is compatible (v2.0)."""
        fixture_path = "config/crucible-py/library/foundry/similarity-fixtures.yaml"

        with open(fixture_path) as f:
            data = yaml.safe_load(f)

        assert "version" in data
        assert data["version"] == "2025.10.3"

    def test_fixture_categories_present(self, fixture_data):
        """Verify all expected categories are present (v2.0 structure)."""
        categories = {tc["category"] for tc in fixture_data}

        expected_categories = {
            "levenshtein",
            "damerau_osa",
            "damerau_unrestricted",
            "jaro_winkler",
            "substring",
            "normalization_presets",
            "suggestions",
        }
        assert categories == expected_categories

    def test_fixture_case_count(self, fixture_data):
        """Verify minimum number of test cases per category."""
        for category_block in fixture_data:
            category = category_block["category"]
            cases = category_block["cases"]

            if category in ("levenshtein", "damerau_osa", "damerau_unrestricted"):
                assert len(cases) >= 4, f"{category} category has only {len(cases)} cases"
            elif category == "normalization_presets":
                assert len(cases) >= 7, (
                    f"normalization_presets category has only {len(cases)} cases"
                )
            elif category == "suggestions":
                assert len(cases) >= 4, f"Suggestions category has only {len(cases)} cases"
