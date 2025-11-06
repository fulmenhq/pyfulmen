"""
Metric registry.

Thread-safe registry for managing metric instruments.
"""

import threading

from ._instruments import Counter, Gauge, Histogram
from .models import MetricEvent


class MetricRegistry:
    """Thread-safe metric registry.

    Registry for creating and tracking metric instruments.
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

    def drain_events(self) -> list[MetricEvent]:
        """Get and clear all recorded events.

        This method consumes all events and clears the internal buffer,
        preventing memory leaks in long-running applications.

        Returns:
            List of MetricEvent instances that were consumed
        """
        with self._lock:
            events = list(self._events)
            self._events.clear()
            return events

    def clear(self) -> None:
        """Clear all events and instruments."""
        with self._lock:
            self._events.clear()
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


# Global default registry singleton for simple use cases
_default_registry = MetricRegistry()


def counter(name: str) -> Counter:
    """Get or create a counter from the default registry.

    This is a convenience function that uses the global default registry.
    For testing or advanced use cases, create a MetricRegistry instance directly.

    Args:
        name: Counter name

    Returns:
        Counter instrument from default registry

    Example:
        >>> from pyfulmen.telemetry import counter
        >>> c = counter("requests_total")
        >>> c.inc()
    """
    return _default_registry.counter(name)


def gauge(name: str) -> Gauge:
    """Get or create a gauge from the default registry.

    This is a convenience function that uses the global default registry.
    For testing or advanced use cases, create a MetricRegistry instance directly.

    Args:
        name: Gauge name

    Returns:
        Gauge instrument from default registry

    Example:
        >>> from pyfulmen.telemetry import gauge
        >>> g = gauge("memory_usage_bytes")
        >>> g.set(1024)
    """
    return _default_registry.gauge(name)


def histogram(name: str, buckets: list[float] | None = None) -> Histogram:
    """Get or create a histogram from the default registry.

    This is a convenience function that uses the global default registry.
    For testing or advanced use cases, create a MetricRegistry instance directly.

    Args:
        name: Histogram name
        buckets: Custom bucket boundaries (optional)

    Returns:
        Histogram instrument from default registry

    Example:
        >>> from pyfulmen.telemetry import histogram
        >>> h = histogram("request_duration_ms")
        >>> h.observe(42.5)
    """
    return _default_registry.histogram(name, buckets)


def get_events() -> list[MetricEvent]:
    """Get all events from the default registry.

    This is a convenience function that uses the global default registry.
    For testing or advanced use cases, create a MetricRegistry instance directly.

    Returns:
        List of MetricEvent instances from default registry

    Example:
        >>> from pyfulmen.telemetry import get_events
        >>> events = get_events()
        >>> len(events)
        3
    """
    return _default_registry.get_events()


def drain_events() -> list[MetricEvent]:
    """Get and clear all events from the default registry.

    This is a convenience function that uses the global default registry.
    For testing or advanced use cases, create a MetricRegistry instance directly.

    Returns:
        List of MetricEvent instances that were consumed from default registry

    Example:
        >>> from pyfulmen.telemetry import drain_events
        >>> events = drain_events()
        >>> len(events)
        3
        >>> # Events are now cleared from default registry
        >>> len(get_events())
        0
    """
    return _default_registry.drain_events()


def clear_metrics() -> None:
    """Clear all events and instruments from the default registry.

    This is a convenience function that uses the global default registry.
    For testing or advanced use cases, create a MetricRegistry instance directly.

    Example:
        >>> from pyfulmen.telemetry import clear_metrics
        >>> clear_metrics()
        >>> # Default registry is now empty
    """
    _default_registry.clear()
