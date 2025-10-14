# PyFulmen Logging Guide

**Progressive logging from zero-complexity to enterprise-grade compliance.**

## Table of Contents

1. [Quick Start](#quick-start)
2. [Progressive Profiles](#progressive-profiles)
3. [Profile Details](#profile-details)
4. [Configuration](#configuration)
5. [Middleware](#middleware)
6. [Policy Enforcement](#policy-enforcement)
7. [Migration Guide](#migration-guide)
8. [Best Practices](#best-practices)

---

## Quick Start

### Zero-Complexity Logging (SIMPLE Profile)

```python
from pyfulmen.logging import Logger

# Create logger - that's it!
logger = Logger(service="my-app")

# Start logging
logger.info("Application started")
logger.warn("Configuration missing", context={"file": "config.yaml"})
logger.error("Failed to connect", context={"host": "db.local"})
```

**Output** (human-readable text to stderr):
```
[2024-10-14 12:00:00] INFO  [my-app] Application started
[2024-10-14 12:00:01] WARN  [my-app] Configuration missing | file=config.yaml
[2024-10-14 12:00:02] ERROR [my-app] Failed to connect | host=db.local
```

---

## Progressive Profiles

PyFulmen logging follows a **progressive enhancement** model. Start simple, add features as you need them.

### The Learning Path

```
SIMPLE → STRUCTURED → ENTERPRISE
  ↓         ↓            ↓
 Dev    Production   Compliance
```

| Profile | Use Case | Output | Features |
|---------|----------|--------|----------|
| **SIMPLE** | Local development, debugging | Text to console | Zero config, human-readable |
| **STRUCTURED** | Production services | JSON to sinks | Structured context, custom sinks |
| **ENTERPRISE** | Compliance, audit | JSON with full envelope | Middleware, policy, redaction |
| **CUSTOM** | Special requirements | User-defined | Full control over config |

---

## Profile Details

### SIMPLE Profile

**Perfect for:** Local development, scripts, debugging

**Features:**
- Console-only output (stderr)
- Human-readable text format
- No configuration required
- No middleware overhead

**Example:**
```python
from pyfulmen.logging import Logger

logger = Logger(service="dev-app")
logger.debug("Loading configuration")
logger.info("Server started on port 8080")
```

**Limitations:**
- Cannot use JSON format
- Cannot add middleware
- Cannot configure multiple sinks
- Cannot enable throttling

---

### STRUCTURED Profile

**Perfect for:** Production services, microservices, cloud deployments

**Features:**
- JSON output with structured envelope
- RFC3339 timestamps
- Configurable sinks (console, file, rolling-file)
- Optional middleware (correlation, throttling)
- Structured context fields

**Example:**
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

**Output** (JSON):
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

---

### ENTERPRISE Profile

**Perfect for:** Compliance requirements (SOC2, HIPAA, PCI-DSS), audit trails, sensitive data

**Features:**
- Complete 20+ field Crucible log envelope
- **Required:** Correlation middleware
- **Automatic:** Secret and PII redaction
- **Policy enforcement:** Organizational logging rules
- **Throttling:** Protection against log flooding
- **Audit trails:** Full compliance-grade logging

**Example:**
```python
from pyfulmen.logging import Logger, LoggingProfile

logger = Logger(
    service="payment-api",
    profile=LoggingProfile.ENTERPRISE,
    environment="production",
    policy_file=".goneat/logging-policy.yaml",
    middleware=["correlation", "redact-secrets", "redact-pii"],
    throttling={
        "enabled": True,
        "maxRate": 10000,
        "burstSize": 1000
    }
)

# Secrets are automatically redacted
logger.info(
    "API call",
    context={
        "endpoint": "https://api.stripe.com/charges",
        "api_key": "sk_live_12345"  # → [REDACTED]
    }
)

# PII is automatically redacted
logger.info(
    "User registration",
    context={
        "email": "alice@example.com",  # → [REDACTED]
        "ssn": "123-45-6789",  # → [REDACTED]
        "username": "alice123"  # Preserved
    }
)
```

**Output** (JSON with redactions):
```json
{
  "timestamp": "2024-10-14T12:00:00.123456Z",
  "severity": "INFO",
  "severityLevel": 20,
  "message": "API call",
  "service": "payment-api",
  "environment": "production",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000",
  "context": {
    "endpoint": "https://api.stripe.com/charges",
    "api_key": "[REDACTED]"
  },
  "redactionFlags": ["secrets"]
}
```

---

## Configuration

### Severity Levels

PyFulmen uses Crucible severity levels:

| Severity | Numeric | Python Level | Use Case |
|----------|---------|--------------|----------|
| TRACE | 0 | DEBUG | Highly verbose diagnostics |
| DEBUG | 10 | DEBUG | Debug-level details |
| INFO | 20 | INFO | Core operational events |
| WARN | 30 | WARNING | Unusual but non-breaking |
| ERROR | 40 | ERROR | Request/operation failure |
| FATAL | 50 | CRITICAL | Unrecoverable failure |
| NONE | 60 | CRITICAL+10 | Disable emission |

**Example:**
```python
logger = Logger(service="app", default_level="WARN")

logger.debug("Not shown")
logger.info("Not shown")
logger.warn("Shown")
logger.error("Shown")

# Change level dynamically
logger.set_level("DEBUG")
logger.debug("Now shown")
```

---

### Sinks Configuration

Configure where logs are written:

**Console Sink:**
```python
logger = Logger(
    service="app",
    profile=LoggingProfile.STRUCTURED,
    sinks=[
        {
            "type": "console",
            "format": "json",
            "level": "INFO"
        }
    ]
)
```

**File Sink:**
```python
logger = Logger(
    service="app",
    profile=LoggingProfile.STRUCTURED,
    sinks=[
        {
            "type": "file",
            "name": "app-logs",
            "format": "json",
            "level": "DEBUG",
            "options": {
                "path": "/var/log/app/app.log"
            }
        }
    ]
)
```

**Rolling File Sink:**
```python
logger = Logger(
    service="app",
    profile=LoggingProfile.STRUCTURED,
    sinks=[
        {
            "type": "rolling-file",
            "name": "app-logs",
            "format": "json",
            "options": {
                "path": "/var/log/app/app.log",
                "maxSize": "100MB",
                "maxBackups": 7,
                "compress": True
            }
        }
    ]
)
```

**Multiple Sinks:**
```python
logger = Logger(
    service="app",
    profile=LoggingProfile.CUSTOM,
    sinks=[
        {"type": "console", "format": "text", "level": "INFO"},
        {"type": "file", "format": "json", "level": "DEBUG",
         "options": {"path": "/var/log/app/debug.log"}},
        {"type": "rolling-file", "format": "json", "level": "ERROR",
         "options": {"path": "/var/log/app/error.log", "maxSize": "50MB"}}
    ]
)
```

---

## Middleware

Middleware processes log events in a pipeline before emission.

### Built-in Middleware

#### 1. Correlation Middleware

Automatically adds correlation IDs for distributed tracing:

```python
from pyfulmen.logging import Logger, correlation_context

logger = Logger(
    service="api",
    profile=LoggingProfile.ENTERPRISE,
    middleware=["correlation"]
)

# Auto-generated correlation ID
logger.info("Event 1")  # correlationId: auto-generated

# Use context for request tracking
with correlation_context(correlation_id="req-abc-123"):
    logger.info("Event 2")  # correlationId: req-abc-123
    logger.info("Event 3")  # correlationId: req-abc-123
```

#### 2. Redact Secrets Middleware

Automatically redacts sensitive credentials:

```python
logger = Logger(
    service="app",
    profile=LoggingProfile.ENTERPRISE,
    middleware=["redact-secrets"]
)

logger.info("Config", context={
    "api_key": "sk_live_12345",  # → [REDACTED]
    "password": "secret123",  # → [REDACTED]
    "token": "bearer_xyz",  # → [REDACTED]
    "username": "alice"  # Preserved
})
```

**Patterns detected:**
- API keys: `api_key`, `apiKey`, `API_KEY`
- Passwords: `password`, `passwd`, `pwd`
- Tokens: `token`, `bearer`, `auth`
- Secret strings: `secret`, `private_key`

#### 3. Redact PII Middleware

Automatically redacts personally identifiable information:

```python
logger = Logger(
    service="app",
    profile=LoggingProfile.ENTERPRISE,
    middleware=["redact-pii"]
)

logger.info("User data", context={
    "email": "alice@example.com",  # → [REDACTED]
    "phone": "+1-555-123-4567",  # → [REDACTED]
    "ssn": "123-45-6789",  # → [REDACTED]
    "user_id": "12345"  # Preserved
})
```

**Patterns detected:**
- Email addresses
- Phone numbers (US and international)
- Social Security Numbers (SSN)
- Credit card numbers

#### 4. Throttling Middleware

Prevents log flooding with rate limiting:

```python
logger = Logger(
    service="app",
    profile=LoggingProfile.ENTERPRISE,
    throttling={
        "enabled": True,
        "maxRate": 1000,  # Max 1000 logs/second
        "burstSize": 100,  # Allow bursts up to 100
        "windowSize": 60,  # 60-second sliding window
        "dropPolicy": "drop-oldest"  # or "drop-newest", "block"
    }
)

# High-frequency logging won't overwhelm system
for i in range(10000):
    logger.debug(f"Event {i}")  # Throttled to maxRate
```

---

## Policy Enforcement

Enterprise profile supports organizational logging policies.

### Policy File Example

`.goneat/logging-policy.yaml`:
```yaml
version: "1.0"
allowedProfiles:
  - STRUCTURED
  - ENTERPRISE

requiredProfiles:
  api-service:
    - ENTERPRISE
  worker-service:
    - STRUCTURED

environmentRules:
  production:
    - ENTERPRISE
  staging:
    - STRUCTURED
    - ENTERPRISE
  development:
    - SIMPLE
    - STRUCTURED

profileRequirements:
  ENTERPRISE:
    requiredMiddleware:
      - correlation
      - redact-secrets
    requiredSinks:
      - console
      - file
```

### Using Policy

```python
from pyfulmen.logging import Logger, LoggingProfile

# Policy is automatically enforced for ENTERPRISE profile
logger = Logger(
    service="api-service",
    profile=LoggingProfile.ENTERPRISE,
    environment="production",
    policy_file=".goneat/logging-policy.yaml"
)

# If policy violations exist, logger will:
# 1. Log policy violation event
# 2. Raise exception (if strict_mode=True)
# 3. Continue with warnings (if strict_mode=False, default)
```

---

## Migration Guide

### From Python logging

**Before:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Application started")
logger.error("Failed to connect")
```

**After (SIMPLE):**
```python
from pyfulmen.logging import Logger

logger = Logger(service="my-app")

logger.info("Application started")
logger.error("Failed to connect")
```

### From Basic to Structured

**Before:**
```python
logger = Logger(service="app")
logger.info("Request processed")
```

**After:**
```python
from pyfulmen.logging import Logger, LoggingProfile

logger = Logger(
    service="app",
    profile=LoggingProfile.STRUCTURED,
    environment="production"
)

logger.info(
    "Request processed",
    context={
        "method": "GET",
        "path": "/api/users",
        "duration_ms": 45
    }
)
```

### From Structured to Enterprise

**Before:**
```python
logger = Logger(
    service="api",
    profile=LoggingProfile.STRUCTURED
)
```

**After:**
```python
logger = Logger(
    service="api",
    profile=LoggingProfile.ENTERPRISE,
    policy_file=".goneat/logging-policy.yaml",
    middleware=["correlation", "redact-secrets", "redact-pii"]
)
```

---

## Best Practices

### 1. Choose the Right Profile

- **Development**: SIMPLE for fast feedback
- **Production**: STRUCTURED for observability
- **Compliance**: ENTERPRISE for audit trails

### 2. Use Structured Context

**Good:**
```python
logger.info(
    "Payment processed",
    context={
        "payment_id": "pay_123",
        "amount": 99.99,
        "currency": "USD"
    }
)
```

**Avoid:**
```python
logger.info(f"Payment pay_123 processed: $99.99 USD")
```

### 3. Leverage Correlation Context

**For request tracking:**
```python
from pyfulmen.logging import correlation_context

@app.route("/api/users")
def get_users():
    correlation_id = extract_correlation_id_from_headers(request.headers)
    
    with correlation_context(correlation_id=correlation_id):
        logger.info("Fetching users")
        users = db.query_users()
        logger.info(f"Found {len(users)} users")
    
    return jsonify(users)
```

### 4. Set Appropriate Levels

- **TRACE**: Function entry/exit, variable values
- **DEBUG**: Detailed operational info
- **INFO**: Key business events
- **WARN**: Degraded operation, using defaults
- **ERROR**: Request failures, recoverable errors
- **FATAL**: System failures requiring restart

### 5. Use Component for Module Identification

```python
logger.info("Database query", component="database")
logger.info("Cache hit", component="cache")
logger.info("API call", component="http-client")
```

### 6. Enable Throttling for High-Frequency Logs

```python
logger = Logger(
    service="worker",
    profile=LoggingProfile.ENTERPRISE,
    throttling={"enabled": True, "maxRate": 1000}
)

# Safe even in tight loops
while processing:
    logger.debug("Processing item")
```

### 7. Resource Management

```python
# Use context manager for automatic cleanup
with Logger(service="app") as logger:
    logger.info("Processing")
    process_data()
# Automatic flush() and close()

# Or manual management
logger = Logger(service="app")
try:
    logger.info("Processing")
    process_data()
finally:
    logger.flush()
    logger.close()
```

---

## Examples

See the `examples/` directory for complete examples:

- `examples/logging_simple.py` - SIMPLE profile usage
- `examples/logging_structured.py` - STRUCTURED profile with JSON
- `examples/logging_enterprise.py` - ENTERPRISE profile with compliance

---

## Further Reading

- [Fulmen Logging Standard](../crucible-py/standards/observability/logging.md)
- [Crucible Log Event Schema](../../schemas/crucible-py/observability/logging/v1.0.0/log-event.schema.json)
- [Logger Config Schema](../../schemas/crucible-py/observability/logging/v1.0.0/logger-config.schema.json)
- [Logging Policy Schema](../../schemas/crucible-py/observability/logging/v1.0.0/logging-policy.schema.json)