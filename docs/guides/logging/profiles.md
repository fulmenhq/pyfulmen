# Logging Profiles

PyFulmen provides four progressive logging profiles, each building on the previous one.

## Profile Overview

```
SIMPLE → STRUCTURED → ENTERPRISE → CUSTOM
  ↓          ↓             ↓          ↓
 Dev    Production    Compliance   Advanced
```

## SIMPLE Profile

**Perfect for:** Local development, scripts, debugging

**Zero configuration required** - just create a logger and start logging.

```python
from pyfulmen.logging import Logger

# That's all you need!
logger = Logger(service="my-app")

logger.debug("Loading configuration")
logger.info("Application started")
logger.warn("Using default settings")
logger.error("Connection failed", context={"host": "localhost"})
```

**Output** (human-readable text to stderr):

```
[2024-10-14 12:00:00] INFO  [my-app] Application started
[2024-10-14 12:00:01] WARN  [my-app] Using default settings
[2024-10-14 12:00:02] ERROR [my-app] Connection failed | host=localhost
```

**Features:**

- ✅ Console-only output (stderr)
- ✅ Human-readable text format
- ✅ No configuration required
- ✅ Perfect for development

**Limitations:**

- ❌ Cannot use JSON format
- ❌ Cannot add middleware
- ❌ Cannot configure multiple sinks
- ❌ No policy enforcement

---

## STRUCTURED Profile

**Perfect for:** Production services, microservices, cloud deployments

**Adds structured JSON output** with configurable sinks for production observability.

```python
from pyfulmen.logging import Logger, LoggingProfile

logger = Logger(
    service="api-service",
    profile=LoggingProfile.STRUCTURED,
    environment="production"
)

logger.info(
    "Request processed",
    context={
        "method": "GET",
        "path": "/api/users",
        "duration_ms": 45,
        "status": 200
    }
)
```

**Output** (JSON to configured sinks):

```json
{
  "timestamp": "2024-10-14T12:00:00.123456Z",
  "severity": "INFO",
  "severityLevel": 20,
  "message": "Request processed",
  "service": "api-service",
  "environment": "production",
  "context": {
    "method": "GET",
    "path": "/api/users",
    "duration_ms": 45,
    "status": 200
  }
}
```

**Features:**

- ✅ JSON output with structured envelope
- ✅ RFC3339 timestamps
- ✅ Configurable sinks (console, file, rolling-file)
- ✅ Optional middleware (via LoggingConfig)
- ✅ Structured context fields

**When to use:**

- Production services
- Microservices architectures
- Cloud-native applications
- Log aggregation (ELK, Splunk, etc.)

---

## ENTERPRISE Profile

**Perfect for:** Compliance requirements (SOC2, HIPAA, PCI-DSS), audit trails

**Adds compliance-grade features** with policy enforcement and mandatory middleware.

```python
from pyfulmen.logging import Logger, LoggingProfile, LoggingConfig

# Configure middleware through LoggingConfig
config = LoggingConfig(
    profile=LoggingProfile.ENTERPRISE,
    service="payment-api",
    environment="production",
    middleware=[
        {"name": "correlation"},
        {"name": "redact-secrets"},
        {"name": "redact-pii"}
    ]
)

logger = Logger(config=config)

# Automatically includes correlation ID
# Automatically redacts secrets and PII
logger.info(
    "Payment processed",
    context={
        "amount": 99.99,
        "api_key": "sk_live_12345",  # → [REDACTED]
        "email": "user@example.com"  # → [REDACTED]
    }
)
```

**Output** (JSON with full envelope):

```json
{
  "timestamp": "2024-10-14T12:00:00.123456Z",
  "severity": "INFO",
  "severityLevel": 20,
  "message": "Payment processed",
  "service": "payment-api",
  "environment": "production",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "context": {
    "amount": 99.99,
    "api_key": "[REDACTED]",
    "email": "[REDACTED]"
  },
  "redactionFlags": ["secrets", "pii"]
}
```

**Features:**

- ✅ Complete 20+ field Crucible envelope
- ✅ Correlation middleware (configured via LoggingConfig)
- ✅ Secret and PII redaction
- ✅ Policy enforcement (optional)
- ✅ Throttling support
- ✅ Audit trails

**When to use:**

- SOC2, HIPAA, PCI-DSS compliance
- Regulated industries
- Sensitive data handling
- Audit requirements

**Important**: Middleware must be configured through `LoggingConfig`, not passed to `Logger()` constructor. See [Middleware Guide](middleware.md) for details.

---

## CUSTOM Profile

**Perfect for:** Special requirements, advanced use cases

**Full control** over all configuration aspects.

```python
from pyfulmen.logging import Logger, LoggingProfile, LoggingConfig

config = LoggingConfig(
    profile=LoggingProfile.CUSTOM,
    service="special-app",
    sinks=[
        {"type": "console", "format": "text"},
        {"type": "file", "format": "json", "options": {"path": "/var/log/app.log"}},
        {"type": "rolling-file", "format": "json", "options": {
            "path": "/var/log/app-rolling.log",
            "maxSize": "100MB",
            "maxBackups": 7
        }}
    ],
    middleware=[
        {"name": "correlation"},
        {"name": "custom-middleware", "config": {...}}
    ],
    custom_config={
        # Your custom configuration
    }
)

logger = Logger(config=config)
```

**When to use:**

- Unique logging requirements
- Custom middleware
- Complex sink configurations
- Non-standard formats

---

## Choosing a Profile

| Requirement         | Profile        |
| ------------------- | -------------- |
| Local development   | **SIMPLE**     |
| Production services | **STRUCTURED** |
| Compliance/audit    | **ENTERPRISE** |
| Special needs       | **CUSTOM**     |

## Migration Path

Start with SIMPLE, upgrade as needs grow:

1. **Development**: SIMPLE (zero config)
2. **Production**: STRUCTURED (add sinks)
3. **Compliance**: ENTERPRISE (add middleware via config)
4. **Advanced**: CUSTOM (full control)

## Next Steps

- **[Middleware Configuration](middleware.md)** - Add correlation, redaction, throttling
- **[Examples](../../../examples/)** - Complete working code

### Coming Soon

- **Configuration Guide** - Comprehensive guide to sinks, severity levels, and configuration options
