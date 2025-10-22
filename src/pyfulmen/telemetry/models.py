"""
Telemetry data models.

Provides models for metrics events conforming to Crucible standards.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class HistogramBucket(BaseModel):
    """OTLP-compatible histogram bucket.

    Attributes:
        le: Upper bound (less-than-or-equal)
        count: Cumulative count of observations <= le
    """

    model_config = ConfigDict(frozen=True)

    le: float
    count: int


class HistogramSummary(BaseModel):
    """Histogram value with buckets.

    Attributes:
        count: Total number of observations
        sum: Sum of all observed values
        buckets: List of cumulative buckets
    """

    model_config = ConfigDict(frozen=True)

    count: int
    sum: float
    buckets: list[HistogramBucket]


class MetricEvent(BaseModel):
    """Telemetry metric event.

    Conforms to schemas/observability/metrics/v1.0.0/metrics-event.schema.json

    Attributes:
        timestamp: Event timestamp (UTC)
        name: Metric name (must be in metrics taxonomy)
        value: Metric value (number or histogram)
        tags: Optional key-value tags
        unit: Optional unit of measurement
    """

    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    name: str
    value: float | int | HistogramSummary
    tags: dict[str, str] | None = None
    unit: str | None = None

    def model_post_init(self, __context: Any) -> None:
        """Set default timestamp if not provided."""
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.now(UTC))
