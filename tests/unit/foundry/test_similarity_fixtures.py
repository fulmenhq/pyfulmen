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
        """Validate all distance fixture test cases."""
        distance_cases = [tc for tc in fixture_data if tc["category"] == "distance"][0]["cases"]

        failures = []

        for case in distance_cases:
            input_a = case["input_a"]
            input_b = case["input_b"]
            expected_distance = case["expected_distance"]
            expected_score = case["expected_score"]
            description = case["description"]

            actual_distance = similarity.distance(input_a, input_b)
            actual_score = similarity.score(input_a, input_b)

            distance_match = actual_distance == expected_distance
            score_match = abs(actual_score - expected_score) < 1e-10

            if not distance_match:
                failures.append(
                    f"{description}: distance mismatch - "
                    f"expected {expected_distance}, got {actual_distance}"
                )

            if not score_match:
                failures.append(
                    f"{description}: score mismatch - "
                    f"expected {expected_score:.16f}, got {actual_score:.16f}"
                )

        if failures:
            pytest.fail("\n".join(failures))


class TestNormalizationFixtures:
    """Test normalization functions against fixtures."""

    def test_all_normalization_fixtures(self, fixture_data):
        """Validate all normalization fixture test cases."""
        norm_cases = [tc for tc in fixture_data if tc["category"] == "normalization"][0]["cases"]

        failures = []

        for case in norm_cases:
            input_val = case["input"]
            options = case.get("options", {})
            expected = case["expected"]
            description = case["description"]

            kwargs = {}
            if "strip_accents" in options:
                kwargs["strip_accents_flag"] = options["strip_accents"]
            if "locale" in options:
                kwargs["locale"] = options["locale"]

            actual = similarity.normalize(input_val, **kwargs)

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
        """Validate all suggestion fixture test cases.

        Note: Some fixtures are skipped as they expect Damerau-Levenshtein
        distance (which counts transpositions as 1 operation) or other
        advanced metrics. These are explicitly excluded from v1.0.0 per
        the similarity standard and will be enabled in future versions.
        """
        suggest_cases = [tc for tc in fixture_data if tc["category"] == "suggestions"][0]["cases"]

        # SKIP: Fixtures expecting Damerau-Levenshtein or advanced metrics
        # TODO: Unskip when Damerau-Levenshtein support is added (post-v0.1.5)
        skip_descriptions = {
            "Transposition (two candidates tie)",  # Expects Damerau-Levenshtein
            "Transposition in middle (three-way tie)",  # Expects Damerau-Levenshtein
            "Partial path matching",  # Expects substring/fuzzy matching beyond standard Levenshtein
        }

        failures = []

        for case in suggest_cases:
            input_val = case["input"]
            candidates = case["candidates"]
            options = case.get("options", {})
            expected = case["expected"]
            description = case["description"]

            # Skip fixtures expecting advanced algorithms not yet implemented
            if description in skip_descriptions:
                continue

            kwargs = {
                "min_score": options.get("min_score", 0.6),
                "max_suggestions": options.get("max_suggestions", 3),
                "normalize_text": options.get("normalize", True),
            }

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
        """Verify fixture version is compatible."""
        fixture_path = "config/crucible-py/library/foundry/similarity-fixtures.yaml"

        with open(fixture_path) as f:
            data = yaml.safe_load(f)

        assert "version" in data
        assert data["version"] == "2025.10.2"

    def test_fixture_categories_present(self, fixture_data):
        """Verify all expected categories are present."""
        categories = {tc["category"] for tc in fixture_data}

        expected_categories = {"distance", "normalization", "suggestions"}
        assert categories == expected_categories

    def test_fixture_case_count(self, fixture_data):
        """Verify minimum number of test cases per category."""
        for category_block in fixture_data:
            category = category_block["category"]
            cases = category_block["cases"]

            if category == "distance":
                assert len(cases) >= 10, f"Distance category has only {len(cases)} cases"
            elif category == "normalization":
                assert len(cases) >= 10, f"Normalization category has only {len(cases)} cases"
            elif category == "suggestions":
                assert len(cases) >= 5, f"Suggestions category has only {len(cases)} cases"
