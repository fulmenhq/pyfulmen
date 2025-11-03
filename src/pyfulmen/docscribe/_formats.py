"""Format detection and multi-document splitting utilities."""

from __future__ import annotations

import json
import re

from ._frontmatter import has_frontmatter
from .models import DocumentInfo


def detect_format(content: str | bytes) -> str:
    """Detect content format using heuristics.

    Does NOT rely on file extensions - uses content analysis.

    Args:
        content: Document content

    Returns:
        Format string: 'markdown', 'yaml', 'json', 'toml', 'text',
                      'multi-yaml', or 'multi-markdown'

    Example:
        >>> detect_format('{"key": "value"}')
        'json'
        >>> detect_format('# Heading\\nContent')
        'markdown'
        >>> detect_format('---\\n...\\n---\\n...')
        'multi-yaml'
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    content_stripped = content.strip()

    if not content_stripped:
        return "text"

    # Check for multi-document formats first
    if _is_multi_yaml(content):
        return "multi-yaml"
    if _is_multi_markdown(content):
        return "multi-markdown"

    # Check for JSON (starts with { or [)
    if content_stripped.startswith(("{", "[")):
        try:
            json.loads(content_stripped)
            return "json"
        except json.JSONDecodeError:
            pass

    # Check for YAML (key: value patterns)
    if _looks_like_yaml(content_stripped):
        return "yaml"

    # Check for markdown (headers, has frontmatter, or markdown syntax)
    if _looks_like_markdown(content_stripped):
        return "markdown"

    # Check for TOML (basic detection)
    if _looks_like_toml(content_stripped):
        return "toml"

    # Default to text
    return "text"


def split_documents(content: str | bytes) -> list[str]:
    """Split multi-document content into individual documents.

    Handles:
    - YAML streams (documents separated by ---)
    - Concatenated markdown (documents separated by ---)

    Critical: Distinguishes between:
    - Frontmatter delimiters (at document start)
    - Document separators (between documents)

    Args:
        content: Multi-document content

    Returns:
        List of individual document strings

    Example:
        >>> yaml_stream = "doc: 1\\n---\\ndoc: 2\\n---\\ndoc: 3"
        >>> docs = split_documents(yaml_stream)
        >>> len(docs)
        3
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    format_type = detect_format(content)

    if format_type == "multi-yaml":
        return _split_yaml_stream(content)
    elif format_type == "multi-markdown":
        return _split_markdown_documents(content)
    else:
        # Single document
        return [content]


def inspect_document(content: str | bytes) -> DocumentInfo:
    """Quick inspection without full parsing.

    Fast analysis for document characteristics without parsing headers
    or validating all syntax.

    Args:
        content: Document content

    Returns:
        DocumentInfo with quick metrics

    Example:
        >>> content = "---\\ntitle: Test\\n---\\n# Section\\nContent"
        >>> info = inspect_document(content)
        >>> info.has_frontmatter
        True
        >>> info.format
        'markdown'
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    lines = content.split("\n")
    has_fm = has_frontmatter(content)
    detected_format = detect_format(content)

    # Count headers (simple # count)
    header_count = sum(1 for line in lines if line.strip().startswith("#"))

    # Estimate sections (only level 1 headers)
    estimated_sections = sum(1 for line in lines if line.strip().startswith("# ") or line.strip() == "#")

    return DocumentInfo(
        has_frontmatter=has_fm,
        header_count=header_count,
        format=detected_format,
        line_count=len(lines),
        estimated_sections=max(1, estimated_sections),  # At least 1 section
    )


def _is_multi_yaml(content: str) -> bool:
    """Check if content is a YAML stream (multiple documents)."""
    # YAML stream has document separator: \n---\n or \n...\n
    # Must have at least 1 separator to be multi-doc
    # AND must look like YAML content (not markdown)

    # Check if content starts with frontmatter
    lines = content.split("\n")
    separator_count = content.count("\n---\n") + content.count("\n...\n")

    # If starts with frontmatter, subtract 1 (the closing delimiter)
    if lines and lines[0].strip() == "---":
        # This might be frontmatter, not a YAML doc
        # Only count as multi-yaml if we have separators AFTER frontmatter
        separator_count -= 1

    # Need at least 1 separator
    if separator_count < 1:
        return False

    # Also check that it looks like YAML (not markdown)
    # If it has markdown headers, it's probably multi-markdown, not multi-yaml
    if _looks_like_markdown(content):
        return False

    # Should have YAML-like content
    return _looks_like_yaml(content)


def _is_multi_markdown(content: str) -> bool:
    """Check if content is concatenated markdown documents."""
    # Look for document separators that aren't frontmatter
    # Pattern: \n---\n followed by content (not at start of doc)
    lines = content.split("\n")

    # Count separators that are NOT frontmatter
    separator_count = 0
    in_frontmatter = False

    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            continue

        if in_frontmatter and line.strip() == "---":
            in_frontmatter = False
            continue

        if not in_frontmatter and line.strip() == "---":
            # This is a document separator
            separator_count += 1

    return separator_count >= 1


def _looks_like_yaml(content: str) -> bool:
    """Heuristic check for YAML content."""
    # Look for key: value patterns
    yaml_pattern = re.compile(r"^\w+:\s*.+$", re.MULTILINE)
    matches = yaml_pattern.findall(content)
    return len(matches) >= 2


def _looks_like_markdown(content: str) -> bool:
    """Heuristic check for markdown content."""
    # Has frontmatter, headers, or markdown syntax
    if has_frontmatter(content):
        return True

    # Check for headers
    if re.search(r"^#{1,6}\s+", content, re.MULTILINE):
        return True

    # Check for markdown links or emphasis
    return bool(re.search(r"\[.+\]\(.+\)", content) or re.search(r"\*\*.+\*\*|__.+__", content))


def _looks_like_toml(content: str) -> bool:
    """Heuristic check for TOML content."""
    # Look for [section] headers or key = value
    if re.search(r"^\[.+\]$", content, re.MULTILINE):
        return True
    return bool(re.search(r"^\w+\s*=\s*.+$", content, re.MULTILINE))


def _split_yaml_stream(content: str) -> list[str]:
    """Split YAML stream into individual documents."""
    # YAML uses --- as document separator
    # Also supports ... as document end marker
    docs = []
    current_doc = []

    lines = content.split("\n")

    for line in lines:
        if line.strip() in ("---", "..."):
            if current_doc:
                docs.append("\n".join(current_doc))
                current_doc = []
        else:
            current_doc.append(line)

    # Add final document
    if current_doc:
        docs.append("\n".join(current_doc))

    return [doc.strip() for doc in docs if doc.strip()]


def _split_markdown_documents(content: str) -> list[str]:
    """Split concatenated markdown documents."""
    docs = []
    current_doc = []
    in_frontmatter = False
    at_doc_start = True

    lines = content.split("\n")

    for line in lines:
        # Check if this is the start of a document with frontmatter
        if at_doc_start and line.strip() == "---":
            in_frontmatter = True
            current_doc.append(line)
            at_doc_start = False
            continue

        # Check if frontmatter is ending
        if in_frontmatter and line.strip() == "---":
            in_frontmatter = False
            current_doc.append(line)
            continue

        # Check for document separator (not at doc start, not in frontmatter)
        if not in_frontmatter and not at_doc_start and line.strip() == "---":
            # This is a document separator
            if current_doc:
                docs.append("\n".join(current_doc))
                current_doc = []
                # Reset state for next document
                at_doc_start = True
            continue

        # Regular content line
        current_doc.append(line)
        at_doc_start = False

    # Add final document
    if current_doc:
        docs.append("\n".join(current_doc))

    return [doc.strip() for doc in docs if doc.strip()]


__all__ = [
    "detect_format",
    "split_documents",
    "inspect_document",
]
