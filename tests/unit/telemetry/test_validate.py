"""Tests for telemetry schema validation."""

from datetime import UTC, datetime

from pyfulmen.telemetry._validate import validate_metric_event, validate_metric_events
from pyfulmen.telemetry.models import HistogramBucket, HistogramSummary, MetricEvent


class TestMetricEventValidation:
    """Test MetricEvent schema validation."""

    def test_valid_scalar_metric(self) -> None:
        """Test validation of valid scalar metric."""
        event = MetricEvent(
            timestamp=datetime.now(UTC),
            name="schema_validations",
            value=42,
            unit="count",
        )

        assert validate_metric_event(event) is True

    def test_valid_histogram_metric(self) -> None:
        """Test validation of valid histogram metric."""
        event = MetricEvent(
            timestamp=datetime.now(UTC),
            name="config_load_ms",
            value=HistogramSummary(
                count=5,
                sum=125.5,
                buckets=[
                    HistogramBucket(le=10, count=1),
                    HistogramBucket(le=50, count=3),
                    HistogramBucket(le=100, count=4),
                    HistogramBucket(le=float("inf"), count=5),
                ],
            ),
            unit="ms",
        )

        assert validate_metric_event(event) is True

    def test_invalid_metric_name(self) -> None:
        """Test validation fails with invalid metric name."""
        event = MetricEvent(
            timestamp=datetime.now(UTC),
            name="invalid_metric_name",
            value=42,
            unit="count",
        )

        assert validate_metric_event(event) is False

    def test_invalid_unit(self) -> None:
        """Test validation fails with invalid unit."""
        event = MetricEvent(
            timestamp=datetime.now(UTC),
            name="schema_validations",
            value=42,
            unit="invalid_unit",
        )

        assert validate_metric_event(event) is False

    def test_missing_required_fields(self) -> None:
        """Test validation fails with missing required fields."""
        # Missing timestamp
        event_dict = {
            "name": "schema_validations",
            "value": 42,
            "unit": "count",
        }

        assert validate_metric_event(event_dict) is False

    def test_invalid_histogram_structure(self) -> None:
        """Test validation fails with invalid histogram structure."""
        event = MetricEvent(
            timestamp=datetime.now(UTC),
            name="config_load_ms",
            value=HistogramSummary(
                count=-1,  # Invalid negative count
                sum=125.5,
                buckets=[],
            ),
            unit="ms",
        )

        assert validate_metric_event(event) is False

    def test_validate_multiple_events(self) -> None:
        """Test validation of multiple events."""
        valid_event = MetricEvent(
            timestamp=datetime.now(UTC),
            name="schema_validations",
            value=42,
            unit="count",
        )

        invalid_event = MetricEvent(
            timestamp=datetime.now(UTC),
            name="invalid_metric",
            value=42,
            unit="count",
        )

        # All valid
        assert validate_metric_events([valid_event, valid_event]) is True

        # One invalid
        assert validate_metric_events([valid_event, invalid_event]) is False

        # Empty list should be valid
        assert validate_metric_events([]) is True

    def test_dict_input_validation(self) -> None:
        """Test validation works with dict input."""
        valid_dict = {
            "timestamp": "2025-10-22T21:36:46.413750Z",
            "name": "schema_validations",
            "value": 42,
            "unit": "count",
        }

        invalid_dict = {
            "timestamp": "2025-10-22T21:36:46.413750Z",
            "name": "invalid_metric",
            "value": 42,
            "unit": "count",
        }

        assert validate_metric_event(valid_dict) is True
        assert validate_metric_event(invalid_dict) is False

    def test_unit_mismatch_regression(self) -> None:
        """Test validation rejects unit mismatch with metric's declared default."""
        # schema_validations should have unit="count", not "ms"
        event = MetricEvent(
            timestamp=datetime.now(UTC),
            name="schema_validations",
            value=42,
            unit="ms",  # Wrong unit for this metric
        )

        assert validate_metric_event(event) is False

        # config_load_ms should have unit="ms", not "count"
        event2 = MetricEvent(
            timestamp=datetime.now(UTC),
            name="config_load_ms",
            value=125.5,
            unit="count",  # Wrong unit for this metric
        )

        assert validate_metric_event(event2) is False

    def test_invalid_histogram_bucket_structure(self) -> None:
        """Test validation rejects invalid histogram bucket structures."""
        # Non-dict bucket (use dict input to bypass Pydantic validation)
        event1_dict = {
            "timestamp": "2025-10-22T21:36:46.413750Z",
            "name": "config_load_ms",
            "value": {
                "count": 2,
                "sum": 125.5,
                "buckets": ["not_a_dict", "also_not_a_dict"],  # Invalid: strings instead of dicts
            },
            "unit": "ms",
        }

        assert validate_metric_event(event1_dict) is False

        # Missing required bucket fields
        event2_dict = {
            "timestamp": "2025-10-22T21:36:46.413750Z",
            "name": "config_load_ms",
            "value": {
                "count": 2,
                "sum": 125.5,
                "buckets": [
                    {"le": 10},  # Missing "count"
                    {"count": 1},  # Missing "le"
                ],
            },
            "unit": "ms",
        }

        assert validate_metric_event(event2_dict) is False

        # Invalid bucket field types
        event3_dict = {
            "timestamp": "2025-10-22T21:36:46.413750Z",
            "name": "config_load_ms",
            "value": {
                "count": 2,
                "sum": 125.5,
                "buckets": [
                    {"le": "not_a_number", "count": 1},  # Invalid: le is string
                    {"le": 50, "count": -1},  # Invalid: negative count
                ],
            },
            "unit": "ms",
        }

        assert validate_metric_event(event3_dict) is False

    def test_new_taxonomy_metrics(self) -> None:
        """Test validation accepts new metrics from taxonomy update."""
        # config_load_errors (count)
        event1 = MetricEvent(
            timestamp=datetime.now(UTC),
            name="config_load_errors",
            value=3,
            unit="count",
        )
        assert validate_metric_event(event1) is True

        # pathfinder_find_ms (ms)
        event2 = MetricEvent(
            timestamp=datetime.now(UTC),
            name="pathfinder_find_ms",
            value=12.5,
            unit="ms",
        )
        assert validate_metric_event(event2) is True

        # pathfinder_validation_errors (count)
        event3 = MetricEvent(
            timestamp=datetime.now(UTC),
            name="pathfinder_validation_errors",
            value=2,
            unit="count",
        )
        assert validate_metric_event(event3) is True

        # pathfinder_security_warnings (count)
        event4 = MetricEvent(
            timestamp=datetime.now(UTC),
            name="pathfinder_security_warnings",
            value=1,
            unit="count",
        )
        assert validate_metric_event(event4) is True

        # Verify unit mismatch still fails for new metrics
        invalid_event = MetricEvent(
            timestamp=datetime.now(UTC),
            name="pathfinder_find_ms",
            value=12.5,
            unit="count",  # Wrong unit (should be ms)
        )
        assert validate_metric_event(invalid_event) is False
