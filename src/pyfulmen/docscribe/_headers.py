"""Header extraction utilities for markdown documents."""

from __future__ import annotations

import re
from typing import Any

from .models import DocumentHeader


def extract_headers(content: str | bytes) -> list[DocumentHeader]:
    """Extract all headers from markdown content.

    Supports ATX-style headers (#, ##, ###, etc.) and includes line numbers
    for source mapping. Generates URL-safe anchor slugs for navigation.

    Args:
        content: Markdown content (string or bytes)

    Returns:
        List of DocumentHeader objects with level, text, anchor, and line_number

    Example:
        >>> content = "# Title\\n## Section\\n### Subsection"
        >>> headers = extract_headers(content)
        >>> print(headers[0].level, headers[0].text)
        1 Title
        >>> print(headers[0].anchor)
        title
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    headers = []
    lines = content.split("\n")

    # ATX-style header pattern: # Header text
    atx_pattern = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#*)?$")

    for line_num, line in enumerate(lines, start=1):
        # Check for ATX-style headers
        match = atx_pattern.match(line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            anchor = _generate_anchor(text)

            headers.append(
                DocumentHeader(
                    level=level,
                    text=text,
                    anchor=anchor,
                    line_number=line_num,
                )
            )

    return headers


def generate_outline(content: str | bytes, max_depth: int = 6) -> list[dict[str, Any]]:
    """Generate hierarchical outline from markdown headers.

    Creates a nested structure suitable for table of contents rendering.
    Headers are organized by their level to create a tree structure.

    Args:
        content: Markdown content
        max_depth: Maximum header level to include (1-6)

    Returns:
        List of outline nodes with 'level', 'text', 'anchor', 'children' keys

    Example:
        >>> content = "# Main\\n## Sub1\\n## Sub2\\n### SubSub"
        >>> outline = generate_outline(content, max_depth=2)
        >>> print(len(outline))  # Just main headers
        1
    """
    headers = extract_headers(content)

    # Filter by max depth
    filtered_headers = [h for h in headers if h.level <= max_depth]

    # Build hierarchical structure
    outline: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []

    for header in filtered_headers:
        node = {
            "level": header.level,
            "text": header.text,
            "anchor": header.anchor,
            "line_number": header.line_number,
            "children": [],
        }

        # Find parent node at appropriate level
        while stack and stack[-1]["level"] >= header.level:
            stack.pop()

        if stack:
            # Add as child of parent
            stack[-1]["children"].append(node)
        else:
            # Top-level node
            outline.append(node)

        stack.append(node)

    return outline


def search_headers(content: str | bytes, pattern: str) -> list[DocumentHeader]:
    """Find headers matching a pattern.

    Case-insensitive search for headers containing the pattern.

    Args:
        content: Markdown content
        pattern: Search pattern (case-insensitive)

    Returns:
        List of matching headers

    Example:
        >>> content = "# Installation\\n## Usage\\n# Configuration"
        >>> results = search_headers(content, "install")
        >>> print(results[0].text)
        Installation
    """
    headers = extract_headers(content)
    pattern_lower = pattern.lower()
    return [h for h in headers if pattern_lower in h.text.lower()]


def _generate_anchor(text: str) -> str:
    """Generate URL-safe anchor slug from header text.

    Args:
        text: Header text

    Returns:
        URL-safe anchor slug

    Example:
        >>> _generate_anchor("Getting Started")
        'getting-started'
        >>> _generate_anchor("API Reference (v2.0)")
        'api-reference-v20'
    """
    # Convert to lowercase
    slug = text.lower()

    # Replace spaces with hyphens first (before removing special chars)
    slug = slug.replace(" ", "-")

    # Remove special chars (keep only word chars and hyphens)
    slug = re.sub(r"[^\w-]", "", slug)

    # Collapse multiple hyphens (3+) to single hyphen, preserve double-hyphens
    slug = re.sub(r"-{3,}", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    return slug


__all__ = [
    "extract_headers",
    "generate_outline",
    "search_headers",
]
