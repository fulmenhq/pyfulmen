"""Severity level definitions and mapping.

Provides Crucible-aligned severity levels and mapping to Python logging levels.

Example:
    >>> from pyfulmen.logging.severity import Severity, to_python_level
    >>> to_python_level(Severity.INFO)
    20
"""

import logging
from enum import Enum


class Severity(str, Enum):
    """Log severity levels from Crucible observability standards."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


def to_python_level(severity: Severity | str) -> int:
    """Map Crucible severity to Python logging level.

    Args:
        severity: Crucible severity level

    Returns:
        Python logging level constant

    Example:
        >>> to_python_level(Severity.INFO)
        20
        >>> to_python_level('error')
        40
    """
    severity_str = severity.value if isinstance(severity, Severity) else severity

    mapping = {
        "debug": logging.DEBUG,  # 10
        "info": logging.INFO,  # 20
        "warn": logging.WARNING,  # 30
        "error": logging.ERROR,  # 40
        "critical": logging.CRITICAL,  # 50
    }

    return mapping.get(severity_str.lower(), logging.INFO)


def from_python_level(level: int) -> Severity:
    """Map Python logging level to Crucible severity.

    Args:
        level: Python logging level constant

    Returns:
        Crucible severity enum value

    Example:
        >>> from_python_level(logging.INFO)
        <Severity.INFO: 'info'>
    """
    if level >= logging.CRITICAL:
        return Severity.CRITICAL
    elif level >= logging.ERROR:
        return Severity.ERROR
    elif level >= logging.WARNING:
        return Severity.WARN
    elif level >= logging.INFO:
        return Severity.INFO
    else:
        return Severity.DEBUG


__all__ = [
    "Severity",
    "to_python_level",
    "from_python_level",
]
