"""Tests for telemetry alias system."""

import os
from unittest.mock import patch

import pytest

from pyfulmen.telemetry import (
    AliasedMetric,
    HistogramSummary,
    MetricRegistry,
    create_aliased_counter,
    create_aliased_gauge,
    create_aliased_histogram,
    is_dual_emission_enabled,
)


class TestDualEmissionFlag:
    """Test dual-emission feature flag behavior."""

    def test_dual_emission_disabled_by_default(self):
        """Test that dual-emission is disabled by default."""
        assert not is_dual_emission_enabled()

    @patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "true"})
    def test_dual_emission_enabled_with_env_var(self):
        """Test that dual-emission can be enabled via environment variable."""
        assert is_dual_emission_enabled()

    @patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "1"})
    def test_dual_emission_enabled_with_numeric_1(self):
        """Test that dual-emission can be enabled with '1'."""
        assert is_dual_emission_enabled()

    @patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "yes"})
    def test_dual_emission_enabled_with_yes(self):
        """Test that dual-emission can be enabled with 'yes'."""
        assert is_dual_emission_enabled()

    @patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "false"})
    def test_dual_emission_disabled_with_false(self):
        """Test that dual-emission can be disabled with 'false'."""
        assert not is_dual_emission_enabled()


class TestAliasedMetric:
    """Test AliasedMetric wrapper functionality."""

    def test_aliased_counter_single_emission(self):
        """Test counter with only canonical metric (dual-emission disabled)."""
        registry = MetricRegistry()

        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "false"}):
            aliased = create_aliased_counter(registry, "test_counter")

            assert aliased.canonical_name == "test_counter"
            assert aliased.legacy_name is None
            assert not aliased.is_dual_emission

        # Should only create one metric
        assert len(registry._counters) == 1
        assert "test_counter" in registry._counters

    def test_aliased_counter_inc(self):
        """Test counter increment propagates to both metrics."""
        registry = MetricRegistry()

        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "true"}):
            aliased = create_aliased_counter(registry, canonical_name="canonical_counter", legacy_name="legacy_counter")

            # Increment with tags
            aliased.inc(5.0, tags={"env": "test"})

            # Check both metrics received the increment
            canonical_events = registry.get_events()
            canonical_counter_events = [e for e in canonical_events if e.name == "canonical_counter"]
            legacy_counter_events = [e for e in canonical_events if e.name == "legacy_counter"]

            assert len(canonical_counter_events) == 1
            assert canonical_counter_events[0].value == 5.0
            assert canonical_counter_events[0].tags == {"env": "test"}

            assert len(legacy_counter_events) == 1
            assert legacy_counter_events[0].value == 5.0
            assert legacy_counter_events[0].tags == {"env": "test"}

    def test_aliased_gauge_set(self):
        """Test gauge set propagates to both metrics."""
        registry = MetricRegistry()

        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "true"}):
            aliased = create_aliased_gauge(registry, canonical_name="canonical_gauge", legacy_name="legacy_gauge")

            # Set value with tags
            aliased.set(42.0, tags={"env": "test"})

            # Check both metrics received the set
            canonical_events = registry.get_events()
            canonical_gauge_events = [e for e in canonical_events if e.name == "canonical_gauge"]
            legacy_gauge_events = [e for e in canonical_events if e.name == "legacy_gauge"]

            assert len(canonical_gauge_events) == 1
            assert canonical_gauge_events[0].value == 42.0
            assert canonical_gauge_events[0].tags == {"env": "test"}

            assert len(legacy_gauge_events) == 1
            assert legacy_gauge_events[0].value == 42.0
            assert legacy_gauge_events[0].tags == {"env": "test"}

    def test_aliased_histogram_observe(self):
        """Test histogram observe propagates to both metrics."""
        registry = MetricRegistry()

        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "true"}):
            aliased = create_aliased_histogram(
                registry, canonical_name="canonical_histogram", legacy_name="legacy_histogram", buckets=[1.0, 5.0, 10.0]
            )

            # Observe value with tags
            aliased.observe(7.5, tags={"env": "test"})

            # Check both metrics received the observation
            canonical_events = registry.get_events()
            canonical_histogram_events = [e for e in canonical_events if e.name == "canonical_histogram"]
            legacy_histogram_events = [e for e in canonical_events if e.name == "legacy_histogram"]

            assert len(canonical_histogram_events) == 1
            canonical_summary = canonical_histogram_events[0].value
            assert isinstance(canonical_summary, HistogramSummary)
            assert canonical_summary.count == 1
            assert canonical_summary.sum == 7.5

            assert len(legacy_histogram_events) == 1
            legacy_summary = legacy_histogram_events[0].value
            assert isinstance(legacy_summary, HistogramSummary)
            assert legacy_summary.count == 1
            assert legacy_summary.sum == 7.5
            assert legacy_histogram_events[0].tags == {"env": "test"}

    def test_method_validation(self):
        """Test that methods validate metric type."""
        registry = MetricRegistry()

        with patch.dict(os.environ, {"PYFULMEN_TELEMETRY_ALIAS": "true"}):
            counter = create_aliased_counter(registry, "test_counter")
            gauge = create_aliased_gauge(registry, "test_gauge")
            histogram = create_aliased_histogram(registry, "test_histogram")

            # Counter should have inc() but not set() or observe()
            counter.inc(1.0)
            with pytest.raises(AttributeError, match="inc\\(\\) not available on gauge metric"):
                gauge.inc(1.0)
            with pytest.raises(AttributeError, match="inc\\(\\) not available on histogram metric"):
                histogram.inc(1.0)

            # Gauge should have set() but not inc() or observe()
            gauge.set(42.0)
            with pytest.raises(AttributeError, match="set\\(\\) not available on counter metric"):
                counter.set(42.0)
            with pytest.raises(AttributeError, match="set\\(\\) not available on histogram metric"):
                histogram.set(42.0)

            # Histogram should have observe() but not inc() or set()
            histogram.observe(1.0)
            with pytest.raises(AttributeError, match="observe\\(\\) not available on counter metric"):
                counter.observe(1.0)
            with pytest.raises(AttributeError, match="observe\\(\\) not available on gauge metric"):
                gauge.observe(1.0)


class TestCreateAliasedMetrics:
    """Test helper functions for creating aliased metrics."""

    def test_create_aliased_counter(self):
        """Test create_aliased_counter helper."""
        registry = MetricRegistry()

        aliased = create_aliased_counter(registry, canonical_name="test_counter", legacy_name="legacy_counter")

        assert isinstance(aliased, AliasedMetric)
        assert aliased.canonical_name == "test_counter"
        assert aliased.legacy_name == "legacy_counter"

    def test_create_aliased_gauge(self):
        """Test create_aliased_gauge helper."""
        registry = MetricRegistry()

        aliased = create_aliased_gauge(registry, canonical_name="test_gauge", legacy_name="legacy_gauge")

        assert isinstance(aliased, AliasedMetric)
        assert aliased.canonical_name == "test_gauge"
        assert aliased.legacy_name == "legacy_gauge"

    def test_create_aliased_histogram(self):
        """Test create_aliased_histogram helper."""
        registry = MetricRegistry()

        aliased = create_aliased_histogram(
            registry, canonical_name="test_histogram", legacy_name="legacy_histogram", buckets=[1.0, 5.0, 10.0]
        )

        assert isinstance(aliased, AliasedMetric)
        assert aliased.canonical_name == "test_histogram"
        assert aliased.legacy_name == "legacy_histogram"

    def test_unsupported_metric_type(self):
        """Test error handling for unsupported metric types."""
        registry = MetricRegistry()

        with pytest.raises(ValueError, match="Unsupported metric type: invalid"):
            AliasedMetric(registry, "test", "legacy", "invalid")
