"""HTTP endpoint helpers for signal management.

Provides provisional request builders for manual signal triggering
via HTTP endpoints, as specified in the Crucible signals catalog
for Windows fallback scenarios.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from pyfulmen.signals._catalog import get_signal_metadata


class SignalEndpointHelper:
    """Helper for building HTTP requests to signal management endpoints.

    Provides request builders for the /admin/signal endpoint that
    allows manual triggering of signals, particularly useful for
    Windows fallback scenarios.
    """

    def __init__(self, base_url: str = "http://localhost:8080") -> None:
        """Initialize endpoint helper.

        Args:
            base_url: Base URL for the admin API (default: localhost:8080).
        """
        self.base_url = base_url.rstrip("/")

    def build_signal_request(
        self, signal_name: str, headers: dict[str, str] | None = None, timeout: int = 30
    ) -> dict[str, Any]:
        """Build a complete HTTP request for triggering a signal.

        Args:
            signal_name: Name of signal to trigger (e.g., "SIGHUP", "SIGTERM").
            headers: Optional HTTP headers to include.
            timeout: Request timeout in seconds.

        Returns:
            Dictionary with complete request parameters.

        Raises:
            ValueError: If signal is not supported or invalid.
        """
        # Validate signal
        metadata = get_signal_metadata(signal_name)
        if not metadata:
            raise ValueError(f"Unsupported signal: {signal_name}")

        # Build request URL
        url = f"{self.base_url}/admin/signal"

        # Build request body
        body = {
            "signal": signal_name,
            "source": "pyfulmen.signals.http_helper",
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

        # Build headers
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "PyFulmen-Signals/1.0.0",
            "Accept": "application/json",
        }

        if headers:
            default_headers.update(headers)

        return {
            "method": "POST",
            "url": url,
            "headers": default_headers,
            "body": json.dumps(body),
            "timeout": timeout,
            "expected_status": 200,
            "signal_metadata": metadata,
        }

    def build_sighup_request(
        self, config_path: str | None = None, headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Build HTTP request for SIGHUP (config reload) signal.

        Args:
            config_path: Optional path to config file to reload.
            headers: Optional HTTP headers to include.

        Returns:
            Dictionary with complete request parameters.
        """
        request = self.build_signal_request("SIGHUP", headers)

        # Add config-specific parameters for SIGHUP
        body = json.loads(request["body"])
        if config_path:
            body["config_path"] = config_path

        request["body"] = json.dumps(body)
        request["description"] = "Trigger config reload via HTTP endpoint"

        return request

    def build_sigterm_request(
        self, timeout_seconds: int | None = None, headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Build HTTP request for SIGTERM (graceful shutdown) signal.

        Args:
            timeout_seconds: Optional shutdown timeout override.
            headers: Optional HTTP headers to include.

        Returns:
            Dictionary with complete request parameters.
        """
        request = self.build_signal_request("SIGTERM", headers)

        # Add shutdown-specific parameters for SIGTERM
        body = json.loads(request["body"])
        if timeout_seconds:
            body["timeout_seconds"] = timeout_seconds

        request["body"] = json.dumps(body)
        request["description"] = "Trigger graceful shutdown via HTTP endpoint"

        return request

    def build_sigint_request(self, force: bool = False, headers: dict[str, str] | None = None) -> dict[str, Any]:
        """Build HTTP request for SIGINT (interrupt) signal.

        Args:
            force: Whether to force immediate exit (skip graceful shutdown).
            headers: Optional HTTP headers to include.

        Returns:
            Dictionary with complete request parameters.
        """
        request = self.build_signal_request("SIGINT", headers)

        # Add interrupt-specific parameters for SIGINT
        body = json.loads(request["body"])
        body["force"] = force

        request["body"] = json.dumps(body)
        request["description"] = "Trigger interrupt via HTTP endpoint"

        return request

    def get_windows_fallback_signals(self) -> list[str]:
        """Get list of signals that have Windows fallback behavior.

        Returns:
            List of signal names that support HTTP fallback.
        """
        # Common Windows fallback signals based on catalog
        fallback_signals = ["SIGHUP", "SIGPIPE", "SIGALRM", "SIGUSR1", "SIGUSR2"]

        # Verify each has fallback metadata
        verified_signals = []
        for signal_name in fallback_signals:
            metadata = get_signal_metadata(signal_name)
            if metadata and metadata.get("windows_fallback"):
                verified_signals.append(signal_name)

        return verified_signals

    def format_curl_command(self, request: dict[str, Any]) -> str:
        """Format a request as a curl command for debugging/documentation.

        Args:
            request: Request dictionary from build_* methods.

        Returns:
            String containing equivalent curl command.
        """
        headers = " ".join([f'-H "{k}: {v}"' for k, v in request["headers"].items()])

        return (
            f"curl -X {request['method']} \\\n"
            f"  {headers} \\\n"
            f"  -d '{request['body']}' \\\n"
            f"  {request['url']} \\\n"
            f"  --connect-timeout {request['timeout']} \\\n"
            f"  --max-time {request['timeout']}"
        )


# Global helper instance
_default_helper = SignalEndpointHelper()


def get_http_helper(base_url: str = "http://localhost:8080") -> SignalEndpointHelper:
    """Get a signal endpoint helper instance.

    Args:
        base_url: Base URL for the admin API.

    Returns:
        SignalEndpointHelper instance.
    """
    return SignalEndpointHelper(base_url)


def build_signal_request(
    signal_name: str, base_url: str = "http://localhost:8080", headers: dict[str, str] | None = None, timeout: int = 30
) -> dict[str, Any]:
    """Build HTTP request for triggering a signal using default helper.

    Args:
        signal_name: Name of signal to trigger.
        base_url: Base URL for the admin API.
        headers: Optional HTTP headers to include.
        timeout: Request timeout in seconds.

    Returns:
        Dictionary with complete request parameters.
    """
    helper = get_http_helper(base_url)
    return helper.build_signal_request(signal_name, headers, timeout)


def build_windows_fallback_docs() -> str:
    """Generate documentation for Windows fallback HTTP endpoints.

    Returns:
        Markdown documentation string with examples.
    """
    helper = get_http_helper()
    fallback_signals = helper.get_windows_fallback_signals()

    docs = ["# Windows Fallback HTTP Endpoints\n"]
    docs.append("When signals are not supported on Windows, use these HTTP endpoints:\n")

    for signal_name in fallback_signals:
        request = helper.build_signal_request(signal_name)
        curl_cmd = helper.format_curl_command(request)

        docs.append(f"## {signal_name}\n")
        docs.append(f"```bash\n{curl_cmd}\n```\n")
        docs.append(f"*Endpoint:* `{request['url']}`\n")
        docs.append(f"*Method:* {request['method']}\n")
        docs.append(f"*Content-Type:* {request['headers']['Content-Type']}\n\n")

    return "\n".join(docs)


def get_windows_fallback_signals() -> list[str]:
    """Get list of signals that have Windows HTTP fallback support.

    Returns:
        List of signal names that support Windows HTTP fallback.
    """
    helper = get_http_helper()
    return helper.get_windows_fallback_signals()
