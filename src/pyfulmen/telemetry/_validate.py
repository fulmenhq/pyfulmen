"""Schema validation for telemetry metrics events."""

from __future__ import annotations

from typing import Any

from .models import MetricEvent


def _load_metrics_taxonomy() -> dict[str, Any]:
    """Load metrics taxonomy for validation."""
    import yaml

    from ..crucible import _paths

    taxonomy_path = _paths.get_config_dir() / "taxonomy" / "metrics.yaml"
    with open(taxonomy_path) as f:
        return yaml.safe_load(f)


def _build_metric_unit_map() -> dict[str, str]:
    """Build mapping of metric names to their required units."""
    taxonomy = _load_metrics_taxonomy()
    return {metric["name"]: metric["unit"] for metric in taxonomy.get("metrics", [])}


def validate_metric_event(event: MetricEvent | dict[str, Any]) -> bool:
    """Validate metric event against schema.

    Args:
        event: MetricEvent instance or dict to validate

    Returns:
        True if valid against observability/metrics/v1.0.0/metrics-event schema
    """
    try:
        payload = (
            event.model_dump(mode="json", exclude_none=True)
            if isinstance(event, MetricEvent)
            else event
        )

        # Basic structural validation
        required_fields = ["timestamp", "name", "value"]
        for field in required_fields:
            if field not in payload:
                return False

        # Validate metric name against taxonomy
        taxonomy = _load_metrics_taxonomy()
        valid_names = [metric["name"] for metric in taxonomy.get("metrics", [])]
        if payload["name"] not in valid_names:
            return False

        # Validate unit if present
        if "unit" in payload:
            # Check unit is globally valid
            valid_units = taxonomy.get("$defs", {}).get("metricUnit", {}).get("enum", [])
            if payload["unit"] not in valid_units:
                return False

            # Check unit matches metric's declared default
            metric_unit_map = _build_metric_unit_map()
            expected_unit = metric_unit_map.get(payload["name"])
            if expected_unit and payload["unit"] != expected_unit:
                return False

        # Validate timestamp format (basic RFC3339 check)
        timestamp = payload["timestamp"]
        if not isinstance(timestamp, str) or "T" not in timestamp:
            return False

        # Validate value type
        value = payload["value"]
        if not isinstance(value, (int, float, dict)):
            return False

        # If value is dict, validate histogram structure
        if isinstance(value, dict):
            required_hist_fields = ["count", "sum", "buckets"]
            for field in required_hist_fields:
                if field not in value:
                    return False
            if not isinstance(value["count"], int) or value["count"] < 0:
                return False
            if not isinstance(value["sum"], (int, float)):
                return False
            if not isinstance(value["buckets"], list):
                return False

            # Validate each bucket structure
            for bucket in value["buckets"]:
                if not isinstance(bucket, dict):
                    return False
                required_bucket_fields = ["le", "count"]
                for field in required_bucket_fields:
                    if field not in bucket:
                        return False
                if not isinstance(bucket["le"], (int, float)):
                    return False
                if not isinstance(bucket["count"], int) or bucket["count"] < 0:
                    return False

        return True

    except Exception:
        return False


def validate_metric_events(events: list[MetricEvent | dict[str, Any]]) -> bool:
    """Validate multiple metric events against schema.

    Args:
        events: List of MetricEvent instances or dicts to validate

    Returns:
        True if all events are valid
    """
    return all(validate_metric_event(event) for event in events)


__all__ = [
    "validate_metric_event",
    "validate_metric_events",
]
