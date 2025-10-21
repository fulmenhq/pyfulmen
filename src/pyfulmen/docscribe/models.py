"""Data models for documentation processing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DocumentHeader:
    """Represents a markdown header with hierarchy information.

    Attributes:
        level: Header level (1-6)
        text: Header text content
        anchor: URL-safe anchor slug for navigation
        line_number: Line number in source document (1-indexed)
    """

    level: int
    text: str
    anchor: str
    line_number: int


@dataclass
class DocumentInfo:
    """Quick inspection result without full parsing.

    Attributes:
        has_frontmatter: Whether document starts with YAML frontmatter
        header_count: Number of headers found
        format: Detected format (markdown, yaml, json, etc.)
        line_count: Total lines in document
        estimated_sections: Estimated number of major sections
    """

    has_frontmatter: bool
    header_count: int
    format: str
    line_count: int
    estimated_sections: int


__all__ = [
    "DocumentHeader",
    "DocumentInfo",
]
