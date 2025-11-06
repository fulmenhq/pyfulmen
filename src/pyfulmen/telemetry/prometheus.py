"""
Prometheus exporter for telemetry metrics.

Bridges pyfulmen MetricRegistry to Prometheus collectors for
exposition via HTTP endpoints. Supports counters, histograms, and gauges
with namespace configuration and taxonomy validation.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._registry import MetricRegistry

# Handle optional prometheus_client dependency
try:
    from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest
    from prometheus_client.exposition import MetricsHandler
    from prometheus_client.metrics_core import HistogramMetricFamily
    from prometheus_client.registry import Collector

    PROMETHEUS_AVAILABLE = True
except ImportError as e:
    msg = "prometheus_client is required for prometheus module. Install with 'uv add \"pyfulmen[telemetry]\"'"
    raise ImportError(msg) from e

from ..appidentity import get_identity
from ..logging import Logger
from ._exporter_metrics import ExporterMetrics, RefreshContext
from ._validate import validate_metric_name

# Create logger for this module
logger = Logger(__name__)


class _HistogramCollector(Collector):
    """Custom collector for histograms with accurate bucket data.

    This collector creates HistogramMetricFamily instances directly
    from HistogramSummary data, preserving the exact bucket distribution
    without accumulating synthetic data.
    """

    def __init__(self, name: str, documentation: str, namespace: str = "") -> None:
        """Initialize histogram collector.

        Args:
            name: Base metric name
            documentation: Metric documentation
            namespace: Optional namespace prefix
        """
        self._name = name
        self._documentation = documentation
        self._namespace = namespace
        self._summary = None
        self._lock = threading.Lock()

    def update(self, summary: Any) -> None:
        """Update histogram with new summary data.

        Args:
            summary: HistogramSummary with bucket data
        """
        with self._lock:
            self._summary = summary

    def collect(self):
        """Collect histogram metric for Prometheus.

        Returns:
            List containing HistogramMetricFamily with current data
        """
        with self._lock:
            if self._summary is None:
                return []

            # Format metric name with namespace
            metric_name = f"{self._namespace}_{self._name}" if self._namespace else self._name

            # Convert buckets to Prometheus format
            buckets = []
            for bucket in self._summary.buckets:
                if bucket.le == float("inf"):
                    # Infinity bucket - use "+Inf" string as Prometheus expects
                    buckets.append(("+Inf", bucket.count))
                else:
                    # Regular bucket
                    buckets.append((str(bucket.le), bucket.count))

            # Create HistogramMetricFamily with accurate data
            histogram_family = HistogramMetricFamily(
                name=metric_name, documentation=self._documentation, buckets=buckets, sum_value=self._summary.sum
            )

            return [histogram_family]


class PrometheusExporter:
    """Bridge between MetricRegistry and Prometheus collectors.

    Converts pyfulmen metrics to Prometheus format with namespace
    configuration and taxonomy validation.

    Example:
        >>> from pyfulmen.telemetry import MetricRegistry
        >>> from pyfulmen.telemetry.prometheus import PrometheusExporter
        >>> registry = MetricRegistry()
        >>> exporter = PrometheusExporter(registry)
        >>> exporter.refresh()  # Sync metrics to Prometheus
    """

    def __init__(self, registry: MetricRegistry, namespace: str | None = None) -> None:
        """Initialize Prometheus exporter.

        Args:
            registry: MetricRegistry to export from
            namespace: Optional namespace prefix (defaults to app identity)
        """
        self.registry = registry

        # Set namespace with validation
        if namespace is not None:
            if not self._is_valid_namespace(namespace):
                msg = f"Invalid namespace format: {namespace}"
                raise ValueError(msg)
            self._namespace = namespace
        else:
            self._namespace = self._get_default_namespace()
            # Validate default namespace as well
            if not self._is_valid_namespace(self._namespace):
                # Fall back to simple namespace if default is invalid
                self._namespace = "pyfulmen"

        self._collector_registry = CollectorRegistry()
        self._prometheus_metrics: dict[str, Any] = {}
        self._histogram_collectors: dict[str, _HistogramCollector] = {}
        self._lock = threading.Lock()

        # Initialize exporter metrics instrumentation
        self._exporter_metrics = ExporterMetrics(registry)

    def _get_default_namespace(self) -> str:
        """Get default namespace from app identity."""
        try:
            identity = get_identity()
            if identity.vendor and identity.binary_name:
                return f"{identity.vendor}_{identity.binary_name}"
            return "pyfulmen"
        except Exception:
            return "pyfulmen"

    def _is_valid_namespace(self, namespace: str) -> bool:
        """Check if namespace follows Prometheus naming conventions."""
        import re

        # Prometheus metric names must match regex: [a-zA-Z_:][a-zA-Z0-9_:]*
        return bool(re.match(r"^[a-zA-Z_:][a-zA-Z0-9_:]*$", namespace))

    def _format_metric_name(self, name: str) -> str:
        """Format metric name with namespace prefix."""
        if self._namespace:
            return f"{self._namespace}_{name}"
        return name

    def _classify_refresh_error(self, exc: Exception) -> str:
        """Classify refresh exception for error_type label.

        Args:
            exc: Exception that occurred

        Returns:
            Error type string for metrics
        """
        if isinstance(exc, (ValueError, TypeError)):
            return "validation"
        elif isinstance(exc, (OSError, IOError, FileNotFoundError)):
            return "io"
        elif isinstance(exc, (TimeoutError, ConnectionError)):
            return "timeout"
        else:
            return "other"

    def refresh(self) -> None:
        """Refresh Prometheus collectors from registry events.

        Drains all events from MetricRegistry and updates Prometheus
        collectors accordingly. Thread-safe.
        """
        # Track refresh with exporter metrics
        with RefreshContext(self._exporter_metrics, "export") as ctx:
            try:
                with self._lock:
                    events = self.registry.drain_events()

                    # Group events by metric name for processing
                    metric_events: dict[str, list[Any]] = {}
                    for event in events:
                        if event.name not in metric_events:
                            metric_events[event.name] = []
                        metric_events[event.name].append(event)

                    # Process each metric
                    for metric_name, events_list in metric_events.items():
                        try:
                            # Validate metric name against taxonomy
                            validate_metric_name(metric_name)

                            # Get the latest event for current value
                            latest_event = events_list[-1]
                            prometheus_name = self._format_metric_name(metric_name)

                            # Handle different metric types
                            if isinstance(latest_event.value, (int, float)):
                                if metric_name.endswith("_total") or metric_name.endswith("_count"):
                                    self._handle_counter(prometheus_name, latest_event)
                                else:
                                    self._handle_gauge(prometheus_name, latest_event)
                            elif hasattr(latest_event.value, "buckets"):  # HistogramSummary
                                self._handle_histogram(prometheus_name, latest_event)

                        except Exception as e:
                            logger.error(
                                "Failed to process metric event",
                                context={
                                    "metric_name": metric_name,
                                    "error": str(e),
                                    "telemetry_event": "metric_processing_error",
                                },
                            )

            except Exception as e:
                # Record refresh error with classification
                error_type = self._classify_refresh_error(e)
                ctx.record_error(error_type, str(e))
                raise

    def _handle_counter(self, prometheus_name: str, event: Any) -> None:
        """Handle counter metric events."""
        if prometheus_name not in self._prometheus_metrics:
            # Create new counter
            counter = Counter(prometheus_name, f"Counter metric for {event.name}", registry=self._collector_registry)
            self._prometheus_metrics[prometheus_name] = counter

        # Update counter value (counters are cumulative)
        # Prometheus counters are set to the latest cumulative value
        self._prometheus_metrics[prometheus_name]._value._value = float(event.value)

    def _handle_gauge(self, prometheus_name: str, event: Any) -> None:
        """Handle gauge metric events."""
        if prometheus_name not in self._prometheus_metrics:
            # Create new gauge
            gauge = Gauge(prometheus_name, f"Gauge metric for {event.name}", registry=self._collector_registry)
            self._prometheus_metrics[prometheus_name] = gauge

        # Set gauge to current value
        self._prometheus_metrics[prometheus_name].set(float(event.value))

    def _handle_histogram(self, prometheus_name: str, event: Any) -> None:
        """Handle histogram metric events with accurate bucket fidelity."""
        summary = event.value

        if prometheus_name not in self._histogram_collectors:
            # Create new custom histogram collector
            collector = _HistogramCollector(
                name=event.name, documentation=f"Histogram metric for {event.name}", namespace=self._namespace
            )
            self._histogram_collectors[prometheus_name] = collector

            # Register the collector with the registry
            self._collector_registry.register(collector)

        # Update the collector with new summary data
        # This replaces the old data entirely, preventing accumulation
        self._histogram_collectors[prometheus_name].update(summary)

    def _get_default_buckets(self) -> list[float]:
        """Get default histogram buckets matching gofulmen."""
        # These should match the default buckets in gofulmen
        # and the DEFAULT_BUCKETS in Histogram class
        return [1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0, 5000.0, 10000.0]

    def get_collector_registry(self) -> CollectorRegistry:
        """Get the Prometheus CollectorRegistry for use with HTTP handlers.

        Returns:
            CollectorRegistry with all registered metrics
        """
        return self._collector_registry

    def generate_latest(self) -> str:
        """Generate the latest Prometheus exposition format.

        Returns:
            Prometheus text format string
        """
        return generate_latest(self._collector_registry).decode("utf-8")


def create_prometheus_app(exporter: PrometheusExporter) -> Any:
    """Create a WSGI app for Prometheus metrics exposition.

    Args:
        exporter: PrometheusExporter instance

    Returns:
        WSGI-compatible application
    """

    # Create a simple WSGI app that serves metrics
    def prometheus_wsgi_app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
        path = environ.get("PATH_INFO", "")
        client_ip = environ.get("REMOTE_ADDR", "")

        try:
            if path == "/metrics":
                handler = MetricsHandler.factory(exporter.get_collector_registry())
                response = handler(environ, start_response)

                # Record successful request
                status = "200"  # MetricsHandler returns 200 on success
                exporter._exporter_metrics.record_http_request(
                    status=int(status), path=path, client=client_ip if client_ip else None
                )

                return response
            else:
                start_response("404 Not Found", [("Content-Type", "text/plain")])
                exporter._exporter_metrics.record_http_request(
                    status=404, path=path, client=client_ip if client_ip else None
                )
                return [b"Not Found - Use /metrics endpoint"]

        except Exception as e:
            # Record HTTP error
            status = "500"
            exporter._exporter_metrics.record_http_error(
                status=int(status), path=path, client=client_ip if client_ip else None, error_message=str(e)
            )
            start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
            return [b"Internal Server Error"]

    return prometheus_wsgi_app


def serve_prometheus_metrics(
    exporter: PrometheusExporter,
    host: str = "0.0.0.0",
    port: int = 9464,
    refresh_interval: float = 5.0,
) -> None:
    """Start a lightweight HTTP server for Prometheus metrics.

    Args:
        exporter: PrometheusExporter instance
        host: Host to bind to
        port: Port to listen on
        refresh_interval: Auto-refresh interval in seconds
    """
    from wsgiref.simple_server import make_server

    # Record server start
    exporter._exporter_metrics.record_restart("manual", "Starting Prometheus metrics server")

    # Start background refresh thread
    stop_event = threading.Event()

    def refresh_worker() -> None:
        """Background worker to refresh metrics."""
        while not stop_event.is_set():
            try:
                exporter.refresh()
                logger.debug("Metrics refreshed", host=host, port=port, telemetry_event="metrics_refresh")
            except Exception as e:
                logger.error("Failed to refresh metrics", error=str(e), telemetry_event="metrics_refresh_error")
            time.sleep(refresh_interval)

    refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
    refresh_thread.start()

    # Create and start HTTP server
    app = create_prometheus_app(exporter)
    httpd = make_server(host, port, app)

    logger.info(
        "Prometheus metrics server started",
        host=host,
        port=port,
        refresh_interval=refresh_interval,
        metrics_url=f"http://{host}:{port}/metrics",
        telemetry_event="metrics_server_started",
    )

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping Prometheus metrics server", telemetry_event="metrics_server_stopped")
        exporter._exporter_metrics.record_restart("manual", "User interrupted server")
        stop_event.set()
        refresh_thread.join(timeout=1.0)
        httpd.shutdown()
    except Exception as e:
        logger.error("Server crashed", error=str(e), telemetry_event="metrics_server_crashed")
        exporter._exporter_metrics.record_restart("error", f"Server crash: {str(e)}")
        raise


def register_metrics_shutdown(exporter: PrometheusExporter) -> None:
    """Register exporter refresh to be called on graceful shutdown.

    Args:
        exporter: PrometheusExporter instance
    """
    import atexit

    def final_refresh() -> None:
        """Final metrics refresh on shutdown."""
        try:
            exporter.refresh()
            logger.info("Final metrics refresh completed", telemetry_event="metrics_shutdown_refresh")
        except Exception as e:
            logger.error(
                "Failed to perform final metrics refresh", error=str(e), telemetry_event="metrics_shutdown_error"
            )

    def shutdown_metrics() -> None:
        """Flush exporter metrics on shutdown."""
        try:
            # Record final refresh with exporter metrics
            with RefreshContext(exporter._exporter_metrics, "export"):
                final_refresh()
            exporter._exporter_metrics.record_restart("manual", "Graceful shutdown")
        except Exception as e:
            logger.error(
                "Failed to flush exporter metrics on shutdown", error=str(e), telemetry_event="metrics_shutdown_error"
            )

    atexit.register(shutdown_metrics)
