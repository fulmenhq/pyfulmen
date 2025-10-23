"""
Metric registry.

Thread-safe singleton registry for managing metric instruments.
"""

import threading

from ._instruments import Counter, Gauge, Histogram
from .models import MetricEvent


class MetricRegistry:
    """Thread-safe metric registry.

    Singleton registry for creating and tracking metric instruments.
    All operations are thread-safe via locking.

    Example:
        >>> registry = MetricRegistry()
        >>> counter = registry.counter("requests_total")
        >>> counter.inc()
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._events: list[MetricEvent] = []
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = threading.Lock()

    def counter(self, name: str) -> Counter:
        """Get or create counter.

        Args:
            name: Metric name

        Returns:
            Counter instrument
        """
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, self)
            return self._counters[name]

    def gauge(self, name: str) -> Gauge:
        """Get or create gauge.

        Args:
            name: Metric name

        Returns:
            Gauge instrument
        """
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, self)
            return self._gauges[name]

    def histogram(self, name: str, buckets: list[float] | None = None) -> Histogram:
        """Get or create histogram.

        Args:
            name: Metric name
            buckets: Custom bucket boundaries (optional)

        Returns:
            Histogram instrument
        """
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, self, buckets)
            return self._histograms[name]

    def _record(self, event: MetricEvent) -> None:
        """Record metric event (internal).

        Args:
            event: MetricEvent to record
        """
        with self._lock:
            self._events.append(event)

    def get_events(self) -> list[MetricEvent]:
        """Get all recorded events.

        Returns:
            List of MetricEvent instances
        """
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        """Clear all events and instruments."""
        with self._lock:
            self._events.clear()
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
