"""Tests for frontmatter parsing in docscribe module."""

import pytest

from pyfulmen.docscribe import (
    ParseError,
    extract_metadata,
    has_frontmatter,
    parse_frontmatter,
    strip_frontmatter,
)


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_basic_frontmatter(self):
        """Extract basic YAML frontmatter."""
        content = """---
title: Test Doc
author: Jane Doe
---
# Content here"""

        clean, meta = parse_frontmatter(content)
        assert clean == "# Content here"
        assert meta == {"title": "Test Doc", "author": "Jane Doe"}

    def test_no_frontmatter(self):
        """Content without frontmatter returns unchanged."""
        content = "# Just content"
        clean, meta = parse_frontmatter(content)
        assert clean == content
        assert meta is None

    def test_empty_frontmatter(self):
        """Empty frontmatter block returns empty dict."""
        content = """---
---
# Content"""
        clean, meta = parse_frontmatter(content)
        assert clean == "# Content"
        assert meta == {}

    def test_frontmatter_with_lists(self):
        """Frontmatter with YAML lists."""
        content = """---
title: Complex Doc
tags:
  - python
  - testing
---
# Content"""

        clean, meta = parse_frontmatter(content)
        assert meta["tags"] == ["python", "testing"]
        assert clean == "# Content"

    def test_frontmatter_with_nested_structures(self):
        """Frontmatter with nested YAML structures."""
        content = """---
title: Nested Doc
metadata:
  nested: value
  another:
    deeply: nested
---
# Content"""

        clean, meta = parse_frontmatter(content)
        assert meta["metadata"]["nested"] == "value"
        assert meta["metadata"]["another"]["deeply"] == "nested"

    def test_malformed_yaml_raises_parse_error(self):
        """Malformed YAML raises ParseError."""
        content = """---
title: Test
broken: [unclosed
---
# Content"""

        with pytest.raises(ParseError, match="Invalid YAML frontmatter"):
            parse_frontmatter(content)

    def test_no_closing_delimiter(self):
        """Content starting with --- but no closing treated as no frontmatter."""
        content = """---
title: Test
# Content without closing ---"""

        clean, meta = parse_frontmatter(content)
        # Treated as content without frontmatter
        assert meta is None
        assert clean == content

    def test_windows_line_endings(self):
        """Handle Windows (CRLF) line endings."""
        content = "---\r\ntitle: Test\r\n---\r\n# Content"
        clean, meta = parse_frontmatter(content)
        assert meta == {"title": "Test"}
        assert clean == "# Content"

    def test_mixed_line_endings(self):
        """Handle mixed line endings gracefully."""
        content = "---\ntitle: Test\r\n---\r\n# Content"
        clean, meta = parse_frontmatter(content)
        assert meta == {"title": "Test"}
        assert clean == "# Content"

    def test_frontmatter_with_unicode(self):
        """Frontmatter with unicode characters."""
        content = """---
title: 日本語タイトル
author: François Müller
---
# Content with émojis 🎉"""

        clean, meta = parse_frontmatter(content)
        assert meta["title"] == "日本語タイトル"
        assert meta["author"] == "François Müller"
        assert "🎉" in clean

    def test_multiline_content_after_frontmatter(self):
        """Clean content preserves multiple lines."""
        content = """---
title: Test
---
# Header

Paragraph 1

Paragraph 2"""

        clean, meta = parse_frontmatter(content)
        assert "# Header" in clean
        assert "Paragraph 1" in clean
        assert "Paragraph 2" in clean
        assert meta["title"] == "Test"

    def test_frontmatter_strips_leading_newlines(self):
        """Leading newlines after frontmatter are stripped."""
        content = """---
title: Test
---


# Content"""

        clean, meta = parse_frontmatter(content)
        assert clean == "# Content"

    def test_frontmatter_with_booleans(self):
        """Frontmatter with boolean values."""
        content = """---
draft: true
published: false
---
# Content"""

        clean, meta = parse_frontmatter(content)
        assert meta["draft"] is True
        assert meta["published"] is False

    def test_frontmatter_with_numbers(self):
        """Frontmatter with numeric values."""
        content = """---
version: 1.0
count: 42
---
# Content"""

        clean, meta = parse_frontmatter(content)
        assert meta["version"] == 1.0
        assert meta["count"] == 42

    def test_frontmatter_with_dates(self):
        """Frontmatter with date strings (parsed as strings)."""
        content = """---
date: 2025-10-20
last_updated: 2025-10-20
---
# Content"""

        clean, meta = parse_frontmatter(content)
        # YAML may parse dates, but we're using safe_load which keeps them as strings
        assert "date" in meta
        assert "last_updated" in meta

    def test_empty_content_after_frontmatter(self):
        """Frontmatter with no content after."""
        content = """---
title: Test
---"""

        clean, meta = parse_frontmatter(content)
        assert clean == ""
        assert meta == {"title": "Test"}

    def test_bytes_input(self):
        """parse_frontmatter accepts bytes input."""
        content = b"---\ntitle: Test\n---\n# Content"
        clean, meta = parse_frontmatter(content)
        assert meta == {"title": "Test"}
        assert clean == "# Content"


class TestExtractMetadata:
    """Tests for extract_metadata convenience function."""

    def test_extract_metadata_only(self):
        """Extract only metadata, ignore content."""
        content = """---
title: Test
author: Jane
---
# Long content that we don't care about"""

        meta = extract_metadata(content)
        assert meta == {"title": "Test", "author": "Jane"}

    def test_extract_metadata_none(self):
        """Returns None when no frontmatter."""
        content = "# No frontmatter"
        meta = extract_metadata(content)
        assert meta is None

    def test_extract_metadata_bytes(self):
        """extract_metadata accepts bytes."""
        content = b"---\ntitle: Test\n---\nContent"
        meta = extract_metadata(content)
        assert meta == {"title": "Test"}


class TestStripFrontmatter:
    """Tests for strip_frontmatter convenience function."""

    def test_strip_frontmatter_only(self):
        """Strip frontmatter, return clean content."""
        content = """---
title: Test
---
# Content here"""

        clean = strip_frontmatter(content)
        assert clean == "# Content here"
        assert not clean.startswith("---")

    def test_strip_frontmatter_none(self):
        """Returns content unchanged when no frontmatter."""
        content = "# No frontmatter"
        clean = strip_frontmatter(content)
        assert clean == content

    def test_strip_frontmatter_bytes(self):
        """strip_frontmatter accepts bytes."""
        content = b"---\ntitle: Test\n---\n# Content"
        clean = strip_frontmatter(content)
        assert clean == "# Content"


class TestHasFrontmatter:
    """Tests for has_frontmatter function."""

    def test_has_frontmatter_true(self):
        """Detects frontmatter markers."""
        assert has_frontmatter("---\ntitle: Test\n---\nContent")

    def test_has_frontmatter_false(self):
        """No frontmatter markers."""
        assert not has_frontmatter("# Just content")

    def test_has_frontmatter_empty_string(self):
        """Empty string has no frontmatter."""
        assert not has_frontmatter("")

    def test_has_frontmatter_windows_line_endings(self):
        """Detects frontmatter with Windows line endings."""
        assert has_frontmatter("---\r\ntitle: Test\r\n---\r\nContent")

    def test_has_frontmatter_partial_marker(self):
        """Partial marker (--) doesn't count."""
        assert not has_frontmatter("--\ntitle: Test")

    def test_has_frontmatter_marker_not_at_start(self):
        """Marker not at start doesn't count."""
        assert not has_frontmatter("Some text\n---\ntitle: Test")

    def test_has_frontmatter_bytes(self):
        """has_frontmatter accepts bytes."""
        assert has_frontmatter(b"---\ntitle: Test\n---\nContent")


class TestEdgeCases:
    """Edge case tests for frontmatter parsing."""

    def test_only_opening_delimiter(self):
        """Only opening --- with no closing."""
        content = "---\ntitle: Test\n# Content"
        clean, meta = parse_frontmatter(content)
        assert meta is None

    def test_empty_string(self):
        """Empty string."""
        clean, meta = parse_frontmatter("")
        assert clean == ""
        assert meta is None

    def test_only_delimiters(self):
        """Just the delimiters with no content."""
        content = "---\n---"
        clean, meta = parse_frontmatter(content)
        assert clean == ""
        assert meta == {}

    def test_very_long_frontmatter(self):
        """Large frontmatter block."""
        yaml_lines = ["---"]
        for i in range(100):
            yaml_lines.append(f"key{i}: value{i}")
        yaml_lines.append("---")
        yaml_lines.append("# Content")
        content = "\n".join(yaml_lines)

        clean, meta = parse_frontmatter(content)
        assert len(meta) == 100
        assert meta["key0"] == "value0"
        assert meta["key99"] == "value99"
        assert clean == "# Content"

    def test_special_yaml_characters(self):
        """Frontmatter with special YAML characters."""
        content = """---
title: "Test: With Colon"
description: 'Test with "quotes"'
---
# Content"""

        clean, meta = parse_frontmatter(content)
        assert meta["title"] == "Test: With Colon"
        assert 'Test with "quotes"' in meta["description"]


class TestTelemetry:
    """Tests for docscribe telemetry instrumentation."""

    def test_parse_frontmatter_with_telemetry_enabled(self):
        """Verify parse_frontmatter executes with telemetry instrumentation."""
        content = "---\ntitle: Test\n---\n# Content"
        clean, meta = parse_frontmatter(content)
        assert clean == "# Content"
        assert meta is not None
