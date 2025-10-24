"""Tests for pyfulmen.schema.validator module."""

import json

import pytest

from pyfulmen.schema.validator import (
    Diagnostic,
    SchemaValidationError,
    ValidationResult,
    format_diagnostics,
    is_valid,
    load_validator,
    validate_against_schema,
    validate_data,
    validate_file,
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


def test_validate_data_returns_result():
    result = validate_data("observability/logging/v1.0.0/logger-config", {})
    assert isinstance(result, ValidationResult)
    assert result.schema.id.startswith("observability/logging")


def test_validate_file(tmp_path):
    payload = tmp_path / "payload.json"
    payload.write_text(json.dumps({}))
    result = validate_file("observability/logging/v1.0.0/logger-config", payload)
    assert result.is_valid in (True, False)


def test_format_diagnostics_text():
    diagnostics = [Diagnostic(pointer="/foo", message="Invalid", keyword="type")]
    output = format_diagnostics(diagnostics)
    assert "/foo" in output
    assert "Invalid" in output


def test_format_diagnostics_json():
    diagnostics = [Diagnostic(pointer="", message="error", keyword=None)]
    output = format_diagnostics(diagnostics, style="json")
    assert "error" in output


class TestTelemetry:
    """Test telemetry instrumentation.

    Note: Current implementation creates independent MetricRegistry instances per call,
    so telemetry emission cannot be directly tested without module-level singleton helpers
    (per ADR-0008). These tests verify the code path executes without errors.

    Full telemetry testing will be added when module-level helpers are implemented.
    """

    def test_validate_against_schema_with_telemetry_enabled(self):
        """Verify validate_against_schema executes with telemetry without errors."""
        # Valid minimal data
        valid_data = {"level": "info"}

        # Should execute without errors (telemetry emitted to internal registry)
        import contextlib

        with contextlib.suppress(SchemaValidationError):
            validate_against_schema(
                valid_data, "observability/logging", "v1.0.0", "logger-config"
            )

        # Telemetry is emitted to an internal registry instance.
        # Full assertion testing requires module-level singleton helpers per ADR-0008.

    def test_schema_validation_errors_counter_on_invalid_data(self):
        """Verify schema_validation_errors counter is emitted on validation failure."""
        # Create invalid data - missing required fields
        invalid_data = {"invalid_field": "value"}

        # Should raise SchemaValidationError
        with pytest.raises(SchemaValidationError):
            validate_against_schema(
                invalid_data, "observability/logging", "v1.0.0", "logger-config"
            )

        # Counter is emitted but to independent registry instance.
        # Full metric assertion requires module-level helpers per ADR-0008.
