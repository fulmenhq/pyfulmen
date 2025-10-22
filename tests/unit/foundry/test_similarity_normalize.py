"""
Unit tests for text normalization utilities.

Tests case folding, accent stripping, normalization pipeline, and
case-insensitive comparison following the Foundry similarity standard.
"""

from pyfulmen.foundry import similarity


class TestCasefold:
    """Test Unicode case folding with locale support."""

    def test_simple_casefold(self):
        """Test basic case folding."""
        assert similarity.casefold("Hello World") == "hello world"
        assert similarity.casefold("CAFÉ") == "café"
        assert similarity.casefold("MiXeD CaSe") == "mixed case"

    def test_turkish_locale_dotted_i(self):
        """Test Turkish locale handling for İ→i."""
        assert similarity.casefold("İstanbul", locale="tr") == "istanbul"
        assert similarity.casefold("İZMİR", locale="tr") == "izmir"

    def test_turkish_locale_dotless_i(self):
        """Test Turkish locale handling for I→ı."""
        assert similarity.casefold("ISTANBUL", locale="tr") == "ıstanbul"
        assert similarity.casefold("IZMIR", locale="tr") == "ızmır"
        assert similarity.casefold("TITLE", locale="tr") == "tıtle"

    def test_empty_string(self):
        """Test empty string handling."""
        assert similarity.casefold("") == ""
        assert similarity.casefold("", locale="tr") == ""

    def test_invalid_locale_fallback(self):
        """Test that invalid locales fall back to simple casefold."""
        assert similarity.casefold("Hello", locale="invalid") == "hello"


class TestStripAccents:
    """Test diacritical mark removal."""

    def test_common_accents(self):
        """Test removal of common accent marks."""
        assert similarity.strip_accents("café") == "cafe"
        assert similarity.strip_accents("naïve") == "naive"
        assert similarity.strip_accents("Zürich") == "Zurich"
        assert similarity.strip_accents("résumé") == "resume"

    def test_multiple_accents(self):
        """Test strings with multiple accented characters."""
        assert similarity.strip_accents("crème brûlée") == "creme brulee"
        assert similarity.strip_accents("Côte d'Azur") == "Cote d'Azur"

    def test_no_accents(self):
        """Test strings without accents remain unchanged."""
        assert similarity.strip_accents("hello") == "hello"
        assert similarity.strip_accents("world") == "world"

    def test_empty_string(self):
        """Test empty string handling."""
        assert similarity.strip_accents("") == ""

    def test_unicode_categories(self):
        """Test that only Mn category marks are removed."""
        assert similarity.strip_accents("e\u0301") == "e"


class TestNormalize:
    """Test complete normalization pipeline."""

    def test_trim_only(self):
        """Test trimming whitespace."""
        assert similarity.normalize("  hello  ") == "hello"
        assert similarity.normalize("\thello\n") == "hello"

    def test_trim_and_casefold(self):
        """Test trim + casefold pipeline."""
        assert similarity.normalize("  Hello World  ") == "hello world"
        assert similarity.normalize("  CAFÉ  ") == "café"

    def test_full_pipeline(self):
        """Test trim + casefold + strip_accents."""
        assert similarity.normalize("  Café  ", strip_accents_flag=True) == "cafe"
        assert similarity.normalize("  RÉSUMÉ  ", strip_accents_flag=True) == "resume"

    def test_turkish_locale(self):
        """Test normalization with Turkish locale."""
        assert similarity.normalize("İstanbul", locale="tr") == "istanbul"
        assert similarity.normalize("  İzmir  ", locale="tr") == "izmir"
        assert similarity.normalize("TITLE", locale="tr") == "tıtle"

    def test_empty_string(self):
        """Test empty string handling."""
        assert similarity.normalize("") == ""
        assert similarity.normalize("", strip_accents_flag=True) == ""

    def test_whitespace_only(self):
        """Test whitespace-only strings return empty."""
        assert similarity.normalize("   ") == ""
        assert similarity.normalize("\t\n") == ""


class TestEqualsIgnoreCase:
    """Test case-insensitive equality comparison."""

    def test_case_insensitive_match(self):
        """Test matching with different cases."""
        assert similarity.equals_ignore_case("Hello", "hello") is True
        assert similarity.equals_ignore_case("WORLD", "world") is True
        assert similarity.equals_ignore_case("MiXeD", "mixed") is True

    def test_with_whitespace(self):
        """Test matching with whitespace normalization."""
        assert similarity.equals_ignore_case("  WORLD  ", "world") is True
        assert similarity.equals_ignore_case("hello  ", "  hello") is True

    def test_with_accents_not_stripped(self):
        """Test that accents matter by default."""
        assert similarity.equals_ignore_case("Café", "cafe") is False
        assert similarity.equals_ignore_case("naïve", "naive") is False

    def test_with_accents_stripped(self):
        """Test matching with accent stripping enabled."""
        assert similarity.equals_ignore_case("Café", "cafe", strip_accents_flag=True) is True
        assert similarity.equals_ignore_case("naïve", "naive", strip_accents_flag=True) is True
        assert similarity.equals_ignore_case("RÉSUMÉ", "resume", strip_accents_flag=True) is True

    def test_different_strings(self):
        """Test non-matching strings."""
        assert similarity.equals_ignore_case("hello", "world") is False
        assert similarity.equals_ignore_case("café", "coffee") is False

    def test_empty_strings(self):
        """Test empty string equality."""
        assert similarity.equals_ignore_case("", "") is True
        assert similarity.equals_ignore_case("hello", "") is False
