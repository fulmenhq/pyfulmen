"""
Foundation Pydantic models for pyfulmen with Fulmen conventions.

This module provides base classes that establish consistent patterns across
all pyfulmen modules for data validation, configuration, and catalog entries.

Design Principles:
- FulmenDataModel: Immutable, strict validation for events/messages
- FulmenConfigModel: Flexible, mergeable configuration with extras allowed
- FulmenCatalogModel: Immutable catalog entries with lazy loading support
- Consistent RFC3339Nano timestamps and UUIDv7 correlation IDs
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

# Python 3.13+ has uuid7 in stdlib, but 3.12 does not
# We support Python 3.12+ so use try/except for compatibility
try:
    from uuid import uuid7 as _uuid7_impl
except ImportError:
    from uuid6 import uuid7 as _uuid7_impl


class FulmenBaseModel(BaseModel):
    """Base class for all Fulmen Pydantic models.

    Provides common configuration and utilities shared across all model types.
    Should not be used directly - use specific subclasses instead.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class FulmenDataModel(FulmenBaseModel):
    """Immutable data model for events, messages, and structured data.

    Use Cases:
    - Log events (LogEvent with 20+ fields)
    - Trace events and spans
    - Metric events
    - API response models
    - Domain events and messages

    Features:
    - Immutable (frozen=True) - prevents accidental mutation
    - Strict schema (extra='forbid') - rejects unknown fields
    - Type-safe validation at construction and assignment
    - JSON serialization helpers with Fulmen conventions
    - Enum values serialized as strings

    Example:
        >>> from pyfulmen.foundry import FulmenDataModel, generate_correlation_id
        >>> class LogEvent(FulmenDataModel):
        ...     message: str
        ...     correlation_id: str = Field(default_factory=generate_correlation_id)
        ...
        >>> event = LogEvent(message="Hello")
        >>> event.message = "World"  # Raises ValidationError - immutable
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )

    def to_json_dict(
        self, exclude_none: bool = True, include_computed: bool = False
    ) -> dict[str, Any]:
        """Convert to JSON-serializable dict with Fulmen conventions.

        Args:
            exclude_none: If True, omit fields with None values
            include_computed: If True, include computed fields in output

        Returns:
            JSON-serializable dictionary

        Note:
            - Computed fields are EXCLUDED by default for safe roundtripping
            - Uses by_alias=True to support field aliases (e.g., camelCase API fields)
            - To include computed fields, use include_computed=True or to_json_dict_with_computed()
        """
        # Get computed field names from class (not instance, to avoid deprecation warning)
        computed_fields = set(self.__class__.model_computed_fields.keys())

        if include_computed:
            # Include computed fields
            return self.model_dump(
                mode="json",
                exclude_none=exclude_none,
                by_alias=True,
            )
        else:
            # Exclude computed fields for safe roundtripping
            return self.model_dump(
                mode="json",
                exclude_none=exclude_none,
                by_alias=True,
                exclude=computed_fields,
            )

    def to_json_str(self, exclude_none: bool = True, include_computed: bool = False) -> str:
        """Convert to JSON string.

        Args:
            exclude_none: If True, omit fields with None values
            include_computed: If True, include computed fields in output

        Returns:
            JSON string representation

        Note:
            Computed fields are EXCLUDED by default for safe roundtripping.
        """
        import json

        return json.dumps(
            self.to_json_dict(exclude_none=exclude_none, include_computed=include_computed)
        )

    def to_json_dict_with_computed(self, exclude_none: bool = True) -> dict[str, Any]:
        """Convenience method to include computed fields in serialization.

        Args:
            exclude_none: If True, omit fields with None values

        Returns:
            JSON-serializable dictionary with computed fields included

        Example:
            >>> from pydantic import computed_field
            >>> class LogEvent(FulmenDataModel):
            ...     message: str
            ...     severity: str
            ...     @computed_field
            ...     @property
            ...     def severity_level(self) -> int:
            ...         return {"INFO": 20, "ERROR": 40}[self.severity]
            ...
            >>> event = LogEvent(message="test", severity="INFO")
            >>> event.to_json_dict()  # Excludes computed
            {'message': 'test', 'severity': 'INFO'}
            >>> event.to_json_dict_with_computed()  # Includes computed
            {'message': 'test', 'severity': 'INFO', 'severity_level': 20}
        """
        return self.to_json_dict(exclude_none=exclude_none, include_computed=True)

    def get_computed_field_names(self) -> set[str]:
        """Get names of all computed fields on this model.

        Returns:
            Set of computed field names

        Example:
            >>> event.get_computed_field_names()
            {'severity_level', 'has_context'}
        """
        return set(self.__class__.model_computed_fields.keys())


class FulmenConfigModel(FulmenBaseModel):
    """Mutable configuration model for three-layer config loading.

    Use Cases:
    - Application configuration (LoggingConfig, AppConfig)
    - Service configuration with environment overrides
    - Three-layer merged configs (Crucible defaults → user → runtime)
    - YAML/JSON config file representations

    Features:
    - Mutable (frozen=False) - supports merge operations
    - Flexible schema (extra='allow') - accepts unknown fields for forward compatibility
    - Validates defaults and assignments
    - Supports both camelCase and snake_case field names
    - Merge helper for config layering

    Example:
        >>> from pyfulmen.foundry import FulmenConfigModel
        >>> class LoggingConfig(FulmenConfigModel):
        ...     service: str
        ...     level: str = "INFO"
        ...
        >>> base = LoggingConfig(service="myapp")
        >>> override = LoggingConfig(service="myapp", level="DEBUG")
        >>> merged = base.merge_with(override)
        >>> merged.level
        'DEBUG'
    """

    model_config = ConfigDict(
        frozen=False,
        extra="allow",
        validate_default=True,
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )

    def merge_with(self, other: "FulmenConfigModel") -> "FulmenConfigModel":
        """Deep merge with another config (other takes precedence).

        Performs a deep merge where values from 'other' override values from
        'self'. Nested dictionaries are merged recursively.

        Args:
            other: Configuration to merge (takes precedence)

        Returns:
            New instance with merged configuration

        Example:
            >>> base = LoggingConfig(service="app", level="INFO", sinks=[...])
            >>> override = LoggingConfig(service="app", level="DEBUG")
            >>> merged = base.merge_with(override)
            >>> merged.level
            'DEBUG'
            >>> merged.sinks  # Preserved from base
            [...]
        """
        from ..config.merger import deep_merge

        merged_dict = deep_merge(
            self.model_dump(exclude_none=True), other.model_dump(exclude_none=True)
        )
        return self.__class__(**merged_dict)


class FulmenCatalogModel(FulmenBaseModel):
    """Immutable catalog entry for Foundry pattern data.

    Use Cases:
    - Pattern definitions (regex, glob, literal)
    - MIME type catalog entries
    - HTTP status code definitions
    - Country code mappings
    - Other reference data from Crucible

    Features:
    - Immutable (frozen=True) - catalog entries never change
    - Flexible schema (extra='ignore') - ignores unknown fields from catalog updates
    - Supports lazy-loaded computed fields
    - Optimized for lookups and caching

    Example:
        >>> from pyfulmen.foundry import FulmenCatalogModel
        >>> class Pattern(FulmenCatalogModel):
        ...     id: str
        ...     pattern: str
        ...     pattern_type: str
        ...
        >>> email_pattern = Pattern(
        ...     id="email",
        ...     pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
        ...     pattern_type="regex"
        ... )
    """

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        validate_assignment=True,
        use_enum_values=True,
    )


def utc_now_rfc3339nano() -> str:
    """Generate RFC3339Nano timestamp with microsecond precision.

    Returns current UTC time in RFC3339 format with microsecond precision
    and 'Z' timezone indicator, conforming to Crucible logging standards.

    Returns:
        RFC3339Nano timestamp string (e.g., "2025-10-13T14:32:15.123456Z")

    Example:
        >>> timestamp = utc_now_rfc3339nano()
        >>> timestamp
        '2025-10-13T14:32:15.123456Z'

    Note:
        Uses microsecond precision (not nanosecond) as Python datetime
        provides microsecond resolution. This is sufficient for log
        correlation and meets enterprise requirements.
    """
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def generate_correlation_id() -> str:
    """Generate time-sortable UUIDv7 for correlation tracking.

    UUIDv7 embeds a timestamp in the UUID, making it naturally time-sortable.
    This is beneficial for log aggregation systems (Splunk, Datadog) and
    ensures consistent cross-service correlation.

    Returns:
        UUIDv7 string in standard format

    Example:
        >>> correlation_id = generate_correlation_id()
        >>> correlation_id
        '018b2c5e-8f4a-7890-b123-456789abcdef'

    Note:
        Uses Python 3.12+ stdlib uuid.uuid7() if available, otherwise
        falls back to uuid6 library. All *fulmen libraries
        (gofulmen, tsfulmen, pyfulmen) use UUIDv7 for consistency.
    """
    return str(_uuid7_impl())
