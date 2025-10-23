"""
Error exit utilities.

Provides exit_with_error() function to log errors and exit processes.
"""

import sys
from typing import Any

from .models import FulmenError


def exit_with_error(exit_code: int, error: FulmenError, *, logger: Any = None) -> None:
    """Log error and exit process.

    Args:
        exit_code: Process exit code (0-255)
        error: FulmenError to log before exiting
        logger: Optional logger instance (creates default if None)

    Raises:
        SystemExit: Always (calls sys.exit)
    """
    # Create logger if not provided
    if logger is None:
        try:
            from ..logging import Logger

            logger = Logger(service="error-handler")
        except Exception:
            # Logging not available, use print
            print(f"Error {error.code}: {error.message}", file=sys.stderr)
            print(f"Details: {error.details}", file=sys.stderr)
            sys.exit(exit_code)

    # Log error at appropriate severity
    severity_map = {
        "info": logger.info,
        "low": logger.warn,
        "medium": logger.error,
        "high": logger.error,
        "critical": logger.fatal,
    }
    log_fn = severity_map.get(error.severity or "error", logger.error)

    # Emit structured log event
    context = {
        "code": error.code,
        "details": error.details,
        "correlation_id": error.correlation_id,
        "exit_code": exit_code,
    }
    # Remove None values to avoid logging issues
    context = {k: v for k, v in context.items() if v is not None}

    log_fn(error.message, context=context)

    # Exit process
    sys.exit(exit_code)
