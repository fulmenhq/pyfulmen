"""
Error wrapping utilities.

Provides wrap() function to augment Pathfinder errors with telemetry metadata.
"""

from datetime import UTC, datetime
from typing import Any

from .models import FulmenError, PathfinderError


def wrap(
    base_error: PathfinderError | dict,
    *,
    context: dict[str, Any] | None = None,
    original: Exception | None = None,
    severity: str | None = None,
    correlation_id: str | None = None,
    trace_id: str | None = None,
    exit_code: int | None = None,
) -> FulmenError:
    """Wrap a Pathfinder error with telemetry metadata.
    
    Auto-populates correlation_id from logging context if not provided.
    Serializes original Python exception if provided.
    
    Args:
        base_error: Pathfinder error or dict with code/message fields
        context: Structured context (non-sensitive debugging info)
        original: Original Python exception to serialize
        severity: Severity name ("info", "low", "medium", "high", "critical")
        correlation_id: Correlation ID (auto-populated from logging if None)
        trace_id: Optional OpenTelemetry trace ID
        exit_code: Process exit code (0-255)
    
    Returns:
        FulmenError with combined base + telemetry fields
    
    Example:
        >>> base = PathfinderError(code="PATH_TRAVERSAL", message="Invalid path")
        >>> err = wrap(base, severity="high", context={"path": "/etc/passwd"})
        >>> err.severity_level
        3
    """
    # Parse base error
    base = PathfinderError(**base_error) if isinstance(base_error, dict) else base_error

    # Auto-populate correlation ID from logging context
    if correlation_id is None:
        try:
            from ..logging import get_correlation_id

            correlation_id = get_correlation_id()
        except Exception:
            # Logging not available or no correlation ID set
            pass

    # Serialize original exception
    original_serialized = None
    if original is not None:
        original_serialized = _serialize_exception(original)

    # Create extended error
    return FulmenError(
        code=base.code,
        message=base.message,
        details=base.details,
        path=base.path,
        timestamp=base.timestamp or datetime.now(UTC),
        severity=severity,
        correlation_id=correlation_id,
        trace_id=trace_id,
        exit_code=exit_code,
        context=context,
        original=original_serialized,
    )


def _serialize_exception(exc: Exception) -> dict[str, Any]:
    """Serialize Python exception to dict.
    
    Args:
        exc: Python exception instance
    
    Returns:
        Dict with type, message, module, and optional traceback
    """
    result = {
        "type": type(exc).__name__,
        "message": str(exc),
        "module": type(exc).__module__,
    }

    # Include traceback if available
    if hasattr(exc, "__traceback__") and exc.__traceback__ is not None:
        import traceback

        result["traceback"] = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )

    return result
