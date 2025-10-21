"""Lightweight frontmatter extraction for markdown documents.

Provides ~50 LOC parser for YAML frontmatter without heavy dependencies.
Uses pyyaml for safe parsing of frontmatter blocks.

This module is source-agnostic - it works with content from Crucible,
Cosmography, local files, or any other documentation source.
"""

from __future__ import annotations

from typing import Any

import yaml

from .errors import ParseError


def parse_frontmatter(content: str | bytes) -> tuple[str, dict[str, Any] | None]:
    """Extract YAML frontmatter from markdown content.

    Frontmatter must be delimited by --- at start and end, e.g.:
        ---
        title: My Document
        author: Jane Doe
        ---
        # Document content here

    Args:
        content: Raw markdown content (may or may not have frontmatter)
                Can be string or bytes (will be decoded as UTF-8)

    Returns:
        Tuple of (clean_content, frontmatter_dict)
        - clean_content: Markdown with frontmatter removed
        - frontmatter_dict: Parsed YAML metadata, or None if no frontmatter

    Raises:
        ParseError: If frontmatter contains malformed YAML

    Example:
        >>> content = "---\\ntitle: Test\\n---\\n# Hello"
        >>> clean, meta = parse_frontmatter(content)
        >>> print(clean)
        # Hello
        >>> print(meta)
        {'title': 'Test'}
    """
    # Handle bytes input
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    # Check for frontmatter start marker
    if not content.startswith("---\n") and not content.startswith("---\r\n"):
        return content, None

    # Determine line ending style and yaml start position
    yaml_start = 4 if content[3] == "\n" else 5  # After opening ---\n or ---\r\n

    # Special case: empty frontmatter (---\n---\n or ---\r\n---\r\n)
    if content[yaml_start : yaml_start + 3] == "---":
        # Check if there's a newline after the closing ---
        next_pos = yaml_start + 3
        if next_pos < len(content) and content[next_pos] in ("\n", "\r"):
            # Empty frontmatter
            newline_len = 2 if content[next_pos : next_pos + 2] == "\r\n" else 1
            content_start = next_pos + newline_len
            clean_content = content[content_start:].lstrip("\n\r")
            return clean_content, {}
        elif next_pos == len(content):
            # Content ends with closing delimiter
            return "", {}

    # Find closing delimiter patterns: \n---\n, \n---\r\n, or \n--- at end
    closing_patterns = [
        ("\n---\n", "\n"),
        ("\n---\r\n", "\r\n"),
        ("\r\n---\r\n", "\r\n"),
        ("\r\n---\n", "\n"),
    ]

    end_idx = -1
    newline_after = "\n"

    for pattern, nl in closing_patterns:
        idx = content.find(pattern, yaml_start)
        if idx != -1:
            end_idx = idx
            newline_after = nl
            break

    # Also check for closing --- at end of string (no newline after)
    if end_idx == -1:
        for ending in ["\n---", "\r\n---"]:
            if content.endswith(ending):
                end_idx = content.rfind(ending)
                newline_after = ""  # No newline after
                break

    if end_idx == -1:
        # No closing delimiter - treat whole thing as content without frontmatter
        return content, None

    # Extract YAML block
    yaml_content = content[yaml_start:end_idx]

    # Extract clean content (skip closing delimiter and newline after it)
    # end_idx points to the \n before ---
    # We need to skip: \n---\n or \n---\r\n
    closing_delimiter_len = 1 + 3 + len(newline_after)  # \n + --- + \n or \r\n
    content_start = end_idx + closing_delimiter_len
    clean_content = content[content_start:].lstrip("\n\r")

    # Parse YAML
    try:
        metadata = yaml.safe_load(yaml_content)
        # yaml.safe_load returns None for empty YAML
        if metadata is None:
            metadata = {}
        return clean_content, metadata
    except yaml.YAMLError as e:
        raise ParseError(f"Invalid YAML frontmatter: {e}") from e


def extract_metadata(content: str | bytes) -> dict[str, Any] | None:
    """Extract only metadata from frontmatter.

    Convenience function for when you only need the metadata
    and don't care about the clean content.

    Args:
        content: Raw markdown content

    Returns:
        Frontmatter metadata dict, or None if no frontmatter

    Raises:
        ParseError: If frontmatter contains malformed YAML

    Example:
        >>> metadata = extract_metadata("---\\ntitle: Test\\n---\\nContent")
        >>> print(metadata)
        {'title': 'Test'}
    """
    _, metadata = parse_frontmatter(content)
    return metadata


def strip_frontmatter(content: str | bytes) -> str:
    """Strip frontmatter and return clean content.

    Convenience function for when you only need the content
    and don't care about the metadata.

    Args:
        content: Raw markdown content

    Returns:
        Clean markdown content with frontmatter removed

    Raises:
        ParseError: If frontmatter contains malformed YAML

    Example:
        >>> clean = strip_frontmatter("---\\ntitle: Test\\n---\\n# Hello")
        >>> print(clean)
        # Hello
    """
    clean_content, _ = parse_frontmatter(content)
    return clean_content


def has_frontmatter(content: str | bytes) -> bool:
    """Check if content has frontmatter without parsing.

    Fast check to determine if content starts with frontmatter markers.

    Args:
        content: Raw markdown content

    Returns:
        True if content starts with frontmatter markers (---)

    Example:
        >>> has_frontmatter("---\\ntitle: Test\\n---\\nContent")
        True
        >>> has_frontmatter("# Just content")
        False
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    return content.startswith("---\n") or content.startswith("---\r\n")


__all__ = [
    "parse_frontmatter",
    "extract_metadata",
    "strip_frontmatter",
    "has_frontmatter",
]
