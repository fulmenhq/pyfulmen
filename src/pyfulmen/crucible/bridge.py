"""Unified bridge API for accessing Crucible assets.

This module provides the primary integration point for tools and applications
to access embedded Crucible schemas, documentation, and configuration defaults.

Tools and applications should use this bridge API instead of implementing
custom Crucible integrations or direct filesystem access.

Example:
    >>> from pyfulmen import crucible
    >>> # Discover assets
    >>> categories = crucible.list_categories()
    >>> schemas = crucible.list_assets('schemas', prefix='observability')
    >>> # Access content
    >>> schema = crucible.load_schema_by_id('observability/logging/v1.0.0/logger-config')
    >>> doc = crucible.get_documentation('standards/observability/logging.md')
    >>> # Stream large assets
    >>> with crucible.open_asset('architecture/fulmen-helper-library-standard.md') as f:
    ...     content = f.read()
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from typing import BinaryIO

from . import config, docs, schemas
from ._version import get_crucible_version as _get_version
from .errors import AssetNotFoundError
from .models import AssetMetadata, CrucibleVersion


def list_categories() -> list[str]:
    """List all available Crucible asset categories.

    Returns:
        List of category names: ['docs', 'schemas', 'config']

    Example:
        >>> categories = list_categories()
        >>> print(categories)
        ['docs', 'schemas', 'config']
    """
    return ["docs", "schemas", "config"]


def list_assets(category: str, prefix: str | None = None) -> list[AssetMetadata]:
    """List all assets in a category, optionally filtered by prefix.

    Recursively discovers all assets in nested directory structures.
    For schemas and configs, walks through all subdirectories to find
    versioned assets (e.g., observability/logging/v1.0.0/*).

    Args:
        category: Asset category ('docs', 'schemas', or 'config')
        prefix: Optional prefix to filter asset IDs (e.g., 'observability')

    Returns:
        List of AssetMetadata instances with id, category, and path

    Raises:
        ValueError: If category is not valid

    Example:
        >>> assets = list_assets('schemas', prefix='observability')
        >>> for asset in assets:
        ...     print(f"{asset.id}: {asset.path}")
        observability/logging/v1.0.0/logger-config: /path/to/schema.json
    """
    if category not in ["docs", "schemas", "config"]:
        valid_categories = ", ".join(list_categories())
        raise ValueError(f"Invalid category: {category}. Must be one of: {valid_categories}")

    assets = []

    if category == "docs":
        # List documentation files
        doc_paths = docs.list_available_docs()
        for doc_path in doc_paths:
            # Filter by prefix if provided
            if prefix and not doc_path.startswith(prefix):
                continue

            # Build AssetMetadata
            full_path = docs.get_doc_path(doc_path)
            asset_id = doc_path  # Use relative path as ID
            assets.append(
                AssetMetadata(
                    id=asset_id,
                    category="docs",
                    path=full_path,
                    description=None,
                    checksum=None,
                )
            )

    elif category == "schemas":
        # Recursively discover all schema categories (including nested ones)
        from . import _paths

        schemas_dir = _paths.get_schemas_dir()
        schema_categories = _discover_schema_categories(schemas_dir)

        for schema_category in schema_categories:
            # For each category, list versions
            versions = schemas.list_schema_versions(schema_category)
            for version in versions:
                # Find schema files in this category/version directory
                version_dir = schemas_dir / schema_category / version

                if version_dir.exists():
                    # Find all .schema.json and .schema.yaml files
                    for schema_file in version_dir.glob("*.schema.*"):
                        # Extract name (remove .schema.json or .schema.yaml)
                        name = schema_file.stem
                        # Remove .schema suffix if present
                        if name.endswith(".schema"):
                            name = name[: -len(".schema")]

                        # Build schema ID
                        schema_id = f"{schema_category}/{version}/{name}"

                        # Apply prefix filter to full asset ID (not just category)
                        if prefix and not schema_id.startswith(prefix):
                            continue

                        assets.append(
                            AssetMetadata(
                                id=schema_id,
                                category="schemas",
                                path=schema_file,
                                description=None,
                                checksum=None,
                            )
                        )

    elif category == "config":
        # Recursively discover all config categories (including nested ones)
        from . import _paths

        config_dir = _paths.get_config_dir()
        config_categories = _discover_config_categories(config_dir)

        for config_category in config_categories:
            # For each category, list versions
            versions = config.list_config_versions(config_category)
            for version in versions:
                # Find config files in this category/version directory
                version_dir = config_dir / config_category / version

                if version_dir.exists():
                    # Find all .yaml and .yml files
                    for config_file in version_dir.glob("*.y*ml"):
                        # Extract name (remove extension)
                        name = config_file.stem

                        # Build config ID
                        config_id = f"{config_category}/{version}/{name}"

                        # Apply prefix filter to full asset ID (not just category)
                        if prefix and not config_id.startswith(prefix):
                            continue

                        assets.append(
                            AssetMetadata(
                                id=config_id,
                                category="config",
                                path=config_file,
                                description=None,
                                checksum=None,
                            )
                        )

    return sorted(assets, key=lambda a: a.id)


def get_crucible_version() -> CrucibleVersion:
    """Get version metadata for embedded Crucible assets.

    Returns:
        CrucibleVersion instance with version, sync_date, and commit

    Raises:
        CrucibleVersionError: If version metadata cannot be determined

    Example:
        >>> version = get_crucible_version()
        >>> print(f"Crucible v{version.version}")
        Crucible v2025.10.0
    """
    return _get_version()


def load_schema_by_id(schema_id: str) -> dict:
    """Load a schema by its ID string.

    Convenience wrapper around schemas.load_schema() with enhanced error handling.

    Args:
        schema_id: Schema ID in format 'category/version/name'
                  (e.g., 'observability/logging/v1.0.0/logger-config')

    Returns:
        Parsed schema as dictionary

    Raises:
        AssetNotFoundError: If schema not found (includes suggestions)

    Example:
        >>> schema = load_schema_by_id('observability/logging/v1.0.0/logger-config')
        >>> print(schema['type'])
        object
    """
    try:
        # Parse schema_id into parts
        # Format: category/version/name or category/subcategory/version/name
        parts = schema_id.split("/")
        if len(parts) < 3:
            raise ValueError(
                f"Invalid schema ID format: {schema_id}. Expected format: category/version/name"
            )

        # Last two parts are version and name
        # Everything before that is the category path
        version = parts[-2]
        name = parts[-1]
        category = "/".join(parts[:-2])

        return schemas.load_schema(category, version, name)

    except FileNotFoundError as e:
        # Generate suggestions for similar schema IDs
        # Get all available schema IDs (not just top-level categories)
        all_schema_assets = list_assets("schemas")
        all_schema_ids = [asset.id for asset in all_schema_assets]
        suggestions = _find_similar_assets(schema_id, all_schema_ids)
        raise AssetNotFoundError(schema_id, category="schemas", suggestions=suggestions) from e
    except ValueError as e:
        # Invalid schema ID format
        raise AssetNotFoundError(schema_id, category="schemas") from e


def get_config_defaults(category: str, version: str, name: str) -> dict:
    """Load configuration defaults.

    Convenience wrapper around config.load_config_defaults() with enhanced
    error handling.

    Args:
        category: Config category (e.g., 'terminal')
        version: Version string (e.g., 'v1.0.0')
        name: Config name (e.g., 'terminal-overrides-defaults')

    Returns:
        Configuration dictionary

    Raises:
        AssetNotFoundError: If config not found (includes suggestions)

    Example:
        >>> cfg = get_config_defaults('terminal', 'v1.0.0', 'terminal-overrides-defaults')
        >>> print(cfg.keys())
        dict_keys(['overrides', 'boxChars', ...])
    """
    try:
        return config.load_config_defaults(category, version, name)
    except FileNotFoundError as e:
        # Generate suggestions
        asset_id = f"{category}/{version}/{name}"
        # Get all available config IDs for suggestions
        all_configs = []
        from . import _paths

        config_dir = _paths.get_config_dir()
        for cat in config.list_config_categories():
            for ver in config.list_config_versions(cat):
                version_dir = config_dir / cat / ver
                if version_dir.exists():
                    for config_file in version_dir.glob("*.y*ml"):
                        all_configs.append(f"{cat}/{ver}/{config_file.stem}")

        suggestions = _find_similar_assets(asset_id, all_configs)
        raise AssetNotFoundError(asset_id, category="config", suggestions=suggestions) from e


@contextmanager
def open_asset(asset_id: str) -> Iterator[BinaryIO]:
    """Open an asset for streaming access.

    Context manager yielding binary file handle for large asset streaming.
    Useful for processing large documentation files or datasets.

    Args:
        asset_id: Asset identifier (e.g., 'architecture/fulmen-helper-library-standard.md')

    Yields:
        Binary file object for reading

    Raises:
        AssetNotFoundError: If asset not found

    Example:
        >>> with open_asset('architecture/fulmen-helper-library-standard.md') as f:
        ...     content = f.read()
        ...     print(len(content))
        50000
    """
    # Try to resolve asset_id to path
    # Asset IDs can be:
    # - docs: relative path like "standards/observability/logging.md"
    # - schemas: ID like "observability/logging/v1.0.0/logger-config"
    # - config: ID like "terminal/v1.0.0"

    asset_path = None

    # Try docs first (most common for large files)
    with suppress(FileNotFoundError):
        asset_path = docs.get_doc_path(asset_id)

    # Try schemas (format: category/version/name or category/subcategory/version/name)
    if not asset_path:
        try:
            parts = asset_id.split("/")
            if len(parts) >= 3:
                # Last two are version and name, rest is category
                version = parts[-2]
                name = parts[-1]
                category = "/".join(parts[:-2])
                asset_path = schemas.get_schema_path(category, version, name)
        except (FileNotFoundError, ValueError):
            pass

    # Try config (format: category/version/name)
    if not asset_path:
        try:
            parts = asset_id.split("/")
            if len(parts) >= 3:
                # Last two are version and name, rest is category
                version = parts[-2]
                name = parts[-1]
                category = "/".join(parts[:-2])
                asset_path = config.get_config_path(category, version, name)
        except FileNotFoundError:
            pass

    if not asset_path:
        raise AssetNotFoundError(
            asset_id,
            category=None,
            suggestions=[],
        )

    # Open file in binary mode and yield
    try:
        with asset_path.open("rb") as f:
            yield f
    except Exception as e:
        raise AssetNotFoundError(asset_id, category=None, suggestions=[]) from e


def _discover_schema_categories(schemas_dir) -> list[str]:
    """Recursively discover all schema category paths.

    Walks the schema directory tree to find all paths that contain
    versioned schema files (e.g., observability/logging, library/foundry).

    Args:
        schemas_dir: Root schemas directory path

    Returns:
        List of schema category paths (e.g., ['ascii', 'observability/logging'])
    """
    from pathlib import Path

    categories = []

    if not schemas_dir.exists():
        return categories

    def _walk_for_versions(current_path: Path, relative_path: str = ""):
        """Recursively walk directories looking for version directories."""
        for item in current_path.iterdir():
            if not item.is_dir() or item.name.startswith("."):
                continue

            # Check if this looks like a version directory (starts with 'v')
            if item.name.startswith("v"):
                # Found a version directory - the parent is a schema category
                if relative_path:
                    categories.append(relative_path)
                return  # Don't recurse into version directories

            # Build relative path and recurse
            new_relative = f"{relative_path}/{item.name}" if relative_path else item.name
            _walk_for_versions(item, new_relative)

    _walk_for_versions(schemas_dir)
    return sorted(set(categories))  # Remove duplicates and sort


def _discover_config_categories(config_dir) -> list[str]:
    """Recursively discover all config category paths.

    Walks the config directory tree to find all paths that contain
    versioned config files (e.g., terminal, library/foundry).

    Args:
        config_dir: Root config directory path

    Returns:
        List of config category paths (e.g., ['terminal', 'library/foundry'])
    """
    from pathlib import Path

    categories = []

    if not config_dir.exists():
        return categories

    def _walk_for_versions(current_path: Path, relative_path: str = ""):
        """Recursively walk directories looking for version directories."""
        for item in current_path.iterdir():
            if not item.is_dir() or item.name.startswith("."):
                continue

            # Check if this looks like a version directory (starts with 'v')
            if item.name.startswith("v"):
                # Found a version directory - the parent is a config category
                if relative_path:
                    categories.append(relative_path)
                return  # Don't recurse into version directories

            # Build relative path and recurse
            new_relative = f"{relative_path}/{item.name}" if relative_path else item.name
            _walk_for_versions(item, new_relative)

    _walk_for_versions(config_dir)
    return sorted(set(categories))  # Remove duplicates and sort


def _find_similar_assets(query: str, candidates: list[str], max_suggestions: int = 3) -> list[str]:
    """Find similar asset IDs for suggestions.

    Uses simple string matching based on path parts to find similar IDs.

    Args:
        query: The asset ID that was not found
        candidates: List of available asset IDs
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of similar asset IDs (up to max_suggestions)
    """
    query_parts = set(query.lower().replace(".md", "").replace(".json", "").split("/"))
    suggestions = []

    for candidate in candidates:
        candidate_parts = set(candidate.lower().replace(".md", "").replace(".json", "").split("/"))
        # Count matching parts
        matches = len(query_parts & candidate_parts)
        if matches > 0:
            suggestions.append((matches, candidate))

    # Sort by match count (descending) and return top N
    suggestions.sort(reverse=True, key=lambda x: x[0])
    return [candidate for _, candidate in suggestions[:max_suggestions]]


__all__ = [
    "list_categories",
    "list_assets",
    "get_crucible_version",
    "load_schema_by_id",
    "get_config_defaults",
    "open_asset",
]
