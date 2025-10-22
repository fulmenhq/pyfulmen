"""
Tests for telemetry._registry

Covers MetricRegistry get-or-create behavior and thread-safety.
"""

import threading

from pyfulmen.telemetry import MetricRegistry


class TestMetricRegistry:
    """Tests for MetricRegistry."""

    def test_registry_creation(self):
        """Test creating a registry."""
        registry = MetricRegistry()

        assert registry is not None
        assert len(registry.get_events()) == 0

    def test_counter_get_or_create(self):
        """Test registry returns same counter for same name."""
        registry = MetricRegistry()

        counter1 = registry.counter("test")
        counter2 = registry.counter("test")

        assert counter1 is counter2

    def test_counter_different_names(self):
        """Test registry returns different counters for different names."""
        registry = MetricRegistry()

        counter1 = registry.counter("test1")
        counter2 = registry.counter("test2")

        assert counter1 is not counter2
        assert counter1.name == "test1"
        assert counter2.name == "test2"

    def test_gauge_get_or_create(self):
        """Test registry returns same gauge for same name."""
        registry = MetricRegistry()

        gauge1 = registry.gauge("test")
        gauge2 = registry.gauge("test")

        assert gauge1 is gauge2

    def test_gauge_different_names(self):
        """Test registry returns different gauges for different names."""
        registry = MetricRegistry()

        gauge1 = registry.gauge("test1")
        gauge2 = registry.gauge("test2")

        assert gauge1 is not gauge2
        assert gauge1.name == "test1"
        assert gauge2.name == "test2"

    def test_histogram_get_or_create(self):
        """Test registry returns same histogram for same name."""
        registry = MetricRegistry()

        hist1 = registry.histogram("test")
        hist2 = registry.histogram("test")

        assert hist1 is hist2

    def test_histogram_different_names(self):
        """Test registry returns different histograms for different names."""
        registry = MetricRegistry()

        hist1 = registry.histogram("test1")
        hist2 = registry.histogram("test2")

        assert hist1 is not hist2
        assert hist1.name == "test1"
        assert hist2.name == "test2"

    def test_histogram_with_custom_buckets(self):
        """Test histogram created with custom buckets."""
        registry = MetricRegistry()
        custom_buckets = [10.0, 20.0, 30.0]

        hist = registry.histogram("test", buckets=custom_buckets)

        assert hist.buckets == custom_buckets

    def test_record_events(self):
        """Test registry records events."""
        registry = MetricRegistry()
        counter = registry.counter("test")

        counter.inc()
        counter.inc()

        events = registry.get_events()
        assert len(events) == 2

    def test_get_events_returns_copy(self):
        """Test get_events returns a copy."""
        registry = MetricRegistry()
        counter = registry.counter("test")
        counter.inc()

        events1 = registry.get_events()
        events2 = registry.get_events()

        assert events1 == events2
        assert events1 is not events2

    def test_clear_registry(self):
        """Test clearing registry."""
        registry = MetricRegistry()
        counter = registry.counter("test")
        counter.inc()

        assert len(registry.get_events()) == 1

        registry.clear()

        assert len(registry.get_events()) == 0
        assert len(registry._counters) == 0

    def test_mixed_instruments(self):
        """Test registry with multiple instrument types."""
        registry = MetricRegistry()

        counter = registry.counter("requests")
        gauge = registry.gauge("queue_depth")
        hist = registry.histogram("latency")

        counter.inc()
        gauge.set(42)
        hist.observe(123.4)

        events = registry.get_events()
        assert len(events) == 3

    def test_concurrent_counter_creation(self):
        """Test concurrent counter creation is thread-safe."""
        registry = MetricRegistry()
        counters = []

        def create_counter():
            c = registry.counter("test")
            counters.append(c)

        threads = [threading.Thread(target=create_counter) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should get the same counter instance
        assert len({id(c) for c in counters}) == 1

    def test_concurrent_event_recording(self):
        """Test concurrent event recording is thread-safe."""
        registry = MetricRegistry()
        counter = registry.counter("test")

        def increment():
            for _ in range(100):
                counter.inc()

        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        events = registry.get_events()
        assert len(events) == 1000
