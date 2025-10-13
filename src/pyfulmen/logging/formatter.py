"""Formatters for log event serialization.

Provides formatter implementations that convert log event dictionaries
into their final output format (JSON, text, console with colors, etc.).

Example:
    >>> from pyfulmen.logging.formatter import JSONFormatter, TextFormatter
    >>>
    >>> # JSON formatter for structured output
    >>> json_fmt = JSONFormatter()
    >>> event = {"timestamp": "2025-10-13T12:00:00Z", "severity": "INFO", "message": "test"}
    >>> json_fmt.format(event)
    '{"timestamp":"2025-10-13T12:00:00Z","severity":"INFO","message":"test"}'
    >>>
    >>> # Text formatter for human-readable output
    >>> text_fmt = TextFormatter()
    >>> text_fmt.format(event)
    '2025-10-13T12:00:00Z INFO test'
"""

import json
from abc import ABC, abstractmethod
from typing import Any


class Formatter(ABC):
    """Base formatter interface for log event serialization.

    Formatters convert log event dictionaries into their final string
    representation for output to sinks.
    """

    @abstractmethod
    def format(self, event: dict[str, Any]) -> str:
        """Format log event into string representation.

        Args:
            event: Log event dictionary to format

        Returns:
            Formatted event as string

        Note:
            Implementations should handle errors gracefully and return
            a safe fallback string if formatting fails.
        """


class JSONFormatter(Formatter):
    """JSON formatter for structured log output.

    Serializes log events as single-line JSON with consistent formatting.
    Uses compact representation without whitespace for efficient storage
    and transmission.

    Example:
        >>> formatter = JSONFormatter()
        >>> event = {"timestamp": "2025-10-13T12:00:00Z", "severity": "INFO", "message": "test"}
        >>> formatter.format(event)
        '{"timestamp":"2025-10-13T12:00:00Z","severity":"INFO","message":"test"}'
    """

    def __init__(self, ensure_ascii: bool = False, indent: int | None = None):
        """Initialize JSON formatter.

        Args:
            ensure_ascii: If True, escape non-ASCII characters (default: False)
            indent: If set, pretty-print with specified indent (default: None for compact)
        """
        self.ensure_ascii = ensure_ascii
        self.indent = indent

    def format(self, event: dict[str, Any]) -> str:
        """Format event as single-line JSON.

        Args:
            event: Log event dictionary to format

        Returns:
            JSON string representation

        Note:
            Returns error message as JSON if formatting fails.
        """
        try:
            if self.indent is not None:
                # Pretty-printed JSON
                return json.dumps(
                    event,
                    ensure_ascii=self.ensure_ascii,
                    indent=self.indent,
                )
            else:
                # Compact JSON (single line)
                return json.dumps(
                    event,
                    ensure_ascii=self.ensure_ascii,
                    separators=(",", ":"),
                )
        except Exception as e:
            # Fallback for formatting errors
            return json.dumps(
                {
                    "error": "JSONFormatter: Failed to format event",
                    "exception": str(e),
                    "severity": "ERROR",
                },
                ensure_ascii=True,
            )


class TextFormatter(Formatter):
    """Text formatter for human-readable log output.

    Formats log events as readable text lines with timestamp, severity,
    and message. Additional fields can be included with optional formatting.

    Example:
        >>> formatter = TextFormatter()
        >>> event = {"timestamp": "2025-10-13T12:00:00Z", "severity": "INFO", "message": "test"}
        >>> formatter.format(event)
        '2025-10-13T12:00:00Z INFO test'
    """

    def __init__(
        self,
        template: str = "{timestamp} {severity} {message}",
        include_context: bool = False,
    ):
        """Initialize text formatter.

        Args:
            template: Format template with {field} placeholders
            include_context: If True, append context dictionary to output
        """
        self.template = template
        self.include_context = include_context

    def format(self, event: dict[str, Any]) -> str:
        """Format event as human-readable text.

        Args:
            event: Log event dictionary to format

        Returns:
            Formatted text string

        Note:
            Missing fields in template are replaced with empty strings.
            Returns error message if formatting fails.
        """
        try:
            # Extract fields for template
            formatted = self.template.format(**{k: event.get(k, "") for k in event})

            # Optionally append context
            if self.include_context and "context" in event and event["context"]:
                context_str = " ".join(f"{k}={v}" for k, v in event["context"].items())
                formatted = f"{formatted} | {context_str}"

            return formatted
        except Exception as e:
            # Fallback for formatting errors
            return f"TextFormatter: Failed to format event: {e}"


class ConsoleFormatter(Formatter):
    """Console formatter with optional ANSI color support.

    Formats log events for console output with optional color coding
    based on severity level. Supports both colored and plain output.

    Example:
        >>> formatter = ConsoleFormatter(use_colors=True)
        >>> event = {"timestamp": "2025-10-13T12:00:00Z", "severity": "ERROR", "message": "Failed"}
        >>> formatter.format(event)  # Returns text with ANSI color codes
    """

    # ANSI color codes
    COLORS = {
        "TRACE": "\033[90m",  # Gray
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARN": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "FATAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def __init__(
        self,
        use_colors: bool = True,
        template: str = "{timestamp} {severity} {message}",
        include_context: bool = False,
    ):
        """Initialize console formatter.

        Args:
            use_colors: If True, use ANSI color codes for severity
            template: Format template with {field} placeholders
            include_context: If True, append context dictionary to output
        """
        self.use_colors = use_colors
        self.template = template
        self.include_context = include_context

    def format(self, event: dict[str, Any]) -> str:
        """Format event for console output with optional colors.

        Args:
            event: Log event dictionary to format

        Returns:
            Formatted console string with optional ANSI colors

        Note:
            Color codes are omitted if use_colors=False.
            Returns error message if formatting fails.
        """
        try:
            severity = event.get("severity", "INFO")

            # Format base message
            formatted = self.template.format(**{k: event.get(k, "") for k in event})

            # Add color if enabled
            if self.use_colors and severity in self.COLORS:
                color = self.COLORS[severity]
                reset = self.COLORS["RESET"]
                formatted = f"{color}{formatted}{reset}"

            # Optionally append context
            if self.include_context and "context" in event and event["context"]:
                context_str = " ".join(f"{k}={v}" for k, v in event["context"].items())
                formatted = f"{formatted} | {context_str}"

            return formatted
        except Exception as e:
            # Fallback for formatting errors
            return f"ConsoleFormatter: Failed to format event: {e}"


__all__ = [
    "Formatter",
    "JSONFormatter",
    "TextFormatter",
    "ConsoleFormatter",
]
