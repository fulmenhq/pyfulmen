"""
File discovery and path finding operations for pyfulmen.pathfinder.

Provides the Finder class for safe, pattern-based file discovery with
proper path normalization using pathlib.
"""

from __future__ import annotations

from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path

from pyfulmen.schema import validator as schema_validator

from .ignore import IgnoreMatcher
from .models import (
    EnforcementLevel,
    FinderConfig,
    FindQuery,
    PathConstraint,
    PathMetadata,
    PathResult,
)
from .safety import PathTraversalError, validate_path


class Finder:
    """
    High-level path discovery operations with safety checks.

    The Finder class provides methods for discovering files based on glob patterns,
    with built-in path validation and normalization using pathlib.Path.

    Example:
        >>> finder = Finder()
        >>> query = FindQuery(root=".", include=["*.py"])
        >>> results = finder.find_files(query)
        >>> for result in results:
        ...     print(result.relative_path)
    """

    def __init__(self, config: FinderConfig | None = None):
        """
        Initialize a new Finder instance.

        Args:
            config: Configuration for finder operations. If None, uses defaults.
        """
        self.config = config or FinderConfig()

    def find_files(self, query: FindQuery) -> list[PathResult]:
        """
        Perform file discovery based on the query parameters.

        Uses pathlib.Path for proper path normalization and traversal.

        Args:
            query: FindQuery specifying discovery parameters

        Returns:
            List of PathResult objects for discovered files

        Raises:
            ValueError: If query validation fails (when validate_inputs=True)
            PathTraversalError: If unsafe paths are detected
        """
        # Validate input if enabled
        if self.config.validate_inputs:
            schema_validator.validate_against_schema(
                query.model_dump(by_alias=True, exclude_none=True),
                "pathfinder",
                "v1.0.0",
                "find-query",
            )

        results: list[PathResult] = []

        # Normalize root path using pathlib
        root_path = Path(query.root).resolve()

        ignore_matcher: IgnoreMatcher | None = None
        try:
            ignore_matcher = IgnoreMatcher(root_path)
        except OSError as err:
            if query.error_handler:
                query.error_handler(str(root_path / ".fulmenignore"), err)

        constraint = self.config.constraint
        constraint_root: Path | None = None
        if constraint:
            constraint_root = Path(constraint.root).resolve()

        # For each include pattern, find matching files
        for pattern in query.include:
            matches = root_path.glob(pattern)

            for match in matches:
                try:
                    # Ensure we are working with absolute paths without resolving symlinks
                    abs_match = match if match.is_absolute() else root_path / match

                    # Skip directories (Path.glob can yield directories)
                    if abs_match.is_dir():
                        continue

                    # Validate path safety using string representation
                    validate_path(str(abs_match))

                    # Skip symlinks unless explicitly following them
                    if abs_match.is_symlink() and not query.follow_symlinks:
                        continue

                    # Get relative path using pathlib
                    try:
                        rel_path = abs_match.relative_to(root_path)
                    except ValueError:
                        # Path is not relative to root, skip
                        if query.error_handler:
                            query.error_handler(
                                str(abs_match),
                                ValueError(f"Path {abs_match} not under root {root_path}"),
                            )
                        continue

                    # Skip if path matches exclude patterns
                    if query.exclude and any(rel_path.match(excl) for excl in query.exclude):
                        continue

                    # Honour .fulmenignore patterns
                    if ignore_matcher and ignore_matcher.is_ignored(rel_path):
                        continue

                    # Skip hidden files/directories unless explicitly included
                    if not query.include_hidden and any(
                        part.startswith(".") for part in rel_path.parts
                    ):
                        continue

                    # Check max depth if specified
                    if query.max_depth > 0 and len(rel_path.parts) > query.max_depth:
                        continue

                    # Enforce path constraints if configured
                    if constraint_root and self._violates_constraint(
                        constraint, constraint_root, rel_path, abs_match
                    ):
                        violation = PathTraversalError(
                            f"Path {abs_match} violates constraint root {constraint_root}"
                        )

                        enforcement_value = constraint.enforcement_level

                        if enforcement_value == EnforcementLevel.STRICT.value:
                            raise violation

                        if enforcement_value == EnforcementLevel.WARN.value:
                            if query.error_handler:
                                query.error_handler(str(abs_match), violation)
                            continue

                        # Permissive enforcement allows the path to pass through.

                    metadata = self._build_metadata(abs_match)

                    # Create result using normalized paths
                    result = PathResult(
                        relative_path=str(rel_path),
                        source_path=str(abs_match),
                        logical_path=str(rel_path),  # Same as relative for now
                        loader_type=self.config.loader_type,
                        metadata=metadata,
                    )

                    results.append(result)

                    # Progress callback
                    if query.progress_callback:
                        query.progress_callback(len(results), -1, str(abs_match))

                except PathTraversalError:
                    raise
                except Exception as err:
                    # Handle errors via callback or continue
                    if query.error_handler:
                        error_result = query.error_handler(str(match), err)
                        if error_result:
                            # If error handler returns an error, propagate it
                            raise error_result from err
                    # Otherwise continue to next file
                    continue

        # Validate outputs if enabled
        if self.config.validate_outputs:
            for result in results:
                schema_validator.validate_against_schema(
                    result.model_dump(by_alias=True, exclude_none=True),
                    "pathfinder",
                    "v1.0.0",
                    "path-result",
                )

        return results

    def find_config_files(self, root: str) -> list[PathResult]:
        """
        Find common configuration files.

        Args:
            root: Root directory to search from

        Returns:
            List of PathResult objects for discovered config files

        Example:
            >>> finder = Finder()
            >>> configs = finder.find_config_files(".")
            >>> print(f"Found {len(configs)} config files")
        """
        query = FindQuery(
            root=root,
            include=["*.json", "*.yaml", "*.yml", "*.toml", "*.config", "*.conf"],
        )
        return self.find_files(query)

    def find_schema_files(self, root: str) -> list[PathResult]:
        """
        Find JSON Schema files.

        Args:
            root: Root directory to search from

        Returns:
            List of PathResult objects for discovered schema files

        Example:
            >>> finder = Finder()
            >>> schemas = finder.find_schema_files("schemas/")
            >>> for schema in schemas:
            ...     print(schema.relative_path)
        """
        query = FindQuery(
            root=root,
            include=["*.schema.json", "schema.json"],
        )
        return self.find_files(query)

    def find_by_extension(self, root: str, extensions: list[str]) -> list[PathResult]:
        """
        Find files with specific extensions.

        Args:
            root: Root directory to search from
            extensions: List of file extensions (without dots)

        Returns:
            List of PathResult objects for discovered files

        Example:
            >>> finder = Finder()
            >>> py_files = finder.find_by_extension(".", ["py", "pyi"])
            >>> print(f"Found {len(py_files)} Python files")
        """
        patterns = [f"*.{ext}" for ext in extensions]
        query = FindQuery(root=root, include=patterns)
        return self.find_files(query)

    def find_python_files(self, root: str) -> list[PathResult]:
        """
        Find Python source files (*.py).

        Args:
            root: Root directory to search from

        Returns:
            List of PathResult objects for discovered Python files

        Example:
            >>> finder = Finder()
            >>> py_files = finder.find_python_files("src/")
            >>> for file in py_files:
            ...     print(file.relative_path)
        """
        return self.find_by_extension(root, ["py"])

    @staticmethod
    def _build_metadata(path: Path) -> PathMetadata:
        """Construct metadata for a discovered path."""
        try:
            stat_result = path.stat()
        except OSError:
            return PathMetadata()

        modified = datetime.fromtimestamp(stat_result.st_mtime, tz=UTC).isoformat()
        permissions = oct(stat_result.st_mode & 0o777)

        return PathMetadata(
            size=stat_result.st_size,
            modified=modified,
            permissions=permissions,
        )

    @staticmethod
    def _violates_constraint(
        constraint: PathConstraint,
        constraint_root: Path,
        relative_path: Path,
        absolute_path: Path,
    ) -> bool:
        """Check whether a discovered path violates the configured constraint."""
        path_posix = relative_path.as_posix()

        # Allowed patterns override constraint failures.
        if constraint.allowed_patterns and any(
            fnmatch(path_posix, pattern) for pattern in constraint.allowed_patterns
        ):
            return False

        # Blocked patterns cause immediate violation.
        if constraint.blocked_patterns and any(
            fnmatch(path_posix, pattern) for pattern in constraint.blocked_patterns
        ):
            return True

        try:
            absolute_path.resolve().relative_to(constraint_root)
        except ValueError:
            return True

        return False
