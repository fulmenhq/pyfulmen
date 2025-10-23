"""
Tests for error_handling._validate

Covers validation of error payloads against schemas.
"""

from datetime import UTC, datetime
from unittest.mock import patch

from pyfulmen.error_handling import FulmenError, validate
from pyfulmen.error_handling._validate import _basic_validate


class TestValidate:
    """Tests for validate() function."""

    def test_validate_fulmen_error_instance(self):
        """Test validating FulmenError instance."""
        ts = datetime.now(UTC)
        err = FulmenError(code="TEST", message="Test", timestamp=ts)

        assert validate(err) is True

    def test_validate_fulmen_error_with_all_fields(self):
        """Test validating FulmenError with all fields."""
        ts = datetime.now(UTC)
        err = FulmenError(
            code="PATH_TRAVERSAL",
            message="Invalid path",
            timestamp=ts,
            severity="high",
            correlation_id="req-123",
            context={"path": "/etc/passwd"},
        )

        assert validate(err) is True

    def test_validate_dict_payload(self):
        """Test validating dict payload."""
        payload = {
            "code": "TEST_ERROR",
            "message": "Test message",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        assert validate(payload) is True

    def test_validate_minimal_dict(self):
        """Test validating minimal dict with required fields only."""
        payload = {"code": "TEST", "message": "Test"}

        assert validate(payload) is True

    def test_validate_dict_with_telemetry_fields(self):
        """Test validating dict with all telemetry fields."""
        payload = {
            "code": "ERROR",
            "message": "Error message",
            "severity": "critical",
            "severity_level": 4,
            "correlation_id": "req-abc",
            "trace_id": "trace-xyz",
            "exit_code": 1,
            "context": {"key": "value"},
            "original": "Exception traceback",
        }

        assert validate(payload) is True

    def test_validate_fallback_when_schema_unavailable(self):
        """Test validate() falls back to basic validation when schema module unavailable."""
        import sys

        payload = {"code": "TEST", "message": "Test"}

        with patch.dict(sys.modules, {"pyfulmen.schema": None}):
            result = validate(payload)

        assert result is True

    def test_validate_fallback_with_invalid_payload(self):
        """Test validate() fallback rejects invalid payload."""
        import sys

        payload = {"code": "TEST"}

        with patch.dict(sys.modules, {"pyfulmen.schema": None}):
            result = validate(payload)

        assert result is False


class TestBasicValidate:
    """Tests for _basic_validate fallback."""

    def test_basic_validate_with_required_fields(self):
        """Test basic validation with code and message."""
        payload = {"code": "TEST", "message": "Test"}

        assert _basic_validate(payload) is True

    def test_basic_validate_with_extra_fields(self):
        """Test basic validation ignores extra fields."""
        payload = {
            "code": "TEST",
            "message": "Test",
            "severity": "high",
            "extra_field": "ignored",
        }

        assert _basic_validate(payload) is True

    def test_basic_validate_missing_code(self):
        """Test basic validation fails without code."""
        payload = {"message": "Test"}

        assert _basic_validate(payload) is False

    def test_basic_validate_missing_message(self):
        """Test basic validation fails without message."""
        payload = {"code": "TEST"}

        assert _basic_validate(payload) is False

    def test_basic_validate_empty_code(self):
        """Test basic validation fails with empty code."""
        payload = {"code": "", "message": "Test"}

        assert _basic_validate(payload) is False

    def test_basic_validate_empty_message(self):
        """Test basic validation fails with empty message."""
        payload = {"code": "TEST", "message": ""}

        assert _basic_validate(payload) is False

    def test_basic_validate_none_code(self):
        """Test basic validation fails with None code."""
        payload = {"code": None, "message": "Test"}

        assert _basic_validate(payload) is False

    def test_basic_validate_none_message(self):
        """Test basic validation fails with None message."""
        payload = {"code": "TEST", "message": None}

        assert _basic_validate(payload) is False

    def test_basic_validate_empty_payload(self):
        """Test basic validation fails with empty dict."""
        payload = {}

        assert _basic_validate(payload) is False
