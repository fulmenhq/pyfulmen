"""Progressive logging with profile-based delegation.

Provides unified Logger interface with three profiles:
- SIMPLE: Console-only, basic formatting (zero-complexity default)
- STRUCTURED: JSON output with core envelope fields
- ENTERPRISE: Full 20+ field envelope with policy enforcement

Example:
    >>> from pyfulmen.logging import Logger, LoggingProfile
    >>> 
    >>> # Simple logging (default)
    >>> log = Logger(service="myapp")
    >>> log.info("Hello World")
    >>> 
    >>> # Structured JSON logging
    >>> log = Logger(service="myapp", profile=LoggingProfile.STRUCTURED)
    >>> log.info("Request processed", request_id="req-123")
    >>> 
    >>> # Enterprise logging
    >>> log = Logger(service="myapp", profile=LoggingProfile.ENTERPRISE)
    >>> log.info("Transaction completed", user_id="user-456", duration_ms=125.3)
"""

from ._models import LogEvent, LoggingConfig, LoggingPolicy, LoggingProfile
from .logger import (
    BaseLoggerImpl,
    EnterpriseLogger,
    Logger,
    SimpleLogger,
    StructuredLogger,
)
from .severity import Severity

__all__ = [
    "Logger",
    "LoggingProfile",
    "LoggingConfig",
    "LoggingPolicy",
    "LogEvent",
    "Severity",
    "BaseLoggerImpl",
    "SimpleLogger",
    "StructuredLogger",
    "EnterpriseLogger",
]
