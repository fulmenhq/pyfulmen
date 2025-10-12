"""Logger configuration based on Crucible schemas.

Provides helpers to configure Python logging using Crucible logging schemas
and config defaults.

Example:
    >>> from pyfulmen.logging import logger
    >>> log = logger.configure_logging()
    >>> log.info('Hello from PyFulmen')
"""

import logging
from typing import Any

from ..config.loader import ConfigLoader
from .severity import Severity, to_python_level


def configure_logging(
    config: dict[str, Any] | None = None,
    app_name: str = "pyfulmen",
    level: Severity | str | None = None,
) -> logging.Logger:
    """Configure structured logging from Crucible config.

    Sets up Python logging with configuration from:
    1. Crucible logging defaults
    2. User overrides
    3. Application-provided config

    Args:
        config: Optional application-provided logging config
        app_name: Application name for logger (default: 'pyfulmen')
        level: Optional log level override (default: from config or INFO)

    Returns:
        Configured logger instance

    Example:
        >>> logger = configure_logging(app_name='myapp', level='debug')
        >>> logger.info('Application started')
    """
    # Get base logger
    logger_instance = logging.getLogger(app_name)

    # Load three-layer config (if available)
    loader = ConfigLoader(app_name="fulmen")
    try:
        # Try to load Crucible logging defaults
        # Note: Adjust path based on actual Crucible logging config structure
        merged_config = loader.load(
            "observability/logging/v1.0.0/logger-config", user_config=config
        )
    except Exception:
        # If Crucible config not available, use provided config or defaults
        merged_config = config or {}

    # Determine log level
    if level:
        log_level = to_python_level(level)
    elif "level" in merged_config:
        log_level = to_python_level(merged_config["level"])
    elif "severity" in merged_config:
        log_level = to_python_level(merged_config["severity"])
    else:
        log_level = logging.INFO

    # Configure logger
    logger_instance.setLevel(log_level)

    # Add console handler if none exist
    if not logger_instance.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)

        # Configure formatter
        format_str = merged_config.get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        formatter = logging.Formatter(format_str)
        handler.setFormatter(formatter)

        logger_instance.addHandler(handler)

    return logger_instance


def get_logger(name: str, level: Severity | str | None = None) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Optional log level (default: from parent or INFO)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info('Module loaded')
    """
    logger_instance = logging.getLogger(name)

    if level:
        logger_instance.setLevel(to_python_level(level))

    return logger_instance


__all__ = [
    "configure_logging",
    "get_logger",
]
