"""Example: Using SIMPLE logging profile.

The SIMPLE profile provides zero-complexity console logging for development
and local testing. No configuration needed!

Features:
- Console-only output (stderr)
- Human-readable text format
- No middleware or policy requirements
- Perfect for development and debugging
"""

from pyfulmen.logging import Logger

# Create a SIMPLE profile logger (this is the default, so no profile needed)
logger = Logger(service="demo-app")

# Log at different severity levels
logger.trace("Entering function calculate_total")
logger.debug("Loading configuration from disk")
logger.info("Application started successfully")
logger.warn("Configuration file missing, using defaults")
logger.error("Failed to connect to database", context={"host": "localhost", "port": 5432})
logger.fatal("Critical system failure, exiting")

# Set component at logger creation for module-specific loggers
api_logger = Logger(service="demo-app", component="api-handler")
api_logger.info("Processing request")

validator_logger = Logger(service="demo-app", component="validator")
validator_logger.error("Validation failed", context={"field": "email"})

# Context is merged into the log message
logger.info(
    "User login attempt",
    context={"username": "alice", "ip_address": "192.168.1.100", "user_agent": "Mozilla/5.0"},
)

# Set log level to filter messages
logger.set_level("WARN")
logger.debug("This will not be shown")
logger.info("This will not be shown either")
logger.warn("But this warning will be shown")
logger.error("And errors are always shown")

# Resource management with context manager
with Logger(service="temp-service") as log:
    log.info("Inside context manager")
    log.info("Automatic flush and close on exit")
