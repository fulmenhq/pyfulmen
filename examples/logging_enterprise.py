"""Example: Using ENTERPRISE logging profile.

The ENTERPRISE profile provides full compliance-grade logging with:
- Complete 20+ field log envelope
- Policy enforcement
- Middleware pipeline (correlation, redaction, throttling)
- Audit trails and compliance features

Perfect for production systems requiring SOC2, HIPAA, or similar compliance.
"""

from pyfulmen.logging import Logger, LoggingProfile

# Create an ENTERPRISE profile logger
# Note: For production use, configure middleware through LoggingConfig
# This example shows the basic setup - see docs for middleware configuration
logger = Logger(
    service="payment-api",
    profile=LoggingProfile.ENTERPRISE,
    environment="production",
    # Optional: policy_file=".goneat/logging-policy.yaml"
)

# All logs include correlation ID automatically
logger.info("Payment processing started", context={"amount": 100.00, "currency": "USD"})

# Secrets are automatically redacted
logger.info(
    "API call made",
    context={
        "endpoint": "https://api.stripe.com/v1/charges",
        "api_key": "sk_live_51234567890",  # Will be redacted to [REDACTED]
        "headers": {
            "Authorization": "Bearer secret_token"  # Will be redacted
        }
    }
)

# PII is automatically redacted
logger.info(
    "User registration",
    context={
        "email": "alice@example.com",  # Will be redacted
        "phone": "+1-555-123-4567",  # Will be redacted
        "ssn": "123-45-6789",  # Will be redacted
        "username": "alice123"  # Username is preserved
    }
)

# Error tracking with full context
try:
    # Simulate an error
    raise ValueError("Invalid payment amount")
except Exception as e:
    import traceback
    logger.error(
        "Payment validation failed",
        context={
            "error": str(e),
            "payment_id": "pay_abc123",
            "customer_id": "cust_xyz789",
            "stacktrace": traceback.format_exc()  # Include stack trace in context
        }
    )

# Correlation context for distributed tracing
from pyfulmen.logging import correlation_context

with correlation_context(correlation_id="req-2024-001"):
    logger.info("Request received from load balancer")
    logger.info("Authenticating user")
    logger.info("Processing payment")
    logger.info("Sending confirmation email")
    # All logs share the same correlation_id

# Extract correlation ID from HTTP headers
from pyfulmen.logging import extract_correlation_id_from_headers

headers = {
    "X-Correlation-ID": "req-from-client-123",
    "X-Request-ID": "backup-id",
    "User-Agent": "Mozilla/5.0"
}

correlation_id = extract_correlation_id_from_headers(headers)
with correlation_context(correlation_id=correlation_id):
    logger.info("Processing request from client")

# Audit logging for compliance
# Create a logger with component for audit logs
audit_logger = Logger(
    service="payment-api",
    profile=LoggingProfile.ENTERPRISE,
    component="audit",
    environment="production"
)

audit_logger.info(
    "User action performed",
    context={
        "action": "DELETE",
        "resource": "users/123",
        "user_id": "admin_001",
        "ip_address": "192.168.1.100",
        "timestamp_utc": "2024-10-14T12:00:00Z"
    }
)

# Throttling prevents log flooding
for i in range(20000):
    logger.debug(f"High-frequency event {i}")  # Will be throttled based on configuration

# Resource cleanup
logger.flush()  # Ensure all logs are written
logger.close()  # Release resources