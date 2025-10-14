"""Example: Using STRUCTURED logging profile.

The STRUCTURED profile provides JSON-formatted logs with structured context,
perfect for production services that need machine-parseable logs.

Features:
- JSON output with full log envelope
- Structured context fields
- RFC3339 timestamps
- Configurable sinks (console, file, rolling-file)
- Optional middleware (correlation, throttling)
"""

from pyfulmen.logging import Logger
from pyfulmen.logging._models import LoggingProfile

# Create a STRUCTURED profile logger
logger = Logger(service="api-service", profile=LoggingProfile.STRUCTURED, environment="production")

# Basic structured logging with context
logger.info(
    "Request received",
    context={
        "method": "GET",
        "path": "/api/users",
        "query": {"page": 1, "limit": 10},
        "response_time_ms": 45
    }
)

# Log with nested context
logger.info(
    "Database query executed",
    component="database",
    context={
        "query": "SELECT * FROM users WHERE active = true",
        "duration_ms": 23,
        "rows_returned": 150,
        "connection": {
            "host": "db.example.com",
            "database": "production",
            "pool_size": 10
        }
    }
)

# Error logging with structured context
logger.error(
    "Payment processing failed",
    component="payment-processor",
    context={
        "payment_id": "pay_12345",
        "amount": 99.99,
        "currency": "USD",
        "error_code": "INSUFFICIENT_FUNDS",
        "customer_id": "cust_67890"
    }
)

# Using correlation context for request tracking
from pyfulmen.logging import correlation_context

with correlation_context(correlation_id="req-abc-123"):
    logger.info("Starting payment processing")
    logger.info("Validating payment method")
    logger.info("Charging customer")
    logger.info("Payment complete")  # All logs share correlation_id

# With custom static fields
logger_with_metadata = Logger(
    service="worker-service",
    profile=LoggingProfile.STRUCTURED,
    environment="staging",
    static_fields={
        "version": "2.1.0",
        "region": "us-west-2",
        "instance_id": "i-1234567890abcdef"
    }
)

logger_with_metadata.info("Worker started", context={"queue": "high-priority"})

# Log level filtering still works
logger.set_level("WARN")
logger.debug("This debug message is filtered out")
logger.warn("But warnings and above are logged")