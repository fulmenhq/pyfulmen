"""Data models for enterprise logging.

Provides Pydantic models for log events, configuration, and policy enforcement
based on the Crucible logging standard.
"""

from typing import Any

from pydantic import Field, computed_field

from ..foundry import (
    FulmenConfigModel,
    FulmenDataModel,
    generate_correlation_id,
    utc_now_rfc3339nano,
)
from .severity import to_numeric_level


class LogEvent(FulmenDataModel):
    """Enterprise log event with full 20+ field envelope.

    Implements the Crucible logging standard with all required and optional
    fields for structured JSON output. Computed fields are excluded by default
    for safe roundtripping.

    Example:
        >>> event = LogEvent(
        ...     message="Request processed",
        ...     severity=Severity.INFO,
        ...     service="myapp"
        ... )
        >>> event.to_json_dict()  # Excludes computed fields
        {...}
        >>> event.to_json_dict_with_computed()  # Includes severity_level
        {..., 'severity_level': 20}
    """

    # Required fields
    timestamp: str = Field(
        default_factory=utc_now_rfc3339nano,
        description="RFC3339Nano UTC timestamp with microsecond precision",
    )
    severity: str = Field(
        description="Severity level (TRACE, DEBUG, INFO, WARN, ERROR, FATAL, NONE)",
    )
    message: str = Field(
        description="Human-readable log message",
    )
    service: str = Field(
        description="Service/application name",
    )

    # Optional identification fields
    component: str | None = Field(
        default=None,
        description="Subsystem/component name",
    )
    logger: str | None = Field(
        default=None,
        description="Logger instance identifier (e.g., 'gofulmen.pathfinder')",
    )
    environment: str | None = Field(
        default=None,
        description="Deployment environment (e.g., 'production', 'staging')",
    )

    # Context and correlation fields
    context: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary key/value map for structured context",
    )
    context_id: str | None = Field(
        default=None,
        description="Execution context identifier (job, pipeline, CLI invocation)",
        serialization_alias="contextId",
    )
    request_id: str | None = Field(
        default=None,
        description="Per-request identifier (HTTP X-Request-ID header)",
        serialization_alias="requestId",
    )
    correlation_id: str = Field(
        default_factory=generate_correlation_id,
        description="Cross-service correlation UUID (UUIDv7, time-sortable)",
        serialization_alias="correlationId",
    )

    # Tracing fields
    trace_id: str | None = Field(
        default=None,
        description="OpenTelemetry trace identifier",
        serialization_alias="traceId",
    )
    span_id: str | None = Field(
        default=None,
        description="Span identifier",
        serialization_alias="spanId",
    )
    parent_span_id: str | None = Field(
        default=None,
        description="Parent span identifier for nested operations",
        serialization_alias="parentSpanId",
    )

    # Operation metadata
    operation: str | None = Field(
        default=None,
        description="Logical operation or handler name (CLI command, HTTP route, job step)",
    )
    duration_ms: float | None = Field(
        default=None,
        description="Operation duration in milliseconds",
        serialization_alias="durationMs",
    )
    user_id: str | None = Field(
        default=None,
        description="Authenticated user identifier when available",
        serialization_alias="userId",
    )

    # Error information
    error: dict[str, str] | None = Field(
        default=None,
        description="Error details: {message, type, stack}",
    )

    # Additional metadata
    tags: list[str] | None = Field(
        default=None,
        description="Optional string array for ad-hoc filtering",
    )
    event_id: str | None = Field(
        default=None,
        description="Optional unique identifier assigned by the producer",
        serialization_alias="eventId",
    )

    # Middleware metadata
    throttle_bucket: str | None = Field(
        default=None,
        description="Set when throttling drops are applied",
        serialization_alias="throttleBucket",
    )
    redaction_flags: list[str] | None = Field(
        default=None,
        description="Redaction indicators emitted by middleware (e.g., ['pii'])",
        serialization_alias="redactionFlags",
    )

    @computed_field(alias="severityLevel")
    @property
    def severity_level(self) -> int:
        """Numeric severity level for filtering and comparison.

        Returns:
            Numeric level (0-60): TRACE=0, DEBUG=10, INFO=20, WARN=30, ERROR=40, FATAL=50, NONE=60
        """
        return to_numeric_level(self.severity)


class LoggingProfile(str):
    """Logging profile constants for progressive configuration."""

    SIMPLE = "SIMPLE"
    STRUCTURED = "STRUCTURED"
    ENTERPRISE = "ENTERPRISE"
    CUSTOM = "CUSTOM"


class LoggingConfig(FulmenConfigModel):
    """Progressive logging configuration model.

    Supports profile-based configuration with optional detailed customization.
    Follows three-layer merge pattern (Crucible defaults → user → runtime).

    Example:
        >>> config = LoggingConfig(
        ...     profile=LoggingProfile.ENTERPRISE,
        ...     service="myapp",
        ...     default_level="INFO"
        ... )
    """

    profile: str = Field(
        default=LoggingProfile.SIMPLE,
        description="Logging profile (SIMPLE, STRUCTURED, ENTERPRISE, CUSTOM)",
    )
    service: str = Field(
        description="Service name for log entries",
    )
    component: str = Field(
        default="",
        description="Component name for log entries",
    )
    environment: str | None = Field(
        default=None,
        description="Deployment environment (e.g., 'production', 'staging')",
    )
    default_level: str = Field(
        default="INFO",
        description="Default severity level",
    )

    # Optional fields for STRUCTURED and ENTERPRISE profiles
    sinks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Sink configurations (console, file, rolling-file, memory)",
    )
    middleware: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Middleware chain definitions (redaction, throttling, etc.)",
    )
    encoders: dict[str, Any] = Field(
        default_factory=dict,
        description="Named encoder configurations",
    )
    fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Static and dynamic field configurations",
    )
    throttling: dict[str, Any] = Field(
        default_factory=dict,
        description="Global throttling configuration",
    )
    policy_file: str | None = Field(
        default=None,
        description="Path to policy file for profile validation",
    )


class LoggingPolicy(FulmenConfigModel):
    """Policy enforcement for logging profiles and features.

    Organizations can define policies to enforce appropriate logging patterns
    across different application types and environments.

    Example:
        >>> policy = LoggingPolicy(
        ...     allowed_profiles=["STRUCTURED", "ENTERPRISE"],
        ...     environment_rules={"production": ["ENTERPRISE"]}
        ... )
    """

    allowed_profiles: list[str] = Field(
        default_factory=lambda: ["SIMPLE", "STRUCTURED", "ENTERPRISE", "CUSTOM"],
        description="Permitted logging profiles",
    )
    required_profiles: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Required profiles by application type (e.g., workhorse: [ENTERPRISE])",
    )
    environment_rules: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Allowed profiles by environment (e.g., production: [ENTERPRISE])",
    )
    profile_requirements: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "Feature requirements per profile (e.g., ENTERPRISE: {requiredFeatures: [correlation]})"
        ),
    )
    audit_settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Audit configuration (logPolicyViolations, enforceStrictMode)",
    )


__all__ = [
    "LogEvent",
    "LoggingProfile",
    "LoggingConfig",
    "LoggingPolicy",
]
