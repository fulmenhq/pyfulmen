"""
Telemetry module.

Provides metrics instrumentation for FulmenHQ ecosystem applications.

This module implements Phase 2 (module-level helpers) of v0.1.6 telemetry rollout.

Simple Usage (default registry):
    >>> from pyfulmen.telemetry import counter, histogram, gauge
    >>> counter("requests_total").inc()
    >>> gauge("memory_usage_bytes").set(1024)
    >>> histogram("request_duration_ms").observe(123.5)

Advanced Usage (custom registry):
    >>> from pyfulmen.telemetry import MetricRegistry
    >>> registry = MetricRegistry()
    >>> counter = registry.counter("requests_total")
    >>> counter.inc()

Testing (isolated registry):
    >>> from pyfulmen.telemetry import MetricRegistry, clear_metrics
    >>> test_registry = MetricRegistry()
    >>> test_counter = test_registry.counter("test_metric")
    >>> test_counter.inc()
    >>> events = test_registry.get_events()  # Isolated from default registry
"""

from ._alias import (
    AliasedMetric,
    create_aliased_counter,
    create_aliased_gauge,
    create_aliased_histogram,
    is_dual_emission_enabled,
)
from ._exporter_metrics import ExporterMetrics, RefreshContext
from ._registry import (
    MetricRegistry,
    clear_metrics,
    counter,
    drain_events,
    gauge,
    get_events,
    histogram,
)
from ._validate import validate_metric_event, validate_metric_events, validate_metric_name
from .models import HistogramBucket, HistogramSummary, MetricEvent

__all__ = [
    # Core classes
    "MetricRegistry",
    "MetricEvent",
    "HistogramSummary",
    "HistogramBucket",
    # Helper functions (default registry)
    "counter",
    "gauge",
    "histogram",
    "get_events",
    "drain_events",
    "clear_metrics",
    # Validation functions
    "validate_metric_event",
    "validate_metric_events",
    "validate_metric_name",
    # Exporter instrumentation
    "ExporterMetrics",
    "RefreshContext",
    # Alias system for dual-emission
    "AliasedMetric",
    "create_aliased_counter",
    "create_aliased_gauge",
    "create_aliased_histogram",
    "is_dual_emission_enabled",
]
