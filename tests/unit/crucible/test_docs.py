"""Tests for pyfulmen.crucible.docs module."""

import pytest

from pyfulmen.crucible import docs


def test_list_available_docs():
    """Test listing documentation files."""
    doc_list = docs.list_available_docs()

    assert isinstance(doc_list, list)
    assert len(doc_list) > 0
    # Should include .md files
    assert any(d.endswith(".md") for d in doc_list)


def test_list_available_docs_with_category():
    """Test listing docs filtered by category."""
    guide_docs = docs.list_available_docs("guides")

    assert isinstance(guide_docs, list)
    # All results should be in guides/
    if len(guide_docs) > 0:
        assert all(d.startswith("guides/") for d in guide_docs)


def test_get_doc_path():
    """Test getting path to a documentation file."""
    # Test with known doc from sync
    path = docs.get_doc_path("guides/bootstrap-goneat.md")

    assert path.exists()
    assert path.suffix == ".md"
    assert "bootstrap-goneat" in path.name


def test_get_doc_path_not_found():
    """Test getting path to non-existent doc."""
    with pytest.raises(FileNotFoundError):
        docs.get_doc_path("invalid/nonexistent.md")


def test_read_doc():
    """Test reading documentation content."""
    content = docs.read_doc("guides/bootstrap-goneat.md")

    assert isinstance(content, str)
    assert len(content) > 0
    # Should contain typical markdown elements
    assert "#" in content or "Goneat" in content or "goneat" in content
