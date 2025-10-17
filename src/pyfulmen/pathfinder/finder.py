"""
File discovery and path finding operations for pyfulmen.pathfinder.

Provides the Finder class for safe, pattern-based file discovery with
proper path normalization using pathlib.
"""

import os
from pathlib import Path
from typing import Optional

from .models import FindQuery, FinderConfig, PathResult
from .safety import validate_path


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

    def __init__(self, config: Optional[FinderConfig] = None):
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
            # TODO: Implement schema validation when pathfinder schemas are available
            pass

        results: list[PathResult] = []

        # Normalize root path using pathlib
        root_path = Path(query.root).resolve()

        # For each include pattern, find matching files
        for pattern in query.include:
            # Use rglob for recursive patterns, glob for non-recursive
            if "**" in pattern:
                matches = root_path.rglob(pattern.replace("**/", ""))
            else:
                matches = root_path.glob(pattern)

            for match in matches:
                try:
                    # Resolve to absolute path for safety checks
                    abs_match = match.resolve()

                    # Validate path safety using string representation
                    validate_path(str(abs_match))

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

                    # Skip hidden files/directories unless explicitly included
                    if not query.include_hidden and any(
                        part.startswith(".") for part in rel_path.parts
                    ):
                        continue

                    # Skip symlinks unless explicitly following them
                    if abs_match.is_symlink() and not query.follow_symlinks:
                        continue

                    # Check max depth if specified
                    if query.max_depth > 0 and len(rel_path.parts) > query.max_depth:
                        continue

                    # Create result using normalized paths
                    result = PathResult(
                        relative_path=str(rel_path),
                        source_path=str(abs_match),
                        logical_path=str(rel_path),  # Same as relative for now
                        loader_type=self.config.loader_type,
                        metadata={},
                    )

                    results.append(result)

                    # Progress callback
                    if query.progress_callback:
                        query.progress_callback(len(results), -1, str(abs_match))

                except Exception as err:
                    # Handle errors via callback or continue
                    if query.error_handler:
                        error_result = query.error_handler(str(match), err)
                        if error_result:
                            # If error handler returns an error, propagate it
                            raise error_result
                    # Otherwise continue to next file
                    continue

        # Validate outputs if enabled
        if self.config.validate_outputs:
            # TODO: Implement schema validation when pathfinder schemas are available
            pass

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
