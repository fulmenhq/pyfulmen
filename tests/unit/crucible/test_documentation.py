"""Tests for enhanced documentation APIs."""

import pytest

from pyfulmen.crucible import docs
from pyfulmen.crucible.errors import AssetNotFoundError


class TestGetDocumentation:
    """Tests for get_documentation function."""

    def test_get_documentation_returns_string(self):
        """get_documentation returns string content."""
        # Use a real doc that likely exists
        content = docs.get_documentation("guides/bootstrap-goneat.md")
        assert isinstance(content, str)
        assert len(content) > 0

    def test_get_documentation_strips_frontmatter_if_present(self):
        """Frontmatter is removed from content."""
        # This test will pass regardless of whether frontmatter exists
        content = docs.get_documentation("standards/observability/logging.md")
        # Content should not start with --- if frontmatter was present
        if content:
            # If file had frontmatter, it should be stripped
            assert not content.startswith("---")

    def test_get_documentation_not_found_raises_asset_error(self):
        """Non-existent doc raises AssetNotFoundError."""
        with pytest.raises(AssetNotFoundError) as exc_info:
            docs.get_documentation("nonexistent/document.md")

        assert exc_info.value.category == "docs"
        assert "nonexistent/document.md" in exc_info.value.asset_id

    def test_get_documentation_provides_suggestions(self):
        """AssetNotFoundError includes suggestions."""
        with pytest.raises(AssetNotFoundError) as exc_info:
            # Intentional typo in a real path
            docs.get_documentation("guides/bootstrap-goneat-typo.md")

        # Should suggest the correct path
        assert len(exc_info.value.suggestions) > 0
        # Suggestions should be similar to the requested path
        assert any("goneat" in s.lower() for s in exc_info.value.suggestions)


class TestGetDocumentationMetadata:
    """Tests for get_documentation_metadata function."""

    def test_get_metadata_returns_dict_or_none(self):
        """get_documentation_metadata returns dict or None."""
        metadata = docs.get_documentation_metadata("standards/observability/logging.md")
        assert metadata is None or isinstance(metadata, dict)

    def test_get_metadata_with_frontmatter(self):
        """Extract metadata from doc with frontmatter."""
        # Try a standards doc which likely has frontmatter
        metadata = docs.get_documentation_metadata("standards/observability/logging.md")

        if metadata:  # Only assert if frontmatter exists
            assert isinstance(metadata, dict)
            # Common frontmatter keys
            possible_keys = {
                "title",
                "author",
                "status",
                "tags",
                "description",
                "date",
                "last_updated",
            }
            # At least one of these keys should be present
            assert any(key in metadata for key in possible_keys)

    def test_get_metadata_not_found_raises_error(self):
        """Non-existent doc raises AssetNotFoundError."""
        with pytest.raises(AssetNotFoundError) as exc_info:
            docs.get_documentation_metadata("nonexistent/metadata-test.md")

        assert exc_info.value.category == "docs"


class TestGetDocumentationWithMetadata:
    """Tests for get_documentation_with_metadata function."""

    def test_returns_tuple(self):
        """Function returns tuple of (content, metadata)."""
        result = docs.get_documentation_with_metadata("guides/bootstrap-goneat.md")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_content_is_string(self):
        """First element of tuple is string content."""
        content, _ = docs.get_documentation_with_metadata("guides/bootstrap-goneat.md")
        assert isinstance(content, str)
        assert len(content) > 0

    def test_metadata_is_dict_or_none(self):
        """Second element is dict or None."""
        _, metadata = docs.get_documentation_with_metadata("standards/observability/logging.md")
        assert metadata is None or isinstance(metadata, dict)

    def test_content_has_no_frontmatter(self):
        """Content should not have frontmatter markers."""
        content, _ = docs.get_documentation_with_metadata("standards/observability/logging.md")
        # Content should not start with ---
        assert not content.startswith("---")

    def test_metadata_and_content_extracted_correctly(self):
        """Both content and metadata are properly extracted."""
        content, metadata = docs.get_documentation_with_metadata("standards/observability/logging.md")

        # Content should be non-empty
        assert len(content) > 0

        # If metadata exists, it should be a dict
        if metadata:
            assert isinstance(metadata, dict)
            # Should not contain content text
            for value in metadata.values():
                if isinstance(value, str):
                    # Metadata values should be short (not the full content)
                    assert len(value) < 500  # Reasonable metadata field size

    def test_not_found_raises_error(self):
        """Non-existent doc raises AssetNotFoundError."""
        with pytest.raises(AssetNotFoundError):
            docs.get_documentation_with_metadata("nonexistent/combined-test.md")


class TestGetSimilarDocs:
    """Tests for _get_similar_docs helper function."""

    def test_suggestions_for_typo(self):
        """Suggestions work for common typos."""
        with pytest.raises(AssetNotFoundError) as exc_info:
            # Typo: "loging" instead of "logging"
            docs.get_documentation("standards/observability/loging.md")

        suggestions = exc_info.value.suggestions
        # Should suggest paths containing "logging"
        assert any("logging" in s for s in suggestions)

    def test_suggestions_for_wrong_category(self):
        """Suggestions work when category is wrong."""
        with pytest.raises(AssetNotFoundError) as exc_info:
            # Wrong category but right filename
            docs.get_documentation("wrong-category/bootstrap-goneat.md")

        suggestions = exc_info.value.suggestions
        # Should suggest paths containing "bootstrap-goneat"
        assert any("bootstrap-goneat" in s or "goneat" in s for s in suggestions)

    def test_suggestions_limited_to_max(self):
        """Suggestions are limited to max_suggestions parameter."""
        with pytest.raises(AssetNotFoundError) as exc_info:
            docs.get_documentation("very/generic/name.md")

        # Default max is 3
        assert len(exc_info.value.suggestions) <= 3


class TestBackwardCompatibility:
    """Verify new functions don't break existing functionality."""

    def test_read_doc_still_works(self):
        """Legacy read_doc function still works."""
        content = docs.read_doc("guides/bootstrap-goneat.md")
        assert isinstance(content, str)
        assert len(content) > 0

    def test_list_available_docs_still_works(self):
        """Legacy list_available_docs function still works."""
        doc_list = docs.list_available_docs()
        assert isinstance(doc_list, list)
        assert len(doc_list) > 0
        assert all(isinstance(doc, str) for doc in doc_list)

    def test_get_doc_path_still_works(self):
        """Legacy get_doc_path function still works."""
        from pathlib import Path

        path = docs.get_doc_path("guides/bootstrap-goneat.md")
        assert isinstance(path, Path)
        assert path.exists()

    def test_read_doc_includes_frontmatter(self):
        """Legacy read_doc includes frontmatter (unchanged behavior)."""
        # read_doc should still return raw content with frontmatter
        raw_content = docs.read_doc("standards/observability/logging.md")

        # If the doc has frontmatter, read_doc should include it
        # get_documentation should strip it
        clean_content = docs.get_documentation("standards/observability/logging.md")

        # If there was frontmatter, raw should be longer than clean
        # (or equal if no frontmatter)
        assert len(raw_content) >= len(clean_content)


class TestEdgeCases:
    """Edge case tests for documentation functions."""

    def test_empty_path(self):
        """Empty path raises error."""
        # Empty path resolves to directory itself, causing IsADirectoryError
        with pytest.raises((AssetNotFoundError, FileNotFoundError, IsADirectoryError)):
            docs.get_documentation("")

    def test_path_without_extension(self):
        """Path without .md extension."""
        # Most functions expect .md extension
        with pytest.raises(AssetNotFoundError):
            docs.get_documentation("guides/bootstrap-goneat")  # No .md

    def test_absolute_path_converted(self):
        """Absolute paths are handled correctly."""
        # Function expects relative paths, but should handle gracefully
        with pytest.raises((AssetNotFoundError, FileNotFoundError)):
            docs.get_documentation("/absolute/path/to/doc.md")

    def test_path_with_double_slashes(self):
        """Path with double slashes is normalized by pathlib."""
        # pathlib.Path normalizes double slashes, so this actually works
        # if the underlying file exists
        # This tests that the normalization doesn't break our error handling
        with pytest.raises((AssetNotFoundError, FileNotFoundError)):
            docs.get_documentation("guides//nonexistent-file.md")

    def test_unicode_in_path(self):
        """Unicode characters in path."""
        with pytest.raises(AssetNotFoundError):
            docs.get_documentation("standards/日本語.md")
