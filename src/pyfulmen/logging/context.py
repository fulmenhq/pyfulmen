"""Correlation context management for distributed tracing.

Provides thread-local storage for correlation IDs and context propagation utilities.
This allows correlation IDs to flow automatically through logging calls without
explicit passing.

Example:
    >>> from pyfulmen.logging import Logger, set_correlation_id
    >>> from pyfulmen.logging.context import correlation_context
    >>>
    >>> logger = Logger(service="myapp", profile="STRUCTURED")
    >>>
    >>> # Manual correlation ID setting
    >>> set_correlation_id("custom-correlation-id")
    >>> logger.info("This log will have the correlation ID")
    >>>
    >>> # Context manager for scoped correlation
    >>> with correlation_context(correlation_id="request-123"):
    ...     logger.info("Processing request")  # Uses request-123
    ...     # Nested contexts inherit parent correlation_id
    ...     with correlation_context():
    ...         logger.info("Nested operation")  # Still uses request-123
"""

import threading
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from ..foundry import generate_correlation_id

# Thread-local storage for correlation context
_context_storage = threading.local()


def get_correlation_id() -> str | None:
    """Get the current thread's correlation ID.

    Returns:
        Current correlation ID or None if not set

    Example:
        >>> from pyfulmen.logging.context import set_correlation_id, get_correlation_id
        >>> set_correlation_id("abc-123")
        >>> get_correlation_id()
        'abc-123'
    """
    return getattr(_context_storage, "correlation_id", None)


def set_correlation_id(correlation_id: str | None) -> None:
    """Set the current thread's correlation ID.

    Args:
        correlation_id: Correlation ID to set, or None to clear

    Example:
        >>> from pyfulmen.logging.context import set_correlation_id
        >>> set_correlation_id("request-456")
        >>> # All subsequent logs in this thread will use request-456
    """
    if correlation_id is None:
        if hasattr(_context_storage, "correlation_id"):
            delattr(_context_storage, "correlation_id")
    else:
        _context_storage.correlation_id = correlation_id


def get_context() -> dict[str, Any]:
    """Get the current thread's logging context.

    Returns:
        Dictionary of context values (may be empty)

    Example:
        >>> from pyfulmen.logging.context import set_context_value, get_context
        >>> set_context_value("user_id", "user-123")
        >>> get_context()
        {'user_id': 'user-123'}
    """
    if not hasattr(_context_storage, "context"):
        _context_storage.context = {}
    return _context_storage.context


def set_context_value(key: str, value: Any) -> None:
    """Set a value in the current thread's logging context.

    Args:
        key: Context key
        value: Context value

    Example:
        >>> from pyfulmen.logging.context import set_context_value
        >>> set_context_value("user_id", "user-123")
        >>> set_context_value("tenant_id", "tenant-456")
    """
    ctx = get_context()
    ctx[key] = value


def clear_context() -> None:
    """Clear the current thread's logging context.

    Example:
        >>> from pyfulmen.logging.context import clear_context, get_context
        >>> set_context_value("key", "value")
        >>> clear_context()
        >>> get_context()
        {}
    """
    if hasattr(_context_storage, "context"):
        _context_storage.context = {}


@contextmanager
def correlation_context(
    correlation_id: str | None = None,
    **context_values: Any,
) -> Generator[str, None, None]:
    """Context manager for scoped correlation ID and context propagation.

    If correlation_id is not provided, generates a new UUIDv7. The correlation ID
    is automatically propagated to all log calls within the context. Additional
    context values can be provided as keyword arguments.

    Args:
        correlation_id: Explicit correlation ID (generates new if None)
        **context_values: Additional context values to set

    Yields:
        The correlation ID being used for this context

    Example:
        >>> from pyfulmen.logging import Logger
        >>> from pyfulmen.logging.context import correlation_context
        >>>
        >>> logger = Logger(service="myapp", profile="STRUCTURED")
        >>>
        >>> with correlation_context() as corr_id:
        ...     logger.info("Starting request")  # Auto-generated correlation_id
        ...     # Do work
        ...     logger.info("Request complete")  # Same correlation_id
        >>>
        >>> # Explicit correlation ID
        >>> with correlation_context(correlation_id="req-123", user_id="user-456"):
        ...     logger.info("Processing")  # Uses req-123, includes user_id
    """
    # Save previous state
    previous_correlation_id = get_correlation_id()
    previous_context = get_context().copy()

    # Set new correlation ID (generate if not provided)
    new_correlation_id = correlation_id or generate_correlation_id()
    set_correlation_id(new_correlation_id)

    # Set additional context values
    for key, value in context_values.items():
        set_context_value(key, value)

    try:
        yield new_correlation_id
    finally:
        # Restore previous state
        set_correlation_id(previous_correlation_id)
        clear_context()
        for key, value in previous_context.items():
            set_context_value(key, value)


def extract_correlation_id_from_headers(
    headers: dict[str, str],
    header_names: list[str] | None = None,
) -> str | None:
    """Extract correlation ID from HTTP headers.

    Searches for correlation ID in common header names. Case-insensitive matching.

    Args:
        headers: HTTP headers dictionary
        header_names: Custom header names to check (defaults to common names)

    Returns:
        Correlation ID from headers or None if not found

    Example:
        >>> from pyfulmen.logging.context import extract_correlation_id_from_headers
        >>> headers = {"X-Correlation-ID": "req-789"}
        >>> extract_correlation_id_from_headers(headers)
        'req-789'
        >>>
        >>> # Flask/WSGI example
        >>> from flask import request
        >>> correlation_id = extract_correlation_id_from_headers(request.headers)
    """
    if header_names is None:
        header_names = [
            "X-Correlation-ID",
            "X-Correlation-Id",
            "X-Request-ID",
            "X-Request-Id",
            "Request-ID",
            "Request-Id",
        ]

    # Normalize headers to lowercase for case-insensitive matching
    headers_lower = {k.lower(): v for k, v in headers.items()}

    # Check each header name (case-insensitive)
    for name in header_names:
        value = headers_lower.get(name.lower())
        if value:
            return value

    return None


__all__ = [
    "get_correlation_id",
    "set_correlation_id",
    "get_context",
    "set_context_value",
    "clear_context",
    "correlation_context",
    "extract_correlation_id_from_headers",
]
