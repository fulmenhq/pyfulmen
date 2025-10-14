"""Progressive logger with profile-based configuration.

Provides unified logger interface with four profiles:
- SIMPLE: Console-only, basic text formatting (zero-complexity default)
- STRUCTURED: JSON output with core envelope fields
- ENTERPRISE: Full 20+ field envelope, policy enforcement, middleware pipeline
- CUSTOM: User-defined configuration

Uses sink/formatter/middleware abstractions for proper resource management
and enterprise-grade features.

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
    >>> # Enterprise logging with policy
    >>> log = Logger(
    ...     service="myapp",
    ...     profile=LoggingProfile.ENTERPRISE,
    ...     policy_file="config/logging-policy.yaml"
    ... )
    >>>
    >>> # Context manager support
    >>> with Logger(service="myapp") as log:
    ...     log.info("Inside context")
"""

from typing import Any

from ._models import LogEvent, LoggingConfig, LoggingPolicy, LoggingProfile
from .context import get_context, get_correlation_id
from .formatter import JSONFormatter, TextFormatter
from .middleware import Middleware, MiddlewarePipeline, MiddlewareRegistry
from .policy import load_policy as _load_policy_impl
from .severity import Severity, to_numeric_level
from .sinks import ConsoleSink, Sink


class ProgressiveLogger:
    """Progressive logger with profile-based configuration.

    Supports four profiles:
    - SIMPLE: Console-only, basic text formatting
    - STRUCTURED: JSON output with core envelope fields
    - ENTERPRISE: Full envelope, policy enforcement, middleware
    - CUSTOM: User-defined configuration

    Features:
    - Proper sink/formatter abstraction usage
    - Resource management (flush/close)
    - Context manager support
    - Thread-safe operations
    """

    def __init__(
        self,
        config: LoggingConfig,
        policy: LoggingPolicy | None = None,
        middleware: list[Middleware] | None = None,
    ):
        """Initialize progressive logger.

        Args:
            config: Logging configuration
            policy: Optional policy for enforcement (ENTERPRISE profile)
            middleware: Optional middleware instances (overrides config.middleware)
        """
        self.config = config
        self.policy = policy
        self.service = config.service
        self.component = config.component
        self.default_level = config.default_level
        self._min_level = to_numeric_level(self.default_level)

        # Initialize components
        self.sinks = self._create_sinks()
        # Use provided middleware instances or create from config
        if middleware is not None:
            self.middleware = MiddlewarePipeline(middleware)
        else:
            self.middleware = self._create_middleware()
        self.throttle = self._create_throttle()

        # Validate policy if ENTERPRISE
        if config.profile == LoggingProfile.ENTERPRISE and self.policy:
            self._enforce_policy()

    def _create_sinks(self) -> list[Sink]:
        """Create sinks based on profile and config."""
        if self.config.profile == LoggingProfile.SIMPLE:
            # Default: console with text formatter
            return [ConsoleSink(formatter=TextFormatter())]

        elif self.config.profile == LoggingProfile.STRUCTURED:
            # Use config.sinks if provided, else default JSON console
            if self.config.sinks:
                return self._instantiate_sinks_from_config(self.config.sinks)
            return [ConsoleSink(formatter=JSONFormatter())]

        elif self.config.profile == LoggingProfile.ENTERPRISE:
            # Use config.sinks (required) or default JSON console
            if self.config.sinks:
                return self._instantiate_sinks_from_config(self.config.sinks)
            return [ConsoleSink(formatter=JSONFormatter())]

        elif self.config.profile == LoggingProfile.CUSTOM:
            # User must provide sinks in customConfig
            if not self.config.sinks:
                raise ValueError("CUSTOM profile requires sinks configuration")
            return self._instantiate_sinks_from_config(self.config.sinks)

        else:
            raise ValueError(f"Unknown profile: {self.config.profile}")

    def _instantiate_sinks_from_config(self, sink_configs: list[dict]) -> list[Sink]:
        """Instantiate sinks from configuration dictionaries.

        Args:
            sink_configs: List of sink configuration dictionaries

        Returns:
            List of instantiated Sink objects

        Note:
            For now, simple instantiation. TODO: Implement sink factory pattern
        """
        sinks = []
        for sink_config in sink_configs:
            sink_type = sink_config.get("type", "console")

            if sink_type == "console":
                from .formatter import ConsoleFormatter, JSONFormatter, TextFormatter

                formatter_type = sink_config.get("format", "json")

                if formatter_type == "json":
                    formatter = JSONFormatter()
                elif formatter_type == "text":
                    formatter = TextFormatter()
                elif formatter_type == "console":
                    use_colors = bool(sink_config.get("colorize", False))
                    formatter = ConsoleFormatter(use_colors=use_colors)
                else:
                    raise ValueError(f"Unknown formatter type: {formatter_type}")

                sinks.append(ConsoleSink(formatter=formatter))

            elif sink_type == "file":
                from .formatter import ConsoleFormatter, JSONFormatter, TextFormatter
                from .sinks import FileSink

                path = sink_config.get("path")
                if not path:
                    raise ValueError("File sink requires 'path' configuration")

                formatter_type = sink_config.get("format", "json")
                if formatter_type == "json":
                    formatter = JSONFormatter()
                elif formatter_type == "text":
                    formatter = TextFormatter()
                elif formatter_type == "console":
                    # For files, default to no ANSI colors regardless of colorize setting
                    formatter = ConsoleFormatter(use_colors=False)
                else:
                    raise ValueError(f"Unknown formatter type: {formatter_type}")

                sinks.append(FileSink(path=path, formatter=formatter))

            else:
                raise ValueError(f"Unknown sink type: {sink_type}")

        return sinks

    def _create_middleware(self) -> MiddlewarePipeline | None:
        """Create middleware pipeline from config."""
        if not self.config.middleware:
            return None

        instances: list[Middleware] = []
        for m_config in self.config.middleware:
            # Honor enabled flag (default True)
            if m_config.get("enabled") is False:
                continue

            name = m_config.get("name") or m_config.get("type", "redact-secrets")

            # Unwrap nested 'config' payload; outer keys handled by pipeline
            inner_cfg = m_config.get("config") or {}
            order = m_config.get("order")

            # Build payload for registry: inner config only, plus 'order' if provided
            cfg_for_registry: dict[str, Any] = (
                dict(inner_cfg) if isinstance(inner_cfg, dict) else {}
            )
            if order is not None:
                cfg_for_registry["order"] = order

            instance = MiddlewareRegistry.create(name, cfg_for_registry)
            instances.append(instance)

        return MiddlewarePipeline(instances) if instances else None

    def _create_throttle(self) -> Any:
        """Create throttle controller if configured.

        Returns:
            ThrottleController instance or None
        """
        # Check if any middleware is ThrottlingMiddleware
        if self.middleware:
            for middleware in self.middleware.middleware:
                if hasattr(middleware, "controller"):
                    return middleware.controller
        return None

    def _enforce_policy(self) -> None:
        """Enforce policy constraints."""
        if not self.policy:
            return

        # Check if ENTERPRISE profile is allowed
        if self.config.profile not in self.policy.allowed_profiles:
            raise ValueError(
                f"Profile '{self.config.profile}' not allowed by policy. "
                f"Allowed profiles: {self.policy.allowed_profiles}"
            )

    def _should_log(self, severity: Severity | str) -> bool:
        """Check if message should be logged based on configured level.

        Args:
            severity: Severity level to check

        Returns:
            True if message should be logged, False otherwise
        """
        severity_obj = Severity(severity) if isinstance(severity, str) else severity
        return to_numeric_level(severity_obj) >= self._min_level

    def _emit_event(self, event: LogEvent) -> None:
        """Process and emit log event through pipeline.

        Args:
            event: Log event to emit
        """
        # Serialize event based on profile
        if self.config.profile == LoggingProfile.SIMPLE:
            # For SIMPLE, pass event fields to TextFormatter
            event_dict = {
                "timestamp": event.timestamp,
                "severity": event.severity,
                "message": event.message,
            }
            for sink in self.sinks:
                sink.emit(event_dict)
        else:
            # STRUCTURED/ENTERPRISE: JSON serialization
            event_dict = event.to_json_dict_with_computed(exclude_none=True, exclude_defaults=False)

            # Process through middleware if configured
            if self.middleware:
                event_dict = self.middleware.process(event_dict)
                if event_dict is None:
                    # Dropped by middleware (e.g., throttling)
                    return

            # Emit to all sinks
            for sink in self.sinks:
                sink.emit(event_dict)

    def log(
        self,
        severity: Severity | str,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log message with specified severity.

        Args:
            severity: Severity level (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
            message: Log message
            **kwargs: Additional context fields
        """
        # Check if should log
        if not self._should_log(severity):
            return

        # Normalize severity
        severity_str = severity.value if isinstance(severity, Severity) else severity

        # Merge thread-local context
        merged_kwargs = kwargs.copy()

        # Add correlation_id from context if not provided
        if "correlation_id" not in merged_kwargs:
            context_correlation_id = get_correlation_id()
            if context_correlation_id:
                merged_kwargs["correlation_id"] = context_correlation_id

        # Merge thread-local context with explicit context
        thread_context = get_context()
        if thread_context:
            if "context" in merged_kwargs:
                merged_context = {**thread_context, **merged_kwargs["context"]}
                merged_kwargs["context"] = merged_context
            else:
                merged_kwargs["context"] = thread_context.copy()

        # Create LogEvent
        event = LogEvent(
            severity=severity_str,
            message=message,
            service=self.service,
            component=self.component or None,
            **merged_kwargs,
        )

        # Emit event
        self._emit_event(event)

    def trace(self, message: str, **kwargs: Any) -> None:
        """Log TRACE level message."""
        self.log(Severity.TRACE, message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log DEBUG level message."""
        self.log(Severity.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log INFO level message."""
        self.log(Severity.INFO, message, **kwargs)

    def warn(self, message: str, **kwargs: Any) -> None:
        """Log WARN level message."""
        self.log(Severity.WARN, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log ERROR level message."""
        self.log(Severity.ERROR, message, **kwargs)

    def fatal(self, message: str, **kwargs: Any) -> None:
        """Log FATAL level message."""
        self.log(Severity.FATAL, message, **kwargs)

    def set_level(self, level: Severity | str) -> None:
        """Dynamically change the minimum logging level.

        Args:
            level: New minimum severity level

        Example:
            >>> logger.set_level(Severity.DEBUG)
            >>> logger.set_level("ERROR")
        """
        level_obj = Severity(level) if isinstance(level, str) else level
        self._min_level = to_numeric_level(level_obj)
        self.default_level = level_obj.value

    def flush(self) -> None:
        """Flush all sinks."""
        for sink in self.sinks:
            sink.flush()

    def close(self) -> None:
        """Close logger and release resources."""
        for sink in self.sinks:
            sink.close()

    def __enter__(self) -> "ProgressiveLogger":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with flush."""
        self.flush()


def Logger(  # noqa: N802
    service: str,
    profile: LoggingProfile = LoggingProfile.SIMPLE,
    component: str | None = None,
    default_level: str = "INFO",
    middleware: list[Middleware] | None = None,
    policy_file: str | None = None,
    config: LoggingConfig | None = None,
    **kwargs: Any,
) -> ProgressiveLogger:
    """Create progressive logger with profile-based configuration.

    Args:
        service: Service name (required)
        profile: Logging profile (default: SIMPLE)
        component: Optional component name
        default_level: Minimum severity level (default: INFO)
        middleware: Optional middleware list
        policy_file: Path to policy file (ENTERPRISE profile)
        config: Optional pre-built LoggingConfig (for advanced usage)
        **kwargs: Additional configuration

    Returns:
        ProgressiveLogger instance

    Example:
        >>> log = Logger(service="myapp")
        >>> log.info("Hello World")

        >>> log = Logger(
        ...     service="myapp",
        ...     profile=LoggingProfile.ENTERPRISE,
        ...     policy_file="config/policy.yaml"
        ... )
    """
    # Use provided config or build new one
    if config is not None:
        # Use provided config, but allow overrides for middleware
        logger_config = config
    else:
        # Build config - middleware passed directly to ProgressiveLogger
        # not through LoggingConfig to avoid type conflicts
        logger_config = LoggingConfig(
            profile=profile,
            service=service,
            component=component or "",
            default_level=default_level,
            **kwargs,
        )

    # Load policy if ENTERPRISE
    policy = None
    if logger_config.profile == LoggingProfile.ENTERPRISE and policy_file:
        policy = _load_policy_impl(policy_file)

    # Create logger
    return ProgressiveLogger(config=logger_config, policy=policy, middleware=middleware)


__all__ = [
    "Logger",
    "ProgressiveLogger",
]
