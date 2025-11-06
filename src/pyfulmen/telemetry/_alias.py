"""
Telemetry alias system for dual-emission support.

Provides backward compatibility during metric migration by emitting both
legacy and canonical metric names behind a feature flag.
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._instruments import Counter, Gauge, Histogram
    from ._registry import MetricRegistry

def _is_dual_emission_enabled() -> bool:
    """Check if dual-emission mode is enabled.
    
    Returns:
        True if PYFULMEN_TELEMETRY_ALIAS=true, False otherwise
    """
    return os.getenv("PYFULMEN_TELEMETRY_ALIAS", "false").lower() in ("true", "1", "yes")


class AliasedMetric:
    """Wrapper that emits both legacy and canonical metrics when dual-emission is enabled.
    
    When PYFULMEN_TELEMETRY_ALIAS=true, this will create two metrics:
    - Legacy metric (original name for backward compatibility)
    - Canonical metric (taxonomy-compliant name)
    
    When disabled, only the canonical metric is created.
    """
    
    _canonical_metric: "Counter | Gauge | Histogram"
    _legacy_metric: "Counter | Gauge | Histogram | None"
    
    def __init__(
        self,
        registry: "MetricRegistry",
        canonical_name: str,
        legacy_name: str | None = None,
        metric_type: str = "counter",
        **kwargs
    ) -> None:
        """Initialize aliased metric.
        
        Args:
            registry: MetricRegistry to create metrics in
            canonical_name: Taxonomy-compliant metric name
            legacy_name: Optional legacy name for backward compatibility
            metric_type: Type of metric (counter, gauge, histogram)
            **kwargs: Additional arguments for metric creation
        """
        self._registry = registry
        self._canonical_name = canonical_name
        self._legacy_name = legacy_name
        self._metric_type = metric_type
        
        # Extract histogram buckets if present
        buckets = kwargs.pop("buckets", None)
        
        # Create canonical metric
        if metric_type == "counter":
            self._canonical_metric = registry.counter(canonical_name)
        elif metric_type == "gauge":
            self._canonical_metric = registry.gauge(canonical_name)
        elif metric_type == "histogram":
            self._canonical_metric = registry.histogram(canonical_name, buckets)
        else:
            raise ValueError(f"Unsupported metric type: {metric_type}")
        
        # Create legacy metric if dual-emission is enabled
        self._legacy_metric = None
        if _is_dual_emission_enabled() and legacy_name and legacy_name != canonical_name:
            if metric_type == "counter":
                self._legacy_metric = registry.counter(legacy_name)
            elif metric_type == "gauge":
                self._legacy_metric = registry.gauge(legacy_name)
            elif metric_type == "histogram":
                self._legacy_metric = registry.histogram(legacy_name, buckets)
    
    def inc(self, delta: float = 1.0, tags: dict[str, str] | None = None) -> None:
        """Increment counter metrics."""
        if self._metric_type != "counter":
            raise AttributeError(f"inc() not available on {self._metric_type} metric")
        
        # Type: ignore for dynamic attribute access
        self._canonical_metric.inc(delta, tags)  # type: ignore
        if self._legacy_metric:
            self._legacy_metric.inc(delta, tags)  # type: ignore
    
    def set(self, value: float, tags: dict[str, str] | None = None) -> None:
        """Set gauge metrics."""
        if self._metric_type != "gauge":
            raise AttributeError(f"set() not available on {self._metric_type} metric")
        
        # Type: ignore for dynamic attribute access
        self._canonical_metric.set(value, tags)  # type: ignore
        if self._legacy_metric:
            self._legacy_metric.set(value, tags)  # type: ignore
    
    def observe(self, value: float, tags: dict[str, str] | None = None) -> None:
        """Observe histogram metrics."""
        if self._metric_type != "histogram":
            raise AttributeError(f"observe() not available on {self._metric_type} metric")
        
        # Type: ignore for dynamic attribute access
        self._canonical_metric.observe(value, tags)  # type: ignore
        if self._legacy_metric:
            self._legacy_metric.observe(value, tags)  # type: ignore
    
    @property
    def canonical_name(self) -> str:
        """Get canonical metric name."""
        return self._canonical_name
    
    @property
    def legacy_name(self) -> str | None:
        """Get legacy metric name."""
        return self._legacy_name
    
    @property
    def is_dual_emission(self) -> bool:
        """Check if dual-emission is active."""
        return self._legacy_metric is not None


def create_aliased_counter(
    registry: "MetricRegistry",
    canonical_name: str,
    legacy_name: str | None = None,
    **kwargs
) -> AliasedMetric:
    """Create an aliased counter metric.
    
    Args:
        registry: MetricRegistry to create metrics in
        canonical_name: Taxonomy-compliant metric name
        legacy_name: Optional legacy name for backward compatibility
        **kwargs: Additional arguments for counter creation
        
    Returns:
        AliasedMetric wrapper
    """
    return AliasedMetric(registry, canonical_name, legacy_name, "counter", **kwargs)


def create_aliased_gauge(
    registry: "MetricRegistry",
    canonical_name: str,
    legacy_name: str | None = None,
    **kwargs
) -> AliasedMetric:
    """Create an aliased gauge metric.
    
    Args:
        registry: MetricRegistry to create metrics in
        canonical_name: Taxonomy-compliant metric name
        legacy_name: Optional legacy name for backward compatibility
        **kwargs: Additional arguments for gauge creation
        
    Returns:
        AliasedMetric wrapper
    """
    return AliasedMetric(registry, canonical_name, legacy_name, "gauge", **kwargs)


def create_aliased_histogram(
    registry: "MetricRegistry",
    canonical_name: str,
    legacy_name: str | None = None,
    **kwargs
) -> AliasedMetric:
    """Create an aliased histogram metric.
    
    Args:
        registry: MetricRegistry to create metrics in
        canonical_name: Taxonomy-compliant metric name
        legacy_name: Optional legacy name for backward compatibility
        **kwargs: Additional arguments for histogram creation
        
    Returns:
        AliasedMetric wrapper
    """
    return AliasedMetric(registry, canonical_name, legacy_name, "histogram", **kwargs)


def is_dual_emission_enabled() -> bool:
    """Check if dual-emission mode is enabled.
    
    Returns:
        True if PYFULMEN_TELEMETRY_ALIAS=true, False otherwise
    """
    return _is_dual_emission_enabled()


__all__ = [
    "AliasedMetric",
    "create_aliased_counter",
    "create_aliased_gauge", 
    "create_aliased_histogram",
    "is_dual_emission_enabled",
]