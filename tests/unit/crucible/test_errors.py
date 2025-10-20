"""Tests for Crucible error classes."""

from pyfulmen.crucible.errors import (
    AssetNotFoundError,
    CrucibleVersionError,
    ParseError,
)


class TestAssetNotFoundError:
    """Tests for AssetNotFoundError exception."""

    def test_basic_error_message(self):
        """Basic error with just asset_id."""
        error = AssetNotFoundError("test/asset")
        assert error.asset_id == "test/asset"
        assert "Asset not found: test/asset" in str(error)

    def test_error_with_category(self):
        """Error with category context."""
        error = AssetNotFoundError("test/asset", category="docs")
        assert error.category == "docs"
        assert "category: docs" in str(error)

    def test_error_with_suggestions(self):
        """Error with suggested alternatives."""
        error = AssetNotFoundError(
            "test/assset",  # Typo
            suggestions=["test/asset", "test/asset2", "test/assets"],
        )
        assert "Did you mean:" in str(error)
        assert "test/asset" in str(error)

    def test_suggestions_limited_to_three(self):
        """Only first 3 suggestions shown in error message."""
        error = AssetNotFoundError(
            "test/doc",
            suggestions=["test/doc1", "test/doc2", "test/doc3", "test/doc4"],
        )
        error_msg = str(error)
        assert "test/doc1" in error_msg
        assert "test/doc2" in error_msg
        assert "test/doc3" in error_msg
        # Should truncate to 3
        assert error_msg.count("test/doc") == 4  # Original + 3 suggestions

    def test_error_with_all_fields(self):
        """Error with all optional fields populated."""
        error = AssetNotFoundError(
            "standards/observability/loging.md",  # Typo
            category="docs",
            suggestions=["standards/observability/logging.md"],
        )
        assert error.asset_id == "standards/observability/loging.md"
        assert error.category == "docs"
        assert len(error.suggestions) == 1
        assert "category: docs" in str(error)
        assert "Did you mean:" in str(error)

    def test_empty_suggestions_list(self):
        """Error with empty suggestions list."""
        error = AssetNotFoundError("test/asset", suggestions=[])
        assert error.suggestions == []
        assert "Did you mean:" not in str(error)


class TestParseError:
    """Tests for ParseError exception."""

    def test_basic_parse_error(self):
        """Basic parse error with message."""
        error = ParseError("Invalid YAML at line 5")
        assert "Invalid YAML at line 5" in str(error)

    def test_parse_error_with_details(self):
        """Parse error with detailed message."""
        error = ParseError("Invalid YAML frontmatter: mapping values are not allowed here")
        assert "Invalid YAML frontmatter" in str(error)
        assert "mapping values are not allowed" in str(error)


class TestCrucibleVersionError:
    """Tests for CrucibleVersionError exception."""

    def test_basic_version_error(self):
        """Basic version error."""
        error = CrucibleVersionError("Cannot determine Crucible version")
        assert "Cannot determine Crucible version" in str(error)

    def test_version_error_with_details(self):
        """Version error with detailed context."""
        error = CrucibleVersionError("Crucible metadata directory not found at .crucible/metadata")
        assert "metadata directory not found" in str(error)
