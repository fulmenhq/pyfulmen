"""
Tests for telemetry.prometheus

Tests Prometheus exporter functionality with mock prometheus_client.
"""

import sys
from unittest.mock import Mock, patch

import pytest


# Test import error handling
def test_prometheus_import_error():
    """Test that ImportError is raised when prometheus_client is not available."""
    # Clear import cache by removing modules and forcing reimport
    import importlib

    # Remove prometheus modules from sys.modules
    original_modules = {}
    for module_name in ["prometheus_client", "prometheus_client.core", "prometheus_client.exposition"]:
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
            del sys.modules[module_name]

    # Also remove our prometheus module from cache
    if "pyfulmen.telemetry.prometheus" in sys.modules:
        del sys.modules["pyfulmen.telemetry.prometheus"]

    try:
        with (
            patch.dict("sys.modules", {"prometheus_client": None}),
            pytest.raises(ImportError, match="prometheus_client is required"),
        ):
            # Force reimport to trigger ImportError
            importlib.import_module("pyfulmen.telemetry.prometheus")
    finally:
        # Restore original modules
        sys.modules.update(original_modules)


# Mock prometheus_client classes for testing
@pytest.fixture
def mock_prometheus_classes():
    """Mock prometheus_client classes."""
    with (
        patch("pyfulmen.telemetry.prometheus.CollectorRegistry") as mock_registry,
        patch("pyfulmen.telemetry.prometheus.Counter") as mock_counter,
        patch("pyfulmen.telemetry.prometheus.Gauge") as mock_gauge,
        patch("pyfulmen.telemetry.prometheus.HistogramMetricFamily") as mock_histogram_family,
        patch("pyfulmen.telemetry.prometheus.generate_latest") as mock_generate,
        patch("pyfulmen.telemetry.prometheus.MetricsHandler") as mock_handler,
    ):
        mock_registry_instance = Mock()
        mock_counter_instance = Mock()
        mock_gauge_instance = Mock()
        mock_histogram_family_instance = Mock()

        mock_registry.return_value = mock_registry_instance
        mock_counter.return_value = mock_counter_instance
        mock_gauge.return_value = mock_gauge_instance
        mock_histogram_family.return_value = mock_histogram_family_instance

        yield {
            "registry": mock_registry,
            "counter": mock_counter,
            "gauge": mock_gauge,
            "histogram_family": mock_histogram_family,
            "generate": mock_generate,
            "handler": mock_handler,
            "registry_instance": mock_registry_instance,
            "counter_instance": mock_counter_instance,
            "gauge_instance": mock_gauge_instance,
            "histogram_family_instance": mock_histogram_family_instance,
        }


class TestPrometheusExporter:
    """Tests for PrometheusExporter."""

    @pytest.fixture(autouse=True)
    def setup_imports(self):
        """Set up imports for each test."""
        # Import after mocking
        from pyfulmen.telemetry import MetricRegistry
        from pyfulmen.telemetry.prometheus import PrometheusExporter

        self.PrometheusExporter = PrometheusExporter
        self.MetricRegistry = MetricRegistry

    def test_exporter_initialization(self, mock_prometheus_classes):
        """Test exporter initialization with default namespace."""
        # Mock app identity
        with patch("pyfulmen.telemetry.prometheus.get_identity") as mock_get_identity:
            mock_identity = Mock()
            mock_identity.vendor = "testvendor"
            mock_identity.binary_name = "testapp"
            mock_get_identity.return_value = mock_identity

            registry = self.MetricRegistry()
            exporter = self.PrometheusExporter(registry)

            assert exporter.registry == registry
            assert exporter._namespace == "testvendor_testapp"
            assert exporter._collector_registry == mock_prometheus_classes["registry_instance"]

    def test_exporter_custom_namespace(self, mock_prometheus_classes):
        """Test exporter initialization with custom namespace."""
        registry = self.MetricRegistry()
        exporter = self.PrometheusExporter(registry, namespace="custom_ns")
        assert exporter._namespace == "custom_ns"

    def test_exporter_invalid_namespace(self, mock_prometheus_classes):
        """Test exporter initialization with invalid namespace."""
        registry = self.MetricRegistry()
        with pytest.raises(ValueError, match="Invalid namespace format"):
            self.PrometheusExporter(registry, namespace="invalid@ns")

    def test_format_metric_name(self, mock_prometheus_classes):
        """Test metric name formatting with namespace."""
        with patch("pyfulmen.telemetry.prometheus.get_identity") as mock_get_identity:
            mock_identity = Mock()
            mock_identity.vendor = "testvendor"
            mock_identity.binary_name = "testapp"
            mock_get_identity.return_value = mock_identity

            registry = self.MetricRegistry()
            exporter = self.PrometheusExporter(registry)

            formatted = exporter._format_metric_name("test_metric")
            assert formatted == "testvendor_testapp_test_metric"

    def test_format_metric_name_no_namespace(self, mock_prometheus_classes):
        """Test metric name formatting without namespace."""
        with patch("pyfulmen.telemetry.prometheus.get_identity") as mock_get_identity:
            mock_identity = Mock()
            mock_identity.vendor = "testvendor"
            mock_identity.binary_name = "testapp"
            mock_get_identity.return_value = mock_identity

            registry = self.MetricRegistry()
            exporter = self.PrometheusExporter(registry, namespace=None)
            formatted = exporter._format_metric_name("test_metric")
            assert formatted == "testvendor_testapp_test_metric"

    def test_handle_counter_creation(self, mock_prometheus_classes):
        """Test handling counter metric creation."""
        from datetime import UTC, datetime

        from pyfulmen.telemetry.models import MetricEvent

        registry = self.MetricRegistry()
        exporter = self.PrometheusExporter(registry)

        event = MetricEvent(timestamp=datetime.now(UTC), name="test_requests_total", value=42.0)

        prometheus_name = exporter._format_metric_name("test_requests_total")
        exporter._handle_counter(prometheus_name, event)

        # Verify counter was created and value set
        assert prometheus_name in exporter._prometheus_metrics
        mock_prometheus_classes["counter_instance"]._value._value = 42.0

    def test_handle_gauge_creation(self, mock_prometheus_classes):
        """Test handling gauge metric creation."""
        from datetime import UTC, datetime

        from pyfulmen.telemetry.models import MetricEvent

        registry = self.MetricRegistry()
        exporter = self.PrometheusExporter(registry)

        event = MetricEvent(timestamp=datetime.now(UTC), name="test_queue_depth", value=10.0)

        prometheus_name = exporter._format_metric_name("test_queue_depth")
        exporter._handle_gauge(prometheus_name, event)

        # Verify gauge was created and value set
        assert prometheus_name in exporter._prometheus_metrics
        mock_prometheus_classes["gauge_instance"].set.assert_called_once_with(10.0)

    def test_handle_histogram_creation(self, mock_prometheus_classes):
        """Test handling histogram metric creation."""
        from datetime import UTC, datetime

        from pyfulmen.telemetry.models import HistogramBucket, HistogramSummary, MetricEvent

        registry = self.MetricRegistry()
        exporter = self.PrometheusExporter(registry)

        buckets = [
            HistogramBucket(le=1.0, count=1),
            HistogramBucket(le=5.0, count=3),
            HistogramBucket(le=float("inf"), count=5),
        ]
        summary = HistogramSummary(count=5, sum=25.0, buckets=buckets)

        event = MetricEvent(timestamp=datetime.now(UTC), name="test_latency_ms", value=summary)

        prometheus_name = exporter._format_metric_name("test_latency_ms")
        exporter._handle_histogram(prometheus_name, event)

        # Verify histogram collector was created
        assert prometheus_name in exporter._histogram_collectors
        collector = exporter._histogram_collectors[prometheus_name]
        assert collector._name == "test_latency_ms"
        assert collector._namespace == "fulmenhq_pyfulmen"

    def test_refresh_with_counter_events(self, mock_prometheus_classes):
        """Test refresh processes counter events correctly."""
        # Mock validate_metric_name to avoid taxonomy dependency
        with patch("pyfulmen.telemetry.prometheus.validate_metric_name"):
            registry = self.MetricRegistry()
            exporter = self.PrometheusExporter(registry)

            # Create counter and generate events
            counter = registry.counter("test_requests_total")
            counter.inc()
            counter.inc(5)

            # Refresh exporter
            exporter.refresh()

            # Verify counter was processed
            prometheus_name = exporter._format_metric_name("test_requests_total")
            assert prometheus_name in exporter._prometheus_metrics

    def test_refresh_with_gauge_events(self, mock_prometheus_classes):
        """Test refresh processes gauge events correctly."""
        # Mock validate_metric_name to avoid taxonomy dependency
        with patch("pyfulmen.telemetry.prometheus.validate_metric_name"):
            registry = self.MetricRegistry()
            exporter = self.PrometheusExporter(registry)

            # Create gauge and generate events
            gauge = registry.gauge("test_queue_depth")
            gauge.set(10)
            gauge.set(20)

            # Refresh exporter
            exporter.refresh()

            # Verify gauge was processed
            prometheus_name = exporter._format_metric_name("test_queue_depth")
            assert prometheus_name in exporter._prometheus_metrics

    def test_refresh_with_histogram_events(self, mock_prometheus_classes):
        """Test refresh processes histogram events correctly."""
        # Mock validate_metric_name to avoid taxonomy dependency
        with patch("pyfulmen.telemetry.prometheus.validate_metric_name"):
            registry = self.MetricRegistry()
            exporter = self.PrometheusExporter(registry)

            # Create histogram and generate events
            histogram = registry.histogram("test_latency_ms")
            histogram.observe(5.0)
            histogram.observe(15.0)

            # Refresh exporter
            exporter.refresh()

            # Verify histogram was processed
            prometheus_name = exporter._format_metric_name("test_latency_ms")
            assert prometheus_name in exporter._histogram_collectors

    def test_refresh_with_invalid_metric_name(self, mock_prometheus_classes):
        """Test refresh handles invalid metric names gracefully."""
        # Mock validate_metric_name to raise ValueError
        with patch("pyfulmen.telemetry.prometheus.validate_metric_name") as mock_validate:
            mock_validate.side_effect = ValueError("Invalid metric name")

            registry = self.MetricRegistry()
            exporter = self.PrometheusExporter(registry)

            # Create counter and generate events
            counter = registry.counter("invalid_metric")
            counter.inc()

            # Refresh should not raise exception
            exporter.refresh()

            # Verify no metrics were created
            assert len(exporter._prometheus_metrics) == 0

    def test_get_collector_registry(self, mock_prometheus_classes):
        """Test getting collector registry."""
        registry = self.MetricRegistry()
        exporter = self.PrometheusExporter(registry)

        registry_obj = exporter.get_collector_registry()
        assert registry_obj == mock_prometheus_classes["registry_instance"]

    def test_generate_latest(self, mock_prometheus_classes):
        """Test generating latest Prometheus output."""
        registry = self.MetricRegistry()
        exporter = self.PrometheusExporter(registry)

        # Mock generate_latest function
        expected_output = "# HELP test_metric Test help\n# TYPE test_metric counter\ntest_metric 42\n"
        mock_prometheus_classes["generate"].return_value = expected_output.encode()

        output = exporter.generate_latest()

        assert output == expected_output
        mock_prometheus_classes["generate"].assert_called_once_with(mock_prometheus_classes["registry_instance"])

    def test_get_default_buckets(self, mock_prometheus_classes):
        """Test default histogram buckets."""
        registry = self.MetricRegistry()
        exporter = self.PrometheusExporter(registry)

        buckets = exporter._get_default_buckets()
        expected = [1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0, 5000.0, 10000.0]
        assert buckets == expected


class TestCreatePrometheusApp:
    """Tests for create_prometheus_app function."""

    @pytest.fixture(autouse=True)
    def setup_imports(self):
        """Set up imports for each test."""
        from pyfulmen.telemetry.prometheus import create_prometheus_app

        self.create_prometheus_app = create_prometheus_app

    def test_create_wsgi_app(self, mock_prometheus_classes):
        """Test creating WSGI application."""
        mock_exporter = Mock()
        mock_exporter.get_collector_registry.return_value = Mock()

        app = self.create_prometheus_app(mock_exporter)

        # Test app is callable
        assert callable(app)

        # Test metrics endpoint
        environ = {"PATH_INFO": "/metrics"}
        start_response = Mock()

        app(environ, start_response)

        # Verify MetricsHandler was used
        mock_prometheus_classes["handler"].factory.assert_called_once()

    def test_wsgi_app_404_for_non_metrics(self, mock_prometheus_classes):
        """Test WSGI app returns 404 for non-metrics paths."""
        mock_exporter = Mock()

        app = self.create_prometheus_app(mock_exporter)

        # Test non-metrics endpoint
        environ = {"PATH_INFO": "/other"}
        start_response = Mock()

        response = app(environ, start_response)

        # Verify 404 response
        start_response.assert_called_once_with("404 Not Found", [("Content-Type", "text/plain")])
        assert response == [b"Not Found - Use /metrics endpoint"]


class TestIntegration:
    """Integration tests for Prometheus exporter."""

    @pytest.fixture(autouse=True)
    def setup_imports(self):
        """Set up imports for each test."""
        from pyfulmen.telemetry import MetricRegistry
        from pyfulmen.telemetry.prometheus import PrometheusExporter

        self.PrometheusExporter = PrometheusExporter
        self.MetricRegistry = MetricRegistry

    def test_full_counter_workflow(self, mock_prometheus_classes):
        """Test complete workflow with counter metrics."""
        # Mock validate_metric_name to avoid taxonomy dependency
        with patch("pyfulmen.telemetry.prometheus.validate_metric_name"):
            # Create registry and exporter
            registry = self.MetricRegistry()
            exporter = self.PrometheusExporter(registry)

            # Create counter and record events
            counter = registry.counter("test_requests_total")
            counter.inc()
            counter.inc(3)

            # Refresh exporter
            exporter.refresh()

            # Verify counter was created and updated
            prometheus_name = exporter._format_metric_name("test_requests_total")
            assert prometheus_name in exporter._prometheus_metrics
            mock_prometheus_classes["counter"].assert_called_once()

    def test_full_gauge_workflow(self, mock_prometheus_classes):
        """Test complete workflow with gauge metrics."""
        # Mock validate_metric_name to avoid taxonomy dependency
        with patch("pyfulmen.telemetry.prometheus.validate_metric_name"):
            # Create registry and exporter
            registry = self.MetricRegistry()
            exporter = self.PrometheusExporter(registry)

            # Create gauge and record events
            gauge = registry.gauge("test_memory_usage")
            gauge.set(100)
            gauge.set(200)

            # Refresh exporter
            exporter.refresh()

            # Verify gauge was created and updated
            prometheus_name = exporter._format_metric_name("test_memory_usage")
            assert prometheus_name in exporter._prometheus_metrics
            mock_prometheus_classes["gauge"].assert_called_once()
            mock_prometheus_classes["gauge_instance"].set.assert_called_with(200)  # Latest value

    def test_histogram_fidelity_accuracy(self, mock_prometheus_classes):
        """Test that histogram export preserves exact bucket distribution."""
        # Mock validate_metric_name to avoid taxonomy dependency
        with patch("pyfulmen.telemetry.prometheus.validate_metric_name"):
            registry = self.MetricRegistry()
            exporter = self.PrometheusExporter(registry)

            # Create histogram with specific observations
            histogram = registry.histogram("test_latency_ms")
            histogram.observe(2.0)  # Should go in bucket le=5.0
            histogram.observe(8.0)  # Should go in bucket le=10.0
            histogram.observe(15.0)  # Should go in bucket le=50.0

            # Refresh exporter
            exporter.refresh()

            # Get the histogram collector
            prometheus_name = exporter._format_metric_name("test_latency_ms")
            collector = exporter._histogram_collectors[prometheus_name]

            # Verify the collector has been updated with summary data
            assert collector._summary is not None
            summary = collector._summary
            assert summary.count == 3
            assert summary.sum == 25.0  # 2.0 + 8.0 + 15.0

            # Verify bucket counts are correct
            bucket_counts = {bucket.le: bucket.count for bucket in summary.buckets}
            assert bucket_counts[5.0] == 1  # Only 2.0
            assert bucket_counts[10.0] == 2  # 2.0 and 8.0
            assert bucket_counts[50.0] == 3  # All three observations
            assert bucket_counts[float("inf")] == 3  # Total count
