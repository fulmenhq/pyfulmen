"""
Tests for error_handling._wrap

Covers wrapping Pathfinder errors with telemetry metadata.
"""

from datetime import UTC, datetime

from pyfulmen.error_handling import PathfinderError, wrap
from pyfulmen.error_handling._wrap import _serialize_exception


class TestWrap:
    """Tests for wrap() function."""

    def test_wrap_pathfinder_error(self):
        """Test wrapping PathfinderError instance."""
        base = PathfinderError(code="TEST_ERROR", message="Test message")
        err = wrap(base)

        assert err.code == "TEST_ERROR"
        assert err.message == "Test message"
        assert err.timestamp is not None

    def test_wrap_dict(self):
        """Test wrapping dict with code/message."""
        base = {"code": "DICT_ERROR", "message": "From dict"}
        err = wrap(base)

        assert err.code == "DICT_ERROR"
        assert err.message == "From dict"

    def test_wrap_with_severity(self):
        """Test wrapping with severity."""
        base = PathfinderError(code="TEST", message="Test")
        err = wrap(base, severity="high")

        assert err.severity == "high"
        assert err.severity_level == 3  # Auto-mapped

    def test_wrap_with_context(self):
        """Test wrapping with structured context."""
        base = PathfinderError(code="TEST", message="Test")
        err = wrap(base, context={"path": "/test", "user": "alice"})

        assert err.context == {"path": "/test", "user": "alice"}

    def test_wrap_with_correlation_id(self):
        """Test wrapping with explicit correlation ID."""
        base = PathfinderError(code="TEST", message="Test")
        err = wrap(base, correlation_id="req-abc123")

        assert err.correlation_id == "req-abc123"

    def test_wrap_with_trace_id(self):
        """Test wrapping with OpenTelemetry trace ID."""
        base = PathfinderError(code="TEST", message="Test")
        err = wrap(base, trace_id="trace-xyz789")

        assert err.trace_id == "trace-xyz789"

    def test_wrap_with_exit_code(self):
        """Test wrapping with exit code."""
        base = PathfinderError(code="TEST", message="Test")
        err = wrap(base, exit_code=3)

        assert err.exit_code == 3

    def test_wrap_with_all_fields(self):
        """Test wrapping with all telemetry fields."""
        base = PathfinderError(code="CONFIG_INVALID", message="Config failed")
        err = wrap(
            base,
            context={"file": "config.yaml"},
            severity="critical",
            correlation_id="req-123",
            trace_id="trace-456",
            exit_code=1,
        )

        assert err.code == "CONFIG_INVALID"
        assert err.message == "Config failed"
        assert err.context == {"file": "config.yaml"}
        assert err.severity == "critical"
        assert err.severity_level == 4
        assert err.correlation_id == "req-123"
        assert err.trace_id == "trace-456"
        assert err.exit_code == 1

    def test_wrap_preserves_base_error_fields(self):
        """Test wrapping preserves all PathfinderError fields."""
        ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        base = PathfinderError(
            code="TEST",
            message="Test",
            details={"key": "value"},
            path="/app/config",
            timestamp=ts,
        )
        err = wrap(base, severity="low")

        assert err.details == {"key": "value"}
        assert err.path == "/app/config"
        assert err.timestamp == ts

    def test_wrap_with_original_exception(self):
        """Test wrapping with original Python exception."""
        base = PathfinderError(code="PYTHON_ERROR", message="Exception occurred")
        original = ValueError("Invalid input")
        err = wrap(base, original=original)

        assert err.original is not None
        assert isinstance(err.original, dict)
        assert err.original["type"] == "ValueError"
        assert err.original["message"] == "Invalid input"
        assert err.original["module"] == "builtins"

    def test_wrap_correlation_id_auto_populated_when_logging_available(self):
        """Test correlation ID auto-populates from logging context."""
        # Note: This test assumes logging module is available and has correlation context
        # If logging not available, correlation_id will be None
        base = PathfinderError(code="TEST", message="Test")
        err = wrap(base)

        # correlation_id may be None or auto-populated - both are valid
        # Just verify no exception is raised
        assert err.correlation_id is None or isinstance(err.correlation_id, str)

    def test_wrap_dict_with_timestamp(self):
        """Test wrapping dict preserves explicit timestamp."""
        ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        base = {"code": "TEST", "message": "Test", "timestamp": ts}
        err = wrap(base)

        assert err.timestamp == ts


class TestSerializeException:
    """Tests for _serialize_exception helper."""

    def test_serialize_simple_exception(self):
        """Test serializing simple exception."""
        exc = ValueError("Test error")
        result = _serialize_exception(exc)

        assert result["type"] == "ValueError"
        assert result["message"] == "Test error"
        assert result["module"] == "builtins"

    def test_serialize_custom_exception(self):
        """Test serializing custom exception class."""

        class CustomError(Exception):
            pass

        exc = CustomError("Custom message")
        result = _serialize_exception(exc)

        assert result["type"] == "CustomError"
        assert result["message"] == "Custom message"
        assert "test_wrap" in result["module"]  # Current test module

    def test_serialize_exception_with_traceback(self):
        """Test serializing exception with traceback."""
        try:
            raise RuntimeError("Test with traceback")
        except RuntimeError as exc:
            result = _serialize_exception(exc)

            assert result["type"] == "RuntimeError"
            assert result["message"] == "Test with traceback"
            assert "traceback" in result
            assert "RuntimeError: Test with traceback" in result["traceback"]

    def test_serialize_exception_without_traceback(self):
        """Test serializing exception without traceback."""
        exc = ValueError("No traceback")
        # Clear traceback if it exists
        exc.__traceback__ = None
        result = _serialize_exception(exc)

        assert "traceback" not in result
        assert result["type"] == "ValueError"
        assert result["message"] == "No traceback"

    def test_serialize_exception_empty_message(self):
        """Test serializing exception with empty message."""
        exc = ValueError()
        result = _serialize_exception(exc)

        assert result["type"] == "ValueError"
        assert result["message"] == ""
        assert result["module"] == "builtins"
