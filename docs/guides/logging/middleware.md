# Middleware Configuration

Middleware processes log events in a pipeline before emission. PyFulmen provides built-in middleware for correlation, redaction, and throttling.

## Important: Middleware Configuration

**Middleware must be configured through `LoggingConfig`, not passed directly to `Logger()`.**

The `Logger()` constructor accepts `middleware` parameter only for advanced use cases where you pass actual middleware **objects**. For typical usage, configure middleware through `LoggingConfig`:

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
```

## Built-in Middleware

### 1. Correlation Middleware

Automatically adds correlation IDs for distributed tracing:

```python
from pyfulmen.logging import Logger, LoggingProfile, LoggingConfig, correlation_context

config = LoggingConfig(
    profile=LoggingProfile.STRUCTURED,
    service="api-service",
    middleware=[{"name": "correlation"}]
)

logger = Logger(config=config)

# Auto-generated correlation ID
logger.info("Event 1")  # correlationId: auto-generated

# Use context for request tracking
with correlation_context(correlation_id="req-abc-123"):
    logger.info("Event 2")  # correlationId: req-abc-123
    logger.info("Event 3")  # correlationId: req-abc-123
```

### 2. Redact Secrets Middleware

Automatically redacts sensitive credentials:

```python
config = LoggingConfig(
    profile=LoggingProfile.ENTERPRISE,
    service="secure-app",
    middleware=[{"name": "redact-secrets"}]
)

logger = Logger(config=config)

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

### 3. Redact PII Middleware

Automatically redacts personally identifiable information:

```python
config = LoggingConfig(
    profile=LoggingProfile.ENTERPRISE,
    service="user-service",
    middleware=[{"name": "redact-pii"}]
)

logger = Logger(config=config)

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

### 4. Throttling Middleware

Prevents log flooding with rate limiting:

```python
config = LoggingConfig(
    profile=LoggingProfile.ENTERPRISE,
    service="high-traffic-app",
    middleware=[
        {"name": "throttling", "config": {
            "maxRate": 1000,  # Max 1000 logs/second
            "burstSize": 100,  # Allow bursts up to 100
            "windowSize": 60,  # 60-second sliding window
            "dropPolicy": "drop-oldest"  # or "drop-newest", "block"
        }}
    ]
)

logger = Logger(config=config)

# High-frequency logging won't overwhelm system
for i in range(10000):
    logger.debug(f"Event {i}")  # Throttled to maxRate
```

## Middleware Pipeline

Multiple middleware can be chained with explicit ordering:

```python
config = LoggingConfig(
    profile=LoggingProfile.ENTERPRISE,
    service="secure-api",
    middleware=[
        {"name": "correlation", "order": 0},  # First: add correlation ID
        {"name": "redact-secrets", "order": 10},  # Second: redact secrets
        {"name": "redact-pii", "order": 20},  # Third: redact PII
        {"name": "throttling", "order": 30, "config": {"maxRate": 1000}}  # Last: throttle
    ]
)

logger = Logger(config=config)
```

## Advanced: Custom Middleware

For advanced use cases, you can pass actual middleware instances:

```python
from pyfulmen.logging import Logger, RedactSecretsMiddleware, RedactPIIMiddleware

# Pass actual middleware objects (only RedactSecretsMiddleware and RedactPIIMiddleware are exported)
logger = Logger(
    service="custom-app",
    middleware=[
        RedactSecretsMiddleware(),
        RedactPIIMiddleware()
    ]
)
```

**Note**: Only `RedactSecretsMiddleware` and `RedactPIIMiddleware` are exported from the public API. For correlation and throttling, use the `LoggingConfig` approach with middleware names. This object-based approach is for advanced use cases; the `LoggingConfig` dict format is simpler and more maintainable.

## Middleware Registry

Available middleware names for configuration:

- `"correlation"` - Correlation ID generation and propagation
- `"redact-secrets"` - Secret pattern detection and redaction
- `"redact-pii"` - PII pattern detection and redaction
- `"throttling"` - Rate limiting and backpressure

## Best Practices

1. **Order matters**: Place correlation first, redaction before throttling
2. **Test patterns**: Verify redaction patterns match your data
3. **Monitor throttling**: Check dropped event counts in production
4. **Use config objects**: Prefer `LoggingConfig` over direct middleware objects

## Examples

See complete examples in:

- `examples/logging_enterprise.py` - Full enterprise setup with middleware
- `tests/unit/logging/test_middleware.py` - Middleware unit tests
- `tests/integration/logging/test_progressive_logger.py` - End-to-end tests
