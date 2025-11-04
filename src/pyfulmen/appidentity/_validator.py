"""
Schema validation for app identity files.

This module provides validation against the canonical Crucible
app identity schema using jsonschema.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError

from .errors import AppIdentityValidationError


class AppIdentityValidator:
    """Validator for app identity files using canonical schema."""

    def __init__(self, schema_path: Path) -> None:
        """Initialize validator with schema file."""
        self.schema_path = schema_path
        self._schema: dict | None = None
        self._validator: Draft7Validator | None = None

    @property
    def schema(self) -> dict:
        """Load and cache the schema."""
        if self._schema is None:
            try:
                with open(self.schema_path, encoding="utf-8") as f:
                    self._schema = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                raise AppIdentityValidationError(self.schema_path, [f"Failed to load schema: {e}"]) from e
        return self._schema  # type: ignore

    @property
    def validator(self) -> Draft7Validator:
        """Get jsonschema validator instance."""
        if self._validator is None:
            try:
                self._validator = Draft7Validator(self.schema)
            except SchemaError as e:
                raise AppIdentityValidationError(self.schema_path, [f"Invalid schema: {e}"]) from e
        return self._validator

    def validate(self, data: dict, data_path: Path) -> None:
        """
        Validate data against schema.

        Args:
            data: Dictionary to validate
            data_path: Path of the data file (for error messages)

        Raises:
            AppIdentityValidationError: If validation fails
        """
        errors = []

        for error in self.validator.iter_errors(data):
            # Build detailed error path
            path_parts = list(error.absolute_path)
            if path_parts:
                field_path = ".".join(str(p) for p in path_parts)
                errors.append(f"Field '{field_path}': {error.message}")
            else:
                errors.append(f"Schema error: {error.message}")

        if errors:
            raise AppIdentityValidationError(data_path, errors)

    def validate_and_normalize(self, data: dict, data_path: Path) -> dict:
        """
        Validate data and apply defaults from schema.

        Args:
            data: Dictionary to validate
            data_path: Path of the data file

        Returns:
            Normalized data with defaults applied

        Raises:
            AppIdentityValidationError: If validation fails
        """
        # First validate the data
        self.validate(data, data_path)

        # Apply defaults from schema
        normalized = data.copy()
        defaults = self.schema.get("properties", {})

        # Apply defaults for app object
        app_defaults = defaults.get("app", {}).get("properties", {})
        for key, default in app_defaults.items():
            if key not in normalized.get("app", {}):
                normalized.setdefault("app", {})[key] = default.get("default")

        # Apply defaults for metadata object
        metadata_defaults = defaults.get("metadata", {}).get("properties", {})
        for key, default in metadata_defaults.items():
            if key not in normalized.get("metadata", {}):
                normalized.setdefault("metadata", {})[key] = default.get("default")

        return normalized


# Create default validator instance
_CANONICAL_SCHEMA_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "schemas"
    / "crucible-py"
    / "config"
    / "repository"
    / "app-identity"
    / "v1.0.0"
    / "app-identity.schema.json"
)

_default_validator: AppIdentityValidator | None = None


def get_validator() -> AppIdentityValidator:
    """Get default validator instance."""
    global _default_validator
    if _default_validator is None:
        _default_validator = AppIdentityValidator(_CANONICAL_SCHEMA_PATH)
    return _default_validator


def validate_app_identity(data: dict, data_path: Path) -> dict:
    """
    Validate app identity data and apply defaults.

    Args:
        data: App identity dictionary to validate
        data_path: Path of the identity file

    Returns:
        Normalized data with defaults applied

    Raises:
        AppIdentityValidationError: If validation fails
    """
    validator = get_validator()
    return validator.validate_and_normalize(data, data_path)
