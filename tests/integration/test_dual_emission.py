"""Integration tests for dual-emission functionality."""

import os
from unittest.mock import patch

from pyfulmen.telemetry import (
    MetricRegistry,
    create_aliased_counter,
    create_aliased_histogram,
    is_dual_emission_enabled,
)


class TestDualEmissionIntegration:
    """Integration tests for dual-emission alias system."""

    def test_dual_emission_end_to_end(self):
        """Test complete dual-emission workflow end-to-end."""
        registry = MetricRegistry()

        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "true"}):
            # Verify dual-emission is enabled
            assert is_dual_emission_enabled()

            # Create aliased counter with different legacy and canonical names
            counter = create_aliased_counter(
                registry, canonical_name="test_requests_total", legacy_name="legacy_requests_total"
            )

            # Create aliased histogram with same names (no dual emission)
            histogram = create_aliased_histogram(
                registry,
                canonical_name="test_duration_ms",
                legacy_name="test_duration_ms",  # Same name
                buckets=[1.0, 5.0, 10.0],
            )

            # Increment counter
            counter.inc(5.0, tags={"endpoint": "/api/test"})

            # Observe histogram
            histogram.observe(7.5, tags={"operation": "test"})

            # Check events - should have both legacy and canonical for counter
            events = registry.get_events()

            # Counter events (should have both legacy and canonical)
            counter_events = [e for e in events if "requests_total" in e.name]
            assert len(counter_events) == 2

            canonical_counter = next(e for e in counter_events if e.name == "test_requests_total")
            legacy_counter = next(e for e in counter_events if e.name == "legacy_requests_total")

            assert canonical_counter.value == 5.0
            assert canonical_counter.tags == {"endpoint": "/api/test"}
            assert legacy_counter.value == 5.0
            assert legacy_counter.tags == {"endpoint": "/api/test"}

            # Histogram events (should only have canonical since names are same)
            histogram_events = [e for e in events if "duration_ms" in e.name]
            assert len(histogram_events) == 1
            assert histogram_events[0].name == "test_duration_ms"

    def test_single_emission_mode(self):
        """Test single-emission mode when dual-emission is disabled."""
        registry = MetricRegistry()

        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "false"}):
            # Verify dual-emission is disabled
            assert not is_dual_emission_enabled()

            # Create aliased counter with different names
            counter = create_aliased_counter(
                registry, canonical_name="test_requests_total", legacy_name="legacy_requests_total"
            )

            # Increment counter
            counter.inc(3.0)

            # Check events - should only have canonical
            events = registry.get_events()
            counter_events = [e for e in events if "requests_total" in e.name]
            assert len(counter_events) == 1
            assert counter_events[0].name == "test_requests_total"
            assert counter_events[0].value == 3.0

    def test_environment_variable_runtime_changes(self):
        """Test that environment variable changes are respected at runtime."""
        registry = MetricRegistry()

        # Test with dual-emission disabled
        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "false"}):
            counter1 = create_aliased_counter(registry, canonical_name="test_metric_1", legacy_name="legacy_metric_1")
            counter1.inc()

            events1 = registry.get_events()
            metric_events1 = [e for e in events1 if "metric_1" in e.name]
            assert len(metric_events1) == 1  # Only canonical

        # Clear events for next test
        registry.clear()

        # Test with dual-emission enabled
        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "true"}):
            counter2 = create_aliased_counter(registry, canonical_name="test_metric_2", legacy_name="legacy_metric_2")
            counter2.inc()

            events2 = registry.get_events()
            metric_events2 = [e for e in events2 if "metric_2" in e.name]
            assert len(metric_events2) == 2  # Both canonical and legacy

    def test_mixed_metric_types_dual_emission(self):
        """Test dual-emission with mixed metric types."""
        registry = MetricRegistry()

        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "true"}):
            # Create different metric types
            counter = create_aliased_counter(
                registry, canonical_name="api_requests_total", legacy_name="legacy_api_requests_total"
            )

            from pyfulmen.telemetry import create_aliased_gauge

            gauge = create_aliased_gauge(
                registry, canonical_name="memory_usage_bytes", legacy_name="legacy_memory_usage_bytes"
            )

            histogram = create_aliased_histogram(
                registry,
                canonical_name="response_time_ms",
                legacy_name="legacy_response_time_ms",
                buckets=[10.0, 50.0, 100.0],
            )

            # Use all metrics
            counter.inc(10)
            gauge.set(1024.0)
            histogram.observe(75.0)

            # Check all events
            events = registry.get_events()

            # Should have 6 events total (2 for each metric type)
            assert len(events) == 6

            # Counter events
            counter_events = [e for e in events if "api_requests_total" in e.name]
            assert len(counter_events) == 2

            # Gauge events
            gauge_events = [e for e in events if "memory_usage_bytes" in e.name]
            assert len(gauge_events) == 2

            # Histogram events
            histogram_events = [e for e in events if "response_time_ms" in e.name]
            assert len(histogram_events) == 2

    def test_no_legacy_name_single_emission(self):
        """Test aliased metric with no legacy name."""
        registry = MetricRegistry()

        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "true"}):
            # Create counter without legacy name
            counter = create_aliased_counter(
                registry,
                canonical_name="simple_counter",
                # No legacy_name provided
            )

            counter.inc()

            # Should only create canonical metric
            events = registry.get_events()
            assert len(events) == 1
            assert events[0].name == "simple_counter"
            assert events[0].value == 1.0
