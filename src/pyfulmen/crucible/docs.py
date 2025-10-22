"""Documentation access utilities for Crucible assets.

This module provides helpers to discover and read documentation
from the synced Crucible repository. It delegates to the standalone
pyfulmen.docscribe module for frontmatter parsing and processing.

Example:
    >>> from pyfulmen.crucible import docs
    >>> docs.list_available_docs()
    ['architecture', 'guides', 'sop', 'standards']
    >>> content = docs.read_doc('guides/bootstrap-goneat.md')

    # Enhanced frontmatter parsing (v0.1.4+) - delegates to docscribe module
    >>> clean_content = docs.get_documentation('standards/observability/logging.md')
    >>> metadata = docs.get_documentation_metadata('standards/observability/logging.md')
    >>> content, meta = docs.get_documentation_with_metadata('guides/bootstrap-goneat.md')

Note:
    For source-agnostic documentation processing, use pyfulmen.docscribe directly.
    This module is specifically for Crucible asset access.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import docscribe
from . import _paths


def list_available_docs(category: str | None = None) -> list[str]:
    """List available documentation files.

    Args:
        category: Optional category filter (e.g., 'guides', 'standards')

    Returns:
        List of documentation paths relative to docs/crucible-py/

    Example:
        >>> list_available_docs()
        ['architecture/fulmen-helper-library-standard.md', ...]
        >>> list_available_docs('guides')
        ['guides/bootstrap-goneat.md', 'guides/integration-guide.md', ...]
    """
    docs_dir = _paths.get_docs_dir()

    if not docs_dir.exists():
        return []

    if category:
        search_dir = docs_dir / category
        if not search_dir.exists():
            return []
    else:
        search_dir = docs_dir

    # Find all .md files recursively
    md_files = search_dir.rglob("*.md")

    # Return paths relative to docs/crucible-py/
    relative_paths = [str(f.relative_to(docs_dir)) for f in md_files]

    return sorted(relative_paths)


def get_doc_path(path: str) -> Path:
    """Get path to a documentation file.

    Args:
        path: Documentation path relative to docs/crucible-py/
              (e.g., 'guides/bootstrap-fuldx.md')

    Returns:
        Absolute path to documentation file

    Raises:
        FileNotFoundError: If documentation file doesn't exist

    Example:
        >>> get_doc_path('guides/bootstrap-goneat.md')
        PosixPath('.../docs/crucible-py/guides/bootstrap-goneat.md')
    """
    docs_dir = _paths.get_docs_dir()
    doc_path = docs_dir / path

    if not doc_path.exists():
        raise FileNotFoundError(
            f"Documentation not found: {path}\n"
            f"Expected at: {doc_path}\n"
            "Run 'make sync-crucible' to sync Crucible assets."
        )

    return doc_path


def read_doc(path: str) -> str:
    """Read documentation markdown file.

    Args:
        path: Documentation path relative to docs/crucible-py/
              (e.g., 'guides/bootstrap-fuldx.md')

    Returns:
        Documentation content as string

    Raises:
        FileNotFoundError: If documentation file doesn't exist

    Example:
        >>> content = read_doc('guides/bootstrap-goneat.md')
        >>> 'Goneat Bootstrap Guide' in content
        True
    """
    doc_path = get_doc_path(path)
    return doc_path.read_text()


def get_documentation(path: str) -> str:
    """Get documentation content without frontmatter.

    Returns clean markdown body with YAML frontmatter removed.
    Use this when you need to render or process markdown content
    without the metadata header.

    Delegates to bridge.get_doc() for single read path, then strips frontmatter.

    Args:
        path: Documentation path relative to docs/crucible-py/
              (e.g., 'standards/observability/logging.md')

    Returns:
        Clean markdown content as string (frontmatter stripped)

    Raises:
        AssetNotFoundError: If documentation not found (includes suggestions)

    Example:
        >>> content = get_documentation('standards/observability/logging.md')
        >>> print(content[:50])
        # Observability Logging Standard...
        >>> # No YAML frontmatter in the output
    """
    from . import bridge

    raw_content, _ = bridge.get_doc(path)
    clean_content, _ = docscribe.parse_frontmatter(raw_content)
    return clean_content


def get_documentation_metadata(path: str) -> dict[str, Any] | None:
    """Get YAML frontmatter metadata from documentation.

    Extracts and parses YAML frontmatter block if present.
    Returns None if the document has no frontmatter.

    Delegates to bridge.get_doc() for single read path, then extracts metadata.

    Args:
        path: Documentation path relative to docs/crucible-py/

    Returns:
        Dictionary of frontmatter metadata, or None if no frontmatter exists

    Raises:
        AssetNotFoundError: If documentation not found (includes suggestions)
        ParseError: If frontmatter contains malformed YAML

    Example:
        >>> metadata = get_documentation_metadata('standards/observability/logging.md')
        >>> if metadata:
        ...     print(f"Status: {metadata['status']}")
        ...     print(f"Tags: {metadata.get('tags', [])}")
        Status: stable
        Tags: ['observability', 'logging']
    """
    from . import bridge

    raw_content, _ = bridge.get_doc(path)
    _, metadata = docscribe.parse_frontmatter(raw_content)
    return metadata


def get_documentation_with_metadata(path: str) -> tuple[str, dict[str, Any] | None]:
    """Get documentation content and metadata together.

    Convenience function returning both clean content and parsed frontmatter
    in a single call. More efficient than calling get_documentation() and
    get_documentation_metadata() separately.

    Delegates to bridge.get_doc() for single read path, then parses frontmatter.

    Args:
        path: Documentation path relative to docs/crucible-py/

    Returns:
        Tuple of (clean_content, metadata_dict)
        - clean_content: Markdown without frontmatter
        - metadata_dict: Parsed frontmatter, or None if absent

    Raises:
        AssetNotFoundError: If documentation not found (includes suggestions)
        ParseError: If frontmatter contains malformed YAML

    Example:
        >>> content, meta = get_documentation_with_metadata('guides/bootstrap-goneat.md')
        >>> if meta:
        ...     print(f"Reading guide by {meta.get('author', 'Unknown')}")
        ...     print(f"Last updated: {meta.get('last_updated', 'N/A')}")
        >>> render_markdown(content)
    """
    from . import bridge

    raw_content, _ = bridge.get_doc(path)
    return docscribe.parse_frontmatter(raw_content)


def _get_similar_docs(path: str, max_suggestions: int = 3) -> list[str]:
    """Get suggestions for similar documentation paths.

    Uses simple string matching to find similar paths. Looks for paths
    that share common parts with the requested path.

    Args:
        path: The path that was not found
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of similar paths (up to max_suggestions)
    """
    # Get all available docs
    all_docs = list_available_docs()

    # Simple similarity: paths that contain parts of the query
    path_parts = set(path.lower().replace(".md", "").split("/"))
    suggestions = []

    for doc_path in all_docs:
        doc_parts = set(doc_path.lower().replace(".md", "").split("/"))
        # Count matching parts
        matches = len(path_parts & doc_parts)
        if matches > 0:
            suggestions.append((matches, doc_path))

    # Sort by match count (descending) and return top N
    suggestions.sort(reverse=True, key=lambda x: x[0])
    return [path for _, path in suggestions[:max_suggestions]]


__all__ = [
    # Legacy functions (backward compatibility)
    "list_available_docs",
    "get_doc_path",
    "read_doc",
    # Enhanced functions (v0.1.4+)
    "get_documentation",
    "get_documentation_metadata",
    "get_documentation_with_metadata",
]
