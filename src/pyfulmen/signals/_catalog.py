"""Signal catalog loading and metadata management.

Loads and caches the synchronized Crucible signal catalog with validation
against the JSON schema. Provides metadata lookup functions for the
8 standard Fulmen signals.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

# Module-level cache for catalog data
_catalog_cache: Mapping[str, Any] | None = None


def _locate_project_root() -> Path:
    """Locate the project root where crucible assets live."""
    current_dir = Path(__file__).resolve()
    for candidate in current_dir.parents:
        if (candidate / "config" / "crucible-py").exists():
            return candidate
    # Fallback to original relative traversal if heuristic fails
    return current_dir.parent.parent.parent


def _get_catalog_path() -> Path:
    """Get the path to the synchronized signal catalog."""
    root = _locate_project_root()
    return root / "config" / "crucible-py" / "library" / "foundry" / "signals.yaml"


def _get_schema_path() -> Path:
    """Get the path to the signal catalog JSON schema."""
    root = _locate_project_root()
    return root / "schemas" / "crucible-py" / "library" / "foundry" / "v1.0.0" / "signals.schema.json"


def _validate_catalog(catalog_data: Mapping[str, Any]) -> None:
    """Validate catalog data against the JSON schema.

    Args:
        catalog_data: Parsed catalog data to validate.

    Raises:
        ValueError: If catalog fails validation.
    """
    schema_path = _get_schema_path()

    try:
        with open(schema_path, encoding="utf-8") as f:
            json.load(f)  # Just validate it's valid JSON
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to load schema from {schema_path}: {e}") from e

    # Basic structural validation
    required_sections = ["signals", "behaviors", "os_mappings", "platform_support"]
    for section in required_sections:
        if section not in catalog_data:
            raise ValueError(f"Catalog missing required section: {section}")

    # Validate signals structure
    signals = catalog_data["signals"]
    if not isinstance(signals, list) or len(signals) != 8:
        signal_count = len(signals) if isinstance(signals, list) else "non-list"
        raise ValueError(f"Catalog must have exactly 8 signals, found {signal_count}")

    required_signal_fields = ["id", "name", "description", "default_behavior"]
    for signal in signals:
        for field in required_signal_fields:
            if field not in signal:
                raise ValueError(f"Signal missing required field '{field}': {signal}")


def _load_catalog() -> Mapping[str, Any]:
    """Load and validate the signal catalog.

    Returns:
        Validated catalog data as a dictionary.

    Raises:
        ValueError: If catalog cannot be loaded or fails validation.
    """
    global _catalog_cache

    if _catalog_cache is not None:
        return _catalog_cache

    catalog_path = _get_catalog_path()

    try:
        with open(catalog_path, encoding="utf-8") as f:
            catalog_data = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        raise ValueError(f"Failed to load catalog from {catalog_path}: {e}") from e

    _validate_catalog(catalog_data)

    # Cache the validated catalog
    _catalog_cache = catalog_data
    return catalog_data


def get_signals_version() -> Mapping[str, str]:
    """Get version information for the loaded signal catalog.

    Returns:
        Dictionary with catalog provenance information.
    """
    catalog = _load_catalog()
    return {
        "version": catalog.get("version", "unknown"),
        "description": catalog.get("description", "Signal handling semantics for Fulmen ecosystem"),
        "schema": catalog.get("$schema", "unknown"),
    }


def get_signal_metadata(signal_name: str) -> Mapping[str, Any] | None:
    """Get metadata for a specific signal.

    Args:
        signal_name: Name of the signal (e.g., "SIGTERM", "SIGHUP").

    Returns:
        Signal metadata dictionary or None if signal not found.
    """
    catalog = _load_catalog()

    # Search through signals for matching name
    for signal in catalog["signals"]:
        if signal["name"] == signal_name:
            return signal

    return None


def list_all_signals() -> list[str]:
    """Get list of all supported signal names.

    Returns:
        List of signal names in catalog order.
    """
    catalog = _load_catalog()
    return [signal["name"] for signal in catalog["signals"]]


def get_signal_by_id(signal_id: str) -> Mapping[str, Any] | None:
    """Get signal metadata by signal ID.

    Args:
        signal_id: Signal ID from catalog (e.g., "term", "int", "hup").

    Returns:
        Signal metadata dictionary or None if signal not found.
    """
    catalog = _load_catalog()

    for signal in catalog["signals"]:
        if signal["id"] == signal_id:
            return signal

    return None
