"""
Data models for pyfulmen.pathfinder.

Defines the core data structures for file discovery operations.
"""

from typing import Any, Callable, Optional

from pydantic import Field

from pyfulmen.foundry import FulmenConfigModel, FulmenDataModel


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

    root: str = Field(..., description="Root directory to search from")
    include: list[str] = Field(..., description="Glob patterns to include")
    exclude: list[str] = Field(default_factory=list, description="Glob patterns to exclude")
    max_depth: int = Field(default=0, description="Maximum directory depth (0 = unlimited)")
    follow_symlinks: bool = Field(default=False, description="Follow symbolic links")
    include_hidden: bool = Field(default=False, description="Include hidden files/directories")

    # Note: Callbacks can't be serialized to JSON, so we mark them as excluded
    error_handler: Optional[Callable[[str, Exception], Optional[Exception]]] = Field(
        default=None, exclude=True, description="Error handler callback"
    )
    progress_callback: Optional[Callable[[int, int, str], None]] = Field(
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

    relative_path: str = Field(..., description="Path relative to search root")
    source_path: str = Field(..., description="Absolute path to the file")
    logical_path: str = Field(..., description="Logical path")
    loader_type: str = Field(default="local", description="Type of loader used")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


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
    """

    max_workers: int = Field(default=4, description="Maximum concurrent workers")
    cache_enabled: bool = Field(default=False, description="Enable result caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    loader_type: str = Field(default="local", description="Default loader type")
    validate_inputs: bool = Field(default=False, description="Validate FindQuery inputs")
    validate_outputs: bool = Field(default=False, description="Validate PathResult outputs")
