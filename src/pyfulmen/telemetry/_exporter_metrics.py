"""
Exporter metrics for Prometheus instrumentation.

Implements the canonical prometheus_exporter_* metrics defined in
Crucible v0.2.7 taxonomy with proper label validation and
structured logging integration.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._registry import MetricRegistry


# Create logger for this module (deferred to avoid circular imports)
def _get_logger():
    from ..logging import Logger

    return Logger(__name__)


class ExporterMetrics:
    """Helper class for managing prometheus_exporter_* metrics.

    Provides thread-safe instrumentation for Prometheus exporter operations
    with proper label validation and structured logging hooks.

    Example:
        >>> from pyfulmen.telemetry import MetricRegistry
        >>> from pyfulmen.telemetry._exporter_metrics import ExporterMetrics
        >>> registry = MetricRegistry()
        >>> metrics = ExporterMetrics(registry)
        >>> metrics.record_refresh_start("collect")
        >>> metrics.record_refresh_success("collect", 0.005)
    """

    # Valid label values based on Crucible taxonomy
    VALID_PHASES = {"collect", "convert", "export"}
    VALID_RESULTS = {"success", "error"}
    VALID_ERROR_TYPES = {"validation", "io", "timeout", "other"}
    VALID_RESTART_REASONS = {"config_change", "error", "manual", "other"}

    def __init__(self, registry: MetricRegistry) -> None:
        """Initialize exporter metrics.

        Args:
            registry: MetricRegistry to record metrics to
        """
        self._registry = registry
        self._lock = threading.Lock()

        # Track inflight operations per phase
        self._inflight: dict[str, int] = {}

        # Initialize counters
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialize all prometheus_exporter_* metrics."""
        # Refresh duration histogram (seconds-based buckets from ADR-0007)
        self._refresh_duration = self._registry.histogram(
            "prometheus_exporter_refresh_duration_seconds", buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
        )

        # Refresh counters
        self._refresh_total = self._registry.counter("prometheus_exporter_refresh_total")
        self._refresh_errors = self._registry.counter("prometheus_exporter_refresh_errors_total")

        # Inflight gauge
        self._refresh_inflight = self._registry.gauge("prometheus_exporter_refresh_inflight")

        # HTTP metrics
        self._http_requests = self._registry.counter("prometheus_exporter_http_requests_total")
        self._http_errors = self._registry.counter("prometheus_exporter_http_errors_total")

        # Restarts counter
        self._restarts_total = self._registry.counter("prometheus_exporter_restarts_total")

    def _validate_phase(self, phase: str) -> None:
        """Validate phase label value."""
        if phase not in self.VALID_PHASES:
            raise ValueError(f"Invalid phase '{phase}'. Must be one of: {self.VALID_PHASES}")

    def _validate_result(self, result: str) -> None:
        """Validate result label value."""
        if result not in self.VALID_RESULTS:
            raise ValueError(f"Invalid result '{result}'. Must be one of: {self.VALID_RESULTS}")

    def _validate_error_type(self, error_type: str) -> None:
        """Validate error_type label value."""
        if error_type not in self.VALID_ERROR_TYPES:
            raise ValueError(f"Invalid error_type '{error_type}'. Must be one of: {self.VALID_ERROR_TYPES}")

    def _validate_restart_reason(self, reason: str) -> None:
        """Validate restart reason label value."""
        if reason not in self.VALID_RESTART_REASONS:
            raise ValueError(f"Invalid restart reason '{reason}'. Must be one of: {self.VALID_RESTART_REASONS}")

    def record_refresh_start(self, phase: str) -> None:
        """Record the start of a refresh operation.

        Args:
            phase: Refresh phase (collect|convert|export)
        """
        self._validate_phase(phase)

        with self._lock:
            current = self._inflight.get(phase, 0)
            self._inflight[phase] = current + 1
            self._refresh_inflight.set(sum(self._inflight.values()))

        _get_logger().debug(
            "Refresh operation started", context={"phase": phase, "telemetry_event": "exporter_refresh_start"}
        )

    def record_refresh_success(self, phase: str, duration_seconds: float) -> None:
        """Record a successful refresh operation.

        Args:
            phase: Refresh phase (collect|convert|export)
            duration_seconds: Duration in seconds
        """
        self._validate_phase(phase)

        with self._lock:
            current = self._inflight.get(phase, 0)
            if current > 0:
                self._inflight[phase] = current - 1
            else:
                _get_logger().warn(
                    "Inflight count underflow detected",
                    context={"phase": phase, "current": current, "telemetry_event": "exporter_inflight_underflow"},
                )
            self._refresh_inflight.set(sum(self._inflight.values()))

        # Record metrics
        self._refresh_total.inc(delta=1.0, tags={"result": "success", "phase": phase})
        self._refresh_duration.observe(duration_seconds, tags={"phase": phase, "result": "success"})

        _get_logger().debug(
            "Refresh operation completed successfully",
            context={
                "phase": phase,
                "duration_seconds": duration_seconds,
                "telemetry_event": "exporter_refresh_success",
            },
        )

    def record_refresh_error(
        self, phase: str, duration_seconds: float, error_type: str, error_message: str | None = None
    ) -> None:
        """Record a failed refresh operation.

        Args:
            phase: Refresh phase (collect|convert|export)
            duration_seconds: Duration in seconds
            error_type: Type of error (validation|io|timeout|other)
            error_message: Optional error message for logging
        """
        self._validate_phase(phase)
        self._validate_error_type(error_type)

        with self._lock:
            current = self._inflight.get(phase, 0)
            if current > 0:
                self._inflight[phase] = current - 1
            else:
                _get_logger().warn(
                    "Inflight count underflow detected",
                    context={"phase": phase, "current": current, "telemetry_event": "exporter_inflight_underflow"},
                )
            self._refresh_inflight.set(sum(self._inflight.values()))

        # Record metrics (dual-counter pattern)
        self._refresh_total.inc(delta=1.0, tags={"result": "error", "phase": phase})
        self._refresh_errors.inc(delta=1.0, tags={"error_type": error_type, "phase": phase})
        self._refresh_duration.observe(
            duration_seconds, tags={"phase": phase, "result": "error", "error_type": error_type}
        )

        _get_logger().error(
            "Refresh operation failed",
            context={
                "phase": phase,
                "duration_seconds": duration_seconds,
                "error_type": error_type,
                "error_message": error_message,
                "telemetry_event": "exporter_refresh_error",
            },
        )

    def record_http_request(self, status: int, path: str, client: str | None = None) -> None:
        """Record an HTTP request to the metrics endpoint.

        Args:
            status: HTTP status code
            path: Request path (e.g., "/metrics")
            client: Optional client identifier (high cardinality warning)
        """
        labels = {"status": str(status), "path": path}
        if client is not None:
            labels["client"] = client

        self._http_requests.inc(delta=1.0, tags=labels)

        # Also record as error if status indicates server error
        if status >= 500:
            self._http_errors.inc(delta=1.0, tags=labels)

        _get_logger().debug(
            "HTTP request recorded",
            context={"status": status, "path": path, "client": client, "telemetry_event": "exporter_http_request"},
        )

    def record_http_error(
        self, status: int, path: str, client: str | None = None, error_message: str | None = None
    ) -> None:
        """Record an HTTP exposition failure.

        Args:
            status: HTTP status code
            path: Request path
            client: Optional client identifier
            error_message: Optional error message
        """
        labels = {"status": str(status), "path": path}
        if client is not None:
            labels["client"] = client

        self._http_errors.inc(delta=1.0, tags=labels)

        _get_logger().error(
            "HTTP exposition failure",
            context={
                "status": status,
                "path": path,
                "client": client,
                "error_message": error_message,
                "telemetry_event": "exporter_http_error",
            },
        )

    def record_restart(self, reason: str, details: str | None = None) -> None:
        """Record an exporter restart.

        Args:
            reason: Restart reason (config_change|error|manual|other)
            details: Optional additional details
        """
        self._validate_restart_reason(reason)

        self._restarts_total.inc(delta=1.0, tags={"reason": reason})

        _get_logger().info(
            "Exporter restart recorded",
            context={"reason": reason, "details": details, "telemetry_event": "exporter_restart"},
        )

    def get_inflight_count(self) -> int:
        """Get current total inflight refresh operations.

        Returns:
            Total number of inflight operations across all phases
        """
        with self._lock:
            return sum(self._inflight.values())

    def get_inflight_by_phase(self) -> dict[str, int]:
        """Get inflight operations broken down by phase.

        Returns:
            Dict mapping phase to inflight count
        """
        with self._lock:
            return self._inflight.copy()


class RefreshContext:
    """Context manager for tracking refresh operations.

    Automatically handles start/success/error recording for refresh
    operations with proper timing and error classification.

    Example:
        >>> with RefreshContext(metrics, "collect") as ctx:
        ...     # Do refresh work
        ...     if error:
        ...         ctx.record_error("validation", "Invalid data")
    """

    def __init__(self, exporter_metrics: ExporterMetrics, phase: str) -> None:
        """Initialize refresh context.

        Args:
            exporter_metrics: ExporterMetrics instance
            phase: Refresh phase (collect|convert|export)
        """
        self._metrics = exporter_metrics
        self._phase = phase
        self._start_time: float | None = None
        self._completed = False

    def __enter__(self) -> RefreshContext:
        """Start refresh operation."""
        self._start_time = time.perf_counter()
        self._metrics.record_refresh_start(self._phase)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Complete refresh operation."""
        if self._start_time is None or self._completed:
            return

        duration = time.perf_counter() - self._start_time

        if exc_type is None:
            # Success
            self._metrics.record_refresh_success(self._phase, duration)
        else:
            # Error - classify based on exception type
            error_type = self._classify_error(exc_type)
            error_message = str(exc_val) if exc_val else None
            self._metrics.record_refresh_error(self._phase, duration, error_type, error_message)

        self._completed = True

    def record_error(self, error_type: str, message: str | None = None) -> None:
        """Manually record an error during refresh.

        Use this when you want to record an error but not raise an exception.

        Args:
            error_type: Type of error (validation|io|timeout|other)
            message: Optional error message
        """
        if self._start_time is None or self._completed:
            return

        duration = time.perf_counter() - self._start_time
        self._metrics.record_refresh_error(self._phase, duration, error_type, message)
        self._completed = True

    def _classify_error(self, exc_type: type) -> str:
        """Classify exception type to error_type label.

        Args:
            exc_type: Exception class

        Returns:
            Error type string for metrics
        """
        if issubclass(exc_type, (ValueError, TypeError)):
            return "validation"
        elif issubclass(exc_type, (TimeoutError, ConnectionError)):
            return "timeout"
        elif issubclass(exc_type, (OSError, IOError, FileNotFoundError)):
            return "io"
        else:
            return "other"
