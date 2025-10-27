"""
Integration tests for Similarity v2.0.0 features.

Tests end-to-end functionality, error handling, and cross-module integration.
"""

import pytest

from pyfulmen.foundry.similarity import (
    apply_normalization_preset,
    distance,
    normalize,
    score,
    substring_match,
    suggest,
)


class TestErrorHandling:
    """Test error handling and validation for v2.0.0 features."""

    def test_invalid_metric_for_distance(self):
        """Test that jaro_winkler raises error when used with distance()."""
        with pytest.raises(ValueError) as exc_info:
            distance("hello", "world", metric="jaro_winkler")

        assert "jaro_winkler metric produces similarity scores" in str(exc_info.value)
        assert "score(a, b" in str(exc_info.value)

    def test_invalid_metric_for_distance_substring(self):
        """Test that substring raises error when used with distance()."""
        with pytest.raises(ValueError) as exc_info:
            distance("hello", "world", metric="substring")

        assert "substring metric does not produce distances" in str(exc_info.value)
        assert "substring_match(needle, haystack)" in str(exc_info.value)

    def test_invalid_metric_name(self):
        """Test that invalid metric name raises clear error."""
        with pytest.raises(ValueError) as exc_info:
            distance("hello", "world", metric="invalid_metric")  # type: ignore

        assert "Invalid metric" in str(exc_info.value)
        assert "levenshtein" in str(exc_info.value)

    def test_invalid_normalization_preset(self):
        """Test that invalid preset raises clear error."""
        with pytest.raises(ValueError) as exc_info:
            apply_normalization_preset("hello", "invalid_preset")  # type: ignore

        assert "Invalid normalization preset" in str(exc_info.value)
        assert "none" in str(exc_info.value)
        assert "minimal" in str(exc_info.value)
        assert "default" in str(exc_info.value)
        assert "aggressive" in str(exc_info.value)


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows for common use cases."""

    def test_cli_typo_correction_workflow(self):
        """Test CLI command typo correction workflow with Jaro-Winkler."""
        # Simulate user typing a command with typo
        user_input = "terrafrom"
        available_commands = [
            "terraform",
            "terraform-apply",
            "terraform-destroy",
            "format",
            "validate",
        ]

        # Get suggestions using Jaro-Winkler (best for prefix matching)
        suggestions = suggest(
            user_input,
            available_commands,
            metric="jaro_winkler",
            max_suggestions=3,
            min_score=0.7,
        )

        # Verify terraform is top suggestion
        assert len(suggestions) > 0
        assert suggestions[0].value == "terraform"
        assert suggestions[0].score > 0.9

        # Verify other terraform commands also suggested
        terraform_suggestions = [s for s in suggestions if "terraform" in s.value]
        assert len(terraform_suggestions) >= 2

    def test_document_similarity_workflow(self):
        """Test document similarity comparison workflow."""
        doc1 = """Configuration Management
The system supports three-layer config loading:
1. Default configuration
2. Environment-specific overrides
3. Runtime parameters"""

        doc2 = """Configuration Management
The system supports three-layer config loading:
1. Default configuration
2. Environment-specific overrides
3. Runtime parameters"""

        doc3 = """Configuration Management
The system supports two-layer config loading:
1. Default configuration
2. Runtime parameters"""

        # Identical documents should score 1.0
        similarity_identical = score(doc1, doc2, metric="levenshtein")
        assert similarity_identical == 1.0

        # Similar but different documents should score high but not 1.0
        similarity_different = score(doc1, doc3, metric="levenshtein")
        assert 0.7 < similarity_different < 1.0

        # Substring matching should find common phrases
        match_range, match_score = substring_match("Configuration Management", doc1)
        assert match_range is not None
        assert match_range[0] == 0  # At start of document

    def test_normalization_workflow(self):
        """Test normalization workflow for fuzzy matching."""
        # User input with various inconsistencies
        user_query = "  café-zürich!  "
        database_entries = [
            "Café Zürich",
            "Cafe Zurich",
            "CAFE-ZURICH",
        ]

        # Without normalization - poor matches
        suggestions_raw = suggest(
            user_query,
            database_entries,
            normalize_text=False,
            min_score=0.8,
            max_suggestions=5,
        )
        assert len(suggestions_raw) == 0  # No good matches without normalization

        # With aggressive normalization - good matches
        suggestions_normalized = suggest(
            user_query,
            database_entries,
            normalize_preset="aggressive",
            min_score=0.8,
            max_suggestions=5,
        )
        assert len(suggestions_normalized) >= 2  # Multiple good matches

        # All should score highly after normalization
        for sug in suggestions_normalized:
            assert sug.score >= 0.8

    def test_transposition_handling_workflow(self):
        """Test that Damerau-Levenshtein handles transpositions better."""
        # Common typo with transposition
        typo = "teh"
        correct = "the"

        # Damerau should give better score (1 transposition)
        score_damerau = score(typo, correct, metric="damerau_osa")
        score_levenshtein = score(typo, correct, metric="levenshtein")

        # Damerau should give perfect score
        # (one swap = distance 1, length 3, so score = 2/3 ≈ 0.667)
        assert score_damerau > 0.6

        # Levenshtein requires 2 edits (delete e, delete h, insert h, insert e = 2 operations)
        # Score = 1/3 ≈ 0.33
        assert score_levenshtein > 0.3

        # Key point: Damerau should be significantly better
        assert score_damerau > score_levenshtein

        # Damerau OSA distance should be 1 (one transposition)
        dist_damerau = distance(typo, correct, metric="damerau_osa")
        assert dist_damerau == 1


class TestCrossModuleIntegration:
    """Test integration with other PyFulmen modules."""

    def test_similarity_with_unicode_normalization(self):
        """Test similarity works correctly with Unicode edge cases."""
        # Test with different Unicode representations
        text1 = "café"  # é as single character
        text2 = "café"  # é as e + combining accent

        # With default normalization, these should match
        suggestions = suggest(
            text1,
            [text2],
            normalize_preset="default",
            min_score=0.9,
        )
        assert len(suggestions) == 1
        assert suggestions[0].score >= 0.9

    def test_similarity_with_multiline_text(self):
        """Test similarity handles multiline text correctly."""
        text1 = "Line 1\nLine 2\nLine 3"
        text2 = "Line 1\nLine 2\nLine 3"
        text3 = "Line 1\r\nLine 2\r\nLine 3"  # Windows line endings

        # Same content with Unix endings
        assert distance(text1, text2) == 0

        # Same content with different line endings (CRLF vs LF)
        # Should have distance equal to number of line endings
        dist = distance(text1, text3)
        assert dist == 2  # Two \r characters difference

    def test_empty_input_handling(self):
        """Test that empty inputs are handled gracefully."""
        # Empty string distance
        assert distance("", "hello") == 5
        assert distance("hello", "") == 5
        assert distance("", "") == 0

        # Empty string score
        assert score("", "hello") == 0.0
        assert score("hello", "") == 0.0
        assert score("", "") == 1.0

        # Empty suggestions
        assert suggest("", ["hello"]) == []
        assert suggest("hello", []) == []


class TestPerformanceCharacteristics:
    """Test performance characteristics meet requirements."""

    def test_typical_string_performance(self):
        """Test that typical strings are processed quickly."""
        import time

        # Test strings under 128 chars (should be < 1ms per standard)
        text1 = "terraform apply -var-file=production.tfvars"
        text2 = "terraform apply -var-file=staging.tfvars"

        # Measure multiple iterations to get reliable timing
        iterations = 100
        start = time.time()
        for _ in range(iterations):
            distance(text1, text2, metric="damerau_osa")
        elapsed = time.time() - start

        avg_time_ms = (elapsed / iterations) * 1000

        # Should be well under 1ms per call (allowing generous margin)
        assert avg_time_ms < 5.0, f"Average time {avg_time_ms:.2f}ms exceeds target"

    def test_suggestion_performance(self):
        """Test that suggestion generation is reasonably fast."""
        import time

        candidates = [f"command-{i}" for i in range(100)]
        user_input = "commnd"

        start = time.time()
        suggestions = suggest(
            user_input,
            candidates,
            metric="jaro_winkler",
            max_suggestions=5,
        )
        elapsed = time.time() - start

        # Should process 100 candidates in reasonable time
        assert elapsed < 0.1, f"Suggestion took {elapsed:.3f}s for 100 candidates"
        assert len(suggestions) <= 5


class TestBackwardCompatibility:
    """Test that v1.0 API continues to work."""

    def test_v1_distance_api(self):
        """Test v1.0 distance() API still works."""
        # v1.0 used levenshtein by default
        dist = distance("hello", "hallo")
        assert isinstance(dist, int)
        assert dist > 0

    def test_v1_score_api(self):
        """Test v1.0 score() API still works."""
        # v1.0 used levenshtein by default
        sc = score("hello", "hallo")
        assert isinstance(sc, float)
        assert 0.0 <= sc <= 1.0

    def test_v1_suggest_api(self):
        """Test v1.0 suggest() API still works."""
        # v1.0 basic signature
        suggestions = suggest("helo", ["hello", "help", "hero"])
        assert len(suggestions) > 0
        assert suggestions[0].value in ["hello", "help", "hero"]
        assert hasattr(suggestions[0], "score")
        assert hasattr(suggestions[0], "value")

    def test_v1_normalize_api(self):
        """Test v1.0 normalize() API still works."""
        # v1.0 signature with strip_accents_flag
        normalized = normalize("  Café  ", strip_accents_flag=True)
        assert normalized == "cafe"

        # v1.0 default behavior
        normalized_default = normalize("  Hello  ")
        assert normalized_default == "hello"
