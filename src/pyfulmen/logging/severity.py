"""Severity level definitions and mapping.

Provides Crucible-aligned severity levels and mapping to Python logging levels.
Implements the complete Fulmen Logging Standard with TRACE, DEBUG, INFO, WARN,
ERROR, FATAL, and NONE levels.

Example:
    >>> from pyfulmen.logging.severity import Severity, to_python_level
    >>> to_python_level(Severity.INFO)
    20
    >>> Severity.INFO.numeric_level
    20
"""

import logging
from enum import Enum


class Severity(str, Enum):
    """Log severity levels from Crucible observability standards.
    
    Severity Model (Crucible Logging Standard):
    - TRACE (0): Highly verbose diagnostics
    - DEBUG (10): Debug-level details
    - INFO (20): Core operational events
    - WARN (30): Unusual but non-breaking conditions
    - ERROR (40): Request/operation failure (recoverable)
    - FATAL (50): Unrecoverable failure, program exit expected
    - NONE (60): Explicitly disable emission
    """

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"
    NONE = "NONE"

    @property
    def numeric_level(self) -> int:
        """Get numeric severity level for filtering and comparison.
        
        Returns:
            Numeric severity level (0-60)
        """
        return _SEVERITY_TO_NUMERIC[self]

    @property
    def python_level(self) -> int:
        """Get Python logging level constant.
        
        Returns:
            Python logging level (logging.DEBUG, logging.INFO, etc.)
        """
        return to_python_level(self)

    def __lt__(self, other) -> bool:
        """Compare severity levels numerically."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.numeric_level < other.numeric_level

    def __le__(self, other) -> bool:
        """Compare severity levels numerically."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.numeric_level <= other.numeric_level

    def __gt__(self, other) -> bool:
        """Compare severity levels numerically."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.numeric_level > other.numeric_level

    def __ge__(self, other) -> bool:
        """Compare severity levels numerically."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.numeric_level >= other.numeric_level


# Severity to numeric level mapping (Crucible standard)
_SEVERITY_TO_NUMERIC: dict[Severity, int] = {
    Severity.TRACE: 0,
    Severity.DEBUG: 10,
    Severity.INFO: 20,
    Severity.WARN: 30,
    Severity.ERROR: 40,
    Severity.FATAL: 50,
    Severity.NONE: 60,
}

# Severity to Python logging level mapping
_SEVERITY_TO_PYTHON: dict[Severity, int] = {
    Severity.TRACE: logging.DEBUG,  # Python has no TRACE, map to DEBUG
    Severity.DEBUG: logging.DEBUG,  # 10
    Severity.INFO: logging.INFO,  # 20
    Severity.WARN: logging.WARNING,  # 30
    Severity.ERROR: logging.ERROR,  # 40
    Severity.FATAL: logging.CRITICAL,  # 50
    Severity.NONE: logging.CRITICAL + 10,  # Above all levels
}


def to_python_level(severity: Severity | str) -> int:
    """Map Crucible severity to Python logging level.

    Args:
        severity: Crucible severity level (enum or string)

    Returns:
        Python logging level constant

    Example:
        >>> to_python_level(Severity.INFO)
        20
        >>> to_python_level('ERROR')
        40
    """
    if isinstance(severity, str):
        try:
            severity = Severity(severity)
        except ValueError:
            # Try uppercase
            try:
                severity = Severity(severity.upper())
            except ValueError:
                return logging.INFO  # Default fallback

    return _SEVERITY_TO_PYTHON.get(severity, logging.INFO)


def to_numeric_level(severity: Severity | str) -> int:
    """Map Crucible severity to numeric level.

    Args:
        severity: Crucible severity level (enum or string)

    Returns:
        Numeric severity level (0-60)

    Example:
        >>> to_numeric_level(Severity.INFO)
        20
        >>> to_numeric_level('WARN')
        30
    """
    if isinstance(severity, str):
        try:
            severity = Severity(severity)
        except ValueError:
            try:
                severity = Severity(severity.upper())
            except ValueError:
                return 20  # Default to INFO

    return _SEVERITY_TO_NUMERIC.get(severity, 20)


def from_python_level(level: int) -> Severity:
    """Map Python logging level to Crucible severity.

    Args:
        level: Python logging level constant

    Returns:
        Crucible severity enum value

    Example:
        >>> from_python_level(logging.INFO)
        <Severity.INFO: 'INFO'>
        >>> from_python_level(logging.CRITICAL)
        <Severity.FATAL: 'FATAL'>
    """
    if level >= logging.CRITICAL:
        return Severity.FATAL
    elif level >= logging.ERROR:
        return Severity.ERROR
    elif level >= logging.WARNING:
        return Severity.WARN
    elif level >= logging.INFO:
        return Severity.INFO
    else:
        return Severity.DEBUG


def from_numeric_level(level: int) -> Severity:
    """Map numeric level to Crucible severity.

    Args:
        level: Numeric severity level

    Returns:
        Closest Crucible severity enum value

    Example:
        >>> from_numeric_level(20)
        <Severity.INFO: 'INFO'>
        >>> from_numeric_level(45)
        <Severity.FATAL: 'FATAL'>
    """
    if level >= 60:
        return Severity.NONE
    elif level >= 50:
        return Severity.FATAL
    elif level >= 40:
        return Severity.ERROR
    elif level >= 30:
        return Severity.WARN
    elif level >= 20:
        return Severity.INFO
    elif level >= 10:
        return Severity.DEBUG
    else:
        return Severity.TRACE


__all__ = [
    "Severity",
    "to_python_level",
    "to_numeric_level",
    "from_python_level",
    "from_numeric_level",
]
