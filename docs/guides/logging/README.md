# PyFulmen Progressive Logging Guide

**Zero-complexity to enterprise-grade logging with progressive profiles.**

## Quick Start

```python
from pyfulmen.logging import Logger

# Development: Zero-complexity console logging (default)
logger = Logger(service="my-app")
logger.info("Application started")
logger.error("Connection failed", context={"host": "db.local"})
```

That's it! No configuration needed for development.

## Learning Path

PyFulmen logging follows a **progressive enhancement** model:

```
SIMPLE → STRUCTURED → ENTERPRISE
  ↓         ↓            ↓
 Dev    Production   Compliance
```

Start with SIMPLE (zero config), add structure as you need it, scale to ENTERPRISE for compliance.

## Documentation

### Available Guides

- **[Profiles Overview](profiles.md)** - SIMPLE, STRUCTURED, ENTERPRISE, CUSTOM
- **[Middleware](middleware.md)** - Correlation, redaction, throttling
- **[Examples](../../../examples/)** - Complete working examples

### Coming Soon

Additional guides are being developed for:

- Configuration (severity levels, sinks, and config)
- Policy enforcement
- Best practices and migration from Python logging

## Profile Quick Reference

| Profile        | Use Case             | Configuration Required |
| -------------- | -------------------- | ---------------------- |
| **SIMPLE**     | Development, scripts | None (default)         |
| **STRUCTURED** | Production services  | Optional sinks         |
| **ENTERPRISE** | Compliance, audit    | Middleware via config  |
| **CUSTOM**     | Special requirements | Full custom config     |

## Telemetry (v0.1.6+)

PyFulmen logging emits telemetry metrics about its own operation (self-instrumentation):

- **`logging_emit_count`**: Number of log emissions (counter)
- **`logging_emit_latency_ms`**: Log emission duration (histogram)

All metrics follow the [Telemetry Instrumentation Pattern](../../development/telemetry-instrumentation-pattern.md).

## Support

- **Issues**: [GitHub Issues](https://github.com/fulmenhq/pyfulmen/issues)
- **Examples**: See `examples/` directory
- **Standards**: [Crucible Logging Standard](../../crucible-py/standards/observability/logging.md)
- **Telemetry**: [Instrumentation Pattern](../../development/telemetry-instrumentation-pattern.md)
