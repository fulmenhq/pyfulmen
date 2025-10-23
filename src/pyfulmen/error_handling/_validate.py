"""
Error validation utilities.

Validates error payloads against Crucible schemas.
"""

from typing import Any

from .models import FulmenError


def validate(error: FulmenError | dict[str, Any]) -> bool:
    """Validate error payload against schema.

    Uses schemas/error-handling/v1.0.0/error-response.schema.json

    Args:
        error: FulmenError instance or dict

    Returns:
        True if valid, False otherwise

    Example:
        >>> from datetime import datetime, UTC
        >>> err = FulmenError(
        ...     code="TEST", message="Test error", timestamp=datetime.now(UTC)
        ... )
        >>> validate(err)
        True
    """
    # Convert to dict if FulmenError
    payload = error.model_dump(mode="json") if isinstance(error, FulmenError) else error

    # Use schema validator
    try:
        from ..schema import validator

        result = validator.validate_data("error-handling", "v1.0.0", "error-response", payload)
        return result.is_valid
    except Exception:
        # Schema validator not available or schema not found
        # Fall back to basic validation
        return _basic_validate(payload)


def _basic_validate(payload: dict[str, Any]) -> bool:
    """Basic validation when schema validator unavailable.

    Checks required fields from Pathfinder base schema.

    Args:
        payload: Error dict to validate

    Returns:
        True if has required fields, False otherwise
    """
    # Required fields from pathfinder/v1.0.0/error-response.schema.json
    required = ["code", "message"]
    return all(field in payload and payload[field] for field in required)
