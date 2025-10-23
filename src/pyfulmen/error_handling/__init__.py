"""
Error handling and propagation for pyfulmen.

Provides structured error wrapping with telemetry metadata, conforming to
the Crucible error-handling-propagation standard. Extends Pathfinder error
responses with optional observability fields.

This module is part of the ecosystem-wide error handling standard and will
be implemented across gofulmen, pyfulmen, and tsfulmen with aligned APIs.

Example:
    >>> from pyfulmen.error_handling import PathfinderError, wrap
    >>>
    >>> # Create base error
    >>> base = PathfinderError(code="CONFIG_INVALID", message="Config load failed")
    >>>
    >>> # Wrap with telemetry metadata
    >>> err = wrap(
    ...     base,
    ...     severity="high",
    ...     context={"path": "/app/config.yaml"}
    ... )
    >>>
    >>> # Error auto-includes correlation_id from logging context
    >>> print(err.correlation_id)  # e.g., "req-abc123"
"""

from ._exit import exit_with_error
from ._validate import validate
from ._wrap import wrap
from .models import FulmenError, PathfinderError

__all__ = [
    "PathfinderError",
    "FulmenError",
    "wrap",
    "validate",
    "exit_with_error",
]
