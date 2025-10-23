"""
Tests for telemetry.models

Covers MetricEvent, HistogramSummary, and HistogramBucket models.
"""

from datetime import UTC, datetime

import pytest

from pyfulmen.telemetry.models import HistogramBucket, HistogramSummary, MetricEvent


class TestHistogramBucket:
    """Tests for HistogramBucket model."""

    def test_basic_bucket(self):
        """Test creating histogram bucket."""
        bucket = HistogramBucket(le=10.0, count=5)

        assert bucket.le == 10.0
        assert bucket.count == 5

    def test_bucket_is_frozen(self):
        """Test bucket is immutable."""
        bucket = HistogramBucket(le=10.0, count=5)

        with pytest.raises(Exception):
            bucket.le = 20.0

    def test_inf_bucket(self):
        """Test +Inf bucket."""
        bucket = HistogramBucket(le=float("inf"), count=100)

        assert bucket.le == float("inf")
        assert bucket.count == 100


class TestHistogramSummary:
    """Tests for HistogramSummary model."""

    def test_basic_summary(self):
        """Test creating histogram summary."""
        buckets = [
            HistogramBucket(le=10.0, count=5),
            HistogramBucket(le=50.0, count=10),
            HistogramBucket(le=float("inf"), count=12),
        ]
        summary = HistogramSummary(count=12, sum=150.5, buckets=buckets)

        assert summary.count == 12
        assert summary.sum == 150.5
        assert len(summary.buckets) == 3

    def test_summary_is_frozen(self):
        """Test summary is immutable."""
        buckets = [HistogramBucket(le=10.0, count=5)]
        summary = HistogramSummary(count=5, sum=25.0, buckets=buckets)

        with pytest.raises(Exception):
            summary.count = 10

    def test_empty_buckets(self):
        """Test summary with no buckets."""
        summary = HistogramSummary(count=0, sum=0.0, buckets=[])

        assert summary.count == 0
        assert summary.sum == 0.0
        assert len(summary.buckets) == 0


class TestMetricEvent:
    """Tests for MetricEvent model."""

    def test_minimal_event(self):
        """Test creating minimal metric event."""
        ts = datetime.now(UTC)
        event = MetricEvent(timestamp=ts, name="test_metric", value=42.5)

        assert event.timestamp == ts
        assert event.name == "test_metric"
        assert event.value == 42.5
        assert event.tags is None
        assert event.unit is None

    def test_event_with_all_fields(self):
        """Test creating event with all fields."""
        ts = datetime.now(UTC)
        tags = {"env": "prod", "service": "api"}
        event = MetricEvent(
            timestamp=ts, name="requests_total", value=1000, tags=tags, unit="count"
        )

        assert event.timestamp == ts
        assert event.name == "requests_total"
        assert event.value == 1000
        assert event.tags == tags
        assert event.unit == "count"

    def test_event_with_histogram_value(self):
        """Test event with histogram summary value."""
        ts = datetime.now(UTC)
        buckets = [HistogramBucket(le=10.0, count=5)]
        summary = HistogramSummary(count=5, sum=25.0, buckets=buckets)
        event = MetricEvent(timestamp=ts, name="request_duration_ms", value=summary)

        assert event.timestamp == ts
        assert event.name == "request_duration_ms"
        assert isinstance(event.value, HistogramSummary)
        assert event.value.count == 5

    def test_event_with_int_value(self):
        """Test event with integer value."""
        ts = datetime.now(UTC)
        event = MetricEvent(timestamp=ts, name="queue_depth", value=42)

        assert event.value == 42
        assert isinstance(event.value, int)

    def test_event_with_float_value(self):
        """Test event with float value."""
        ts = datetime.now(UTC)
        event = MetricEvent(timestamp=ts, name="cpu_usage", value=75.5)

        assert event.value == 75.5
        assert isinstance(event.value, float)

    def test_event_is_frozen(self):
        """Test event is immutable."""
        ts = datetime.now(UTC)
        event = MetricEvent(timestamp=ts, name="test", value=1.0)

        with pytest.raises(Exception):
            event.value = 2.0

    def test_event_serialization(self):
        """Test event can be serialized to dict."""
        ts = datetime.now(UTC)
        tags = {"env": "test"}
        event = MetricEvent(timestamp=ts, name="test_metric", value=123.4, tags=tags, unit="ms")

        data = event.model_dump()

        assert data["name"] == "test_metric"
        assert data["value"] == 123.4
        assert data["tags"] == tags
        assert data["unit"] == "ms"
