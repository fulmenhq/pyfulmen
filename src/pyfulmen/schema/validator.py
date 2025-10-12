"""Schema validation utilities using jsonschema.

Provides helpers to validate data against JSON/YAML schemas from Crucible.

Example:
    >>> from pyfulmen.schema import validator
    >>> data = {'severity': 'info', 'message': 'test'}
    >>> validator.validate_against_schema(
    ...     data,
    ...     'observability/logging',
    ...     'v1.0.0',
    ...     'log-event'
    ... )
"""

from typing import Any

from jsonschema import Draft7Validator, ValidationError
from jsonschema import validate as jsonschema_validate

from .. import crucible


class SchemaValidationError(Exception):
    """Schema validation failed."""

    def __init__(self, message: str, errors: list[str] | None = None):
        """Initialize validation error.

        Args:
            message: Error message
            errors: List of validation error details
        """
        super().__init__(message)
        self.errors = errors or []


def load_validator(category: str, version: str, name: str) -> Draft7Validator:
    """Load a jsonschema validator for a Crucible schema.

    Args:
        category: Schema category (e.g., 'observability/logging')
        version: Schema version (e.g., 'v1.0.0')
        name: Schema name without extension (e.g., 'logger-config')

    Returns:
        jsonschema validator instance

    Raises:
        FileNotFoundError: If schema doesn't exist

    Example:
        >>> validator = load_validator('observability/logging', 'v1.0.0', 'logger-config')
        >>> validator.is_valid({'severity': 'info'})
        True
    """
    schema = crucible.schemas.load_schema(category, version, name)
    return Draft7Validator(schema)


def validate_against_schema(
    data: dict[str, Any],
    category: str,
    version: str,
    name: str,
) -> None:
    """Validate data against a Crucible schema.

    Args:
        data: Data to validate
        category: Schema category (e.g., 'observability/logging')
        version: Schema version (e.g., 'v1.0.0')
        name: Schema name without extension (e.g., 'logger-config')

    Raises:
        SchemaValidationError: If validation fails
        FileNotFoundError: If schema doesn't exist

    Example:
        >>> data = {'severity': 'info', 'message': 'test'}
        >>> validate_against_schema(
        ...     data,
        ...     'observability/logging',
        ...     'v1.0.0',
        ...     'log-event'
        ... )
    """
    schema = crucible.schemas.load_schema(category, version, name)

    try:
        jsonschema_validate(instance=data, schema=schema)
    except ValidationError as e:
        # Collect all validation errors
        validator = Draft7Validator(schema)
        errors = [err.message for err in validator.iter_errors(data)]

        raise SchemaValidationError(
            f"Schema validation failed for {category}/{version}/{name}",
            errors=errors,
        ) from e


def is_valid(
    data: dict[str, Any],
    category: str,
    version: str,
    name: str,
) -> bool:
    """Check if data is valid against a schema (non-raising).

    Args:
        data: Data to validate
        category: Schema category (e.g., 'observability/logging')
        version: Schema version (e.g., 'v1.0.0')
        name: Schema name without extension (e.g., 'logger-config')

    Returns:
        True if valid, False otherwise

    Example:
        >>> data = {'severity': 'info', 'message': 'test'}
        >>> is_valid(
        ...     data,
        ...     'observability/logging',
        ...     'v1.0.0',
        ...     'log-event'
        ... )
        True
    """
    try:
        validate_against_schema(data, category, version, name)
        return True
    except (SchemaValidationError, FileNotFoundError):
        return False


__all__ = [
    "SchemaValidationError",
    "load_validator",
    "validate_against_schema",
    "is_valid",
]
