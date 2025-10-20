"""
Pathfinder - Safe filesystem discovery and traversal for pyfulmen.

This module provides safe, pattern-based file discovery operations with
built-in path validation and normalization. It addresses the brittleness
of doublestar and glob patterns with a canonical, well-tested implementation.

Key Features:
- Safe path validation (prevents traversal attacks)
- Glob pattern matching for file discovery
- Proper path normalization using pathlib
- Configurable discovery options
- Schema validation support

Example:
    >>> from pyfulmen.pathfinder import Finder, FindQuery
    >>>
    >>> # Simple discovery
    >>> finder = Finder()
    >>> results = finder.find_python_files("src/")
    >>>
    >>> # Advanced discovery with patterns
    >>> query = FindQuery(
    ...     root=".",
    ...     include=["*.py", "*.md"],
    ...     exclude=["**/test_*.py"],
    ...     max_depth=3
    ... )
    >>> results = finder.find_files(query)
"""

from .finder import Finder
from .models import (
    ConstraintType,
    EnforcementLevel,
    FinderConfig,
    FindQuery,
    PathConstraint,
    PathMetadata,
    PathResult,
)
from .safety import (
    InvalidPathError,
    PathTraversalError,
    is_safe_path,
    validate_path,
)

__all__ = [
    # Core classes
    "Finder",
    # Data models
    "FindQuery",
    "PathResult",
    "FinderConfig",
    "PathConstraint",
    "ConstraintType",
    "EnforcementLevel",
    "PathMetadata",
    # Safety functions
    "validate_path",
    "is_safe_path",
    # Exceptions
    "PathTraversalError",
    "InvalidPathError",
]
