"""
Data models for error handling.

Defines PathfinderError (base) and FulmenError (extended with telemetry).
"""

from datetime import UTC, datetime
from typing import Any

from ..foundry import FulmenDataModel


class PathfinderError(FulmenDataModel):
    """Base Pathfinder error structure.
    
    Conforms to schemas/pathfinder/v1.0.0/error-response.schema.json
    
    Attributes:
        code: Error code identifier (e.g., "CONFIG_INVALID", "PATH_TRAVERSAL")
        message: Human-readable error message
        details: Additional error details (optional)
        path: Path that caused the error (optional)
        timestamp: When the error occurred (auto-generated if omitted)
    """

    code: str
    message: str
    details: dict[str, Any] | None = None
    path: str | None = None
    timestamp: datetime | None = None

    def model_post_init(self, __context: Any) -> None:
        """Set default timestamp if not provided."""
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.now(UTC))


class FulmenError(FulmenDataModel):
    """Extended error with telemetry metadata.
    
    Extends PathfinderError with optional telemetry fields per
    schemas/error-handling/v1.0.0/error-response.schema.json
    
    This is the ecosystem-standard error model used across all Fulmen
    helper libraries for structured error emission.
    
    Attributes:
        code: Error code identifier
        message: Human-readable error message
        details: Additional error details (optional)
        path: Path that caused the error (optional)
        timestamp: When the error occurred
        severity: Severity classification ("info", "low", "medium", "high", "critical")
        severity_level: Numeric severity for sorting (0=info, 1=low, 2=medium, 3=high, 4=critical)
        correlation_id: Correlation identifier from observability logging
        trace_id: Optional tracing identifier (OpenTelemetry trace/span)
        exit_code: Optional process exit code (0-255)
        context: Structured context key/values (non-sensitive debugging info)
        original: Serialized form of the wrapped/original error
    """

    # Pathfinder base fields
    code: str
    message: str
    details: dict[str, Any] | None = None
    path: str | None = None
    timestamp: datetime

    # Telemetry extensions
    severity: str | None = None
    severity_level: int | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    exit_code: int | None = None
    context: dict[str, Any] | None = None
    original: str | dict[str, Any] | None = None

    def model_post_init(self, __context: Any) -> None:
        """Auto-map severity to severity_level if not provided."""
        if self.severity and self.severity_level is None:
            object.__setattr__(self, "severity_level", _map_severity_level(self.severity))


# Severity mapping per assessment/v1.0.0/severity-definitions.schema.json
_SEVERITY_MAP = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def _map_severity_level(severity: str) -> int:
    """Map severity name to numeric level.
    
    Args:
        severity: Severity name ("info", "low", "medium", "high", "critical")
    
    Returns:
        Numeric severity level (0-4)
    
    Raises:
        ValueError: If severity is not recognized
    """
    level = _SEVERITY_MAP.get(severity.lower())
    if level is None:
        raise ValueError(
            f"Invalid severity '{severity}'. Must be one of: {', '.join(_SEVERITY_MAP.keys())}"
        )
    return level
