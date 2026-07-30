"""
Metric instruments.

Provides Counter, Gauge, and Histogram instruments for telemetry.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from ._validate import _build_metric_unit_map
from .models import HistogramBucket, HistogramSummary, MetricEvent

if TYPE_CHECKING:
    from ._registry import MetricRegistry


def _unit_for(name: str) -> str:
    """Resolve the taxonomy-declared unit for a metric name.

    Falls back to "count" for names outside the taxonomy or if the
    taxonomy cannot be loaded (telemetry must never break the host app).
    """
    try:
        return _build_metric_unit_map().get(name, "count")
    except Exception:
        return "count"


class Counter:
    """Monotonically increasing counter.

    Thread-safe counter that only increases. Useful for counting events,
    requests, errors, etc.

    Example:
        >>> registry = MetricRegistry()
        >>> counter = registry.counter("requests_total")
        >>> counter.inc()
        >>> counter.inc(5)
    """

    def __init__(self, name: str, registry: MetricRegistry) -> None:
        """Initialize counter.

        Args:
            name: Metric name
            registry: Parent registry
        """
        self.name = name
        self.registry = registry
        self._value = 0.0
        self._lock = threading.Lock()

    def inc(self, delta: float = 1.0, tags: dict[str, str] | None = None) -> None:
        """Increment counter by delta.

        Args:
            delta: Amount to increment (must be >= 0)
            tags: Optional tags for this metric event

        Raises:
            ValueError: If delta is negative
        """
        if delta < 0:
            msg = "Counter delta must be >= 0"
            raise ValueError(msg)

        with self._lock:
            self._value += delta
            current_value = self._value

        self.registry._record(
            MetricEvent(
                timestamp=datetime.now(UTC),
                name=self.name,
                value=current_value,
                unit=_unit_for(self.name),
                tags=tags,
            )
        )


class Gauge:
    """Instantaneous gauge value.

    Gauge that can increase and decrease. Useful for measuring current values
    like memory usage, queue depth, etc.

    Example:
        >>> registry = MetricRegistry()
        >>> gauge = registry.gauge("queue_depth")
        >>> gauge.set(42)
    """

    def __init__(self, name: str, registry: MetricRegistry) -> None:
        """Initialize gauge.

        Args:
            name: Metric name
            registry: Parent registry
        """
        self.name = name
        self.registry = registry

    def set(self, value: float, tags: dict[str, str] | None = None) -> None:
        """Set gauge to value.

        Args:
            value: New gauge value
            tags: Optional tags for this metric event
        """
        self.registry._record(MetricEvent(timestamp=datetime.now(UTC), name=self.name, value=value, tags=tags))


class Histogram:
    """Histogram with configurable buckets.

    Tracks distribution of values using OTLP-compatible buckets.

    Example:
        >>> registry = MetricRegistry()
        >>> hist = registry.histogram("request_duration_ms")
        >>> hist.observe(42.5)
        >>> hist.observe(123.7)
    """

    DEFAULT_BUCKETS = [1, 5, 10, 50, 100, 500, 1000, 5000, 10000]

    def __init__(
        self,
        name: str,
        registry: MetricRegistry,
        buckets: list[float] | None = None,
    ) -> None:
        """Initialize histogram.

        Args:
            name: Metric name
            registry: Parent registry
            buckets: Custom bucket boundaries (defaults to DEFAULT_BUCKETS)
        """
        self.name = name
        self.registry = registry
        self.buckets = sorted(buckets) if buckets else self.DEFAULT_BUCKETS
        self._count = 0
        self._sum = 0.0
        self._bucket_counts = [0] * len(self.buckets)
        self._lock = threading.Lock()

    def observe(self, value: float, tags: dict[str, str] | None = None) -> None:
        """Record observation in histogram.

        Bucket state is maintained incrementally, so each observation is
        O(number of buckets) regardless of how many observations have been
        recorded.

        Args:
            value: Observed value
            tags: Optional tags for this metric event
        """
        with self._lock:
            self._count += 1
            self._sum += value
            for i, upper_bound in enumerate(self.buckets):
                if value <= upper_bound:
                    self._bucket_counts[i] += 1
            summary = self._create_summary()

        self.registry._record(
            MetricEvent(
                timestamp=datetime.now(UTC),
                name=self.name,
                value=summary,
                unit="ms" if "ms" in self.name else ("s" if "seconds" in self.name else None),
                tags=tags,
            )
        )

    def _create_summary(self) -> HistogramSummary:
        """Create histogram summary from the incremental bucket state.

        Returns:
            HistogramSummary with cumulative bucket counts
        """
        buckets = [
            HistogramBucket(le=upper_bound, count=count)
            for upper_bound, count in zip(self.buckets, self._bucket_counts, strict=True)
        ]
        buckets.append(HistogramBucket(le=float("inf"), count=self._count))

        return HistogramSummary(count=self._count, sum=self._sum, buckets=buckets)
