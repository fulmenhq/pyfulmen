"""Schema loading utilities for Crucible assets.

This module provides helpers to discover and load JSON/YAML schemas
from the synced Crucible repository.

Example:
    >>> from pyfulmen.crucible import schemas
    >>> schemas.list_available_schemas()
    ['ascii', 'config', 'observability', 'pathfinder', ...]
    >>> schema = schemas.load_schema('observability', 'logging', 'v1.0.0', 'logger-config')
"""

import json
from pathlib import Path
from typing import Any

import yaml

from . import _paths


def list_available_schemas() -> list[str]:
    """List all available schema categories.

    Returns:
        List of schema category names (e.g., ['ascii', 'config', ...])

    Example:
        >>> list_available_schemas()
        ['ascii', 'config', 'observability', ...]
    """
    schemas_dir = _paths.get_schemas_dir()

    if not schemas_dir.exists():
        return []

    categories = [
        d.name
        for d in schemas_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]

    return sorted(categories)


def list_schema_versions(category: str) -> list[str]:
    """List available versions for a schema category.

    Args:
        category: Schema category (e.g., 'observability/logging')

    Returns:
        List of version directories (e.g., ['v1.0.0', 'v1.1.0'])

    Example:
        >>> list_schema_versions('observability/logging')
        ['v1.0.0']
    """
    schemas_dir = _paths.get_schemas_dir()
    category_path = schemas_dir / category

    if not category_path.exists():
        return []

    versions = [
        d.name
        for d in category_path.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]

    return sorted(versions)


def get_schema_path(category: str, version: str, name: str) -> Path:
    """Get path to a schema file.

    Args:
        category: Schema category (e.g., 'observability/logging')
        version: Schema version (e.g., 'v1.0.0')
        name: Schema name without extension (e.g., 'logger-config')

    Returns:
        Path to schema file

    Raises:
        FileNotFoundError: If schema file doesn't exist

    Example:
        >>> get_schema_path('observability/logging', 'v1.0.0', 'logger-config')
        PosixPath('.../schemas/crucible-py/observability/logging/v1.0.0/logger-config.schema.json')
    """
    schemas_dir = _paths.get_schemas_dir()

    # Try both .json and .yaml extensions
    for ext in [".schema.json", ".schema.yaml", ".json", ".yaml"]:
        schema_path = schemas_dir / category / version / f"{name}{ext}"
        if schema_path.exists():
            return schema_path

    # Not found - raise with helpful message
    raise FileNotFoundError(
        f"Schema not found: {category}/{version}/{name}\n"
        f"Searched in: {schemas_dir / category / version}\n"
        "Run 'make sync-crucible' to sync Crucible assets."
    )


def load_schema(category: str, version: str, name: str) -> dict[str, Any]:
    """Load a JSON/YAML schema from Crucible.

    Args:
        category: Schema category (e.g., 'observability/logging')
        version: Schema version (e.g., 'v1.0.0')
        name: Schema name without extension (e.g., 'logger-config')

    Returns:
        Parsed schema as dictionary

    Raises:
        FileNotFoundError: If schema file doesn't exist
        ValueError: If schema file cannot be parsed

    Example:
        >>> schema = load_schema('observability/logging', 'v1.0.0', 'logger-config')
        >>> schema['$schema']
        'https://json-schema.org/draft/2020-12/schema'
    """
    schema_path = get_schema_path(category, version, name)

    try:
        with open(schema_path) as f:
            if schema_path.suffix == ".json":
                return json.load(f)
            else:  # .yaml or .yml
                return yaml.safe_load(f)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise ValueError(f"Failed to parse schema {schema_path}: {e}") from e


__all__ = [
    "list_available_schemas",
    "list_schema_versions",
    "get_schema_path",
    "load_schema",
]
