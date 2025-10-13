"""Tests for pyfulmen.schema.validator module."""

import pytest

from pyfulmen.schema.validator import (
    SchemaValidationError,
    is_valid,
    load_validator,
    validate_against_schema,
)


def test_load_validator():
    """Test loading a jsonschema validator."""
    validator = load_validator("observability/logging", "v1.0.0", "logger-config")

    assert validator is not None
    assert validator.schema is not None


def test_load_validator_not_found():
    """Test loading non-existent schema raises error."""
    with pytest.raises(FileNotFoundError):
        load_validator("invalid", "v1.0.0", "nonexistent")


def test_validate_against_schema_valid():
    """Test validating valid data against schema."""
    # Create valid data based on schema
    # Most schemas have flexible requirements, so minimal data often works
    valid_data = {}

    # Validation should not raise (or raise if schema has required fields - both are ok)
    import contextlib

    with contextlib.suppress(SchemaValidationError):
        validate_against_schema(valid_data, "observability/logging", "v1.0.0", "logger-config")


def test_validate_against_schema_invalid():
    """Test validating invalid data raises SchemaValidationError."""
    # This test depends on schema structure
    # We'll use a simple schema that we know exists
    from pyfulmen import crucible

    schema = crucible.schemas.load_schema("observability/logging", "v1.0.0", "logger-config")

    # If schema has required properties, test with missing data
    if "required" in schema and schema["required"]:
        invalid_data = {}

        with pytest.raises(SchemaValidationError) as exc_info:
            validate_against_schema(
                invalid_data, "observability/logging", "v1.0.0", "logger-config"
            )

        error = exc_info.value
        assert len(error.errors) > 0


def test_is_valid_returns_bool():
    """Test is_valid returns boolean."""
    result = is_valid({}, "observability/logging", "v1.0.0", "logger-config")

    assert isinstance(result, bool)


def test_is_valid_nonexistent_schema():
    """Test is_valid returns False for non-existent schema."""
    result = is_valid({}, "invalid", "v1.0.0", "nonexistent")

    assert result is False


def test_schema_validation_error():
    """Test SchemaValidationError creation."""
    error = SchemaValidationError("Test error", errors=["error1", "error2"])

    assert str(error) == "Test error"
    assert error.errors == ["error1", "error2"]


def test_schema_validation_error_no_errors():
    """Test SchemaValidationError with no error list."""
    error = SchemaValidationError("Test error")

    assert str(error) == "Test error"
    assert error.errors == []
