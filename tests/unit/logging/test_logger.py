"""Tests for progressive logger with profile-based configuration."""

import json

import pytest

from pyfulmen.logging._models import LoggingConfig, LoggingPolicy, LoggingProfile
from pyfulmen.logging.logger import Logger, ProgressiveLogger
from pyfulmen.logging.severity import Severity
from pyfulmen.logging.throttling import ThrottlingMiddleware


class TestProgressiveLogger:
    """Tests for ProgressiveLogger across all profiles."""

    def test_simple_profile_initialization(self):
        """Test SIMPLE profile initializes correctly."""
        config = LoggingConfig(
            profile=LoggingProfile.SIMPLE,
            service="test-service",
        )
        logger = ProgressiveLogger(config)

        assert logger.service == "test-service"
        assert logger.default_level == "INFO"
        assert len(logger.sinks) == 1

    def test_simple_profile_text_output(self, capsys):
        """SIMPLE profile emits human-readable text."""
        logger = Logger(service="test", profile=LoggingProfile.SIMPLE)
        logger.info("Test message")

        captured = capsys.readouterr()
        assert "INFO" in captured.err
        assert "Test message" in captured.err

    def test_structured_profile_initialization(self):
        """Test STRUCTURED profile initializes correctly."""
        config = LoggingConfig(
            profile=LoggingProfile.STRUCTURED,
            service="test-service",
            component="api",
        )
        logger = ProgressiveLogger(config)

        assert logger.service == "test-service"
        assert logger.component == "api"

    def test_structured_profile_json_output(self, capsys):
        """STRUCTURED profile emits JSON."""
        logger = Logger(service="test", profile=LoggingProfile.STRUCTURED)
        logger.info("Test message")

        captured = capsys.readouterr()
        log_line = json.loads(captured.err.strip())
        assert log_line["severity"] == "INFO"
        assert log_line["message"] == "Test message"
        assert "severityLevel" in log_line

    def test_enterprise_profile_initialization(self):
        """Test ENTERPRISE profile initializes correctly."""
        config = LoggingConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
            component="payment-processor",
        )
        logger = ProgressiveLogger(config)

        assert logger.service == "test-service"
        assert logger.component == "payment-processor"

    def test_enterprise_profile_full_envelope(self, capsys):
        """Test ENTERPRISE profile emits full LogEvent envelope."""
        logger = Logger(
            service="test-service", profile=LoggingProfile.ENTERPRISE, component="payment-processor"
        )

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
        parsed = json.loads(captured.err.strip())

        assert parsed["severity"] == "INFO"
        assert parsed["message"] == "Transaction completed"
        assert parsed["service"] == "test-service"
        assert parsed["component"] == "payment-processor"
        assert parsed["userId"] == "user-789"
        assert parsed["operation"] == "charge"
        assert parsed["durationMs"] == 152.3
        assert parsed["traceId"] == "trace-abc"
        assert parsed["spanId"] == "span-def"
        assert parsed["tags"] == ["payment", "success"]
        assert "timestamp" in parsed
        assert "correlationId" in parsed
        assert "severityLevel" in parsed
        assert parsed["severityLevel"] == 20

    def test_custom_profile_with_sinks(self):
        """Test CUSTOM profile requires sinks configuration."""
        config = LoggingConfig(
            profile=LoggingProfile.CUSTOM,
            service="test-service",
            sinks=[{"type": "console", "formatter": "json"}],
        )
        logger = ProgressiveLogger(config)

        assert len(logger.sinks) == 1

    def test_custom_profile_without_sinks_fails(self):
        """Test CUSTOM profile fails without sinks configuration."""
        config = LoggingConfig(
            profile=LoggingProfile.CUSTOM,
            service="test-service",
        )

        with pytest.raises(ValueError, match="CUSTOM profile requires sinks configuration"):
            ProgressiveLogger(config)

    def test_all_severity_levels(self, capsys):
        """Test all severity levels work correctly."""
        logger = Logger(
            service="test-service",
            profile=LoggingProfile.STRUCTURED,
            default_level="TRACE",
        )

        logger.trace("Trace")
        logger.debug("Debug")
        logger.info("Info")
        logger.warn("Warn")
        logger.error("Error")
        logger.fatal("Fatal")

        captured = capsys.readouterr()
        lines = captured.err.strip().split("\n")

        assert len(lines) == 6

        severities = [json.loads(line)["severity"] for line in lines]
        assert severities == ["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL"]

    def test_level_filtering(self, capsys):
        """Test level filtering works correctly."""
        logger = Logger(
            service="test-service",
            profile=LoggingProfile.STRUCTURED,
            default_level="WARN",
        )

        logger.debug("Debug message")  # Should be filtered out
        logger.info("Info message")  # Should be filtered out
        logger.warn("Warn message")  # Should be logged
        logger.error("Error message")  # Should be logged

        captured = capsys.readouterr()
        lines = captured.err.strip().split("\n")

        assert len(lines) == 2

        severities = [json.loads(line)["severity"] for line in lines]
        assert severities == ["WARN", "ERROR"]

    def test_context_merging(self, capsys):
        """Test context merging works correctly."""
        logger = Logger(service="test", profile=LoggingProfile.STRUCTURED)

        logger.info(
            "Request received",
            request_id="req-123",
            user_id="user-456",
            context={"method": "GET", "path": "/api/users"},
        )

        captured = capsys.readouterr()
        parsed = json.loads(captured.err.strip())

        assert parsed["requestId"] == "req-123"
        assert parsed["userId"] == "user-456"
        assert parsed["context"]["method"] == "GET"
        assert parsed["context"]["path"] == "/api/users"

    def test_set_level(self):
        """Test dynamic level changing."""
        logger = Logger(service="test", default_level="INFO")

        assert logger._min_level == 20  # INFO level

        logger.set_level("DEBUG")
        assert logger._min_level == 10  # DEBUG level

        logger.set_level(Severity.ERROR)
        assert logger._min_level == 40  # ERROR level

    def test_resource_management_flush(self):
        """Test flush() flushes all sinks."""
        logger = Logger(service="test")
        logger.info("Message 1")
        logger.flush()  # Should not raise

    def test_resource_management_close(self):
        """Test close() closes all sinks."""
        logger = Logger(service="test")
        logger.info("Message 1")
        logger.close()  # Should not raise

    def test_context_manager(self, capsys):
        """Test logger works as context manager."""
        with Logger(service="test") as log:
            log.info("Inside context")

        captured = capsys.readouterr()
        assert "Inside context" in captured.err

    def test_custom_sinks_configuration(self, capsys):
        """Test custom sinks configuration."""
        logger = Logger(
            service="test",
            profile=LoggingProfile.STRUCTURED,
            sinks=[
                {"type": "console", "formatter": "text"},
                {"type": "console", "formatter": "json"},
            ],
        )

        logger.info("Test message")

        captured = capsys.readouterr()
        lines = captured.err.strip().split("\n")

        # Should have 2 lines (one from each sink)
        assert len(lines) == 2

        # First line should be text format
        assert "INFO" in lines[0]
        assert "Test message" in lines[0]

        # Second line should be JSON format
        json_line = json.loads(lines[1])
        assert json_line["severity"] == "INFO"
        assert json_line["message"] == "Test message"

    def test_middleware_config_unwrap_and_enabled(self):
        """Middleware config is unwrapped and enabled flag respected."""
        config = LoggingConfig(
            profile=LoggingProfile.STRUCTURED,
            service="svc",
            middleware=[
                {
                    "name": "throttling",
                    "order": 3,
                    "config": {
                        "maxRate": 1000,
                        "burstSize": 50,
                        "windowSize": 1.0,
                        "dropPolicy": "drop-newest",
                        "bucketId": "api",
                    },
                },
                {  # should be ignored entirely
                    "name": "redact-secrets",
                    "enabled": False,
                    "order": 1,
                    "config": {"dummy": True},
                },
            ],
        )
        logger = ProgressiveLogger(config)
        assert logger.middleware is not None
        chain = logger.middleware.middleware
        # Only throttling should be present
        assert len(chain) == 1
        m = chain[0]
        assert isinstance(m, ThrottlingMiddleware)
        # Order comes from outer key
        assert m.order == 3
        # Inner config flattened and camelCase consumed
        assert m.controller.max_rate == 1000
        assert m.controller.window_size == 1.0
        assert m.controller.drop_policy == "drop-newest"
        # 'order' is not forwarded inside config payload
        assert "order" not in m.config


class TestLogger:
    """Tests for unified Logger factory function."""

    def test_logger_default_profile(self):
        """Test Logger defaults to SIMPLE profile."""
        logger = Logger(service="test-service")

        assert logger.config.profile == LoggingProfile.SIMPLE
        assert isinstance(logger, ProgressiveLogger)

    def test_logger_simple_profile(self, capsys):
        """Test Logger with SIMPLE profile."""
        logger = Logger(service="test-service", profile=LoggingProfile.SIMPLE)

        logger.info("Simple log")

        captured = capsys.readouterr()
        assert "simple log" in captured.err.lower()

    def test_logger_structured_profile(self, capsys):
        """Test Logger with STRUCTURED profile."""
        logger = Logger(service="test-service", profile=LoggingProfile.STRUCTURED)

        logger.info("Structured log", request_id="req-123")

        captured = capsys.readouterr()
        parsed = json.loads(captured.err.strip())

        assert parsed["severity"] == "INFO"
        assert parsed["message"] == "Structured log"
        assert parsed["requestId"] == "req-123"

    def test_logger_enterprise_profile(self, capsys):
        """Test Logger with ENTERPRISE profile."""
        logger = Logger(service="test-service", profile=LoggingProfile.ENTERPRISE)

        logger.info("Enterprise log", user_id="user-123", operation="login")

        captured = capsys.readouterr()
        parsed = json.loads(captured.err.strip())

        assert parsed["severity"] == "INFO"
        assert parsed["userId"] == "user-123"
        assert parsed["operation"] == "login"
        assert "severityLevel" in parsed

    def test_logger_with_component(self, capsys):
        """Test Logger with component identification."""
        logger = Logger(
            service="test-service",
            component="auth-handler",
            profile=LoggingProfile.STRUCTURED,
        )
        logger.info("Auth event")

        captured = capsys.readouterr()
        parsed = json.loads(captured.err.strip())

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
        parsed = json.loads(captured.err.strip())

        assert parsed["severity"] == "DEBUG"

    def test_logger_all_log_methods(self, capsys):
        """Test all Logger log methods."""
        logger = Logger(
            service="test-service",
            profile=LoggingProfile.STRUCTURED,
            default_level="TRACE",
        )

        logger.trace("Trace")
        logger.debug("Debug")
        logger.info("Info")
        logger.warn("Warn")
        logger.error("Error")
        logger.fatal("Fatal")

        captured = capsys.readouterr()
        lines = captured.err.strip().split("\n")

        assert len(lines) == 6

        messages = [json.loads(line)["message"] for line in lines]
        assert messages == ["Trace", "Debug", "Info", "Warn", "Error", "Fatal"]

    def test_logger_generic_log_method(self, capsys):
        """Test Logger.log() method with explicit severity."""
        logger = Logger(service="test-service", profile=LoggingProfile.STRUCTURED)

        logger.log(Severity.WARN, "Warning via log()")
        logger.log("ERROR", "Error via log() with string")

        captured = capsys.readouterr()
        lines = captured.err.strip().split("\n")

        parsed1 = json.loads(lines[0])
        parsed2 = json.loads(lines[1])

        assert parsed1["severity"] == "WARN"
        assert parsed2["severity"] == "ERROR"


class TestLoggerPolicyEnforcement:
    """Tests for policy enforcement in Logger."""

    def test_logger_policy_file_placeholder(self):
        """Test Logger with policy_file parameter."""
        # Note: This will fail if the file doesn't exist, but that's expected
        # The policy loading functionality should be tested separately
        with pytest.raises((FileNotFoundError, ValueError, OSError)):  # Expected errors
            Logger(
                service="test-service",
                profile=LoggingProfile.ENTERPRISE,
                policy_file="nonexistent-policy.yaml",
            )

    def test_enterprise_logger_policy_enforcement_allowed(self):
        """Test ENTERPRISE profile accepts valid policy."""
        config = LoggingConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
        )
        policy = LoggingPolicy(
            allowed_profiles=["ENTERPRISE", "STRUCTURED"],
        )

        logger = ProgressiveLogger(config, policy)

        assert logger.policy == policy

    def test_enterprise_logger_policy_enforcement_denied(self):
        """Test ENTERPRISE profile rejects invalid policy."""
        config = LoggingConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
        )
        policy = LoggingPolicy(
            allowed_profiles=["SIMPLE"],
        )

        with pytest.raises(ValueError, match="not allowed by policy"):
            ProgressiveLogger(config, policy)


class TestLoggerProfileComparison:
    """Comparative tests across logger profiles."""

    def test_same_message_different_profiles(self, capsys):
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
        lines = captured.err.strip().split("\n")

        # Should have 3 lines (one from each logger)
        assert len(lines) == 3

        # First line should be text (SIMPLE) - doesn't include extra fields like request_id
        assert message in lines[0]

        # Second and third lines should be JSON
        structured_event = json.loads(lines[1])
        enterprise_event = json.loads(lines[2])

        assert structured_event["message"] == message
        assert structured_event["requestId"] == request_id
        assert "severityLevel" in structured_event

        assert enterprise_event["message"] == message
        assert enterprise_event["requestId"] == request_id
        assert "severityLevel" in enterprise_event

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
        lines = [line for line in captured.err.strip().split("\n") if line.startswith("{")]

        assert len(lines) == 2

        structured_event = json.loads(lines[0])
        enterprise_event = json.loads(lines[1])

        assert structured_event["requestId"] == "req-1"
        # throttle_bucket should be camelCased in STRUCTURED profile
        assert structured_event.get("throttleBucket") == "bucket-1"

        assert enterprise_event["requestId"] == "req-2"
        # throttle_bucket should be camelCased in ENTERPRISE profile
        assert enterprise_event.get("throttleBucket") == "bucket-2"
