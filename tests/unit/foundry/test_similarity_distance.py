"""
Unit tests for Levenshtein distance and similarity scoring.

Tests edit distance calculation and normalized similarity scores following
the Foundry similarity standard with fixture validation.
"""

import pytest

from pyfulmen.foundry import similarity


class TestDistance:
    """Test Levenshtein edit distance calculation."""
    
    def test_classic_levenshtein(self):
        """Test classic Levenshtein examples."""
        assert similarity.distance("kitten", "sitting") == 3
        assert similarity.distance("saturday", "sunday") == 3
    
    def test_simple_edits(self):
        """Test basic edit operations."""
        assert similarity.distance("book", "back") == 2
        assert similarity.distance("hello", "helo") == 1
    
    def test_identical_strings(self):
        """Test identical strings have zero distance."""
        assert similarity.distance("test", "test") == 0
        assert similarity.distance("hello", "hello") == 0
    
    def test_empty_strings(self):
        """Test empty string handling."""
        assert similarity.distance("", "") == 0
        assert similarity.distance("", "hello") == 5
        assert similarity.distance("hello", "") == 5
    
    def test_unicode_strings(self):
        """Test Unicode character handling."""
        assert similarity.distance("café", "cafe") == 1
        assert similarity.distance("naïve", "naive") == 1
        assert similarity.distance("hello", "hëllo") == 1
    
    def test_emoji(self):
        """Test emoji as single graphemes."""
        assert similarity.distance("🎉", "🎊") == 1
        assert similarity.distance("hello😀", "hello😃") == 1
    
    def test_case_sensitivity(self):
        """Test that distance is case-sensitive."""
        assert similarity.distance("Hello", "hello") == 1
        assert similarity.distance("UPPER", "lower") == 5


class TestScore:
    """Test normalized similarity scoring."""
    
    def test_identical_strings(self):
        """Test identical strings have score 1.0."""
        assert similarity.score("test", "test") == 1.0
        assert similarity.score("hello", "hello") == 1.0
    
    def test_empty_strings(self):
        """Test empty strings are considered identical."""
        assert similarity.score("", "") == 1.0
    
    def test_completely_different(self):
        """Test completely different strings have score 0.0."""
        assert similarity.score("", "hello") == 0.0
        assert similarity.score("UPPER", "lower") == 0.0
    
    def test_classic_examples(self):
        """Test classic Levenshtein examples."""
        assert abs(similarity.score("kitten", "sitting") - 0.5714285714285714) < 1e-10
        assert abs(similarity.score("saturday", "sunday") - 0.625) < 1e-10
    
    def test_simple_similarity(self):
        """Test simple similarity calculations."""
        assert similarity.score("book", "back") == 0.5
        assert similarity.score("hello", "helo") == 0.8
    
    def test_unicode_similarity(self):
        """Test Unicode character similarity."""
        assert similarity.score("café", "cafe") == 0.75
        assert similarity.score("naïve", "naive") == 0.8
        assert similarity.score("hello", "hëllo") == 0.8
    
    def test_emoji_similarity(self):
        """Test emoji similarity scoring."""
        assert similarity.score("🎉", "🎊") == 0.0
        assert abs(similarity.score("hello😀", "hello😃") - 0.8333333333333334) < 1e-10
    
    def test_case_sensitivity(self):
        """Test score is case-sensitive."""
        assert similarity.score("Hello", "hello") == 0.8
    
    def test_score_range(self):
        """Test score always in range [0.0, 1.0]."""
        test_cases = [
            ("", ""),
            ("test", "test"),
            ("hello", "world"),
            ("", "hello"),
            ("abc", "xyz"),
        ]
        for a, b in test_cases:
            scr = similarity.score(a, b)
            assert 0.0 <= scr <= 1.0, f"Score {scr} out of range for {repr(a)}, {repr(b)}"


class TestDistanceProperties:
    """Test mathematical properties of distance metric."""
    
    def test_identity(self):
        """Test distance(a, a) == 0 for all strings."""
        test_strings = ["", "test", "hello world", "café", "🎉"]
        for s in test_strings:
            assert similarity.distance(s, s) == 0
    
    def test_symmetry(self):
        """Test distance(a, b) == distance(b, a) for all strings."""
        test_pairs = [
            ("hello", "world"),
            ("test", "tset"),
            ("", "hello"),
            ("café", "cafe"),
        ]
        for a, b in test_pairs:
            assert similarity.distance(a, b) == similarity.distance(b, a)
    
    def test_triangle_inequality(self):
        """Test distance(a, c) <= distance(a, b) + distance(b, c)."""
        test_cases = [
            ("hello", "helo", "help"),
            ("test", "best", "rest"),
            ("abc", "ab", "a"),
        ]
        for a, b, c in test_cases:
            d_ac = similarity.distance(a, c)
            d_ab = similarity.distance(a, b)
            d_bc = similarity.distance(b, c)
            assert d_ac <= d_ab + d_bc, f"Triangle inequality failed: {a}, {b}, {c}"
