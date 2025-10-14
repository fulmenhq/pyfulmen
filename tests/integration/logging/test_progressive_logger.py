"""Integration tests for progressive logging profiles end-to-end."""

import io
import json
from contextlib import redirect_stderr

from pyfulmen.logging import Logger, LoggingProfile


class TestSimpleProfileIntegration:
    """Integration tests for SIMPLE profile end-to-end."""

    def test_simple_profile_console_output(self):
        """Test SIMPLE profile logs to console with text format."""
        stderr = io.StringIO()
        logger = Logger(service="test-app", profile=LoggingProfile.SIMPLE)

        with redirect_stderr(stderr):
            logger.info("Starting application")
            logger.warn("Configuration incomplete", component="config")
            logger.error("Failed to connect", context={"host": "db.local"})

        output = stderr.getvalue()
        assert "Starting application" in output
        assert "Configuration incomplete" in output
        assert "Failed to connect" in output
        assert "test-app" in output

    def test_simple_profile_no_json_structure(self):
        """Test SIMPLE profile output is human-readable, not JSON."""
        stderr = io.StringIO()
        logger = Logger(service="test-app", profile=LoggingProfile.SIMPLE)

        with redirect_stderr(stderr):
            logger.info("Test message")

        output = stderr.getvalue()
        # Should not be JSON
        assert not output.strip().startswith("{")

    def test_simple_profile_level_filtering(self):
        """Test SIMPLE profile filters logs below threshold."""
        stderr = io.StringIO()
        logger = Logger(
            service="test-app",
            profile=LoggingProfile.SIMPLE,
            default_level="WARN",
        )

        with redirect_stderr(stderr):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warn("Warning message")

        output = stderr.getvalue()
        assert "Debug message" not in output
        assert "Info message" not in output
        assert "Warning message" in output


class TestStructuredProfileIntegration:
    """Integration tests for STRUCTURED profile end-to-end."""

    def test_structured_profile_json_output(self):
        """Test STRUCTURED profile outputs structured JSON."""
        stderr = io.StringIO()
        logger = Logger(profile=LoggingProfile.STRUCTURED, service="api-service")

        with redirect_stderr(stderr):
            logger.info("Request received", context={"path": "/api/users", "method": "GET"})

        output = stderr.getvalue().strip()
        log_event = json.loads(output)

        assert log_event["message"] == "Request received"
        assert log_event["severity"] == "INFO"
        assert log_event["service"] == "api-service"
        assert "context" in log_event
        assert log_event["context"]["path"] == "/api/users"
        assert log_event["context"]["method"] == "GET"

    def test_structured_profile_timestamp_format(self):
        """Test STRUCTURED profile includes RFC3339 timestamps."""
        stderr = io.StringIO()
        logger = Logger(profile=LoggingProfile.STRUCTURED, service="api-service")

        with redirect_stderr(stderr):
            logger.info("Test event")

        output = stderr.getvalue().strip()
        log_event = json.loads(output)

        assert "timestamp" in log_event
        # RFC3339 format check
        assert "T" in log_event["timestamp"]
        assert "Z" in log_event["timestamp"] or "+" in log_event["timestamp"]

    def test_structured_profile_severity_level(self):
        """Test STRUCTURED profile includes severityLevel."""
        stderr = io.StringIO()
        logger = Logger(profile=LoggingProfile.STRUCTURED, service="api-service")

        with redirect_stderr(stderr):
            logger.info("Info event")
            logger.error("Error event")

        output = stderr.getvalue().strip().split("\n")
        info_event = json.loads(output[0])
        error_event = json.loads(output[1])

        assert info_event["severityLevel"] == 20
        assert error_event["severityLevel"] == 40


class TestEnterpriseProfileIntegration:
    """Integration tests for ENTERPRISE profile end-to-end."""

    def test_enterprise_profile_full_envelope(self):
        """Test ENTERPRISE profile includes all required fields."""
        stderr = io.StringIO()
        logger = Logger(
            profile=LoggingProfile.ENTERPRISE,
            service="payment-service",
            environment="production",
        )

        with redirect_stderr(stderr):
            logger.info("Payment processed", context={"amount": 100.00, "currency": "USD"})

        output = stderr.getvalue().strip()
        log_event = json.loads(output)

        # Required Crucible fields
        assert "timestamp" in log_event
        assert "severity" in log_event
        assert "severityLevel" in log_event
        assert "message" in log_event
        assert "service" in log_event
        assert "environment" in log_event
        assert "context" in log_event

        assert log_event["service"] == "payment-service"
        assert log_event["environment"] == "production"

    def test_enterprise_profile_correlation_middleware(self):
        """Test ENTERPRISE profile includes correlation ID from middleware."""
        stderr = io.StringIO()
        logger = Logger(
            profile=LoggingProfile.ENTERPRISE,
            service="order-service",
        )

        with redirect_stderr(stderr):
            logger.info("Order created")

        output = stderr.getvalue().strip()
        log_event = json.loads(output)

        # Correlation middleware should add correlationId
        assert "correlationId" in log_event
        assert log_event["correlationId"] is not None

    def test_enterprise_profile_multiple_middleware(self):
        """Test ENTERPRISE profile with multiple middleware in pipeline."""
        stderr = io.StringIO()
        logger = Logger(
            profile=LoggingProfile.ENTERPRISE,
            service="secure-service",
            middleware=["correlation", "redact-secrets"],
        )

        with redirect_stderr(stderr):
            logger.info("User authenticated", context={"user": "alice", "api_key": "sk_live_12345"})

        output = stderr.getvalue().strip()
        log_event = json.loads(output)

        # Should have correlation ID
        assert "correlationId" in log_event

        # API key should be redacted
        assert "REDACTED" in str(log_event["context"])
        assert "sk_live_12345" not in str(log_event["context"])


class TestCustomProfileIntegration:
    """Integration tests for CUSTOM profile end-to-end."""

    def test_custom_profile_with_multiple_sinks(self):
        """Test CUSTOM profile with multiple configured sinks."""
        stderr = io.StringIO()
        logger = Logger(
            profile=LoggingProfile.CUSTOM,
            service="custom-app",
            sinks=[
                {"type": "console", "format": "json"},
            ],
        )

        with redirect_stderr(stderr):
            logger.info("Custom event")

        output = stderr.getvalue().strip()
        log_event = json.loads(output)

        assert log_event["message"] == "Custom event"
        assert log_event["service"] == "custom-app"

    def test_custom_profile_custom_middleware(self):
        """Test CUSTOM profile with custom middleware configuration."""
        stderr = io.StringIO()
        logger = Logger(
            profile=LoggingProfile.CUSTOM,
            service="custom-app",
            sinks=[{"type": "console", "format": "json"}],
            middleware=["correlation"],
        )

        with redirect_stderr(stderr):
            logger.info("Custom event with middleware")

        output = stderr.getvalue().strip()
        log_event = json.loads(output)

        assert "correlationId" in log_event


class TestProfileComparison:
    """Test differences between profiles in same scenarios."""

    def test_same_log_different_profiles(self):
        """Test same log message across different profiles."""
        message = "Application started"
        context = {"version": "1.0.0"}

        # SIMPLE profile
        simple_stderr = io.StringIO()
        simple_logger = Logger(profile=LoggingProfile.SIMPLE, service="app")
        with redirect_stderr(simple_stderr):
            simple_logger.info(message, context=context)
        simple_output = simple_stderr.getvalue()

        # STRUCTURED profile
        structured_stderr = io.StringIO()
        structured_logger = Logger(profile=LoggingProfile.STRUCTURED, service="app")
        with redirect_stderr(structured_stderr):
            structured_logger.info(message, context=context)
        structured_output = structured_stderr.getvalue()

        # ENTERPRISE profile
        enterprise_stderr = io.StringIO()
        enterprise_logger = Logger(profile=LoggingProfile.ENTERPRISE, service="app")
        with redirect_stderr(enterprise_stderr):
            enterprise_logger.info(message, context=context)
        enterprise_output = enterprise_stderr.getvalue()

        # SIMPLE should be text
        assert not simple_output.strip().startswith("{")

        # STRUCTURED and ENTERPRISE should be JSON
        structured_event = json.loads(structured_output.strip())
        enterprise_event = json.loads(enterprise_output.strip())

        assert structured_event["message"] == message
        assert enterprise_event["message"] == message

        # ENTERPRISE should have correlation ID, STRUCTURED might not
        assert "correlationId" in enterprise_event


class TestErrorScenarios:
    """Test error handling and edge cases."""

    def test_logger_handles_large_context(self):
        """Test logger handles large context objects."""
        stderr = io.StringIO()
        logger = Logger(profile=LoggingProfile.STRUCTURED, service="test-app")

        large_context = {f"key_{i}": f"value_{i}" for i in range(1000)}

        with redirect_stderr(stderr):
            logger.info("Event with large context", context=large_context)

        output = stderr.getvalue().strip()
        log_event = json.loads(output)

        assert len(log_event["context"]) == 1000

    def test_logger_handles_nested_context(self):
        """Test logger handles deeply nested context."""
        stderr = io.StringIO()
        logger = Logger(profile=LoggingProfile.STRUCTURED, service="test-app")

        nested_context = {"level1": {"level2": {"level3": {"data": "value"}}}}

        with redirect_stderr(stderr):
            logger.info("Nested event", context=nested_context)

        output = stderr.getvalue().strip()
        log_event = json.loads(output)

        assert log_event["context"]["level1"]["level2"]["level3"]["data"] == "value"

    def test_logger_handles_special_characters(self):
        """Test logger handles special characters in messages."""
        stderr = io.StringIO()
        logger = Logger(profile=LoggingProfile.STRUCTURED, service="test-app")

        special_message = 'Message with "quotes", newlines\n, and unicode: 你好'

        with redirect_stderr(stderr):
            logger.info(special_message)

        output = stderr.getvalue().strip()
        log_event = json.loads(output)

        assert log_event["message"] == special_message
