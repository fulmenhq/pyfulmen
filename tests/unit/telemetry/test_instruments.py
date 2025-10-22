"""
Tests for telemetry._instruments

Covers Counter, Gauge, and Histogram instruments.
"""

import threading

import pytest

from pyfulmen.telemetry import MetricRegistry
from pyfulmen.telemetry.models import HistogramSummary


class TestCounter:
    """Tests for Counter instrument."""

    def test_counter_inc_default(self):
        """Test counter increment with default delta."""
        registry = MetricRegistry()
        counter = registry.counter("test_counter")

        counter.inc()

        events = registry.get_events()
        assert len(events) == 1
        assert events[0].value == 1.0

    def test_counter_inc_custom_delta(self):
        """Test counter increment with custom delta."""
        registry = MetricRegistry()
        counter = registry.counter("test_counter")

        counter.inc(5.5)

        events = registry.get_events()
        assert events[0].value == 5.5

    def test_counter_multiple_increments(self):
        """Test counter with multiple increments."""
        registry = MetricRegistry()
        counter = registry.counter("test_counter")

        counter.inc()
        counter.inc(2.0)
        counter.inc(3.0)

        events = registry.get_events()
        assert len(events) == 3
        assert events[0].value == 1.0
        assert events[1].value == 3.0
        assert events[2].value == 6.0

    def test_counter_negative_delta_raises(self):
        """Test counter rejects negative delta."""
        registry = MetricRegistry()
        counter = registry.counter("test_counter")

        with pytest.raises(ValueError, match="Counter delta must be >= 0"):
            counter.inc(-1.0)

    def test_counter_has_count_unit(self):
        """Test counter events have count unit."""
        registry = MetricRegistry()
        counter = registry.counter("test_counter")

        counter.inc()

        events = registry.get_events()
        assert events[0].unit == "count"

    def test_counter_thread_safety(self):
        """Test counter is thread-safe."""
        registry = MetricRegistry()
        counter = registry.counter("test_counter")

        def increment():
            for _ in range(100):
                counter.inc()

        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        events = registry.get_events()
        final_value = events[-1].value
        assert final_value == 1000.0


class TestGauge:
    """Tests for Gauge instrument."""

    def test_gauge_set(self):
        """Test gauge set value."""
        registry = MetricRegistry()
        gauge = registry.gauge("test_gauge")

        gauge.set(42.5)

        events = registry.get_events()
        assert len(events) == 1
        assert events[0].value == 42.5

    def test_gauge_multiple_sets(self):
        """Test gauge with multiple set operations."""
        registry = MetricRegistry()
        gauge = registry.gauge("test_gauge")

        gauge.set(10.0)
        gauge.set(20.0)
        gauge.set(15.0)

        events = registry.get_events()
        assert len(events) == 3
        assert events[0].value == 10.0
        assert events[1].value == 20.0
        assert events[2].value == 15.0

    def test_gauge_can_decrease(self):
        """Test gauge value can decrease."""
        registry = MetricRegistry()
        gauge = registry.gauge("test_gauge")

        gauge.set(100.0)
        gauge.set(50.0)

        events = registry.get_events()
        assert events[0].value == 100.0
        assert events[1].value == 50.0

    def test_gauge_no_unit(self):
        """Test gauge has no default unit."""
        registry = MetricRegistry()
        gauge = registry.gauge("test_gauge")

        gauge.set(42)

        events = registry.get_events()
        assert events[0].unit is None


class TestHistogram:
    """Tests for Histogram instrument."""

    def test_histogram_single_observation(self):
        """Test histogram with single observation."""
        registry = MetricRegistry()
        hist = registry.histogram("test_hist")

        hist.observe(42.5)

        events = registry.get_events()
        assert len(events) == 1
        assert isinstance(events[0].value, HistogramSummary)
        assert events[0].value.count == 1
        assert events[0].value.sum == 42.5

    def test_histogram_multiple_observations(self):
        """Test histogram with multiple observations."""
        registry = MetricRegistry()
        hist = registry.histogram("test_hist")

        hist.observe(10.0)
        hist.observe(50.0)
        hist.observe(25.0)

        events = registry.get_events()
        last_event = events[-1]
        assert last_event.value.count == 3
        assert last_event.value.sum == 85.0

    def test_histogram_default_buckets(self):
        """Test histogram uses default buckets."""
        registry = MetricRegistry()
        hist = registry.histogram("test_hist")

        hist.observe(42.5)

        events = registry.get_events()
        summary = events[0].value
        assert len(summary.buckets) == 10  # 9 default + inf

    def test_histogram_custom_buckets(self):
        """Test histogram with custom buckets."""
        registry = MetricRegistry()
        custom_buckets = [10.0, 20.0, 30.0]
        hist = registry.histogram("test_hist", buckets=custom_buckets)

        hist.observe(15.0)

        events = registry.get_events()
        summary = events[0].value
        assert len(summary.buckets) == 4  # 3 custom + inf
        assert summary.buckets[0].le == 10.0
        assert summary.buckets[1].le == 20.0
        assert summary.buckets[2].le == 30.0
        assert summary.buckets[3].le == float("inf")

    def test_histogram_bucket_counts(self):
        """Test histogram bucket cumulative counts."""
        registry = MetricRegistry()
        custom_buckets = [10.0, 50.0, 100.0]
        hist = registry.histogram("test_hist", buckets=custom_buckets)

        hist.observe(5.0)
        hist.observe(15.0)
        hist.observe(75.0)
        hist.observe(150.0)

        events = registry.get_events()
        summary = events[-1].value

        assert summary.buckets[0].count == 1  # <= 10.0
        assert summary.buckets[1].count == 2  # <= 50.0
        assert summary.buckets[2].count == 3  # <= 100.0
        assert summary.buckets[3].count == 4  # <= inf

    def test_histogram_inf_bucket(self):
        """Test histogram includes +Inf bucket."""
        registry = MetricRegistry()
        hist = registry.histogram("test_hist")

        hist.observe(99999.0)

        events = registry.get_events()
        summary = events[0].value
        last_bucket = summary.buckets[-1]
        assert last_bucket.le == float("inf")
        assert last_bucket.count == 1

    def test_histogram_ms_unit_inference(self):
        """Test histogram infers ms unit from name."""
        registry = MetricRegistry()
        hist = registry.histogram("request_duration_ms")

        hist.observe(123.4)

        events = registry.get_events()
        assert events[0].unit == "ms"

    def test_histogram_no_unit_without_ms(self):
        """Test histogram has no unit without ms in name."""
        registry = MetricRegistry()
        hist = registry.histogram("response_size")

        hist.observe(1024.0)

        events = registry.get_events()
        assert events[0].unit is None

    def test_histogram_thread_safety(self):
        """Test histogram is thread-safe."""
        registry = MetricRegistry()
        hist = registry.histogram("test_hist")

        def observe():
            for i in range(10):
                hist.observe(float(i))

        threads = [threading.Thread(target=observe) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        events = registry.get_events()
        final_summary = events[-1].value
        assert final_summary.count == 50
