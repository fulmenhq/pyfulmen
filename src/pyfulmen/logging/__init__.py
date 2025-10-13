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
    >>> # Enterprise logging with correlation context
    >>> from pyfulmen.logging import correlation_context
    >>> log = Logger(service="myapp", profile=LoggingProfile.ENTERPRISE)
    >>> with correlation_context(correlation_id="req-789"):
    ...     log.info("Processing request")  # Auto-includes req-789
    ...     log.info("Request complete")    # Same correlation_id
"""

from ._models import LogEvent, LoggingConfig, LoggingPolicy, LoggingProfile
from .context import (
    clear_context,
    correlation_context,
    extract_correlation_id_from_headers,
    get_context,
    get_correlation_id,
    set_context_value,
    set_correlation_id,
)
from .formatter import ConsoleFormatter, Formatter, JSONFormatter, TextFormatter
from .logger import (
    BaseLoggerImpl,
    EnterpriseLogger,
    Logger,
    SimpleLogger,
    StructuredLogger,
)
from .middleware import (
    Middleware,
    MiddlewarePipeline,
    MiddlewareRegistry,
    RedactPIIMiddleware,
    RedactSecretsMiddleware,
)
from .policy import enforce_policy, load_policy, validate_config_against_policy
from .severity import Severity
from .sinks import ConsoleSink, FileSink, Sink
from .throttling import ThrottleController, ThrottlingMiddleware

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
    "Middleware",
    "MiddlewarePipeline",
    "MiddlewareRegistry",
    "RedactSecretsMiddleware",
    "RedactPIIMiddleware",
    "ThrottleController",
    "ThrottlingMiddleware",
    "Formatter",
    "JSONFormatter",
    "TextFormatter",
    "ConsoleFormatter",
    "Sink",
    "ConsoleSink",
    "FileSink",
    "load_policy",
    "validate_config_against_policy",
    "enforce_policy",
    "correlation_context",
    "get_correlation_id",
    "set_correlation_id",
    "get_context",
    "set_context_value",
    "clear_context",
    "extract_correlation_id_from_headers",
]
