#!/usr/bin/env -S uv run python
"""Progressive Logging Demo - Showcasing enterprise-grade structured logging.

This demo script showcases PyFulmen's progressive logging module capabilities:
- SIMPLE profile: Zero-config console logging for CLI tools
- STRUCTURED profile: JSON output for services and background jobs
- ENTERPRISE profile: Full correlation, middleware, and policy enforcement
- Severity levels: TRACE, DEBUG, INFO, WARN, ERROR, FATAL
- Context propagation and correlation IDs
- Error handling with stack traces

Prerequisites:
    1. Clone the pyfulmen repository
    2. Install uv package manager: https://docs.astral.sh/uv/
    3. Run from repository root directory

Setup (one-time):
    # Install uv if not already installed
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Clone and setup repository
    cd /path/to/pyfulmen
    uv sync  # Creates .venv and installs dependencies

Usage:
    # From repository root (recommended - uses shebang)
    ./scripts/demos/logging_demo.py

    # Or explicitly with uv run (works from any directory in repo)
    uv run python scripts/demos/logging_demo.py

    # Or with activated virtual environment
    source .venv/bin/activate
    python scripts/demos/logging_demo.py

Note:
    - This script adds src/ to Python path for development environment
    - Does NOT require pyfulmen to be installed via pip
    - Designed for developers working on the library itself
    - All log output goes to stderr (terminal), not stdout
"""

import sys
import time
from pathlib import Path

# Add src to path for development environment
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

from pyfulmen.logging import (
    Logger,
    LoggingProfile,
    correlation_context,
    get_correlation_id,
)


def print_section(title: str, subtitle: str = "") -> None:
    """Print a section header to stdout (not stderr like logs)."""
    print(f"\n{'=' * 80}", file=sys.stdout)
    print(f"  {title}", file=sys.stdout)
    if subtitle:
        print(f"  {subtitle}", file=sys.stdout)
    print(f"{'=' * 80}\n", file=sys.stdout)
    sys.stdout.flush()
    time.sleep(0.5)  # Give time to read section header


def demo_simple_profile() -> None:
    """Demonstrate SIMPLE profile - zero-config CLI logging."""
    print_section(
        "SIMPLE Profile",
        "Zero-config console logging for CLI tools and scripts",
    )

    # Create logger with SIMPLE profile (minimal configuration)
    logger = Logger(
        service="cli-tool",
        profile=LoggingProfile.SIMPLE,
        default_level="INFO",
    )

    print(">>> Logging at different severity levels:\n", file=sys.stdout)
    sys.stdout.flush()
    time.sleep(0.3)

    logger.info("Application started", component="main")
    time.sleep(0.2)
    logger.info("Processing user request", user_id="user-123")
    time.sleep(0.2)
    logger.warn("Slow response detected", duration_ms=1250)
    time.sleep(0.2)
    logger.error(
        "Failed to connect to external API", context={"api": "payments.example.com"}
    )

    time.sleep(0.5)


def demo_structured_profile() -> None:
    """Demonstrate STRUCTURED profile - JSON output for services."""
    print_section(
        "STRUCTURED Profile",
        "Structured JSON logging for services and background jobs",
    )

    # Create logger with STRUCTURED profile (JSON output)
    logger = Logger(
        profile=LoggingProfile.STRUCTURED,
        service="api-gateway",
        default_level="DEBUG",
        component="request-handler",
    )

    print(">>> JSON-formatted log events:\n", file=sys.stdout)
    sys.stdout.flush()
    time.sleep(0.3)

    logger.debug("Request received", context={"method": "POST", "path": "/api/users"})
    time.sleep(0.2)
    logger.info(
        "User authenticated",
        user_id="usr_42",
        context={"method": "jwt", "scope": "read:profile write:profile"},
    )
    time.sleep(0.2)
    logger.info(
        "Database query executed",
        duration_ms=15.3,
        context={"table": "users", "rows": 1},
    )
    time.sleep(0.2)
    logger.info(
        "Response sent",
        context={"status": 200, "content_type": "application/json", "size": 1024},
    )

    time.sleep(0.5)


def demo_enterprise_profile() -> None:
    """Demonstrate ENTERPRISE profile - full observability with correlation."""
    print_section(
        "ENTERPRISE Profile",
        "Production-grade logging with correlation IDs and middleware",
    )

    # Create logger with ENTERPRISE profile (correlation, middleware, etc.)
    logger = Logger(
        profile=LoggingProfile.ENTERPRISE,
        service="payment-processor",
        default_level="INFO",
        component="transaction-service",
        environment="production",
    )

    print(">>> Simulating a payment transaction with correlation:\n", file=sys.stdout)
    sys.stdout.flush()
    time.sleep(0.3)

    # Simulate transaction lifecycle with correlation context
    with correlation_context():
        correlation_id = get_correlation_id()

        logger.info(
            "Payment request received",
            context={"amount": 99.99, "currency": "USD", "merchant_id": "mch_789"},
        )
        time.sleep(0.2)

        logger.debug(
            "Validating payment method",
            context={"card_last4": "4242", "card_brand": "visa"},
        )
        time.sleep(0.2)

        logger.info(
            "Fraud check passed",
            duration_ms=45.2,
            context={"risk_score": 0.15, "rules_evaluated": 12},
        )
        time.sleep(0.2)

        logger.info(
            "Payment authorized",
            context={"transaction_id": "txn_abc123", "authorization_code": "AUTH456"},
        )
        time.sleep(0.2)

        logger.info(
            "Payment completed",
            context={
                "transaction_id": "txn_abc123",
                "status": "success",
                "total_duration_ms": 152.7,
            },
        )

    print(
        f"\n>>> All logs above share correlation_id: {correlation_id[:16]}...\n",
        file=sys.stdout,
    )
    time.sleep(0.5)


def demo_severity_levels() -> None:
    """Demonstrate all severity levels."""
    print_section(
        "Severity Levels",
        "TRACE → DEBUG → INFO → WARN → ERROR → FATAL",
    )

    logger = Logger(
        profile=LoggingProfile.STRUCTURED,
        service="demo-app",
        default_level="TRACE",  # Show all levels
    )

    print(
        ">>> All severity levels (TRACE requires explicit configuration):\n",
        file=sys.stdout,
    )
    sys.stdout.flush()
    time.sleep(0.3)

    logger.trace("Entering function processOrder()", context={"order_id": "ord_999"})
    time.sleep(0.2)
    logger.debug("Cache lookup", context={"key": "user:123", "hit": True})
    time.sleep(0.2)
    logger.info("Order validated", context={"order_id": "ord_999", "items": 3})
    time.sleep(0.2)
    logger.warn(
        "Inventory low",
        context={"product_id": "SKU-456", "quantity": 5, "threshold": 10},
    )
    time.sleep(0.2)
    logger.error(
        "Payment gateway timeout", context={"gateway": "stripe", "timeout_ms": 5000}
    )
    time.sleep(0.2)
    logger.fatal(
        "Database connection lost",
        context={"host": "db.example.com", "retry_count": 3, "exit_code": 1},
    )

    time.sleep(0.5)


def demo_error_with_exception() -> None:
    """Demonstrate error logging with exception details."""
    print_section(
        "Error Logging",
        "Capturing exceptions with stack traces",
    )

    logger = Logger(
        profile=LoggingProfile.STRUCTURED,
        service="file-processor",
        default_level="INFO",
    )

    print(">>> Logging an exception with stack trace:\n", file=sys.stdout)
    sys.stdout.flush()
    time.sleep(0.3)

    try:
        # Simulate an error
        int("not-a-number")  # This will raise ValueError
    except ValueError as e:
        logger.error(
            "Failed to parse configuration value",
            error={"message": str(e), "type": type(e).__name__},
            context={"field": "max_retries", "value": "not-a-number"},
        )

    time.sleep(0.5)


def demo_contextual_logging() -> None:
    """Demonstrate contextual logging with nested contexts."""
    print_section(
        "Contextual Logging",
        "Building context across function calls",
    )

    logger = Logger(
        profile=LoggingProfile.ENTERPRISE,
        service="batch-processor",
        default_level="INFO",
    )

    print(">>> Processing batch with contextual information:\n", file=sys.stdout)
    sys.stdout.flush()
    time.sleep(0.3)

    with correlation_context():
        logger.info(
            "Batch job started",
            context={"batch_id": "batch_2024_001", "total_items": 100},
        )
        time.sleep(0.2)

        # Simulate processing items
        for i in range(1, 4):
            logger.info(
                "Processing item",
                context={
                    "item_number": i,
                    "item_id": f"item_{i:03d}",
                    "progress": f"{i}/100",
                },
            )
            time.sleep(0.2)

        logger.info(
            "Batch job completed",
            context={"processed": 3, "failed": 0, "duration_s": 15.3},
        )

    time.sleep(0.5)


def demo_profile_comparison() -> None:
    """Demonstrate the same log across different profiles."""
    print_section(
        "Profile Comparison",
        "Same log event across SIMPLE, STRUCTURED, and ENTERPRISE",
    )

    print(">>> SIMPLE profile (human-readable):\n", file=sys.stdout)
    sys.stdout.flush()
    time.sleep(0.3)

    simple_logger = Logger(
        service="demo",
        profile=LoggingProfile.SIMPLE,
        default_level="INFO",
    )
    simple_logger.info(
        "User login successful", user_id="alice", context={"ip": "192.168.1.100"}
    )

    time.sleep(0.5)

    print("\n>>> STRUCTURED profile (JSON):\n", file=sys.stdout)
    sys.stdout.flush()
    time.sleep(0.3)

    structured_logger = Logger(
        profile=LoggingProfile.STRUCTURED, service="demo", default_level="INFO"
    )
    structured_logger.info(
        "User login successful", user_id="alice", context={"ip": "192.168.1.100"}
    )

    time.sleep(0.5)

    print("\n>>> ENTERPRISE profile (JSON with correlation):\n", file=sys.stdout)
    sys.stdout.flush()
    time.sleep(0.3)

    enterprise_logger = Logger(
        profile=LoggingProfile.ENTERPRISE, service="demo", default_level="INFO"
    )
    with correlation_context():
        enterprise_logger.info(
            "User login successful", user_id="alice", context={"ip": "192.168.1.100"}
        )

    time.sleep(0.5)


def main() -> None:
    """Run all logging demos."""
    print("\n" + "=" * 80, file=sys.stdout)
    print("  PyFulmen Progressive Logging - Demo", file=sys.stdout)
    print(
        "  Enterprise-grade structured logging for Python applications", file=sys.stdout
    )
    print("=" * 80, file=sys.stdout)
    print("\nNote: All logs are written to stderr (shown below)", file=sys.stdout)
    print(
        "      Section headers are written to stdout (shown above)\n", file=sys.stdout
    )
    sys.stdout.flush()

    time.sleep(1)

    demo_simple_profile()
    demo_structured_profile()
    demo_enterprise_profile()
    demo_severity_levels()
    demo_error_with_exception()
    demo_contextual_logging()
    demo_profile_comparison()

    print("\n" + "=" * 80, file=sys.stdout)
    print("  Demo Complete!", file=sys.stdout)
    print("=" * 80, file=sys.stdout)
    print("\nKey Takeaways:", file=sys.stdout)
    print("  • SIMPLE: Perfect for CLI tools (human-readable output)", file=sys.stdout)
    print("  • STRUCTURED: JSON logs for services (machine-parseable)", file=sys.stdout)
    print(
        "  • ENTERPRISE: Full observability with correlation and middleware",
        file=sys.stdout,
    )
    print(
        "  • All logs go to stderr, preserving stdout for application output",
        file=sys.stdout,
    )
    print("\nFor more information, see:", file=sys.stdout)
    print("  - src/pyfulmen/logging/README.md", file=sys.stdout)
    print("  - docs/releases/v0.1.3.md (Logging section)", file=sys.stdout)
    print(
        "  - examples/logging/ (simple.py, structured.py, enterprise.py)\n",
        file=sys.stdout,
    )
    sys.stdout.flush()


if __name__ == "__main__":
    main()
