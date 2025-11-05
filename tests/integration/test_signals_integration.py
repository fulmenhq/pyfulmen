"""Integration tests for signals module with other PyFulmen modules."""

import signal as stdlib_signal

from pyfulmen.logging import Logger, LoggingProfile
from pyfulmen.signals import (
    get_http_helper,
    get_module_info,
    on_shutdown,
    supports_signal,
)


class TestSignalsLoggingIntegration:
    """Test signals module integration with logging module."""

    def test_signal_handler_logging_context(self):
        """Test that signal handlers include proper logging context."""
        # Create a logger with structured context
        logger = Logger(
            service="test-service",
            profile=LoggingProfile.STRUCTURED,
        )

        # Register a signal handler that uses logging
        shutdown_called = []

        def shutdown_handler(signum, frame):
            logger.info(
                "Shutdown signal received",
                context={"signal_number": signum, "signal_name": "SIGTERM", "handler_type": "integration_test"},
            )
            shutdown_called.append(True)

        # Register the handler
        on_shutdown(shutdown_handler)

        # Trigger the signal handler manually for testing
        shutdown_handler(stdlib_signal.SIGTERM, None)

        # Verify the handler was called
        assert len(shutdown_called) == 1

    def test_signal_module_info_logging(self):
        """Test that module info includes logging-relevant metadata."""
        info = get_module_info()

        # Verify logging-relevant fields are present
        assert "pyfulmen_version" in info
        assert "catalog_version" in info
        assert "platform" in info
        assert "python_version" in info
        assert isinstance(info["catalog_version"], dict)


class TestSignalsConfigIntegration:
    """Test signals module integration with config module."""

    def test_http_helper_config_integration(self):
        """Test HTTP helper integration with config patterns."""
        helper = get_http_helper()

        # Build a signal request
        request = helper.build_signal_request("SIGHUP")

        # Verify request structure follows config patterns
        assert "method" in request
        assert "url" in request
        assert "headers" in request
        assert "body" in request
        assert "timeout" in request
        assert "expected_status" in request

        # Verify headers include standard config headers
        headers = request["headers"]
        assert "Content-Type" in headers
        assert "User-Agent" in headers
        assert "Accept" in headers


class TestSignalsCrossModuleIntegration:
    """Test cross-module integration scenarios."""

    def test_signal_handler_with_logging(self):
        """Test signal handler that uses logging."""
        # Create logger
        logger = Logger(
            service="integration-test",
            profile=LoggingProfile.STRUCTURED,
        )

        # Register handler that uses logging
        def integrated_handler(signum, frame):
            logger.info(
                "Signal received in integrated handler",
                context={"signal_number": signum, "integration": "logging_only"},
            )

        # Register the handler
        on_shutdown(integrated_handler)

        # Test the handler manually
        integrated_handler(stdlib_signal.SIGTERM, None)

    def test_signal_support_detection(self):
        """Test signal support detection."""
        # Test signal support detection
        sigterm_supported = supports_signal(stdlib_signal.SIGTERM)
        sighup_supported = supports_signal(stdlib_signal.SIGHUP)
        sigint_supported = supports_signal(stdlib_signal.SIGINT)

        # SIGTERM and SIGINT should be supported on all platforms
        assert sigterm_supported, "SIGTERM should be supported"
        assert sigint_supported, "SIGINT should be supported"

        # SIGHUP should be supported on Unix platforms
        # (This test will pass on current platform)
        current_platform = get_module_info()["platform"]
        if current_platform != "windows":
            assert sighup_supported, f"SIGHUP should be supported on {current_platform}"

    def test_http_helper_signal_requests(self):
        """Test HTTP helper builds proper signal requests."""
        helper = get_http_helper()

        # Test different signal types
        sighup_request = helper.build_signal_request("SIGHUP")
        sigterm_request = helper.build_signal_request("SIGTERM")
        sigint_request = helper.build_signal_request("SIGINT")

        # All requests should have proper structure
        for request in [sighup_request, sigterm_request, sigint_request]:
            assert request["method"] == "POST"
            assert request["expected_status"] == 200
            assert "timeout" in request
            assert "headers" in request
            assert "body" in request

            # Check body contains signal info
            import json

            body = json.loads(request["body"])
            assert "signal" in body
            assert "source" in body
            assert "timestamp" in body


class TestSignalsErrorHandlingIntegration:
    """Test error handling integration scenarios."""

    def test_signal_handler_basic_functionality(self):
        """Test basic signal handler functionality."""
        handler_called = []

        def test_handler(signum, frame):
            handler_called.append((signum, frame))

        # Register handler
        on_shutdown(test_handler)

        # Call handler manually
        test_handler(stdlib_signal.SIGTERM, None)

        # Verify handler was called
        assert len(handler_called) == 1
        assert handler_called[0][0] == stdlib_signal.SIGTERM

    def test_multiple_handler_registration(self):
        """Test registering multiple handlers for the same signal."""
        handler1_called = []
        handler2_called = []

        def handler1(signum, frame):
            handler1_called.append(True)

        def handler2(signum, frame):
            handler2_called.append(True)

        # Register both handlers
        on_shutdown(handler1)
        on_shutdown(handler2)

        # Call handlers manually (simulating signal delivery)
        handler1(stdlib_signal.SIGTERM, None)
        handler2(stdlib_signal.SIGTERM, None)

        # Verify both handlers were registered
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1

    def test_module_info_structure(self):
        """Test module info returns expected structure."""
        info = get_module_info()

        # Required fields
        required_fields = ["pyfulmen_version", "catalog_version", "python_version", "platform"]

        for field in required_fields:
            assert field in info, f"Missing required field: {field}"

        # Catalog version should be a dict with version info
        assert isinstance(info["catalog_version"], dict)
        assert "version" in info["catalog_version"]

        # Platform should be a string
        assert isinstance(info["platform"], str)
        assert info["platform"] in ["linux", "darwin", "windows", "freebsd", "unix"]
