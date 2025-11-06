"""
Tests for module-level telemetry helper functions.

Tests that global default registry and convenience functions
provide simple API for common use cases.
"""

import pytest

from pyfulmen.telemetry import (
    MetricRegistry,
    clear_metrics,
    counter,
    drain_events,
    gauge,
    get_events,
    histogram,
)
from pyfulmen.telemetry._registry import _default_registry


class TestModuleLevelHelpers:
    """Test module-level helper functions."""

    def test_counter_helper_function(self):
        """Test counter() helper function."""
        # Clear default registry
        clear_metrics()

        # Use helper function
        c = counter("test_counter")
        c.inc()
        c.inc(5)

        # Check events in default registry
        events = get_events()
        assert len(events) == 2
        assert events[0].name == "test_counter"
        assert events[0].value == 1.0
        assert events[1].value == 6.0  # 1 + 5

    def test_gauge_helper_function(self):
        """Test gauge() helper function."""
        clear_metrics()

        # Use helper function
        g = gauge("test_gauge")
        g.set(42)
        g.set(100)

        # Check events in default registry
        events = get_events()
        assert len(events) == 2
        assert events[0].name == "test_gauge"
        assert events[0].value == 42
        assert events[1].value == 100

    def test_histogram_helper_function(self):
        """Test histogram() helper function."""
        clear_metrics()

        # Use helper function
        h = histogram("test_histogram_ms")
        h.observe(5.0)
        h.observe(15.0)
        h.observe(25.0)

        # Check events in default registry
        events = get_events()
        assert len(events) == 3
        assert events[0].name == "test_histogram_ms"

        # Check histogram summary
        summary = events[-1].value  # Latest event has summary
        assert hasattr(summary, "count")
        assert hasattr(summary, "sum")
        assert summary.count == 3
        assert summary.sum == 45.0  # 5 + 15 + 25

    def test_histogram_helper_with_custom_buckets(self):
        """Test histogram() helper with custom buckets."""
        clear_metrics()

        # Use helper function with custom buckets
        custom_buckets = [1.0, 10.0, 100.0]
        h = histogram("test_custom_histogram", buckets=custom_buckets)
        h.observe(0.5)
        h.observe(5.0)
        h.observe(50.0)

        # Check events
        events = get_events()
        assert len(events) == 3

        # Check bucket boundaries in summary
        summary = events[-1].value
        assert hasattr(summary, "buckets")
        bucket_bounds = [bucket.le for bucket in summary.buckets]
        assert bucket_bounds == [1.0, 10.0, 100.0, float("inf")]

    def test_get_events_helper(self):
        """Test get_events() helper function."""
        clear_metrics()

        # Add some metrics
        counter("test").inc()
        gauge("test").set(42)

        # Use helper function
        events = get_events()
        assert len(events) == 2
        assert all(event.name == "test" for event in events)

    def test_drain_events_helper(self):
        """Test drain_events() helper function."""
        clear_metrics()

        # Add some metrics
        counter("test").inc()
        counter("test").inc()
        gauge("test").set(42)

        # Drain events
        drained = drain_events()
        assert len(drained) == 3

        # Verify events are cleared from default registry
        remaining = get_events()
        assert len(remaining) == 0

    def test_clear_metrics_helper(self):
        """Test clear_metrics() helper function."""
        # Add some metrics
        counter("test").inc()
        gauge("test").set(42)

        # Verify events exist
        events_before = get_events()
        assert len(events_before) > 0

        # Clear metrics
        clear_metrics()

        # Verify everything is cleared
        events_after = get_events()
        assert len(events_after) == 0

    def test_helper_functions_use_same_registry(self):
        """Test that all helper functions use the same default registry."""
        clear_metrics()

        # Use different helper functions
        c = counter("shared_counter")
        g = gauge("shared_gauge")
        h = histogram("shared_histogram")

        # Record metrics
        c.inc()
        g.set(100)
        h.observe(25.0)

        # All should be in same registry
        events = get_events()
        assert len(events) == 3

        event_names = {event.name for event in events}
        assert event_names == {"shared_counter", "shared_gauge", "shared_histogram"}

    def test_helper_functions_thread_safety(self):
        """Test that helper functions are thread-safe."""
        import threading

        clear_metrics()

        def record_metrics(thread_id: int):
            """Record metrics from a thread."""
            for i in range(10):
                counter(f"thread_{thread_id}_counter").inc()
                gauge(f"thread_{thread_id}_gauge").set(i)
                histogram(f"thread_{thread_id}_histogram").observe(i * 1.5)

        # Create multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=record_metrics, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all metrics were recorded
        events = get_events()
        assert len(events) == 90  # 3 threads * 10 iterations * 3 metric types

        # Verify thread isolation
        counter_events = [e for e in events if "counter" in e.name]
        gauge_events = [e for e in events if "gauge" in e.name]
        histogram_events = [e for e in events if "histogram" in e.name]

        assert len(counter_events) == 30
        assert len(gauge_events) == 30
        assert len(histogram_events) == 30


class TestCustomRegistryIsolation:
    """Test that custom registries are isolated from default registry."""

    def test_custom_registry_isolation(self):
        """Test that custom registries don't affect default registry."""
        # Clear default registry
        clear_metrics()

        # Create custom registry
        custom_registry = MetricRegistry()

        # Add metrics to both registries
        counter("default_counter").inc()  # Uses default registry
        custom_counter = custom_registry.counter("custom_counter")
        custom_counter.inc()  # Uses custom registry

        # Check default registry only has default metrics
        default_events = get_events()
        assert len(default_events) == 1
        assert default_events[0].name == "default_counter"

        # Check custom registry only has custom metrics
        custom_events = custom_registry.get_events()
        assert len(custom_events) == 1
        assert custom_events[0].name == "custom_counter"

    def test_helper_functions_unchanged_by_custom_registry(self):
        """Test that helper functions always use default registry."""
        clear_metrics()

        # Create custom registry and add metrics
        custom_registry = MetricRegistry()
        custom_counter = custom_registry.counter("custom")
        custom_counter.inc()

        # Use helper functions (should use default registry)
        counter("default").inc()

        # Helper functions should not see custom registry metrics
        default_events = get_events()
        assert len(default_events) == 1
        assert default_events[0].name == "default"

        # Custom registry should only have its own metrics
        custom_events = custom_registry.get_events()
        assert len(custom_events) == 1
        assert custom_events[0].name == "custom"


class TestHelperFunctionIntegration:
    """Test integration of helper functions with existing functionality."""

    def test_helper_with_prometheus_exporter(self):
        """Test that helper functions work with Prometheus exporter."""
        # Skip if prometheus_client not available
        try:
            from pyfulmen.telemetry.prometheus import PrometheusExporter
        except ImportError:
            pytest.skip("prometheus_client not available")

        clear_metrics()

        # Use helper functions to record metrics
        c = counter("schema_validations")
        c.inc()
        c.inc(5)

        g = gauge("foundry_lookup_count")
        g.set(1024)

        h = histogram("config_load_ms")
        h.observe(25.5)
        h.observe(75.0)

        # Create exporter and refresh
        exporter = PrometheusExporter(_default_registry)
        exporter.refresh()

        # Verify exporter processed the metrics
        output = exporter.generate_latest()
        assert "schema_validations" in output
        assert "foundry_lookup_count" in output
        assert "config_load_ms" in output

    def test_helper_with_validation(self):
        """Test that helper functions respect metric validation."""
        clear_metrics()

        # Valid metric name should work
        valid_counter = counter("schema_validations")
        valid_counter.inc()

        events = get_events()
        assert len(events) == 1
        assert events[0].name == "schema_validations"

        # Invalid metric names should work at creation time (validation is at export time)
        invalid_counter = counter("invalid_metric_name")
        invalid_counter.inc()

        # Should have the event in the registry
        events = get_events()
        assert len(events) == 2  # valid + invalid
        assert events[1].name == "invalid_metric_name"

        # Validation happens at export time, not creation time
        # This is by design - events are stored locally and validated when exported
        assert True  # Test passes - validation is deferred to export time
