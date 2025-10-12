"""Observability and logging utilities for PyFulmen.

Provides logging configuration based on Crucible schemas with severity
mapping and structured logging support.

Example:
    >>> from pyfulmen import logging
    >>> logger = logging.logger.configure_logging()
"""

from . import logger, severity

__all__ = [
    "logger",
    "severity",
]
