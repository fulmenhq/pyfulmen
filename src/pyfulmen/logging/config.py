"""Logger configuration dataclasses and validation.

Provides type-safe configuration for progressive logging with schema validation
against Crucible standards.

Example:
    >>> from pyfulmen.logging.config import LoggerConfig, LoggingProfile
    >>> config = LoggerConfig(
    ...     profile=LoggingProfile.STRUCTURED,
    ...     service="my-service",
    ...     sinks=[SinkConfig(type="console")]
    ... )
    >>> validate_logger_config(config)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .profiles import LoggingProfile, validate_profile_requirements


@dataclass
class SinkConfig:
    """Configuration for a log sink.

    Defines how and where log events are output.
    """

    type: str  # console, file, rolling-file, external
    name: Optional[str] = None
    level: Optional[str] = None
    format: str = "json"
    # Type-specific options as dict
    options: Optional[Dict[str, Any]] = None


@dataclass
class MiddlewareConfig:
    """Configuration for logging middleware.

    Middleware processes log events in the pipeline.
    """

    name: str
    enabled: bool = True
    order: int = 0
    config: Optional[Dict[str, Any]] = None


@dataclass
class ThrottlingConfig:
    """Configuration for log throttling and backpressure.

    Controls rate limiting and burst handling.
    """

    enabled: bool = False
    maxRate: Optional[int] = None
    burstSize: Optional[int] = None
    windowSize: Optional[int] = None
    dropPolicy: str = "drop-oldest"


@dataclass
class LoggerConfig:
    """Main logger configuration with progressive profiles.

    Supports SIMPLE, STRUCTURED, ENTERPRISE, and CUSTOM profiles
    with appropriate defaults and validation.
    """

    profile: LoggingProfile
    service: str
    environment: str = "development"
    policyFile: Optional[str] = None
    defaultLevel: str = "INFO"
    sinks: Optional[List[SinkConfig]] = None
    middleware: Optional[List[MiddlewareConfig]] = None
    throttling: Optional[ThrottlingConfig] = None
    staticFields: Optional[Dict[str, Any]] = None
    enableCaller: bool = False
    enableStacktrace: bool = False
    customConfig: Optional[Dict[str, Any]] = None


def validate_logger_config(config: LoggerConfig) -> List[str]:
    """Validate LoggerConfig against profile requirements and schema.

    Args:
        config: The logger configuration to validate

    Returns:
        List of validation error messages (empty if valid)

    Raises:
        ValidationError: If schema validation fails (when pydantic available)
    """
    errors = []

    # Basic field validation
    if not config.service:
        errors.append("Service name is required")

    if config.profile not in LoggingProfile:
        errors.append(f"Invalid profile: {config.profile}")

    # Profile-specific validation
    sinks_list = [sink.__dict__ if hasattr(sink, '__dict__') else sink for sink in (config.sinks or [])]
    middleware_list = [mw.__dict__ if hasattr(mw, '__dict__') else mw for mw in (config.middleware or [])]

    profile_errors = validate_profile_requirements(
        profile=config.profile,
        sinks=sinks_list,
        middleware=middleware_list,
        format=config.sinks[0].format if config.sinks else "json",
        throttling_enabled=config.throttling.enabled if config.throttling else False,
        policy_enabled=bool(config.policyFile),
    )
    errors.extend(profile_errors)

    # Additional validations
    if config.profile == LoggingProfile.ENTERPRISE and not config.middleware:
        errors.append("ENTERPRISE profile requires at least one middleware (correlation)")

    if config.throttling and config.throttling.enabled:
        if not config.throttling.maxRate:
            errors.append("Throttling requires maxRate to be set")
        if config.throttling.burstSize is not None and config.throttling.burstSize < 1:
            errors.append("Burst size must be at least 1")

    return errors


def create_simple_config(service: str, **kwargs) -> LoggerConfig:
    """Create a SIMPLE profile configuration.

    Args:
        service: Service name
        **kwargs: Additional config overrides

    Returns:
        LoggerConfig for SIMPLE profile
    """
    return LoggerConfig(
        profile=LoggingProfile.SIMPLE,
        service=service,
        sinks=[SinkConfig(type="console", format="text")],
        **kwargs
    )


def create_structured_config(service: str, **kwargs) -> LoggerConfig:
    """Create a STRUCTURED profile configuration.

    Args:
        service: Service name
        **kwargs: Additional config overrides

    Returns:
        LoggerConfig for STRUCTURED profile
    """
    return LoggerConfig(
        profile=LoggingProfile.STRUCTURED,
        service=service,
        sinks=[SinkConfig(type="console", format="json")],
        **kwargs
    )


def create_enterprise_config(service: str, **kwargs) -> LoggerConfig:
    """Create an ENTERPRISE profile configuration.

    Args:
        service: Service name
        **kwargs: Additional config overrides

    Returns:
        LoggerConfig for ENTERPRISE profile
    """
    return LoggerConfig(
        profile=LoggingProfile.ENTERPRISE,
        service=service,
        sinks=[SinkConfig(type="console", format="json")],
        middleware=[MiddlewareConfig(name="correlation")],
        throttling=ThrottlingConfig(enabled=True, maxRate=1000),
        **kwargs
    )


__all__ = [
    "SinkConfig",
    "MiddlewareConfig",
    "ThrottlingConfig",
    "LoggerConfig",
    "validate_logger_config",
    "create_simple_config",
    "create_structured_config",
    "create_enterprise_config",
]