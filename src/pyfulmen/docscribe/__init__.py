"""Standalone documentation processing module.

Provides lightweight processing capabilities for markdown and YAML documentation
from any source (Crucible, Cosmography, local files, etc.). Handles frontmatter
extraction, header parsing, format detection, and multi-document splitting.

This module is intentionally source-agnostic - it processes content without
coupling to specific storage or access patterns.

Example:
    >>> from pyfulmen import documentation
    >>>
    >>> # Parse frontmatter from any source
    >>> content, metadata = documentation.parse_frontmatter(markdown_text)
    >>>
    >>> # Quick inspection
    >>> info = documentation.inspect_document(content)
    >>> print(f"Format: {info.format}, Sections: {info.estimated_sections}")
    >>>
    >>> # Extract headers
    >>> headers = documentation.extract_headers(content)
    >>> for h in headers:
    ...     print(f"{'  ' * (h.level - 1)}{h.text}")
    >>>
    >>> # Multi-document handling
    >>> docs = documentation.split_documents(yaml_stream)
"""

from __future__ import annotations

# Import all public APIs
from ._formats import detect_format, inspect_document, split_documents
from ._frontmatter import extract_metadata, has_frontmatter, parse_frontmatter, strip_frontmatter
from ._headers import extract_headers, generate_outline, search_headers
from .errors import FormatError, ParseError
from .models import DocumentHeader, DocumentInfo

__version__ = "0.1.4"

__all__ = [
    # Frontmatter processing (Phase 1 - Mandatory)
    "parse_frontmatter",
    "extract_metadata",
    "strip_frontmatter",
    "has_frontmatter",
    # Header extraction (Phase 1 - Mandatory)
    "extract_headers",
    "search_headers",
    # Format detection (Phase 1 - Mandatory)
    "detect_format",
    # Document inspection (Phase 1 - Mandatory)
    "inspect_document",
    # Multi-document handling (Phase 1 - Mandatory)
    "split_documents",
    # Outline generation (Phase 2 - Enhanced)
    "generate_outline",
    # Data models
    "DocumentHeader",
    "DocumentInfo",
    # Errors
    "ParseError",
    "FormatError",
]
