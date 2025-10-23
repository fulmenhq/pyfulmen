#!/usr/bin/env python3
"""
Demonstration of PyFulmen error handling and telemetry integration.

This example shows how to:
1. Create and wrap errors with telemetry metadata
2. Validate errors against Crucible schemas
3. Record metrics using counters and histograms
4. Integrate metrics with the logging pipeline
5. Handle graceful exit with structured error logging
"""

from datetime import UTC, datetime

from pyfulmen import error_handling, logging, telemetry


def main():
    """Run error handling and telemetry demo."""
    print("=" * 60)
    print("PyFulmen Error Handling & Telemetry Demo")
    print("=" * 60)
    print()

    # Setup structured logging
    logger = logging.Logger(service="demo", profile=logging.LoggingProfile.STRUCTURED)

    # 1. Error Handling Demo
    print("1. Error Handling")
    print("-" * 60)

    # Create a base Pathfinder error
    base = error_handling.PathfinderError(
        code="DEMO_CONFIG_ERROR",
        message="Failed to load demo configuration",
        details={"file": "/app/config.yaml", "reason": "File not found"},
        timestamp=datetime.now(UTC),
    )
    print(f"Created PathfinderError: {base.code} - {base.message}")

    # Wrap with telemetry metadata
    err = error_handling.wrap(
        base,
        context={"demo": "example", "environment": "development"},
        severity="medium",
        correlation_id="demo-req-001",
    )
    print(f"Wrapped with telemetry: severity={err.severity}, correlation_id={err.correlation_id}")

    # Validate against schema
    is_valid = error_handling.validate(err)
    print(f"Schema validation: {'✓ VALID' if is_valid else '✗ INVALID'}")
    print()

    # 2. Telemetry Demo
    print("2. Telemetry Metrics")
    print("-" * 60)

    # Get metric registry instance
    registry = telemetry.MetricRegistry()

    # Record some counter metrics
    print("Recording counter metrics...")
    schema_counter = registry.counter("schema_validations")
    schema_counter.inc()
    schema_counter.inc()
    schema_counter.inc()
    print("  schema_validations: incremented 3 times")

    # Record histogram metrics
    print("Recording histogram metrics...")
    latency_histogram = registry.histogram("config_load_ms")
    latency_histogram.observe(12.5)
    latency_histogram.observe(45.2)
    latency_histogram.observe(8.3)
    print("  config_load_ms: recorded 3 observations")

    # Get metric events
    events = registry.get_events()
    print(f"Retrieved {len(events)} metric events")

    # Convert to dicts for logging
    event_dicts = [event.model_dump(mode="json") for event in events]
    print()

    # 3. Logging Integration Demo
    print("3. Logging Integration")
    print("-" * 60)

    # Emit metrics through logging pipeline
    print("Emitting metrics to log...")
    logging.emit_metrics_to_log(logger, event_dicts)
    print(f"  Emitted {len(events)} metric events to logger")
    print()

    # 4. Metric Validation Demo
    print("4. Metric Validation")
    print("-" * 60)

    # Validate a single metric event
    valid_event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "name": "schema_validations",
        "value": 42,
        "unit": "count",
    }
    is_valid = telemetry.validate_metric_event(valid_event)
    print(f"Valid metric event: {'✓ VALID' if is_valid else '✗ INVALID'}")

    # Try an invalid metric (wrong name not in taxonomy)
    invalid_event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "name": "unknown_metric",
        "value": 100,
        "unit": "count",
    }
    is_valid = telemetry.validate_metric_event(invalid_event)
    print(f"Invalid metric event: {'✓ VALID' if is_valid else '✗ INVALID (expected)'}")
    print()

    # 5. Error Exit Demo (commented out to not actually exit)
    print("5. Error Exit Handling")
    print("-" * 60)
    print("Would call: error_handling.exit_with_error(1, err, logger=logger)")
    print("This would:")
    print("  - Log the error at 'medium' severity (maps to error level)")
    print("  - Include structured context with code and correlation_id")
    print("  - Call sys.exit(1)")
    print("(Skipped to keep demo running)")
    print()

    # Summary
    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ PathfinderError and FulmenError creation")
    print("  ✓ Error wrapping with telemetry metadata")
    print("  ✓ Schema validation for errors and metrics")
    print("  ✓ Counter and histogram metric recording")
    print("  ✓ Metric export and logging integration")
    print("  ✓ Error exit handling with structured logging")


if __name__ == "__main__":
    main()
