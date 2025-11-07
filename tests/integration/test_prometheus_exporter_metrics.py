"""Integration tests for Prometheus exporter metrics.

Tests that all prometheus_exporter_* metrics are properly emitted
with correct labels and values as defined in Crucible v0.2.7 taxonomy.
"""

import time

import pytest

from pyfulmen.telemetry import MetricRegistry
from pyfulmen.telemetry._exporter_metrics import ExporterMetrics, RefreshContext


class TestPrometheusExporterMetrics:
    """Integration tests for prometheus_exporter_* metrics."""

    def test_exporter_metrics_initialization(self):
        """Test that all prometheus_exporter_* metrics are created."""
        registry = MetricRegistry()
        exporter_metrics = ExporterMetrics(registry)

        # Check that all expected metrics exist in registry
        events = registry.get_events()
        metric_names = {event.name for event in events}

        expected_metrics = {
            "prometheus_exporter_refresh_duration_seconds",
            "prometheus_exporter_refresh_total",
            "prometheus_exporter_refresh_errors_total",
            "prometheus_exporter_refresh_inflight",
            "prometheus_exporter_http_requests_total",
            "prometheus_exporter_http_errors_total",
            "prometheus_exporter_restarts_total",
        }

        # Metrics should be created but no events yet
        assert len(metric_names) == 0  # No events recorded yet

        # Verify metrics exist by checking registry internals
        assert len(registry._histograms) >= 1  # refresh duration
        assert len(registry._counters) >= 5  # refresh total, errors, http requests, http errors, restarts
        assert len(registry._gauges) >= 1  # inflight gauge

    def test_refresh_success_metrics(self):
        """Test successful refresh operation metrics."""
        registry = MetricRegistry()
        exporter_metrics = ExporterMetrics(registry)

        # Record successful refresh
        with RefreshContext(exporter_metrics, "collect"):
            time.sleep(0.01)  # Small delay for duration

        events = registry.get_events()

        # Should have refresh_total, refresh_duration, and inflight events
        refresh_events = [e for e in events if "prometheus_exporter_refresh" in e.name]
        assert len(refresh_events) >= 3

        # Check refresh_total counter
        refresh_total_events = [e for e in refresh_events if e.name == "prometheus_exporter_refresh_total"]
        assert len(refresh_total_events) == 1
        assert refresh_total_events[0].value == 1.0
        assert refresh_total_events[0].tags == {"result": "success", "phase": "collect"}

        # Check refresh_duration histogram
        duration_events = [e for e in refresh_events if e.name == "prometheus_exporter_refresh_duration_seconds"]
        assert len(duration_events) == 1
        assert duration_events[0].tags == {"phase": "collect", "result": "success"}
        assert 0.01 <= duration_events[0].value.sum <= 0.1  # Reasonable duration range

    def test_refresh_error_metrics(self):
        """Test failed refresh operation metrics."""
        registry = MetricRegistry()
        exporter_metrics = ExporterMetrics(registry)

        # Record failed refresh
        with RefreshContext(exporter_metrics, "convert") as ctx:
            time.sleep(0.005)
            ctx.record_error("validation", "Invalid data format")

        events = registry.get_events()

        # Should have refresh_total, refresh_errors, refresh_duration, and inflight events
        refresh_events = [e for e in events if "prometheus_exporter_refresh" in e.name]
        assert len(refresh_events) >= 4

        # Check refresh_total counter (should count both success and error)
        refresh_total_events = [e for e in refresh_events if e.name == "prometheus_exporter_refresh_total"]
        error_refresh_events = [e for e in refresh_total_events if e.tags.get("result") == "error"]
        assert len(error_refresh_events) == 1
        assert error_refresh_events[0].tags == {"result": "error", "phase": "convert"}

        # Check refresh_errors counter
        error_events = [e for e in refresh_events if e.name == "prometheus_exporter_refresh_errors_total"]
        assert len(error_events) == 1
        assert error_events[0].value == 1.0
        assert error_events[0].tags == {"error_type": "validation", "phase": "convert"}

        # Check refresh_duration histogram (should record error duration too)
        duration_events = [e for e in refresh_events if e.name == "prometheus_exporter_refresh_duration_seconds"]
        error_duration_events = [e for e in duration_events if e.tags.get("result") == "error"]
        assert len(error_duration_events) == 1
        assert error_duration_events[0].tags == {"phase": "convert", "result": "error", "error_type": "validation"}

    def test_inflight_gauge_tracking(self):
        """Test inflight gauge tracking across phases."""
        registry = MetricRegistry()
        exporter_metrics = ExporterMetrics(registry)

        # Start multiple operations
        exporter_metrics.record_refresh_start("collect")
        exporter_metrics.record_refresh_start("convert")

        # Check inflight count
        assert exporter_metrics.get_inflight_count() == 2
        assert exporter_metrics.get_inflight_by_phase() == {"collect": 1, "convert": 1}

        # Complete one operation
        exporter_metrics.record_refresh_success("collect", 0.01)

        # Check updated inflight count
        assert exporter_metrics.get_inflight_count() == 1
        inflight_by_phase = exporter_metrics.get_inflight_by_phase()
        assert inflight_by_phase.get("convert") == 1
        assert inflight_by_phase.get("collect") == 0

        # Complete remaining operation
        exporter_metrics.record_refresh_success("convert", 0.02)

        # Check final inflight count
        assert exporter_metrics.get_inflight_count() == 0
        inflight_by_phase = exporter_metrics.get_inflight_by_phase()
        assert inflight_by_phase == {"collect": 0, "convert": 0}

        # Check events were recorded with correct phases
        events = registry.get_events()
        phase_events = [e for e in events if "phase" in (e.tags or {})]

        # Should have events for the two phases we used
        phases = {e.tags["phase"] for e in phase_events}
        assert phases == {"collect", "convert"}

    def test_http_request_metrics(self):
        """Test HTTP request metrics."""
        registry = MetricRegistry()
        exporter_metrics = ExporterMetrics(registry)

        # Record successful HTTP request
        exporter_metrics.record_http_request(200, "/metrics", "test-client")

        # Record failed HTTP request
        exporter_metrics.record_http_request(500, "/metrics", "test-client")

        events = registry.get_events()
        http_events = [e for e in events if "prometheus_exporter_http" in e.name]

        # Should have request and error events
        assert len(http_events) >= 3

        # Check request events
        request_events = [e for e in http_events if e.name == "prometheus_exporter_http_requests_total"]
        assert len(request_events) == 2

        success_request = next(e for e in request_events if e.tags.get("status") == "200")
        assert success_request.tags == {"status": "200", "path": "/metrics", "client": "test-client"}

        error_request = next(e for e in request_events if e.tags.get("status") == "500")
        assert error_request.tags == {"status": "500", "path": "/metrics", "client": "test-client"}

        # Check error events (500 status should generate error)
        error_events = [e for e in http_events if e.name == "prometheus_exporter_http_errors_total"]
        assert len(error_events) == 1  # 500 status generates one error event

    def test_http_error_metrics(self):
        """Test HTTP error metrics."""
        registry = MetricRegistry()
        exporter_metrics = ExporterMetrics(registry)

        # Record HTTP error
        exporter_metrics.record_http_error(503, "/metrics", "test-client", "Service unavailable")

        events = registry.get_events()
        error_events = [e for e in events if e.name == "prometheus_exporter_http_errors_total"]

        assert len(error_events) == 1
        assert error_events[0].value == 1.0
        assert error_events[0].tags == {"status": "503", "path": "/metrics", "client": "test-client"}

    def test_restart_metrics(self):
        """Test restart metrics."""
        registry = MetricRegistry()
        exporter_metrics = ExporterMetrics(registry)

        # Record restart
        exporter_metrics.record_restart("config_change", "Configuration file updated")

        events = registry.get_events()
        restart_events = [e for e in events if e.name == "prometheus_exporter_restarts_total"]

        assert len(restart_events) == 1
        assert restart_events[0].value == 1.0
        assert restart_events[0].tags == {"reason": "config_change"}

    def test_label_validation(self):
        """Test that invalid label values are rejected."""
        registry = MetricRegistry()
        exporter_metrics = ExporterMetrics(registry)

        # Test invalid phase
        with pytest.raises(ValueError, match="Invalid phase 'invalid_phase'"):
            exporter_metrics.record_refresh_start("invalid_phase")

        # Test invalid result (this won't raise because success doesn't validate result)
        # The result is hardcoded to "success" in record_refresh_success
        exporter_metrics.record_refresh_success("collect", 0.01)

        # But invalid phase should still raise
        with pytest.raises(ValueError, match="Invalid phase 'invalid_phase'"):
            exporter_metrics.record_refresh_success("invalid_phase", 0.01)

        # Test invalid error type
        with pytest.raises(ValueError, match="Invalid error_type 'invalid_error'"):
            exporter_metrics.record_refresh_error("collect", 0.01, "invalid_error")

        # Test invalid restart reason
        with pytest.raises(ValueError, match="Invalid restart reason 'invalid_reason'"):
            exporter_metrics.record_restart("invalid_reason")

    def test_multiple_phases_tracking(self):
        """Test tracking multiple refresh phases simultaneously."""
        registry = MetricRegistry()
        exporter_metrics = ExporterMetrics(registry)

        # Start operations in all phases
        exporter_metrics.record_refresh_start("collect")
        exporter_metrics.record_refresh_start("convert")
        exporter_metrics.record_refresh_start("export")

        assert exporter_metrics.get_inflight_count() == 3
        assert exporter_metrics.get_inflight_by_phase() == {"collect": 1, "convert": 1, "export": 1}

        # Complete operations in different order
        exporter_metrics.record_refresh_success("convert", 0.02)
        exporter_metrics.record_refresh_error("export", 0.05, "timeout")
        exporter_metrics.record_refresh_success("collect", 0.01)

        # All should be completed
        assert exporter_metrics.get_inflight_count() == 0
        inflight_by_phase = exporter_metrics.get_inflight_by_phase()
        assert inflight_by_phase == {"collect": 0, "convert": 0, "export": 0}

    def test_http_request_without_client(self):
        """Test HTTP request metrics without optional client label."""
        registry = MetricRegistry()
        exporter_metrics = ExporterMetrics(registry)

        # Record request without client
        exporter_metrics.record_http_request(200, "/metrics")

        events = registry.get_events()
        request_events = [e for e in events if e.name == "prometheus_exporter_http_requests_total"]

        assert len(request_events) == 1
        assert request_events[0].tags == {"status": "200", "path": "/metrics"}
        assert "client" not in request_events[0].tags
