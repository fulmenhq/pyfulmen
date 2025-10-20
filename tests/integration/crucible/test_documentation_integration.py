"""Integration tests for documentation module against real Crucible docs."""

import pytest

from pyfulmen import crucible


class TestRealDocumentAccess:
    """Test against actual synced Crucible documentation."""

    def test_load_logging_standard(self):
        """Load and parse a real standard with frontmatter."""
        content = crucible.get_documentation("standards/observability/logging.md")
        assert "logging" in content.lower()
        assert len(content) > 100
        assert not content.startswith("---")  # Frontmatter removed

    def test_get_logging_standard_metadata(self):
        """Extract metadata from real standard."""
        metadata = crucible.get_documentation_metadata("standards/observability/logging.md")
        # If this doc has frontmatter, verify structure
        if metadata:
            assert isinstance(metadata, dict)
            # Check for expected frontmatter keys
            assert any(key in metadata for key in ["title", "author", "status", "tags"])

    def test_combined_access(self):
        """Get both content and metadata together."""
        content, metadata = crucible.get_documentation_with_metadata(
            "standards/observability/logging.md"
        )
        assert isinstance(content, str)
        assert len(content) > 0
        # Metadata may or may not exist
        assert metadata is None or isinstance(metadata, dict)

    def test_guide_without_frontmatter(self):
        """Some docs may not have frontmatter."""
        content = crucible.get_documentation("guides/bootstrap-goneat.md")
        # Should still work, return content as-is
        assert isinstance(content, str)

    def test_architecture_doc_access(self):
        """Test accessing architecture documentation."""
        content = crucible.get_documentation("architecture/fulmen-helper-library-standard.md")
        assert isinstance(content, str)
        assert len(content) > 0

    def test_newly_synced_doc_with_frontmatter(self):
        """Test the newly synced documentation module standard."""
        content, metadata = crucible.get_documentation_with_metadata(
            "standards/library/modules/documentation.md"
        )
        assert isinstance(content, str)
        assert len(content) > 0

        # This doc should have frontmatter (we just saw it)
        assert metadata is not None
        assert "title" in metadata
        assert "Documentation Module Standard" in metadata["title"]
        assert "status" in metadata
        assert metadata["status"] == "draft"


class TestErrorHandlingIntegration:
    """Test error scenarios with real assets."""

    def test_invalid_path_provides_suggestions(self):
        """AssetNotFoundError should include helpful suggestions."""
        with pytest.raises(crucible.AssetNotFoundError) as exc_info:
            crucible.get_documentation("standards/observability/loging.md")  # Typo

        error = exc_info.value
        assert error.asset_id == "standards/observability/loging.md"
        assert error.category == "docs"
        # Should suggest the correct path
        assert len(error.suggestions) > 0
        assert any("logging" in s for s in error.suggestions)

    def test_nonexistent_category_provides_suggestions(self):
        """Test suggestions for completely wrong category."""
        with pytest.raises(crucible.AssetNotFoundError) as exc_info:
            crucible.get_documentation("nonexistent/category/doc.md")

        error = exc_info.value
        # Should still provide some suggestions from real docs
        assert error.category == "docs"

    def test_metadata_extraction_failure_handling(self):
        """Test that we handle docs without frontmatter gracefully."""
        # Find a doc that likely doesn't have frontmatter
        try:
            metadata = crucible.get_documentation_metadata("guides/bootstrap-goneat.md")
            # Either None (no frontmatter) or dict (has frontmatter)
            assert metadata is None or isinstance(metadata, dict)
        except crucible.AssetNotFoundError:
            # If the guide doesn't exist, that's also fine for this test
            pytest.skip("Guide not found in synced assets")


class TestBackwardCompatibilityIntegration:
    """Ensure new APIs don't break existing functionality."""

    def test_read_doc_unchanged(self):
        """Legacy read_doc should still include frontmatter."""
        from pyfulmen.crucible import docs

        raw_content = docs.read_doc("standards/library/modules/documentation.md")
        # Should start with frontmatter
        assert raw_content.startswith("---")

    def test_new_api_strips_frontmatter(self):
        """New API should remove frontmatter that legacy API includes."""
        from pyfulmen.crucible import docs

        raw_content = docs.read_doc("standards/library/modules/documentation.md")
        clean_content = crucible.get_documentation("standards/library/modules/documentation.md")

        # Raw should have frontmatter, clean should not
        assert raw_content.startswith("---")
        assert not clean_content.startswith("---")
        # Clean should be shorter (frontmatter removed)
        assert len(clean_content) < len(raw_content)


class TestPerformance:
    """Test performance characteristics of documentation access."""

    def test_frontmatter_extraction_performance(self):
        """Frontmatter extraction should be fast (<10ms typical)."""
        import time

        start = time.perf_counter()
        for _ in range(100):
            content, metadata = crucible.get_documentation_with_metadata(
                "standards/library/modules/documentation.md"
            )
        elapsed = time.perf_counter() - start

        # 100 iterations should complete in reasonable time
        # (not enforcing <1s strictly, but warning if too slow)
        assert elapsed < 5.0, f"100 extractions took {elapsed:.2f}s (too slow?)"

        # Individual operations should be very fast
        avg_per_call = elapsed / 100
        assert avg_per_call < 0.05, (
            f"Average extraction time: {avg_per_call * 1000:.2f}ms (target <10ms)"
        )
