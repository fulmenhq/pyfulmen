"""
Telemetry integration for logging module.

Provides utilities to emit metric events through the logging pipeline.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import Logger


def emit_metrics_to_log(logger: "Logger", events: list[dict]) -> None:
    """Emit metric events through logging pipeline.

    Useful for SIMPLE/STRUCTURED profiles to export metrics via logs.
    Each metric event is logged at INFO level with the metric data in context.

    Args:
        logger: Logger instance to use for emission
        events: List of metric event dicts (from telemetry.export() or telemetry.flush())

    Example:
        >>> from pyfulmen import logging, telemetry
        >>> logger = logging.Logger(service="myapp")
        >>> telemetry.counter("requests").inc()
        >>> events = telemetry.flush()
        >>> emit_metrics_to_log(logger, events)
    """
    for event in events:
        logger.info(f"Metric: {event['name']}", context={"metric_event": event})
