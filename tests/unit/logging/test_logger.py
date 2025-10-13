"""Tests for progressive logger with profile-based delegation."""

import json

import pytest

from pyfulmen.logging._models import LoggingConfig, LoggingPolicy, LoggingProfile
from pyfulmen.logging.logger import (
    EnterpriseLogger,
    Logger,
    SimpleLogger,
    StructuredLogger,
)
from pyfulmen.logging.severity import Severity


class TestSimpleLogger:
    """Tests for SimpleLogger profile."""

    def test_simple_logger_initialization(self):
        """Test SimpleLogger initializes with basic config."""
        config = LoggingConfig(
            profile=LoggingProfile.SIMPLE,
            service="test-service",
        )
        logger = SimpleLogger(config)

        assert logger.service == "test-service"
        assert logger.default_level == "INFO"

    def test_simple_logger_with_component(self):
        """Test SimpleLogger with component name."""
        config = LoggingConfig(
            profile=LoggingProfile.SIMPLE,
            service="test-service",
            component="auth",
        )
        logger = SimpleLogger(config)

        assert logger.component == "auth"

    def test_simple_logger_log_methods(self, caplog):
        """Test SimpleLogger log methods produce output."""
        config = LoggingConfig(
            profile=LoggingProfile.SIMPLE,
            service="test-service",
        )
        logger = SimpleLogger(config)

        logger.trace("Trace message")
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warn("Warn message")
        logger.error("Error message")
        logger.fatal("Fatal message")

        log_output = caplog.text.lower()
        assert "info message" in log_output
        assert "warn" in log_output or "warning" in log_output
        assert "error message" in log_output


class TestStructuredLogger:
    """Tests for StructuredLogger profile."""

    def test_structured_logger_initialization(self):
        """Test StructuredLogger initializes correctly."""
        config = LoggingConfig(
            profile=LoggingProfile.STRUCTURED,
            service="test-service",
            component="api",
        )
        logger = StructuredLogger(config)

        assert logger.service == "test-service"
        assert logger.component == "api"

    def test_structured_logger_json_output(self, capsys):
        """Test StructuredLogger emits valid JSON."""
        config = LoggingConfig(
            profile=LoggingProfile.STRUCTURED,
            service="test-service",
        )
        logger = StructuredLogger(config)

        logger.info("Test message")

        captured = capsys.readouterr()
        output_line = captured.out.strip()

        parsed = json.loads(output_line)

        assert parsed["severity"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["service"] == "test-service"
        assert "timestamp" in parsed
        assert "correlation_id" in parsed

    def test_structured_logger_with_context(self, capsys):
        """Test StructuredLogger includes context fields."""
        config = LoggingConfig(
            profile=LoggingProfile.STRUCTURED,
            service="test-service",
        )
        logger = StructuredLogger(config)

        logger.info(
            "Request received",
            request_id="req-123",
            user_id="user-456",
            context={"method": "GET", "path": "/api/users"},
        )

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())

        assert parsed["request_id"] == "req-123"
        assert parsed["user_id"] == "user-456"
        assert parsed["context"]["method"] == "GET"

    def test_structured_logger_all_severity_levels(self, capsys):
        """Test StructuredLogger handles all severity levels."""
        config = LoggingConfig(
            profile=LoggingProfile.STRUCTURED,
            service="test-service",
        )
        logger = StructuredLogger(config)

        logger.trace("Trace")
        logger.debug("Debug")
        logger.info("Info")
        logger.warn("Warn")
        logger.error("Error")
        logger.fatal("Fatal")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        assert len(lines) == 6

        severities = [json.loads(line)["severity"] for line in lines]
        assert severities == ["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"]


class TestEnterpriseLogger:
    """Tests for EnterpriseLogger profile."""

    def test_enterprise_logger_initialization(self):
        """Test EnterpriseLogger initializes correctly."""
        config = LoggingConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
        )
        logger = EnterpriseLogger(config)

        assert logger.service == "test-service"

    def test_enterprise_logger_full_envelope(self, capsys):
        """Test EnterpriseLogger emits full LogEvent envelope."""
        config = LoggingConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
            component="payment-processor",
        )
        logger = EnterpriseLogger(config)

        logger.info(
            "Transaction completed",
            user_id="user-789",
            operation="charge",
            duration_ms=152.3,
            trace_id="trace-abc",
            span_id="span-def",
            tags=["payment", "success"],
        )

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())

        assert parsed["severity"] == "INFO"
        assert parsed["message"] == "Transaction completed"
        assert parsed["service"] == "test-service"
        assert parsed["component"] == "payment-processor"
        assert parsed["user_id"] == "user-789"
        assert parsed["operation"] == "charge"
        assert parsed["duration_ms"] == 152.3
        assert parsed["trace_id"] == "trace-abc"
        assert parsed["span_id"] == "span-def"
        assert parsed["tags"] == ["payment", "success"]
        assert "timestamp" in parsed
        assert "correlation_id" in parsed
        assert "severity_level" in parsed
        assert parsed["severity_level"] == 20

    def test_enterprise_logger_with_error_details(self, capsys):
        """Test EnterpriseLogger includes error details."""
        config = LoggingConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
        )
        logger = EnterpriseLogger(config)

        logger.error(
            "Database connection failed",
            error={
                "message": "Connection timeout",
                "type": "TimeoutError",
                "stack": "at connect() line 42",
            },
        )

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())

        assert parsed["severity"] == "ERROR"
        assert parsed["error"]["message"] == "Connection timeout"
        assert parsed["error"]["type"] == "TimeoutError"

    def test_enterprise_logger_policy_enforcement_allowed(self):
        """Test EnterpriseLogger accepts valid policy."""
        config = LoggingConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
        )
        policy = LoggingPolicy(
            allowed_profiles=["ENTERPRISE", "STRUCTURED"],
        )

        logger = EnterpriseLogger(config, policy)

        assert logger.policy == policy

    def test_enterprise_logger_policy_enforcement_denied(self):
        """Test EnterpriseLogger rejects invalid profile."""
        config = LoggingConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
        )
        policy = LoggingPolicy(
            allowed_profiles=["SIMPLE"],
        )

        with pytest.raises(ValueError, match="not allowed by policy"):
            EnterpriseLogger(config, policy)


class TestLogger:
    """Tests for unified Logger interface."""

    def test_logger_default_profile(self):
        """Test Logger defaults to SIMPLE profile."""
        logger = Logger(service="test-service")

        assert logger.config.profile == LoggingProfile.SIMPLE
        assert isinstance(logger._impl, SimpleLogger)

    def test_logger_simple_profile(self, caplog):
        """Test Logger with SIMPLE profile."""
        logger = Logger(service="test-service", profile=LoggingProfile.SIMPLE)

        logger.info("Simple log")

        assert "simple log" in caplog.text.lower()

    def test_logger_structured_profile(self, capsys):
        """Test Logger with STRUCTURED profile."""
        logger = Logger(service="test-service", profile=LoggingProfile.STRUCTURED)

        logger.info("Structured log", request_id="req-123")

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())

        assert parsed["severity"] == "INFO"
        assert parsed["message"] == "Structured log"
        assert parsed["request_id"] == "req-123"

    def test_logger_enterprise_profile(self, capsys):
        """Test Logger with ENTERPRISE profile."""
        logger = Logger(service="test-service", profile=LoggingProfile.ENTERPRISE)

        logger.info("Enterprise log", user_id="user-123", operation="login")

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())

        assert parsed["severity"] == "INFO"
        assert parsed["user_id"] == "user-123"
        assert parsed["operation"] == "login"
        assert "severity_level" in parsed

    def test_logger_with_component(self, capsys):
        """Test Logger with component identification."""
        logger = Logger(
            service="test-service",
            component="auth-handler",
            profile=LoggingProfile.STRUCTURED,
        )

        logger.info("Auth event")

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())

        assert parsed["component"] == "auth-handler"

    def test_logger_with_custom_level(self, capsys):
        """Test Logger with custom default level."""
        logger = Logger(
            service="test-service",
            profile=LoggingProfile.STRUCTURED,
            default_level="DEBUG",
        )

        logger.debug("Debug message")

        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())

        assert parsed["severity"] == "DEBUG"

    def test_logger_invalid_profile(self):
        """Test Logger rejects invalid profile."""
        with pytest.raises(ValueError, match="Invalid profile"):
            Logger(service="test-service", profile="INVALID")

    def test_logger_custom_profile_not_implemented(self):
        """Test Logger rejects CUSTOM profile (not yet implemented)."""
        with pytest.raises(ValueError, match="CUSTOM profile not yet implemented"):
            Logger(service="test-service", profile=LoggingProfile.CUSTOM)

    def test_logger_with_prebuilt_config(self, capsys):
        """Test Logger with pre-built LoggingConfig."""
        config = LoggingConfig(
            profile=LoggingProfile.STRUCTURED,
            service="test-service",
            component="worker",
            default_level="WARN",
        )

        logger = Logger(service="ignored", config=config)

        assert logger.config.service == "test-service"
        assert logger.config.component == "worker"
        assert logger.config.default_level == "WARN"

    def test_logger_all_log_methods(self, capsys):
        """Test all Logger log methods."""
        logger = Logger(service="test-service", profile=LoggingProfile.STRUCTURED)

        logger.trace("Trace")
        logger.debug("Debug")
        logger.info("Info")
        logger.warn("Warn")
        logger.error("Error")
        logger.fatal("Fatal")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        assert len(lines) == 6

        messages = [json.loads(line)["message"] for line in lines]
        assert messages == ["Trace", "Debug", "Info", "Warn", "Error", "Fatal"]

    def test_logger_generic_log_method(self, capsys):
        """Test Logger.log() method with explicit severity."""
        logger = Logger(service="test-service", profile=LoggingProfile.STRUCTURED)

        logger.log(Severity.WARN, "Warning via log()")
        logger.log("ERROR", "Error via log() with string")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        parsed1 = json.loads(lines[0])
        parsed2 = json.loads(lines[1])

        assert parsed1["severity"] == "WARN"
        assert parsed2["severity"] == "ERROR"


class TestLoggerPolicyEnforcement:
    """Tests for policy enforcement in Logger."""

    def test_logger_policy_file_placeholder(self):
        """Test Logger with policy_file parameter (placeholder implementation)."""
        logger = Logger(
            service="test-service",
            profile=LoggingProfile.ENTERPRISE,
            policy_file="config/logging-policy.yaml",
        )

        assert logger.policy is not None
        assert isinstance(logger.policy, LoggingPolicy)

    def test_logger_policy_validation_passes(self):
        """Test Logger policy validation allows permitted profiles."""
        policy = LoggingPolicy(
            allowed_profiles=["SIMPLE", "STRUCTURED", "ENTERPRISE"],
        )

        logger = Logger(
            service="test-service",
            profile=LoggingProfile.STRUCTURED,
        )
        logger.policy = policy
        logger._validate_profile()

    def test_logger_policy_validation_fails(self):
        """Test Logger policy validation rejects forbidden profiles."""
        logger = Logger(
            service="test-service",
            profile=LoggingProfile.SIMPLE,
        )
        logger.policy = LoggingPolicy(allowed_profiles=["ENTERPRISE"])

        with pytest.raises(ValueError, match="not allowed by policy"):
            logger._validate_profile()


class TestLoggerProfileComparison:
    """Comparative tests across logger profiles."""

    def test_same_message_different_profiles(self, capsys, caplog):
        """Test same message logged across all profiles."""
        message = "Test event"
        request_id = "req-xyz"

        simple_logger = Logger(service="svc", profile=LoggingProfile.SIMPLE)
        simple_logger.info(message, request_id=request_id)

        structured_logger = Logger(service="svc", profile=LoggingProfile.STRUCTURED)
        structured_logger.info(message, request_id=request_id)

        enterprise_logger = Logger(service="svc", profile=LoggingProfile.ENTERPRISE)
        enterprise_logger.info(message, request_id=request_id)

        captured = capsys.readouterr()
        json_lines = [line for line in captured.out.strip().split("\n") if line.startswith("{")]

        assert len(json_lines) == 2

        structured_event = json.loads(json_lines[0])
        enterprise_event = json.loads(json_lines[1])

        assert structured_event["message"] == message
        assert structured_event["request_id"] == request_id
        assert "severity_level" not in structured_event

        assert enterprise_event["message"] == message
        assert enterprise_event["request_id"] == request_id
        assert "severity_level" in enterprise_event

    def test_field_availability_by_profile(self, capsys):
        """Test which fields are available in each profile."""
        structured_logger = Logger(service="svc", profile=LoggingProfile.STRUCTURED)
        structured_logger.info(
            "msg",
            request_id="req-1",
            throttle_bucket="bucket-1",
        )

        enterprise_logger = Logger(service="svc", profile=LoggingProfile.ENTERPRISE)
        enterprise_logger.info(
            "msg",
            request_id="req-2",
            throttle_bucket="bucket-2",
        )

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        structured_event = json.loads(lines[0])
        enterprise_event = json.loads(lines[1])

        assert structured_event["request_id"] == "req-1"
        assert "throttle_bucket" not in structured_event

        assert enterprise_event["request_id"] == "req-2"
        assert enterprise_event["throttle_bucket"] == "bucket-2"
