"""Unified bridge API for accessing Crucible assets.

This module provides the primary integration point for tools and applications
to access embedded Crucible schemas, documentation, and configuration defaults.

Tools and applications should use this bridge API instead of implementing
custom Crucible integrations or direct filesystem access.

Example:
    >>> from pyfulmen import crucible
    >>> # Discover assets with metadata
    >>> categories = crucible.list_categories()
    >>> assets = crucible.list_assets('schemas', prefix='observability')
    >>> # Access content with full metadata (v0.1.5+)
    >>> schema, meta = crucible.find_schema('observability/logging/v1.0.0/logger-config')
    >>> print(f"Schema: {meta.format}, {meta.size} bytes, checksum: {meta.checksum[:8]}...")
    >>> doc, doc_meta = crucible.get_doc('standards/agentic-attribution.md')
    >>> # Stream large assets
    >>> with crucible.open_asset('architecture/fulmen-helper-library-standard.md') as f:
    ...     content = f.read()
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from typing import BinaryIO

from .. import foundry
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
        from . import _metadata

        doc_paths = docs.list_available_docs()
        for doc_path in doc_paths:
            if prefix and not doc_path.startswith(prefix):
                continue

            full_path = docs.get_doc_path(doc_path)
            asset_id = doc_path

            assets.append(
                AssetMetadata(
                    id=asset_id,
                    category="docs",
                    path=full_path,
                    description=None,
                    format=_metadata.get_file_format(full_path),
                    size=_metadata.get_file_size(full_path),
                    modified=_metadata.get_modified_time(full_path),
                    checksum=_metadata.compute_checksum(full_path),
                )
            )

    elif category == "schemas":
        from . import _metadata, _paths

        schemas_dir = _paths.get_schemas_dir()
        schema_categories = _discover_schema_categories(schemas_dir)

        for schema_category in schema_categories:
            versions = schemas.list_schema_versions(schema_category)
            for version in versions:
                version_dir = schemas_dir / schema_category / version

                if version_dir.exists():
                    for schema_file in version_dir.glob("*.schema.*"):
                        name = schema_file.stem
                        if name.endswith(".schema"):
                            name = name[: -len(".schema")]

                        schema_id = f"{schema_category}/{version}/{name}"

                        if prefix and not schema_id.startswith(prefix):
                            continue

                        assets.append(
                            AssetMetadata(
                                id=schema_id,
                                category="schemas",
                                path=schema_file,
                                description=None,
                                format=_metadata.get_file_format(schema_file),
                                size=_metadata.get_file_size(schema_file),
                                modified=_metadata.get_modified_time(schema_file),
                                checksum=_metadata.compute_checksum(schema_file),
                            )
                        )

    elif category == "config":
        from . import _metadata, _paths

        config_dir = _paths.get_config_dir()
        config_categories = _discover_config_categories(config_dir)

        for config_category in config_categories:
            versions = config.list_config_versions(config_category)
            for version in versions:
                version_dir = config_dir / config_category / version

                if version_dir.exists():
                    for config_file in version_dir.glob("*.y*ml"):
                        name = config_file.stem
                        config_id = f"{config_category}/{version}/{name}"

                        if prefix and not config_id.startswith(prefix):
                            continue

                        assets.append(
                            AssetMetadata(
                                id=config_id,
                                category="config",
                                path=config_file,
                                description=None,
                                format=_metadata.get_file_format(config_file),
                                size=_metadata.get_file_size(config_file),
                                modified=_metadata.get_modified_time(config_file),
                                checksum=_metadata.compute_checksum(config_file),
                            )
                        )

    return sorted(assets, key=lambda a: a.id)


def get_crucible_version() -> CrucibleVersion:
    """Get version metadata for embedded Crucible assets.

    Returns:
        CrucibleVersion instance with version, commit, and synced_at

    Raises:
        CrucibleVersionError: If version metadata cannot be determined

    Example:
        >>> version = get_crucible_version()
        >>> print(f"Crucible v{version.version} (commit: {version.commit})")
        Crucible v2025.10.0 (commit: unknown)
    """
    return _get_version()


def find_schema(schema_id: str) -> tuple[dict, AssetMetadata]:
    """Load schema by ID and return with full metadata.

    Implements JSON-first, YAML-fallback resolution per Crucible Shim Standard.
    Populates complete AssetMetadata including format, size, checksum, and modified.

    Args:
        schema_id: Schema ID in format 'category/version/name'
                  (e.g., 'observability/logging/v1.0.0/logger-config')

    Returns:
        Tuple of (parsed_schema_dict, asset_metadata)

    Raises:
        AssetNotFoundError: If schema not found (includes suggestions)

    Example:
        >>> schema, meta = find_schema('observability/logging/v1.0.0/logger-config')
        >>> print(f"Schema format: {meta.format}, size: {meta.size} bytes")
        Schema format: json, size: 2048 bytes
    """
    from . import _metadata

    try:
        parts = schema_id.split("/")
        if len(parts) < 3:
            raise ValueError(
                f"Invalid schema ID format: {schema_id}. Expected format: category/version/name"
            )

        version = parts[-2]
        name = parts[-1]
        category = "/".join(parts[:-2])

        schema_path = schemas.get_schema_path(category, version, name)
        schema_data = schemas.load_schema(category, version, name)

        metadata = AssetMetadata(
            id=schema_id,
            category="schemas",
            path=schema_path,
            description=None,
            format=_metadata.get_file_format(schema_path),
            size=_metadata.get_file_size(schema_path),
            modified=_metadata.get_modified_time(schema_path),
            checksum=_metadata.compute_checksum(schema_path),
        )

        return (schema_data, metadata)

    except FileNotFoundError as e:
        all_schema_assets = list_assets("schemas")
        all_schema_ids = [asset.id for asset in all_schema_assets]
        suggestions = _find_similar_assets(schema_id, all_schema_ids)
        raise AssetNotFoundError(schema_id, category="schemas", suggestions=suggestions) from e
    except ValueError as e:
        raise AssetNotFoundError(schema_id, category="schemas") from e


def find_config(config_id: str) -> tuple[dict, AssetMetadata]:
    """Load config by ID and return with full metadata.

    Populates complete AssetMetadata including format, size, checksum, and modified.

    Args:
        config_id: Config ID in format 'category/version/name'
                  (e.g., 'terminal/v1.0.0/terminal-overrides-defaults')

    Returns:
        Tuple of (parsed_config_dict, asset_metadata)

    Raises:
        AssetNotFoundError: If config not found (includes suggestions)

    Example:
        >>> cfg, meta = find_config('terminal/v1.0.0/terminal-overrides-defaults')
        >>> print(f"Config format: {meta.format}, checksum: {meta.checksum[:8]}...")
        Config format: yaml, checksum: abc12345...
    """
    from . import _metadata

    try:
        parts = config_id.split("/")
        if len(parts) < 3:
            raise ValueError(
                f"Invalid config ID format: {config_id}. Expected format: category/version/name"
            )

        version = parts[-2]
        name = parts[-1]
        category = "/".join(parts[:-2])

        config_data = config.load_config_defaults(category, version, name)
        config_path = config.get_config_path(category, version, name)

        metadata = AssetMetadata(
            id=config_id,
            category="config",
            path=config_path,
            description=None,
            format=_metadata.get_file_format(config_path),
            size=_metadata.get_file_size(config_path),
            modified=_metadata.get_modified_time(config_path),
            checksum=_metadata.compute_checksum(config_path),
        )

        return (config_data, metadata)

    except FileNotFoundError as e:
        all_configs = []
        from . import _paths

        config_dir = _paths.get_config_dir()
        for cat in config.list_config_categories():
            for ver in config.list_config_versions(cat):
                version_dir = config_dir / cat / ver
                if version_dir.exists():
                    for config_file in version_dir.glob("*.y*ml"):
                        all_configs.append(f"{cat}/{ver}/{config_file.stem}")

        suggestions = _find_similar_assets(config_id, all_configs)
        raise AssetNotFoundError(config_id, category="config", suggestions=suggestions) from e


def get_doc(doc_id: str) -> tuple[str, AssetMetadata]:
    """Get raw documentation markdown with metadata.

    Returns raw markdown INCLUDING frontmatter. Use docscribe module for parsing.
    Populates complete AssetMetadata including format, size, checksum, and modified.

    Args:
        doc_id: Document ID (relative path with .md extension)
               (e.g., 'standards/agentic-attribution.md')

    Returns:
        Tuple of (raw_markdown_string, asset_metadata)

    Raises:
        AssetNotFoundError: If document not found (includes suggestions)

    Example:
        >>> doc, meta = get_doc('standards/agentic-attribution.md')
        >>> print(f"Doc size: {meta.size} bytes, format: {meta.format}")
        Doc size: 5120 bytes, format: md
    """
    from . import _metadata

    try:
        doc_path = docs.get_doc_path(doc_id)

        with doc_path.open("r", encoding="utf-8") as f:
            raw_content = f.read()

        metadata = AssetMetadata(
            id=doc_id,
            category="docs",
            path=doc_path,
            description=None,
            format=_metadata.get_file_format(doc_path),
            size=_metadata.get_file_size(doc_path),
            modified=_metadata.get_modified_time(doc_path),
            checksum=_metadata.compute_checksum(doc_path),
        )

        return (raw_content, metadata)

    except FileNotFoundError as e:
        all_doc_assets = list_assets("docs")
        all_doc_ids = [asset.id for asset in all_doc_assets]
        suggestions = _find_similar_assets(doc_id, all_doc_ids)
        raise AssetNotFoundError(doc_id, category="docs", suggestions=suggestions) from e


def load_schema_by_id(schema_id: str) -> dict:
    """Load a schema by its ID string.

    .. deprecated:: 0.1.5
        Use :func:`find_schema` instead to get schema with full metadata.
        This function will be removed in v0.2.0.

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
    import warnings

    warnings.warn(
        "load_schema_by_id() is deprecated. Use find_schema() to get schema with metadata. "
        "Will be removed in v0.2.0.",
        DeprecationWarning,
        stacklevel=2,
    )

    schema_data, _ = find_schema(schema_id)
    return schema_data


def get_config_defaults(category: str, version: str, name: str) -> dict:
    """Load configuration defaults.

    .. deprecated:: 0.1.5
        Use :func:`find_config` instead to get config with full metadata.
        This function will be removed in v0.2.0.

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
    import warnings

    warnings.warn(
        "get_config_defaults() is deprecated. Use find_config() to get config with metadata. "
        "Will be removed in v0.2.0.",
        DeprecationWarning,
        stacklevel=2,
    )

    config_id = f"{category}/{version}/{name}"
    config_data, _ = find_config(config_id)
    return config_data


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
    """Find similar asset IDs for suggestions using Foundry similarity module.

    Uses Levenshtein distance with normalization for accurate fuzzy matching.
    Follows Foundry standard defaults (min_score=0.6, normalization enabled).

    Args:
        query: The asset ID that was not found
        candidates: List of available asset IDs
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of similar asset IDs (up to max_suggestions)
    """
    suggestions = foundry.similarity.suggest(
        query,
        candidates,
        min_score=0.6,
        max_suggestions=max_suggestions,
        normalize_text=True
    )
    
    return [s.value for s in suggestions]


__all__ = [
    "list_categories",
    "list_assets",
    "get_crucible_version",
    "find_schema",
    "find_config",
    "get_doc",
    "load_schema_by_id",
    "get_config_defaults",
    "open_asset",
]
