"""Tests for format detection and document splitting."""

from pyfulmen.docscribe import detect_format, inspect_document, split_documents


class TestDetectFormat:
    """Tests for detect_format function."""

    def test_detect_json(self):
        """Detect JSON format."""
        assert detect_format('{"key": "value"}') == "json"
        assert detect_format("[1, 2, 3]") == "json"

    def test_detect_markdown(self):
        """Detect markdown format."""
        assert detect_format("# Heading\nContent") == "markdown"
        assert detect_format("---\ntitle: Test\n---\n# Content") == "markdown"
        assert detect_format("[link](url)") == "markdown"
        assert detect_format("**bold** text") == "markdown"

    def test_detect_yaml(self):
        """Detect YAML format."""
        assert detect_format("key: value\nanother: test") == "yaml"

    def test_detect_multi_yaml(self):
        """Detect YAML stream (multi-document)."""
        yaml_stream = """doc: 1
---
doc: 2
---
doc: 3"""
        assert detect_format(yaml_stream) == "multi-yaml"

    def test_detect_multi_markdown(self):
        """Detect concatenated markdown documents."""
        multi_md = """# Doc 1
Content 1
---
# Doc 2
Content 2"""
        assert detect_format(multi_md) == "multi-markdown"

    def test_detect_text(self):
        """Plain text when no specific format detected."""
        assert detect_format("Just some plain text") == "text"
        assert detect_format("") == "text"

    def test_detect_toml(self):
        """Detect TOML format."""
        assert detect_format("[section]\nkey = value") == "toml"

    def test_detect_with_bytes(self):
        """detect_format accepts bytes."""
        assert detect_format(b'{"key": "value"}') == "json"


class TestSplitDocuments:
    """Tests for split_documents function."""

    def test_split_yaml_stream(self):
        """Split YAML stream into documents."""
        yaml_stream = """doc: 1
name: first
---
doc: 2
name: second
---
doc: 3
name: third"""

        docs = split_documents(yaml_stream)
        assert len(docs) == 3
        assert "doc: 1" in docs[0]
        assert "doc: 2" in docs[1]
        assert "doc: 3" in docs[2]

    def test_split_yaml_with_ellipsis(self):
        """Split YAML using ... end marker."""
        yaml_stream = """doc: 1
...
doc: 2
...
doc: 3"""

        docs = split_documents(yaml_stream)
        assert len(docs) == 3

    def test_split_markdown_documents(self):
        """Split concatenated markdown."""
        multi_md = """---
title: Doc 1
---
# First Document
Content 1
---
---
title: Doc 2
---
# Second Document
Content 2"""

        docs = split_documents(multi_md)
        assert len(docs) == 2
        assert "First Document" in docs[0]
        assert "Second Document" in docs[1]

    def test_split_single_document(self):
        """Single document returns list with one item."""
        content = "# Just one document"
        docs = split_documents(content)
        assert len(docs) == 1
        assert docs[0] == content

    def test_split_with_frontmatter_not_separator(self):
        """Frontmatter delimiters not treated as doc separators."""
        content = """---
title: Test
---
# Content here
Not a separator"""

        docs = split_documents(content)
        assert len(docs) == 1
        assert "title: Test" in docs[0]

    def test_split_empty_documents_filtered(self):
        """Empty documents are filtered out."""
        yaml_stream = "---\n---\ndoc: real"
        docs = split_documents(yaml_stream)
        # Empty docs should be filtered
        assert all(doc.strip() for doc in docs)

    def test_split_with_bytes(self):
        """split_documents accepts bytes."""
        yaml_stream = b"doc: 1\n---\ndoc: 2"
        docs = split_documents(yaml_stream)
        assert len(docs) == 2


class TestInspectDocument:
    """Tests for inspect_document function."""

    def test_inspect_markdown_with_frontmatter(self):
        """Inspect markdown with frontmatter."""
        content = """---
title: Test
---
# Section 1
## Subsection
# Section 2"""

        info = inspect_document(content)
        assert info.has_frontmatter is True
        assert info.format == "markdown"
        assert info.header_count == 3
        assert info.line_count == 6
        assert info.estimated_sections >= 2

    def test_inspect_plain_markdown(self):
        """Inspect markdown without frontmatter."""
        content = """# Heading 1
Content
## Heading 2
More content"""

        info = inspect_document(content)
        assert info.has_frontmatter is False
        assert info.format == "markdown"
        assert info.header_count == 2

    def test_inspect_json(self):
        """Inspect JSON document."""
        content = '{"key": "value", "nested": {"data": true}}'

        info = inspect_document(content)
        assert info.format == "json"
        assert info.has_frontmatter is False
        assert info.line_count == 1

    def test_inspect_yaml_stream(self):
        """Inspect YAML stream."""
        content = """doc: 1
---
doc: 2
---
doc: 3"""

        info = inspect_document(content)
        assert info.format == "multi-yaml"
        assert info.line_count == 5

    def test_inspect_empty_content(self):
        """Inspect empty content."""
        info = inspect_document("")
        assert info.format == "text"
        assert info.line_count == 1
        assert info.header_count == 0
        assert info.estimated_sections == 1

    def test_inspect_large_document(self):
        """Inspect large document quickly."""
        lines = ["# Header"] + ["Content line"] * 1000
        content = "\n".join(lines)

        info = inspect_document(content)
        assert info.line_count == 1001
        assert info.header_count == 1

    def test_inspect_with_bytes(self):
        """inspect_document accepts bytes."""
        content = b"# Heading\nContent"
        info = inspect_document(content)
        assert info.format == "markdown"
        assert info.header_count == 1


class TestEdgeCases:
    """Edge cases for format detection and splitting."""

    def test_detect_format_whitespace_only(self):
        """Whitespace-only content is text."""
        assert detect_format("   \n  \n  ") == "text"

    def test_split_documents_preserves_content(self):
        """Splitting preserves all content."""
        yaml_stream = """doc: 1
data: value1
---
doc: 2
data: value2"""

        docs = split_documents(yaml_stream)
        # Join back and compare
        rejoined = "\n---\n".join(docs)
        assert "value1" in rejoined
        assert "value2" in rejoined

    def test_detect_json_with_whitespace(self):
        """JSON detection works with leading whitespace."""
        content = """
  {"key": "value"}"""
        assert detect_format(content) == "json"

    def test_split_yaml_single_separator(self):
        """Single separator creates two documents."""
        yaml = "doc: 1\n---\ndoc: 2"
        docs = split_documents(yaml)
        assert len(docs) == 2

    def test_inspect_document_estimates_sections(self):
        """Section estimation based on top-level headers."""
        content = """# Section 1
## Subsection 1.1
## Subsection 1.2
# Section 2
## Subsection 2.1"""

        info = inspect_document(content)
        # Should estimate 2 sections (two # headers)
        assert info.estimated_sections == 2
