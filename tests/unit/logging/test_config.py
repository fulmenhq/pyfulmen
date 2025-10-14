"""Unit tests for logging config module."""

import pytest

from pyfulmen.logging.config import (
    LoggerConfig,
    MiddlewareConfig,
    SinkConfig,
    ThrottlingConfig,
    create_enterprise_config,
    create_simple_config,
    create_structured_config,
    validate_logger_config,
)
from pyfulmen.logging.profiles import LoggingProfile


class TestSinkConfig:
    """Test SinkConfig dataclass."""

    def test_minimal_sink_config(self):
        """Test sink config with minimal fields."""
        sink = SinkConfig(type="console")
        assert sink.type == "console"
        assert sink.name is None
        assert sink.level is None
        assert sink.format == "json"
        assert sink.options is None

    def test_full_sink_config(self):
        """Test sink config with all fields."""
        sink = SinkConfig(
            type="rolling-file",
            name="app-logs",
            level="INFO",
            format="json",
            options={"maxSize": "100MB", "maxBackups": 5},
        )
        assert sink.type == "rolling-file"
        assert sink.name == "app-logs"
        assert sink.level == "INFO"
        assert sink.format == "json"
        assert sink.options == {"maxSize": "100MB", "maxBackups": 5}


class TestMiddlewareConfig:
    """Test MiddlewareConfig dataclass."""

    def test_minimal_middleware_config(self):
        """Test middleware config with minimal fields."""
        mw = MiddlewareConfig(name="correlation")
        assert mw.name == "correlation"
        assert mw.enabled is True
        assert mw.order == 0
        assert mw.config is None

    def test_full_middleware_config(self):
        """Test middleware config with all fields."""
        mw = MiddlewareConfig(
            name="redaction",
            enabled=True,
            order=10,
            config={"patterns": ["api_key", "password"]},
        )
        assert mw.name == "redaction"
        assert mw.enabled is True
        assert mw.order == 10
        assert mw.config == {"patterns": ["api_key", "password"]}


class TestThrottlingConfig:
    """Test ThrottlingConfig dataclass."""

    def test_disabled_throttling(self):
        """Test throttling config disabled."""
        throttle = ThrottlingConfig()
        assert throttle.enabled is False
        assert throttle.maxRate is None
        assert throttle.burstSize is None
        assert throttle.windowSize is None
        assert throttle.dropPolicy == "drop-oldest"

    def test_enabled_throttling(self):
        """Test throttling config enabled with settings."""
        throttle = ThrottlingConfig(
            enabled=True,
            maxRate=1000,
            burstSize=100,
            windowSize=60,
            dropPolicy="drop-newest",
        )
        assert throttle.enabled is True
        assert throttle.maxRate == 1000
        assert throttle.burstSize == 100
        assert throttle.windowSize == 60
        assert throttle.dropPolicy == "drop-newest"


class TestLoggerConfig:
    """Test LoggerConfig dataclass."""

    def test_minimal_logger_config(self):
        """Test logger config with minimal fields."""
        config = LoggerConfig(
            profile=LoggingProfile.SIMPLE,
            service="test-service",
        )
        assert config.profile == LoggingProfile.SIMPLE
        assert config.service == "test-service"
        assert config.environment == "development"
        assert config.defaultLevel == "INFO"
        assert config.sinks is None
        assert config.middleware is None
        assert config.throttling is None

    def test_full_logger_config(self):
        """Test logger config with all fields."""
        config = LoggerConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
            environment="production",
            policyFile="/etc/fulmen/logging-policy.yaml",
            defaultLevel="DEBUG",
            sinks=[SinkConfig(type="console")],
            middleware=[MiddlewareConfig(name="correlation")],
            throttling=ThrottlingConfig(enabled=True, maxRate=1000),
            staticFields={"app": "test"},
            enableCaller=True,
            enableStacktrace=True,
        )
        assert config.profile == LoggingProfile.ENTERPRISE
        assert config.service == "test-service"
        assert config.environment == "production"
        assert config.policyFile == "/etc/fulmen/logging-policy.yaml"
        assert config.defaultLevel == "DEBUG"
        assert len(config.sinks) == 1
        assert len(config.middleware) == 1
        assert config.throttling.enabled is True
        assert config.staticFields == {"app": "test"}
        assert config.enableCaller is True
        assert config.enableStacktrace is True


class TestValidateLoggerConfig:
    """Test validate_logger_config function."""

    def test_valid_simple_config(self):
        """Test validation of valid SIMPLE config."""
        config = LoggerConfig(
            profile=LoggingProfile.SIMPLE,
            service="test-service",
            sinks=[SinkConfig(type="console", format="text")],
        )
        errors = validate_logger_config(config)
        assert errors == []

    def test_missing_service_name(self):
        """Test validation fails for missing service name."""
        config = LoggerConfig(
            profile=LoggingProfile.SIMPLE,
            service="",
        )
        errors = validate_logger_config(config)
        assert "Service name is required" in errors

    def test_valid_structured_config(self):
        """Test validation of valid STRUCTURED config."""
        config = LoggerConfig(
            profile=LoggingProfile.STRUCTURED,
            service="test-service",
            sinks=[SinkConfig(type="console", format="json")],
        )
        errors = validate_logger_config(config)
        assert errors == []

    def test_valid_enterprise_config(self):
        """Test validation of valid ENTERPRISE config."""
        config = LoggerConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
            sinks=[SinkConfig(type="console", format="json")],
            middleware=[MiddlewareConfig(name="correlation")],
            policyFile="/etc/fulmen/logging-policy.yaml",
        )
        errors = validate_logger_config(config)
        assert errors == []

    def test_enterprise_missing_middleware(self):
        """Test ENTERPRISE profile requires middleware."""
        config = LoggerConfig(
            profile=LoggingProfile.ENTERPRISE,
            service="test-service",
            sinks=[SinkConfig(type="console", format="json")],
            policyFile="/etc/fulmen/logging-policy.yaml",
        )
        errors = validate_logger_config(config)
        assert any("requires at least one middleware" in err for err in errors)

    def test_throttling_without_maxrate(self):
        """Test throttling requires maxRate."""
        config = LoggerConfig(
            profile=LoggingProfile.STRUCTURED,
            service="test-service",
            sinks=[SinkConfig(type="console")],
            throttling=ThrottlingConfig(enabled=True),
        )
        errors = validate_logger_config(config)
        assert any("requires maxRate" in err for err in errors)

    def test_throttling_invalid_burst_size(self):
        """Test throttling with invalid burst size."""
        config = LoggerConfig(
            profile=LoggingProfile.STRUCTURED,
            service="test-service",
            sinks=[SinkConfig(type="console")],
            throttling=ThrottlingConfig(enabled=True, maxRate=1000, burstSize=0),
        )
        errors = validate_logger_config(config)
        assert any("Burst size must be at least 1" in err for err in errors)


class TestConfigFactories:
    """Test config factory functions."""

    def test_create_simple_config(self):
        """Test create_simple_config factory."""
        config = create_simple_config("test-service")
        assert config.profile == LoggingProfile.SIMPLE
        assert config.service == "test-service"
        assert len(config.sinks) == 1
        assert config.sinks[0].type == "console"
        assert config.sinks[0].format == "text"

    def test_create_simple_config_with_overrides(self):
        """Test create_simple_config with overrides."""
        config = create_simple_config(
            "test-service",
            environment="production",
            defaultLevel="DEBUG",
        )
        assert config.environment == "production"
        assert config.defaultLevel == "DEBUG"

    def test_create_structured_config(self):
        """Test create_structured_config factory."""
        config = create_structured_config("test-service")
        assert config.profile == LoggingProfile.STRUCTURED
        assert config.service == "test-service"
        assert len(config.sinks) == 1
        assert config.sinks[0].type == "console"
        assert config.sinks[0].format == "json"

    def test_create_structured_config_with_overrides(self):
        """Test create_structured_config with overrides."""
        config = create_structured_config(
            "test-service",
            environment="staging",
        )
        assert config.environment == "staging"

    def test_create_enterprise_config(self):
        """Test create_enterprise_config factory."""
        config = create_enterprise_config("test-service")
        assert config.profile == LoggingProfile.ENTERPRISE
        assert config.service == "test-service"
        assert len(config.sinks) == 1
        assert config.sinks[0].type == "console"
        assert config.sinks[0].format == "json"
        assert len(config.middleware) == 1
        assert config.middleware[0].name == "correlation"
        assert config.throttling is not None
        assert config.throttling.enabled is True
        assert config.throttling.maxRate == 1000

    def test_create_enterprise_config_with_overrides(self):
        """Test create_enterprise_config with overrides."""
        config = create_enterprise_config(
            "test-service",
            environment="production",
            policyFile="/custom/policy.yaml",
        )
        assert config.environment == "production"
        assert config.policyFile == "/custom/policy.yaml"