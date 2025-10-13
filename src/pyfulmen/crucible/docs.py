"""Documentation access utilities for Crucible assets.

This module provides helpers to discover and read documentation
from the synced Crucible repository.

Example:
    >>> from pyfulmen.crucible import docs
    >>> docs.list_available_docs()
    ['architecture', 'guides', 'sop', 'standards']
    >>> content = docs.read_doc('guides/bootstrap-goneat.md')
"""

from pathlib import Path

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


__all__ = [
    "list_available_docs",
    "get_doc_path",
    "read_doc",
]
