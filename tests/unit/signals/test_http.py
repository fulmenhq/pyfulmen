"""Tests for HTTP endpoint helpers."""

import json

import pytest

from pyfulmen.signals._http import (
    SignalEndpointHelper,
    build_signal_request,
    build_windows_fallback_docs,
    get_http_helper,
)


class TestSignalEndpointHelper:
    """Test signal endpoint helper functionality."""

    def test_initialization(self):
        """Test helper initialization."""
        helper = SignalEndpointHelper("http://example.com:9000")

        assert helper.base_url == "http://example.com:9000"

        # Test URL trimming
        helper2 = SignalEndpointHelper("http://example.com:9000/")
        assert helper2.base_url == "http://example.com:9000"

    def test_build_signal_request_valid(self):
        """Test building valid signal request."""
        helper = SignalEndpointHelper()

        request = helper.build_signal_request("SIGHUP")

        assert request["method"] == "POST"
        assert request["url"] == "http://localhost:8080/admin/signal"
        assert request["expected_status"] == 200
        assert request["timeout"] == 30

        # Check headers
        headers = request["headers"]
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "PyFulmen-Signals/1.0.0"
        assert headers["Accept"] == "application/json"

        # Check body
        body = json.loads(request["body"])
        assert body["signal"] == "SIGHUP"
        assert body["source"] == "pyfulmen.signals.http_helper"

        # Check timestamp is dynamic and in ISO format
        assert "timestamp" in body
        timestamp = body["timestamp"]
        assert timestamp != "2025-11-05T19:00:00Z"  # Not the old placeholder
        assert "T" in timestamp and timestamp.endswith("Z")  # ISO format with Z suffix

    def test_build_signal_request_with_options(self):
        """Test building signal request with custom options."""
        helper = SignalEndpointHelper("https://api.example.com")

        custom_headers = {"Authorization": "Bearer token123"}
        request = helper.build_signal_request("SIGTERM", headers=custom_headers, timeout=60)

        assert request["url"] == "https://api.example.com/admin/signal"
        assert request["timeout"] == 60
        assert request["headers"]["Authorization"] == "Bearer token123"

    def test_build_signal_request_invalid_signal(self):
        """Test building request for invalid signal."""
        helper = SignalEndpointHelper()

        with pytest.raises(ValueError, match="Unsupported signal"):
            helper.build_signal_request("INVALID_SIGNAL")

    def test_build_sighup_request(self):
        """Test building SIGHUP-specific request."""
        helper = SignalEndpointHelper()

        request = helper.build_sighup_request(config_path="/etc/app/config.yaml")

        body = json.loads(request["body"])
        assert body["signal"] == "SIGHUP"
        assert body["config_path"] == "/etc/app/config.yaml"
        assert request["description"] == "Trigger config reload via HTTP endpoint"

    def test_build_sigterm_request(self):
        """Test building SIGTERM-specific request."""
        helper = SignalEndpointHelper()

        request = helper.build_sigterm_request(timeout_seconds=45)

        body = json.loads(request["body"])
        assert body["signal"] == "SIGTERM"
        assert body["timeout_seconds"] == 45
        assert request["description"] == "Trigger graceful shutdown via HTTP endpoint"

    def test_build_sigint_request(self):
        """Test building SIGINT-specific request."""
        helper = SignalEndpointHelper()

        request = helper.build_sigint_request(force=True)

        body = json.loads(request["body"])
        assert body["signal"] == "SIGINT"
        assert body["force"] is True
        assert request["description"] == "Trigger interrupt via HTTP endpoint"

    def test_get_windows_fallback_signals(self):
        """Test getting Windows fallback signals."""
        helper = SignalEndpointHelper()

        fallback_signals = helper.get_windows_fallback_signals()

        # Should include common Windows fallback signals
        assert "SIGHUP" in fallback_signals
        assert "SIGPIPE" in fallback_signals
        assert "SIGALRM" in fallback_signals
        assert "SIGUSR1" in fallback_signals
        assert "SIGUSR2" in fallback_signals

        # Should not include signals without fallback
        assert "SIGTERM" not in fallback_signals
        assert "SIGINT" not in fallback_signals

    def test_format_curl_command(self):
        """Test formatting curl command."""
        helper = SignalEndpointHelper()

        request = helper.build_signal_request("SIGHUP")
        curl_cmd = helper.format_curl_command(request)

        assert "curl -X POST" in curl_cmd
        assert '-H "Content-Type: application/json"' in curl_cmd
        assert '-H "User-Agent: PyFulmen-Signals/1.0.0"' in curl_cmd
        assert "http://localhost:8080/admin/signal" in curl_cmd
        assert "--connect-timeout 30" in curl_cmd


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_get_http_helper(self):
        """Test getting HTTP helper instance."""
        helper1 = get_http_helper("http://custom:8080")
        helper2 = get_http_helper("http://custom:8080")

        # Should return different instances
        assert helper1 is not helper2
        assert helper1.base_url == "http://custom:8080"
        assert helper2.base_url == "http://custom:8080"

    def test_build_signal_request_default(self):
        """Test global build_signal_request function."""
        request = build_signal_request("SIGTERM")

        assert request["method"] == "POST"
        assert request["url"] == "http://localhost:8080/admin/signal"

        body = json.loads(request["body"])
        assert body["signal"] == "SIGTERM"

    def test_build_windows_fallback_docs(self):
        """Test building Windows fallback documentation."""
        docs = build_windows_fallback_docs()

        assert "# Windows Fallback HTTP Endpoints" in docs
        assert "## SIGHUP" in docs
        assert "## SIGPIPE" in docs
        assert "curl -X POST" in docs
        assert "Endpoint:* `http://localhost:8080/admin/signal`" in docs
