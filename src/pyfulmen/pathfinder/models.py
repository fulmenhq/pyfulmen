"""
Data models for pyfulmen.pathfinder.

Defines the core data structures for file discovery operations.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import ConfigDict, Field

from pyfulmen.foundry import FulmenConfigModel, FulmenDataModel


def _to_camel(value: str) -> str:
    """Convert snake_case strings to camelCase for schema parity."""
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _data_model_config(**updates: Any) -> ConfigDict:
    cfg = FulmenDataModel.model_config.copy()
    cfg.update(updates)
    return cfg


def _config_model_config(**updates: Any) -> ConfigDict:
    cfg = FulmenConfigModel.model_config.copy()
    cfg.update(updates)
    return cfg


class FindQuery(FulmenDataModel):
    """
    Specifies parameters for file discovery operations.

    Attributes:
        root: Root directory to search from
        include: Glob patterns to include (e.g., ["*.py", "*.md"])
        exclude: Glob patterns to exclude (optional)
        max_depth: Maximum directory depth (0 = unlimited)
        follow_symlinks: Whether to follow symbolic links
        include_hidden: Whether to include hidden files/directories
        error_handler: Callback for handling errors during discovery
        progress_callback: Callback for reporting discovery progress
    """

    model_config = _data_model_config(alias_generator=_to_camel, populate_by_name=True)

    root: str = Field(..., description="Root directory to search from")
    include: list[str] = Field(..., description="Glob patterns to include")
    exclude: list[str] = Field(default_factory=list, description="Glob patterns to exclude")
    max_depth: int = Field(default=0, description="Maximum directory depth (0 = unlimited)")
    follow_symlinks: bool = Field(default=False, description="Follow symbolic links")
    include_hidden: bool = Field(default=False, description="Include hidden files/directories")

    # Note: Callbacks can't be serialized to JSON, so we mark them as excluded
    error_handler: Callable[[str, Exception], Exception | None] | None = Field(
        default=None, exclude=True, description="Error handler callback"
    )
    progress_callback: Callable[[int, int, str], None] | None = Field(
        default=None, exclude=True, description="Progress callback"
    )


class PathResult(FulmenDataModel):
    """
    Represents a discovered file or directory.

    Attributes:
        relative_path: Path relative to search root
        source_path: Absolute path to the file
        logical_path: Logical path (defaults to relative_path)
        loader_type: Type of loader used (e.g., "local")
        metadata: Additional metadata about the path
    """

    model_config = _data_model_config(alias_generator=_to_camel, populate_by_name=True)

    relative_path: str = Field(..., description="Path relative to search root")
    source_path: str = Field(..., description="Absolute path to the file")
    logical_path: str = Field(..., description="Logical path")
    loader_type: str = Field(default="local", description="Type of loader used")
    metadata: PathMetadata = Field(
        default_factory=lambda: PathMetadata(), description="Additional metadata"
    )


class ConstraintType(str, Enum):
    """Constraint classification for enforcement context."""

    REPOSITORY = "repository"
    WORKSPACE = "workspace"
    CLOUD = "cloud"


class EnforcementLevel(str, Enum):
    """Enforcement severity levels for constraint violations."""

    STRICT = "strict"
    WARN = "warn"
    PERMISSIVE = "permissive"


class PathConstraint(FulmenConfigModel):
    """
    Path constraint configuration describing permissible filesystem boundaries.

    Attributes:
        root: Canonical root directory for the constraint
        constraint_type: Classification of boundary (repository/workspace/cloud)
        enforcement_level: Severity when paths escape boundary
        allowed_patterns: Overrides that permit additional paths
        blocked_patterns: Patterns that should always be rejected
    """

    model_config = _config_model_config(alias_generator=_to_camel, populate_by_name=True)

    root: str = Field(..., description="Root path for the constraint boundary")
    constraint_type: ConstraintType = Field(
        default=ConstraintType.REPOSITORY, alias="type", description="Type of constraint"
    )
    enforcement_level: EnforcementLevel = Field(
        default=EnforcementLevel.STRICT,
        alias="enforcementLevel",
        description="Constraint enforcement strictness",
    )
    allowed_patterns: list[str] = Field(
        default_factory=list,
        alias="allowedPatterns",
        description="Additional allowed path patterns",
    )
    blocked_patterns: list[str] = Field(
        default_factory=list,
        alias="blockedPatterns",
        description="Blocked path patterns",
    )


class PathMetadata(FulmenDataModel):
    """
    File metadata captured during discovery operations.

    Attributes mirror the Crucible metadata schema.
    """

    model_config = _data_model_config(alias_generator=_to_camel, populate_by_name=True)

    size: int | None = Field(default=None, ge=0, description="File size in bytes")
    modified: str | None = Field(default=None, description="Last modification timestamp (RFC3339)")
    permissions: str | None = Field(
        default=None, description="File permissions (octal or symbolic)"
    )
    mime_type: str | None = Field(
        default=None, description="MIME type of the file", alias="mimeType"
    )
    encoding: str | None = Field(default=None, description="Character encoding")
    checksum: str | None = Field(default=None, description="Checksum or hash")
    checksum_algorithm: str | None = Field(
        default=None, alias="checksumAlgorithm", description="Algorithm used for checksum"
    )
    checksum_error: str | None = Field(
        default=None,
        alias="checksumError",
        description="Error message if checksum calculation failed",
    )
    tags: list[str] = Field(default_factory=list, description="User-defined tags")
    custom: dict[str, Any] = Field(default_factory=dict, description="Custom metadata fields")


class FinderConfig(FulmenConfigModel):
    """
    Configuration for Finder operations.

    Attributes:
        max_workers: Maximum number of concurrent workers
        cache_enabled: Whether to enable result caching
        cache_ttl: Cache TTL in seconds
        loader_type: Default loader type ("local", "remote", etc.)
        validate_inputs: Whether to validate FindQuery inputs against schema
        validate_outputs: Whether to validate PathResult outputs against schema
        calculate_checksums: Whether to calculate file checksums during discovery
        checksum_algorithm: Hash algorithm for checksums ("xxh3-128" or "sha256")
        checksum_encoding: Output encoding for checksums ("hex")
    """

    model_config = _config_model_config(alias_generator=_to_camel, populate_by_name=True)

    max_workers: int = Field(default=4, description="Maximum concurrent workers")
    cache_enabled: bool = Field(default=False, description="Enable result caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    loader_type: str = Field(default="local", description="Default loader type")
    validate_inputs: bool = Field(default=False, description="Validate FindQuery inputs")
    validate_outputs: bool = Field(default=False, description="Validate PathResult outputs")
    constraint: PathConstraint | None = Field(
        default=None, description="Constraint configuration for permissible paths"
    )
    calculate_checksums: bool = Field(
        default=False,
        alias="calculateChecksums",
        description="Calculate file checksums during discovery",
    )
    checksum_algorithm: str = Field(
        default="xxh3-128", alias="checksumAlgorithm", description="Hash algorithm for checksums"
    )
    checksum_encoding: str = Field(
        default="hex", alias="checksumEncoding", description="Output encoding for checksums"
    )


__all__ = [
    "FindQuery",
    "PathResult",
    "FinderConfig",
    "PathConstraint",
    "ConstraintType",
    "EnforcementLevel",
    "PathMetadata",
]
