"""Exceptions for documentation processing."""

from __future__ import annotations


class ParseError(Exception):
    """Raised when parsing fails (malformed YAML, invalid format, etc.)."""

    pass


class FormatError(Exception):
    """Raised when content doesn't match expected format."""

    pass


__all__ = [
    "ParseError",
    "FormatError",
]
