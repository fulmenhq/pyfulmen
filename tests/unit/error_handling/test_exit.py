"""Tests for error exit utilities."""

import contextlib
from datetime import UTC, datetime

import pytest

from pyfulmen.error_handling._exit import exit_with_error
from pyfulmen.error_handling.models import FulmenError


class TestExitWithError:
    """Test exit_with_error function."""

    def test_exit_with_logger(self) -> None:
        """Test exit with provided logger."""
        error = FulmenError(
            code="TEST_ERROR",
            message="Test error",
            timestamp=datetime.now(UTC),
            severity="medium",
        )

        # Mock logger
        class MockLogger:
            def __init__(self, service: str):
                self.service = service
                self.calls = []

            def info(self, msg, context=None, **kwargs):
                self.calls.append(("info", msg, context or {}))

            def warn(self, msg, context=None, **kwargs):
                self.calls.append(("warn", msg, context or {}))

            def error(self, msg, context=None, **kwargs):
                self.calls.append(("error", msg, context or {}))

            def fatal(self, msg, context=None, **kwargs):
                self.calls.append(("fatal", msg, context or {}))

        logger = MockLogger("test")

        # Should raise SystemExit
        with pytest.raises(SystemExit) as exc_info:
            exit_with_error(42, error, logger=logger)

        # Check exit code
        assert exc_info.value.code == 42

        # Check logger was called correctly
        assert len(logger.calls) == 1
        level, msg, ctx = logger.calls[0]
        assert level == "error"  # medium severity maps to error
        assert msg == "Test error"
        assert ctx["code"] == "TEST_ERROR"
        assert ctx["exit_code"] == 42

    def test_exit_without_logger(self) -> None:
        """Test exit without provided logger (creates default)."""
        error = FulmenError(
            code="NO_LOGGER",
            message="No logger test",
            timestamp=datetime.now(UTC),
            severity="low",
        )

        # Should raise SystemExit even without logger
        with pytest.raises(SystemExit) as exc_info:
            exit_with_error(1, error)

        assert exc_info.value.code == 1

    def test_severity_mapping(self) -> None:
        """Test severity to logger method mapping."""

        class MockLogger:
            def __init__(self):
                self.method_calls = []

            def info(self, msg, context=None, **kwargs):
                self.method_calls.append("info")

            def warn(self, msg, context=None, **kwargs):
                self.method_calls.append("warn")

            def error(self, msg, context=None, **kwargs):
                self.method_calls.append("error")

            def fatal(self, msg, context=None, **kwargs):
                self.method_calls.append("fatal")

        logger = MockLogger()

        # Test each severity level
        severities = ["info", "low", "medium", "high", "critical"]
        expected_methods = ["info", "warn", "error", "error", "fatal"]

        for severity, expected_method in zip(severities, expected_methods, strict=False):
            error = FulmenError(
                code=f"TEST_{severity.upper()}",
                message=f"Test {severity}",
                timestamp=datetime.now(UTC),
                severity=severity,
            )

            logger.method_calls.clear()

            with contextlib.suppress(SystemExit):
                exit_with_error(0, error, logger=logger)

            assert logger.method_calls == [expected_method]

    def test_default_severity(self) -> None:
        """Test exit with no severity (defaults to error)."""
        error = FulmenError(
            code="NO_SEVERITY",
            message="No severity test",
            timestamp=datetime.now(UTC),
            # No severity specified
        )

        class MockLogger:
            def __init__(self):
                self.method_calls = []

            def info(self, msg, context=None, **kwargs):
                self.method_calls.append("info")

            def warn(self, msg, context=None, **kwargs):
                self.method_calls.append("warn")

            def error(self, msg, context=None, **kwargs):
                self.method_calls.append("error")

            def fatal(self, msg, context=None, **kwargs):
                self.method_calls.append("fatal")

        logger = MockLogger()

        with contextlib.suppress(SystemExit):
            exit_with_error(0, error, logger=logger)

        # Should default to error level
        assert logger.method_calls == ["error"]
