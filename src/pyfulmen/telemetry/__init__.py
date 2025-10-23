"""
Telemetry module.

Provides metrics instrumentation for FulmenHQ ecosystem applications.

This module implements Phase 1 (Days 3-4) of the v0.1.6 error/telemetry rollout.

Example:
    >>> from pyfulmen.telemetry import MetricRegistry
    >>> registry = MetricRegistry()
    >>> counter = registry.counter("requests_total")
    >>> counter.inc()
    >>>
    >>> gauge = registry.gauge("queue_depth")
    >>> gauge.set(42)
    >>>
    >>> hist = registry.histogram("request_duration_ms")
    >>> hist.observe(123.5)
"""

from ._registry import MetricRegistry
from ._validate import validate_metric_event, validate_metric_events
from .models import HistogramBucket, HistogramSummary, MetricEvent

__all__ = [
    "MetricRegistry",
    "MetricEvent",
    "HistogramSummary",
    "HistogramBucket",
    "validate_metric_event",
    "validate_metric_events",
]
