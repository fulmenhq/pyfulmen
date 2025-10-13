"""Progressive logger interface with profile-based delegation.

Provides Logger class with three profiles:
- SIMPLE: Console-only, basic formatting (zero-complexity default)
- STRUCTURED: JSON output with core envelope fields
- ENTERPRISE: Full 20+ field envelope, policy enforcement, middleware pipeline

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
"""

import json
import logging
import sys
from abc import ABC, abstractmethod
from typing import Any

from ._models import LogEvent, LoggingConfig, LoggingPolicy, LoggingProfile
from .severity import Severity, to_python_level


class BaseLoggerImpl(ABC):
    """Abstract base for logger profile implementations."""

    def __init__(self, config: LoggingConfig):
        """Initialize logger implementation.
        
        Args:
            config: Logging configuration model
        """
        self.config = config
        self.service = config.service
        self.component = config.component
        self.default_level = config.default_level

    @abstractmethod
    def log(
        self,
        severity: Severity | str,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log a message at the specified severity level.
        
        Args:
            severity: Severity level (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
            message: Log message
            **kwargs: Additional context fields (profile-dependent)
        """
        pass

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


class SimpleLogger(BaseLoggerImpl):
    """Simple console-only logger with basic formatting.
    
    Zero-complexity default for rapid development and debugging.
    Uses Python's stdlib logging with minimal configuration.
    """

    def __init__(self, config: LoggingConfig):
        """Initialize simple logger.
        
        Args:
            config: Logging configuration
        """
        super().__init__(config)
        
        # Set up stdlib logger
        logger_name = (
            f"{self.service}.{self.component}" if self.component else self.service
        )
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(to_python_level(self.default_level))
        
        # Add console handler if none exist
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(to_python_level(self.default_level))
            
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def log(
        self,
        severity: Severity | str,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log message using stdlib logging.
        
        Args:
            severity: Severity level
            message: Log message
            **kwargs: Ignored for SIMPLE profile
        """
        severity_obj = Severity(severity) if isinstance(severity, str) else severity
        python_level = to_python_level(severity_obj)
        
        self._logger.log(python_level, message)


class StructuredLogger(BaseLoggerImpl):
    """Structured JSON logger with core envelope fields.
    
    Emits single-line JSON to stdout with:
    - timestamp, severity, message, service
    - Optional: component, context, request_id, correlation_id
    
    Suitable for cloud-native deployments with log aggregation.
    """

    def __init__(self, config: LoggingConfig):
        """Initialize structured logger.
        
        Args:
            config: Logging configuration
        """
        super().__init__(config)
        self._output = sys.stdout

    def log(
        self,
        severity: Severity | str,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log structured JSON message.
        
        Args:
            severity: Severity level
            message: Log message
            **kwargs: Additional context fields (context, request_id, correlation_id, etc.)
        """
        severity_str = severity.value if isinstance(severity, Severity) else severity
        
        # Build core envelope
        event_dict = {
            "severity": severity_str,
            "message": message,
            "service": self.service,
        }
        
        # Add optional identification fields
        if self.component:
            event_dict["component"] = self.component
        
        # Add allowed kwargs (subset of LogEvent fields)
        allowed_fields = {
            "context", "context_id", "request_id", "correlation_id",
            "trace_id", "span_id", "parent_span_id",
            "operation", "duration_ms", "user_id",
            "error", "tags", "event_id",
        }
        
        for key, value in kwargs.items():
            if key in allowed_fields and value:
                event_dict[key] = value
        
        # Create LogEvent for timestamp generation
        event = LogEvent(
            severity=severity_str,
            message=message,
            service=self.service,
            component=self.component,
            **{k: v for k, v in kwargs.items() if k in allowed_fields}
        )
        
        # Use event's timestamp
        event_dict["timestamp"] = event.timestamp
        if "correlation_id" not in event_dict:
            event_dict["correlation_id"] = event.correlation_id
        
        # Emit single-line JSON
        json_line = json.dumps(event_dict, ensure_ascii=False, separators=(',', ':'))
        print(json_line, file=self._output, flush=True)


class EnterpriseLogger(BaseLoggerImpl):
    """Enterprise logger with full 20+ field envelope.
    
    Emits complete LogEvent structures with:
    - All envelope fields (identification, context, tracing, metadata)
    - Policy enforcement
    - Middleware pipeline support (future: Phase 3)
    
    Suitable for production systems requiring audit, compliance, and observability.
    """

    def __init__(self, config: LoggingConfig, policy: LoggingPolicy | None = None):
        """Initialize enterprise logger.
        
        Args:
            config: Logging configuration
            policy: Optional policy for enforcement
        """
        super().__init__(config)
        self.policy = policy
        self._output = sys.stdout
        
        # Validate against policy if provided
        if self.policy:
            self._enforce_policy()

    def _enforce_policy(self) -> None:
        """Enforce policy constraints on configuration.
        
        Raises:
            ValueError: If configuration violates policy
        """
        if not self.policy:
            return
        
        # Check if ENTERPRISE profile is allowed
        if self.config.profile not in self.policy.allowed_profiles:
            raise ValueError(
                f"Profile '{self.config.profile}' not allowed by policy. "
                f"Allowed profiles: {self.policy.allowed_profiles}"
            )

    def log(
        self,
        severity: Severity | str,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log full enterprise event.
        
        Args:
            severity: Severity level
            message: Log message
            **kwargs: All LogEvent fields supported
        """
        severity_str = severity.value if isinstance(severity, Severity) else severity
        
        # Create full LogEvent
        event = LogEvent(
            severity=severity_str,
            message=message,
            service=self.service,
            component=self.component,
            **kwargs
        )
        
        # Emit complete JSON structure with computed fields
        event_dict = event.to_json_dict_with_computed()
        json_line = json.dumps(event_dict, ensure_ascii=False, separators=(',', ':'))
        print(json_line, file=self._output, flush=True)


class Logger:
    """Progressive logger with profile-based delegation.
    
    Provides unified interface across three logging profiles:
    - SIMPLE: Console-only, basic formatting (default)
    - STRUCTURED: JSON output, core envelope fields
    - ENTERPRISE: Full envelope, policy enforcement
    
    Example:
        >>> # Simple logging (zero-complexity default)
        >>> log = Logger(service="myapp")
        >>> log.info("Hello World")
        
        >>> # Structured logging
        >>> log = Logger(service="myapp", profile=LoggingProfile.STRUCTURED)
        >>> log.info("Request received", request_id="req-123")
        
        >>> # Enterprise logging with policy
        >>> log = Logger(
        ...     service="myapp",
        ...     profile=LoggingProfile.ENTERPRISE,
        ...     policy_file="config/logging-policy.yaml"
        ... )
        >>> log.info("Transaction completed", user_id="user-456", duration_ms=125.3)
    """

    def __init__(
        self,
        service: str,
        profile: str = LoggingProfile.SIMPLE,
        component: str = "",
        default_level: str = "INFO",
        policy_file: str | None = None,
        config: LoggingConfig | None = None,
    ):
        """Initialize logger with profile-based delegation.
        
        Args:
            service: Service name (required for all profiles)
            profile: Logging profile (SIMPLE, STRUCTURED, ENTERPRISE)
            component: Component name (optional, for subsystem identification)
            default_level: Default severity level (default: INFO)
            policy_file: Path to policy YAML file (for ENTERPRISE profile)
            config: Optional pre-built LoggingConfig (overrides other params)
        
        Raises:
            ValueError: If profile is invalid or violates policy
        """
        # Build or use provided config
        if config:
            self.config = config
        else:
            self.config = LoggingConfig(
                profile=profile,
                service=service,
                component=component,
                default_level=default_level,
                policy_file=policy_file,
            )
        
        # Load policy if specified
        self.policy: LoggingPolicy | None = None
        if policy_file:
            self.policy = self._load_policy(policy_file)
        
        # Validate profile
        self._validate_profile()
        
        # Create implementation based on profile
        self._impl = self._create_implementation()

    def _load_policy(self, policy_file: str) -> LoggingPolicy:
        """Load policy from YAML file.
        
        Args:
            policy_file: Path to policy file
        
        Returns:
            LoggingPolicy instance
        
        Note:
            Implementation placeholder - will use ConfigLoader in future
        """
        # TODO: Load from YAML using ConfigLoader
        # For now, return permissive default
        return LoggingPolicy()

    def _validate_profile(self) -> None:
        """Validate profile against policy constraints.
        
        Raises:
            ValueError: If profile is invalid or violates policy
        """
        valid_profiles = {
            LoggingProfile.SIMPLE,
            LoggingProfile.STRUCTURED,
            LoggingProfile.ENTERPRISE,
            LoggingProfile.CUSTOM,
        }
        
        if self.config.profile not in valid_profiles:
            raise ValueError(
                f"Invalid profile '{self.config.profile}'. "
                f"Valid profiles: {valid_profiles}"
            )
        
        # Check policy if loaded
        if self.policy and self.config.profile not in self.policy.allowed_profiles:
            raise ValueError(
                f"Profile '{self.config.profile}' not allowed by policy. "
                f"Allowed profiles: {self.policy.allowed_profiles}"
            )

    def _create_implementation(self) -> BaseLoggerImpl:
        """Create logger implementation based on profile.
        
        Returns:
            Logger implementation instance
        
        Raises:
            ValueError: If profile is CUSTOM (not yet implemented)
        """
        if self.config.profile == LoggingProfile.SIMPLE:
            return SimpleLogger(self.config)
        elif self.config.profile == LoggingProfile.STRUCTURED:
            return StructuredLogger(self.config)
        elif self.config.profile == LoggingProfile.ENTERPRISE:
            return EnterpriseLogger(self.config, self.policy)
        elif self.config.profile == LoggingProfile.CUSTOM:
            raise ValueError("CUSTOM profile not yet implemented (Phase 5)")
        else:
            raise ValueError(f"Unknown profile: {self.config.profile}")

    def log(
        self,
        severity: Severity | str,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log message at specified severity level.
        
        Args:
            severity: Severity level (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
            message: Log message
            **kwargs: Additional context (profile-dependent fields)
        """
        self._impl.log(severity, message, **kwargs)

    def trace(self, message: str, **kwargs: Any) -> None:
        """Log TRACE level message."""
        self._impl.trace(message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log DEBUG level message."""
        self._impl.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log INFO level message."""
        self._impl.info(message, **kwargs)

    def warn(self, message: str, **kwargs: Any) -> None:
        """Log WARN level message."""
        self._impl.warn(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log ERROR level message."""
        self._impl.error(message, **kwargs)

    def fatal(self, message: str, **kwargs: Any) -> None:
        """Log FATAL level message."""
        self._impl.fatal(message, **kwargs)


__all__ = [
    "Logger",
    "BaseLoggerImpl",
    "SimpleLogger",
    "StructuredLogger",
    "EnterpriseLogger",
]
