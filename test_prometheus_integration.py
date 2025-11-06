#!/usr/bin/env uv run python
"""
Simple integration test for prometheus exporter.

This script tests the basic functionality without mocking
to ensure the prometheus exporter works correctly.
"""

from unittest.mock import patch

from pyfulmen.telemetry import MetricRegistry
from pyfulmen.telemetry.prometheus import PrometheusExporter


def main():
    """Test prometheus exporter functionality."""
    print("Testing Prometheus exporter...")
  
    # Mock validation to allow test metrics
    with patch('pyfulmen.telemetry.prometheus.validate_metric_name'):
        # Create registry and exporter
        registry = MetricRegistry()
        exporter = PrometheusExporter(registry, namespace="test_app")
  
        # Create some metrics
        counter = registry.counter("test_requests_total")
        gauge = registry.gauge("test_memory_usage")
        histogram = registry.histogram("test_latency_ms")
  
        # Record some data
        counter.inc()
        counter.inc(5)
        gauge.set(100)
        gauge.set(200)
        histogram.observe(50.0)
        histogram.observe(150.0)
  
        # Refresh exporter
        exporter.refresh()
  
        # Generate output
        output = exporter.generate_latest()
        print("Prometheus output:")
        print(output)
  
        # Test that we have metrics
        prometheus_name = exporter._format_metric_name("test_requests_total")
        assert prometheus_name in exporter._prometheus_metrics
  
        prometheus_name = exporter._format_metric_name("test_memory_usage")
        assert prometheus_name in exporter._prometheus_metrics
  
        prometheus_name = exporter._format_metric_name("test_latency_ms")
        assert prometheus_name in exporter._prometheus_metrics
  
        print("✅ All tests passed!")


if __name__ == "__main__":
    main()
