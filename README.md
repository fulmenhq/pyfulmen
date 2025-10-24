# pyfulmen

Python Fulmen libraries for enterprise-scale development.

**Lifecycle Phase**: `alpha` | **Version**: 0.1.6 | **Coverage**: 93%

## Overview

PyFulmen is part of the Fulmen ecosystem, providing templates, processes, and tools for enterprise-scale development in Python.

📖 **[Read the full PyFulmen Overview](docs/pyfulmen_overview.md)** for a comprehensive guide to modules, observability features, and the roadmap.

> **Alpha Status**: Early adopters; rapidly evolving features. Minimum coverage: 30%. See [Repository Lifecycle Standard](docs/crucible-py/standards/repository-lifecycle.md) for quality expectations.

**Key Features:**

- **Progressive Logging** - Zero-complexity to enterprise-grade logging with SIMPLE → STRUCTURED → ENTERPRISE profiles
- **Error Handling** - Pathfinder-compatible errors with telemetry metadata and schema validation (v0.1.6+)
- **Telemetry & Metrics** - Counter/gauge/histogram recording with Crucible taxonomy validation (v0.1.6+)
- **FulHash** - Fast, consistent hashing with xxh3-128 (default) and sha256 support, thread-safe streaming (v0.1.6+)
- **Crucible Shim** - Idiomatic Python access to Crucible schemas, docs, and config defaults
- **Config Path API** - XDG-compliant, platform-aware configuration paths
- **Three-Layer Config Loading** - Crucible defaults → User overrides → App config
- **Schema Validation** - Helpers for validating data against Crucible JSON schemas
- **Version Management** - Utilities for reading and validating repository versions

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
pip install /path/to/pyfulmen/dist/pyfulmen-0.1.5-py3-none-any.whl

# Or with uv
uv add /path/to/pyfulmen/dist/pyfulmen-0.1.5-py3-none-any.whl
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
```

### Version Management

```python
from pyfulmen import version

# Read version from VERSION file
ver = version.read_version()  # "0.1.3"

# Get detailed version info
info = version.get_version_info()
# {'version': '0.1.3', 'source': 'VERSION', 'valid': True}

# Validate version sync across files
sync = version.validate_version_sync()
# {'synced': True, 'version_file': '0.1.3', ...}
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
make test   # Run test suite (should see 613 tests passing)

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
make test  # Should see 613 tests passing
```

The `.venv/` virtual environment is created automatically by `make bootstrap` (via `uv sync`).

### IDE Setup (VS Code / VSCodium)

We provide opinionated `.vscode/settings.json` configuration to eliminate false positive linter errors and configure the development environment optimally. This is a **convenience only** - the actual quality gates are enforced via:

- `make test` - Test suite (currently 613 tests, 93% coverage)
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
