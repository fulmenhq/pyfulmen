# pyfulmen

** Curated Libraries for Scale**

Python Fulmen libraries for enterprise-scale development.

**Lifecycle Phase**: `alpha` | **Version**: 0.1.12 | **Coverage**: 93%

## Overview

PyFulmen is part of the Fulmen ecosystem, providing templates, processes, and tools for enterprise-scale development in Python.

📖 **[Read the full PyFulmen Overview](docs/pyfulmen_overview.md)** for a comprehensive guide to modules, observability features, and the roadmap.

> **Alpha Status**: Early adopters; rapidly evolving features. Minimum coverage: 30%. See [Repository Lifecycle Standard](docs/crucible-py/standards/repository-lifecycle.md) for quality expectations.

**Key Features:**

- **Progressive Logging** - Zero-complexity to enterprise-grade logging with SIMPLE → STRUCTURED → ENTERPRISE profiles
- **Error Handling** - Pathfinder-compatible errors with telemetry metadata and schema validation (v0.1.6+)
- **Exit Codes** - Standardized 54-code catalog with simplified modes for monitoring/alerting (v0.1.9+)
- **Enterprise Telemetry** - Comprehensive metrics system with MetricRegistry, Prometheus export, and cross-module instrumentation (v0.1.12+)
- **FulHash** - Fast, consistent hashing with xxh3-128 (default) and sha256 support, thread-safe streaming (v0.1.6+)
- **Crucible Shim** - Idiomatic Python access to Crucible schemas, docs, and config defaults
- **Schema Export** - Export Crucible schemas to local files with provenance metadata (v0.1.9+)
- **Config Path API** - XDG-compliant, platform-aware configuration paths
- **Three-Layer Config Loading** - Crucible defaults → User overrides → App config
- **Schema Validation** - Helpers for validating data against Crucible JSON schemas
- **Version Management** - Utilities for reading and validating repository versions
- **Application Identity** - Canonical app metadata from `.fulmen/app.yaml` with discovery, validation, and caching (v0.1.10+)
- **Signal Handling** - Cross-platform signal handling with Windows fallbacks, asyncio integration, and enterprise features (v0.1.11+)

## Application Identity (v0.1.10+)

PyFulmen provides canonical application metadata following the Crucible app identity standard. The `pyfulmen.appidentity` module discovers, validates, and caches application identity from `.fulmen/app.yaml` files.

### Quick Start

```python
from pyfulmen.appidentity import get_identity

# Get current application identity
identity = get_identity()
print(f"Binary: {identity.binary_name}")
print(f"Vendor: {identity.vendor}")
print(f"Environment Prefix: {identity.env_prefix}")
```

### Configuration File

Create a `.fulmen/app.yaml` file in your repository root:

```yaml
# Required application information
app:
  binary_name: "myapp"
  vendor: "mycompany"
  env_prefix: "MYAPP_"
  config_name: "myapp"
  description: "My awesome application"

# Optional metadata
metadata:
  project_url: "https://github.com/mycompany/myapp"
  support_email: "support@mycompany.com"
  license: "MIT"
  repository_category: "application"
  telemetry_namespace: "myapp.telemetry"

  # Python-specific metadata
  python:
    distribution_name: "myapp"
    package_name: "myapp_core"
    console_scripts:
      - name: "myapp"
        module: "myapp.cli:main"
```

### CLI Commands

```bash
# Show current identity
pyfulmen appidentity show

# Show identity in JSON format
pyfulmen appidentity show --format json

# Validate identity file
pyfulmen appidentity validate .fulmen/app.yaml
```

### Integration with Config

The app identity integrates seamlessly with the config module:

```python
from pyfulmen.appidentity import get_identity
from pyfulmen.config import load_layered_config

identity = get_identity()

# Config loader automatically uses identity for:
# - Environment variable prefix (identity.env_prefix)
# - Configuration file names (identity.config_name)
config, diagnostics, sources = load_layered_config(
    category="myapp",
    version="1.0.0",
    identity=identity  # Optional - will use get_identity() if not provided
)
```

### Discovery Precedence

The module follows this precedence order for discovering identity files:

1. **Environment Variable**: `FULMEN_APP_IDENTITY_PATH`
2. **Ancestor Search**: Look for `.fulmen/app.yaml` in current directory and parent directories
3. **Error**: Raise `AppIdentityNotFoundError` if no file found

📖 **[Complete Application Identity Documentation](src/pyfulmen/appidentity/README.md)** for detailed API reference, testing utilities, and troubleshooting.

## Signal Handling (v0.1.11+)

PyFulmen provides enterprise-grade signal handling with cross-platform support, Windows HTTP fallbacks, and asyncio integration. The `pyfulmen.signals` module implements the Crucible signal-handling standard with progressive interface design.

### Quick Start

```python
from pyfulmen.signals import on_shutdown, on_reload

def cleanup_handler():
    print("Shutting down gracefully...")

def reload_handler():
    print("Reloading configuration...")

# Register handlers - zero complexity defaults
on_shutdown(cleanup_handler)
on_reload(reload_handler)
```

### Cross-Platform Support

```python
from pyfulmen.signals import supports_signal, get_signal_metadata
import signal

# Check signal support on current platform
if supports_signal(signal.SIGHUP):
    print("SIGHUP is supported")
else:
    print("SIGHUP not supported - will use HTTP fallback")

# Get signal metadata
metadata = get_signal_metadata("SIGHUP")
print(f"Description: {metadata['description']}")
```

### Windows HTTP Fallbacks

For signals not supported on Windows, PyFulmen provides HTTP endpoint fallbacks:

```python
from pyfulmen.signals import get_http_helper, build_signal_request

helper = get_http_helper()
request = build_signal_request("SIGHUP")
curl_cmd = helper.format_curl_command(request)
print(f"Windows fallback: {curl_cmd}")
```

### CLI Commands

```bash
# Show signals module information
pyfulmen signals info

# List available signals with platform support
pyfulmen signals list

# Show Windows fallback documentation
pyfulmen signals windows-fallback --format markdown
```

📖 **[Complete Signal Handling Documentation](src/pyfulmen/signals/README.md)** for detailed API reference, asyncio integration, and enterprise features.

## Enterprise Telemetry (v0.1.12+)

PyFulmen provides comprehensive enterprise telemetry with MetricRegistry, Prometheus export, and cross-module instrumentation. The `pyfulmen.telemetry` module implements ADR-0008 with thread-safe metrics collection and performance optimization.

### Quick Start

```python
from pyfulmen.telemetry import counter, gauge, histogram, get_global_registry

# Create metrics instantly - zero complexity
ops_counter = counter("operations_total")
memory_gauge = gauge("memory_bytes")
request_duration = histogram("request_duration_ms")

# Use in your code
ops_counter.inc()
memory_gauge.set(1024 * 1024)
request_duration.observe(45.2)

# Retrieve metrics for monitoring
registry = get_global_registry()
events = registry.get_events()
for event in events:
    print(f"{event.name}: {event.value}")
```

### Enterprise Features

```python
from pyfulmen.telemetry import MetricRegistry, PrometheusExporter

# Create custom registry
registry = MetricRegistry()

# Add metrics with labels
request_counter = registry.counter("http_requests_total", labels=["method", "status"])
request_counter.labels(method="GET", status="200").inc()

# Export for Prometheus
exporter = PrometheusExporter(registry)
metrics_text = exporter.export()
print(metrics_text)
```

### Cross-Module Instrumentation

PyFulmen modules automatically instrument themselves:

```python
from pyfulmen import foundry, fulhash, error_handling

# These operations are automatically instrumented
mime_type = foundry.detect_mime_type("example.txt")  # Records timing and algorithm
file_hash = fulhash.hash_file("example.txt")         # Records bytes processed and timing
wrapped_error = error_handling.wrap(base_error)      # Records wrap operations

# All metrics are available in the global registry
registry = get_global_registry()
events = registry.get_events()
```

### CLI Commands

```bash
# Show telemetry system information
pyfulmen telemetry info

# List available metrics with current values
pyfulmen telemetry list

# Export metrics in Prometheus format
pyfulmen telemetry export --format prometheus
```

📖 **[Complete Telemetry Documentation](src/pyfulmen/telemetry/README.md)** for detailed API reference, Prometheus integration, and instrumentation patterns.

## Installation

### From PyPI (when published)

```bash
pip install pyfulmen
# or with uv
uv add pyfulmen
```

### From Local Wheel (for testing/development)

```bash
# Build the wheel
make build

# Install in another project
cd /path/to/your/project
pip install /path/to/pyfulmen/dist/pyfulmen-0.1.11-py3-none-any.whl

# Or with uv
uv add /path/to/pyfulmen/dist/pyfulmen-0.1.11-py3-none-any.whl
```

### Editable Install (for library development)

```bash
# Install pyfulmen in editable mode
cd /path/to/your/project
pip install -e /path/to/pyfulmen

# Or with uv
uv add --editable /path/to/pyfulmen
```

This allows you to modify PyFulmen code and see changes immediately without rebuilding.

## Usage

### Progressive Logging

PyFulmen provides a progressive logging system that grows with your needs:

```python
from pyfulmen.logging import Logger, LoggingProfile

# SIMPLE: Zero-complexity console logging (perfect for development)
logger = Logger(service="my-app")
logger.info("Application started")
logger.error("Connection failed", context={"host": "db.local"})

# STRUCTURED: Production-ready JSON logging
logger = Logger(
    service="api-service",
    profile=LoggingProfile.STRUCTURED,
    environment="production"
)
logger.info(
    "Request processed",
    context={"method": "GET", "path": "/api/users", "duration_ms": 45}
)

# ENTERPRISE: Compliance-grade logging with policy enforcement
# Note: Configure middleware through LoggingConfig for advanced use cases
logger = Logger(
    service="payment-api",
    profile=LoggingProfile.ENTERPRISE,
    environment="production"
    # Optional: policy_file=".goneat/logging-policy.yaml"
)
```

📖 **[Read the complete Logging Guide](docs/guides/logging.md)** for progressive profiles, middleware, policy enforcement, and best practices.

### Crucible Bridge API (v0.1.5+)

PyFulmen provides a unified bridge API for accessing Crucible assets with full metadata support. **This is the recommended pattern** for new code.

```python
from pyfulmen import crucible

# Discover available assets with metadata
categories = crucible.list_categories()  # ['docs', 'schemas', 'config']
assets = crucible.list_assets('schemas', prefix='observability')
for asset in assets:
    print(f"{asset.id}: {asset.format}, {asset.size} bytes, checksum: {asset.checksum[:8]}...")

# NEW in v0.1.5: Load assets with full metadata
schema, meta = crucible.find_schema('observability/logging/v1.0.0/logger-config')
print(f"Schema format: {meta.format}, size: {meta.size} bytes")

config, cfg_meta = crucible.find_config('terminal/v1.0.0/terminal-overrides-defaults')
print(f"Config checksum: {cfg_meta.checksum[:16]}...")

# Get raw documentation (preserves frontmatter for Docscribe)
doc, doc_meta = crucible.get_doc('standards/agentic-attribution.md')
print(f"Doc: {len(doc)} chars, format: {doc_meta.format}")

# Documentation with frontmatter processing (via Docscribe)
clean_content = crucible.get_documentation('standards/observability/logging.md')
metadata = crucible.get_documentation_metadata('standards/observability/logging.md')

# Get version metadata
version = crucible.get_crucible_version()
print(f"Crucible v{version.version} (commit: {version.commit})")
```

**Migration from Legacy APIs:**

```python
# Deprecated (v0.1.5, removal in v0.2.0) - still works but emits warnings
schema = crucible.load_schema_by_id('observability/logging/v1.0.0/logger-config')
config = crucible.get_config_defaults('terminal', 'v1.0.0', 'terminal-overrides-defaults')

# Recommended - use new helpers with metadata
schema, meta = crucible.find_schema('observability/logging/v1.0.0/logger-config')
config, cfg_meta = crucible.find_config('terminal/v1.0.0/terminal-overrides-defaults')
```

### Schema Export (v0.1.9+)

Export Crucible schemas to local files with provenance metadata, validation, and overwrite safeguards.

```python
from pyfulmen.schema import export_schema

# Export schema to JSON with provenance
path = export_schema(
    "observability/logging/v1.0.0/logger-config",
    "schemas/logger-config.json"
)
print(f"Exported to: {path}")

# Export to YAML without provenance
path = export_schema(
    "observability/logging/v1.0.0/logger-config",
    "schemas/logger-config.yaml",
    include_provenance=False
)

# Overwrite existing file
path = export_schema(
    "observability/logging/v1.0.0/logger-config",
    "schemas/logger-config.json",
    overwrite=True
)
```

**CLI Usage:**

```bash
# Export schema
uv run python -m pyfulmen.schema.cli export \
    observability/logging/v1.0.0/logger-config \
    --out schemas/logger-config.json

# Export without provenance
uv run python -m pyfulmen.schema.cli export \
    observability/logging/v1.0.0/logger-config \
    --out schemas/logger-config.json \
    --no-provenance

# Force overwrite
uv run python -m pyfulmen.schema.cli export \
    observability/logging/v1.0.0/logger-config \
    --out schemas/logger-config.json \
    --force

# Verbose output
uv run python -m pyfulmen.schema.cli export \
    observability/logging/v1.0.0/logger-config \
    --out schemas/logger-config.json \
    --verbose
```

**Key Features:**

- **Provenance Metadata** - Includes Crucible version, PyFulmen version, revision hash, and export timestamp
- **Format Support** - JSON and YAML output with automatic format detection
- **Validation** - Optional schema validation before export
- **Safety** - Overwrite protection with force option
- **CLI Integration** - Full command-line interface with exit codes

### Error Handling (v0.1.6+)

PyFulmen provides structured error handling with telemetry integration, extending Pathfinder errors with correlation tracking and severity classification.

```python
from pyfulmen import error_handling, logging
from datetime import datetime, UTC

# Create a Pathfinder error
base_error = error_handling.PathfinderError(
    code="CONFIG_LOAD_FAILED",
    message="Failed to load configuration file",
    details={"file": "/app/config.yaml", "reason": "File not found"},
    timestamp=datetime.now(UTC)
)

# Wrap with telemetry metadata
error = error_handling.wrap(
    base_error,
    severity="high",  # "info", "low", "medium", "high", "critical"
    context={"environment": "production", "version": "0.1.6"},
    correlation_id="req-abc123"  # Auto-populated from logging context if omitted
)

# Validate against Crucible schema
is_valid = error_handling.validate(error)  # Returns bool

# Log and exit gracefully (exits with code 1)
logger = logging.Logger(service="my-app")
# error_handling.exit_with_error(1, error, logger=logger)
# Logs error at appropriate severity level, then calls sys.exit(1)
```

**Key Features:**

- **Pathfinder Compatibility** - Extends standard Pathfinder error structure
- **Telemetry Integration** - Severity levels, correlation IDs, trace IDs
- **Schema Validation** - Validates against Crucible error-handling schemas
- **Graceful Exit** - Structured logging before process exit with severity mapping

### Telemetry & Metrics (v0.1.6+)

Record and validate application metrics with support for counters, gauges, and histograms conforming to the Crucible metrics taxonomy.

```python
from pyfulmen import telemetry, logging

# Create a metric registry
registry = telemetry.MetricRegistry()

# Record counter metrics
counter = registry.counter("schema_validations")
counter.inc()  # Increment by 1
counter.inc(5)  # Increment by 5

# Record gauge values (point-in-time measurements)
gauge = registry.gauge("active_connections")
gauge.set(42)

# Record histogram observations (with automatic bucketing)
histogram = registry.histogram("config_load_ms")
histogram.observe(12.5)
histogram.observe(45.2)
histogram.observe(8.3)

# Get recorded events
events = registry.get_events()  # Returns list[MetricEvent]

# Convert to JSON for export
event_dicts = [event.model_dump(mode="json") for event in events]

# Validate against Crucible metrics schema
is_valid = telemetry.validate_metric_event(event_dicts[0])

# Integrate with logging pipeline
logger = logging.Logger(service="my-app", profile=logging.LoggingProfile.STRUCTURED)
logging.emit_metrics_to_log(logger, event_dicts)
```

**Key Features:**

- **Three Metric Types** - Counter (monotonic), Gauge (instantaneous), Histogram (distribution)
- **Crucible Taxonomy** - Validates metric names against official taxonomy
- **Thread-Safe Registry** - Safe for concurrent metric recording
- **Histogram Bucketing** - Default buckets optimized for millisecond latencies
- **Logging Integration** - Export metrics through standard logging pipeline
- **Self-Instrumentation** - PyFulmen modules instrument themselves (Pathfinder, Config, Schema, Foundry, Logging)

📖 **[See examples/error_telemetry_demo.py](examples/error_telemetry_demo.py)** for a complete integration example.  
📖 **[See docs/development/telemetry-instrumentation-pattern.md](docs/development/telemetry-instrumentation-pattern.md)** for instrumentation patterns.

### FulHash - Fast, Consistent Hashing (v0.1.6+)

PyFulmen provides fast, deterministic hashing with xxh3-128 (default, fast) and sha256 (cryptographic) algorithms, designed for checksums, content addressing, and integrity verification across the Fulmen ecosystem.

```python
from pyfulmen import fulhash

# Block hashing (one-shot)
digest = fulhash.hash_bytes(b"Hello, World!")
print(digest.formatted)  # "xxh3-128:531df2844447dd5077db03842cd75395"

# String hashing with encoding
digest = fulhash.hash_string("Hello, World!", encoding="utf-8")

# File hashing (streaming internally)
from pathlib import Path
digest = fulhash.hash_file(Path("config.yaml"))

# Streaming API (for large data)
hasher = fulhash.stream(fulhash.Algorithm.XXH3_128)
hasher.update(b"chunk 1")
hasher.update(b"chunk 2")
digest = hasher.digest()

# Universal hash dispatcher
digest = fulhash.hash(b"bytes")           # Detects bytes
digest = fulhash.hash("string")           # Detects string
digest = fulhash.hash(Path("file.txt"))   # Detects Path

# Metadata helpers
checksum = fulhash.format_checksum("xxh3-128", "abc123...")  # "xxh3-128:abc123..."
algorithm, hex_value = fulhash.parse_checksum(checksum)
is_valid = fulhash.validate_checksum_string("xxh3-128:abc123...")
match = fulhash.compare_digests(digest1, digest2)  # Constant-time comparison
```

**Key Features:**

- **Two Algorithms** - xxh3-128 (default, 5-10x faster) and sha256 (cryptographic)
- **Thread-Safe** - All APIs safe for concurrent use (independent instances, no singletons)
- **Streaming Support** - Memory-efficient hashing of large files (64KB chunks)
- **Schema Compliance** - Validates against Crucible digest and checksum-string schemas
- **Cross-Language Fixtures** - Shared test vectors with gofulmen and tsfulmen
- **Production Ready** - 156 tests including 14 concurrency tests, 121K ops/sec sustained throughput

📖 **Thread Safety**: See [FulHash Thread Safety Guide](docs/fulhash_thread_safety.md) for concurrency guarantees and validation results.

📖 **Architecture**: See [ADR-0009](docs/development/adr/ADR-0009-fulhash-independent-stream-instances.md) for independent instance design rationale.

### Pathfinder - File Discovery with Checksums (v0.1.6+)

Fast file discovery with optional FulHash checksum calculation for integrity verification.

```python
from pyfulmen.pathfinder import Finder, FindQuery, FinderConfig

# Basic file discovery
finder = Finder()
results = finder.find_files(FindQuery(
    root="/path/to/project",
    include=["**/*.py", "**/*.json"],
    exclude=["**/__pycache__/**", "**/node_modules/**"]
))

for result in results:
    print(f"{result.relative_path}: {result.metadata.size} bytes")

# With checksums (opt-in)
finder = Finder(FinderConfig(
    calculateChecksums=True,
    checksumAlgorithm="xxh3-128"  # or "sha256"
))
results = finder.find_files(FindQuery(root="/path/to/project", include=["**/*.py"]))

for result in results:
    print(f"{result.relative_path}")
    print(f"  Size: {result.metadata.size} bytes")
    print(f"  Checksum: {result.metadata.checksum}")  # "xxh3-128:abc123..."
```

**Performance**: ~23,800 files/sec with checksums enabled. See [ADR-0010](docs/development/adr/ADR-0010-pathfinder-checksum-performance-acceptable-delta.md) for overhead analysis.

### Exit Codes - Standardized Process Exit Codes (v0.1.9+)

Standardized exit codes for consistent error reporting across the Fulmen ecosystem, with simplified mode mappings for monitoring systems.

```python
from pyfulmen.foundry import ExitCode, SimplifiedMode, get_exit_code_info, map_to_simplified

# Use semantic exit codes
import sys
sys.exit(ExitCode.EXIT_PORT_IN_USE.value)  # 10

# Get exit code metadata
info = get_exit_code_info(10)
print(info["name"])          # "EXIT_PORT_IN_USE"
print(info["description"])   # "Specified port is already in use"
print(info["category"])      # "networking"
print(info.get("retry_hint")) # "Check if port is available, try alternative port"

# Map to simplified modes (for monitoring/alerting)
simplified = map_to_simplified(10, SimplifiedMode.BASIC)
print(simplified)  # 1 (success=0, any_error=1)

simplified = map_to_simplified(10, SimplifiedMode.SEVERITY)
print(simplified)  # 2 (0=success, 1=warning, 2=error, 3=critical)

# Use with error handling
from pyfulmen.error_handling import FulmenError
from datetime import datetime, UTC

error = FulmenError(
    code="SERVER_STARTUP_FAILED",
    message="Failed to bind to port 8080",
    exit_code=ExitCode.EXIT_PORT_IN_USE.value,
    severity="high",
    timestamp=datetime.now(UTC),
    context={"port": 8080, "service": "api-server"}
)

# Log and exit with appropriate code
sys.exit(error.exit_code)
```

**54 Exit Codes across 11 categories**:

- **Standard** (0-1): SUCCESS, FAILURE
- **Networking** (10-15): PORT_IN_USE, CONNECTION_TIMEOUT, CONNECTION_REFUSED, etc.
- **Configuration** (20-24): CONFIG_INVALID, CONFIG_MISSING, CONFIG_PARSE_FAILED, etc.
- **Runtime** (30-34): TIMEOUT, OUT_OF_MEMORY, DISK_FULL, PROCESS_LIMIT, etc.
- **Usage** (40-44): USAGE_ERROR, NO_INPUT, DATAERR
- **Permissions** (50-54): PERMISSION_DENIED, EACCES, EPERM, ENOENT, etc.
- **Data** (60-63): VALIDATION_FAILED, CORRUPTION, FORMAT_ERROR, CHECKSUM_MISMATCH
- **Security** (70-73): AUTH_FAILED, CERT_INVALID, TOKEN_EXPIRED, CRYPTO_ERROR
- **Observability** (80-84): TELEMETRY_INIT_FAILED, LOGGING_INIT_FAILED, etc.
- **Testing** (91-96): TEST_FAILURE, TEST_TIMEOUT, FIXTURE_ERROR, etc.
- **Signals** (129-160): SIGHUP, SIGINT, SIGTERM, SIGKILL, SIGQUIT, etc.

**Key Features**:

- **Cross-Language Parity** - Same codes in gofulmen, pyfulmen, tsfulmen
- **Simplified Modes** - Basic (0/1) and Severity (0-3) for monitoring
- **Rich Metadata** - Description, context, category, retry hints
- **BSD Compatibility** - Maps to standard sysexits.h codes where applicable

### Other Features

```python
from pyfulmen import config, schema, version

# Get platform-aware config paths
config_dir = config.paths.get_fulmen_config_dir()

# Load config with three-layer merge
loader = config.loader.ConfigLoader()
cfg = loader.load('terminal/v1.0.0/terminal-overrides-defaults')

# Validate data against schemas
schema.validator.validate_data(
    category='observability/logging',
    version='v1.0.0',
    name='log-event',
    data={'severity': 'info'}
)

# Export schemas to local files
path = schema.export_schema(
    'observability/logging/v1.0.0/logger-config',
    'schemas/logger-config.json'
)
```

### Version Management

```python
from pyfulmen import version

# Read version from VERSION file
ver = version.read_version()  # "0.1.9"

# Get detailed version info
info = version.get_version_info()
# {'version': '0.1.9', 'source': 'VERSION', 'valid': True}

# Validate version sync across files
sync = version.validate_version_sync()
# {'synced': True, 'version_file': '0.1.9', ...}
```

## Development

This repository uses:

- **uv** for Python package management (fast, modern alternative to pip/virtualenv)
- **goneat** for version management and SSOT sync (successor to FulDX)
- **Crucible** for standards and schemas

### Prerequisites

Install `uv` (Python package manager):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv

# Or via pipx
pipx install uv
```

See [uv installation docs](https://github.com/astral-sh/uv#installation) for other platforms.

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/fulmenhq/pyfulmen.git
cd pyfulmen

# 2. Bootstrap development environment (creates .venv, installs tools and dependencies)
make bootstrap

# This command:
# - Creates .venv/ virtual environment (if not exists)
# - Installs goneat CLI tool
# - Installs all Python dependencies via uv
# - Syncs Crucible assets

# 3. Verify setup
make tools  # Check that goneat and other tools are available
make test   # Run test suite (should see 1343 tests passing)

# 4. Development cycle
make fmt              # Format code with Ruff
make lint             # Check linting
make test             # Run tests
make check-all        # Run all checks (lint + test)
```

### Manual Virtual Environment Setup (Optional)

The `make bootstrap` command handles this automatically, but if you need to create the virtual environment manually:

```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv sync --all-extras

# Verify installation
uv run pytest --version
uv run ruff --version
```

**Note**: `uv` manages the virtual environment automatically when you run `uv run <command>`, so you typically don't need to activate it manually.

### Building & Releasing

```bash
# Build wheel
make build

# Build with checksums
make release-build

# Run release checks
make release-check

# Bump version
make version-bump-patch  # or -minor, -major
```

### Makefile Targets

See `make help` for all available targets. Key commands:

| Target                | Description                    |
| --------------------- | ------------------------------ |
| `make bootstrap`      | Install tools and dependencies |
| `make tools`          | Verify external tools          |
| `make test`           | Run full test suite            |
| `make lint`           | Run linting checks             |
| `make fmt`            | Apply code formatting          |
| `make check-all`      | Run all checks                 |
| `make build`          | Build distributable package    |
| `make release-build`  | Build with checksums           |
| `make version`        | Print current version          |
| `make version-bump-*` | Bump version                   |

## Project Structure

```
pyfulmen/
├── src/pyfulmen/           # Main package
│   ├── crucible/          # Crucible shim (schemas, docs, config)
│   ├── config/            # Config paths and loading
│   ├── schema/            # Schema validation utilities
│   ├── logging/           # Observability integration
│   └── version.py         # Version management
├── tests/                 # Test suite
├── scripts/               # Build scripts
│   └── bootstrap.py       # Tool installation script
├── .crucible/             # Crucible integration
│   ├── tools.yaml         # Tool definitions
│   └── tools.local.yaml.example
├── .goneat/               # Goneat configuration
│   ├── tools.yaml         # Tool definitions
│   └── ssot-consumer.yaml # SSOT sync config
└── docs/                  # Documentation
    └── crucible-py/       # Synced Crucible docs
```

## Library Developers

**Note**: This section is for developers working on pyfulmen itself. Library users can skip this section.

### First-Time Setup

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and bootstrap
git clone https://github.com/fulmenhq/pyfulmen.git
cd pyfulmen
make bootstrap

# 3. Verify setup
make test  # Should see 1343 tests passing
```

The `.venv/` virtual environment is created automatically by `make bootstrap` (via `uv sync`).

### IDE Setup (VS Code / VSCodium)

We provide opinionated `.vscode/settings.json` configuration to eliminate false positive linter errors and configure the development environment optimally. This is a **convenience only** - the actual quality gates are enforced via:

- `make test` - Test suite (currently 1343 tests, 93% coverage)
- `make lint` - Ruff linting
- `make fmt` - Code formatting
- `make check-all` - All quality checks

The `.vscode/` configuration:

- Points Python interpreter to `.venv/bin/python`
- Configures Ruff as the formatter
- Enables format-on-save
- Sets up pytest integration
- Hides build artifacts and cache directories

**Recommended VS Code Extensions** (see `.vscode/extensions.json`):

- `ms-python.python` - Python language support
- `ms-python.vscode-pylance` - Fast, feature-rich language server
- `charliermarsh.ruff` - Ruff linting and formatting

### Development Workflow

```bash
# 1. Bootstrap environment (first time only)
make bootstrap

# 2. Sync Crucible assets (when schemas/docs update)
make sync-crucible

# 3. Development cycle
make fmt              # Format code
make lint             # Check linting
make test             # Run tests
make check-all        # Run all checks (lint + test)

# 4. Before commit
make precommit        # Runs fmt + lint
make prepush          # Runs check-all
```

### Quality Gates

**All contributions must pass**:

1. ✅ `make lint` - No linting errors
2. ✅ `make test` - All tests passing
3. ✅ `make test-cov` - Minimum coverage maintained (30% alpha, target 93%)
4. ✅ Type hints present for public APIs
5. ✅ Docstrings for all public functions/classes

**Note**: IDE linter warnings (e.g., "Import could not be resolved") are often false positives. The actual quality gate is `make lint` and `make test` passing.

### Testing

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
uv run pytest tests/unit/foundry/test_models.py -v

# Run specific test class
uv run pytest tests/unit/logging/test_severity.py::TestSeverityComparison -v
```

### Code Style

- **Formatter**: Ruff (line length: 100)
- **Linter**: Ruff with pyproject.toml configuration
- **Type Hints**: Required for public APIs (Python 3.12+)
- **Docstrings**: Google style
- **Imports**: Organized automatically by Ruff

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Ensure all quality gates pass (`make check-all`).
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
5. Push to the branch (`git push origin feature/AmazingFeature`).
6. Open a Pull Request.

PyFulmen follows the [Fulmen Helper Library Standard](docs/crucible-py/architecture/fulmen-helper-library-standard.md).

See [Python Coding Standards](docs/crucible-py/standards/coding/python.md) for code style guidelines.

### Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for more information.

### Attribution

AI-assisted contributions should be attributed in commits:

```
feat: add schema validation utilities

Co-authored-by: Agent Name <noreply@3leaps.net>
```

For more details, see [MAINTAINERS.md](MAINTAINERS.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Licensing

[pyfulmen](https://github.com/fulmenhq/pyfulmen) is licensed under MIT license - see [LICENSE](LICENSE) for complete details.

**Trademarks**: "Fulmen" and "3 Leaps" are trademarks of 3 Leaps, LLC. While code is open source, please use distinct names for derivative works to prevent confusion.

### OSS Policies (Organization-wide)

- Authoritative policies repository: https://github.com/3leaps/oss-policies/
- Code of Conduct: https://github.com/3leaps/oss-policies/blob/main/CODE_OF_CONDUCT.md
- Security Policy: https://github.com/3leaps/oss-policies/blob/main/SECURITY.md
- Contributing Guide: https://github.com/3leaps/oss-policies/blob/main/CONTRIBUTING.md

## Status

**Lifecycle Phase**: `alpha` ([Repository Lifecycle Standard](docs/crucible-py/standards/repository-lifecycle.md))

- **Quality Bar**: 30% minimum test coverage (currently: 93%)
- **Stability**: Early adopters; rapidly evolving features
- **Breaking Changes**: Expected without deprecation warnings
- **Documentation**: Major gaps documented; kept current

See `LIFECYCLE_PHASE` file and [CHANGELOG.md](CHANGELOG.md) for version history.

---

<div align="center">

⚡ **Python Foundation for the Fulmen Ecosystem** ⚡

_Idiomatic Python access to Crucible schemas, platform-aware config paths, and three-layer configuration loading_

<br><br>

**Built with 🔨 by the 3 Leaps team**
**Part of the [Fulmen Ecosystem](https://fulmenhq.dev) - Lightning-fast enterprise development**

**Crucible Integration** • **Config Management** • **Schema Validation** • **Observability**

</div>
