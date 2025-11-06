---
title: "PyFulmen Overview"
description: "Python foundation library for the Fulmen ecosystem"
author: "PyFulmen Architect"
date: "2025-10-11"
last_updated: "2025-11-06"
status: "active"
lifecycle_phase: "alpha"
version: "0.1.12"
tags:
  ["python", "library", "fulmen", "enterprise", "telemetry", "observability"]
---

# PyFulmen Overview

## Purpose & Scope

**PyFulmen** is the Python foundation library for the FulmenHQ ecosystem, providing enterprise-grade capabilities for configuration management, observability, schema validation, and Crucible integration. It follows the [Fulmen Helper Library Standard](docs/crucible-py/architecture/fulmen-helper-library-standard.md) and enables Python applications to adopt progressive interfaces—starting with zero-complexity defaults and scaling to full enterprise features as requirements grow.

### Design Philosophy

- **Progressive Interfaces**: Simple defaults for CLI tools, structured capabilities for services, full enterprise features for production workloads
- **Enterprise First**: Production-ready from the start with comprehensive testing, type safety, and observability
- **Standards Compliance**: Implements all mandatory capabilities from the Fulmen Helper Library Standard
- **Developer Experience**: Idiomatic Python APIs with clear documentation and comprehensive examples

### Target Audience

- **Python Developers** building enterprise applications with Fulmen ecosystem integration
- **CLI Tool Authors** requiring structured logging and configuration management
- **API/Service Developers** needing production-grade observability and schema validation
- **Platform Engineers** standardizing Python tooling across organizations

## Crucible Overview

**What is Crucible?**

Crucible is the FulmenHQ single source of truth (SSOT) for schemas, standards, and configuration templates. It ensures consistent APIs, documentation structures, and behavioral contracts across all language foundations (gofulmen, pyfulmen, tsfulmen, etc.).

**Why the Shim & Docscribe Module?**

Rather than copying Crucible assets into every project, helper libraries provide idiomatic access through shim APIs. This keeps your application lightweight, versioned correctly, and aligned with ecosystem-wide standards. The docscribe module lets you discover, parse, and validate Crucible content programmatically without manual file management.

**Where to Learn More:**

- [Crucible Repository](https://github.com/fulmenhq/crucible) - SSOT schemas, docs, and configs
- [Fulmen Technical Manifesto](docs/crucible-py/architecture/fulmen-technical-manifesto.md) - Philosophy and design principles
- [SSOT Sync Standard](docs/crucible-py/standards/library/modules/ssot-sync.md) - How libraries stay synchronized

## Module Catalog

PyFulmen implements the mandatory core modules defined in the [Module Manifest](config/crucible-py/library/v1.0.0/module-manifest.yaml). Each module follows the progressive interface pattern and targets 90%+ test coverage.

| Module ID                      | Status    | Coverage Target | Specification                                                            | Description                                                                                                   |
| ------------------------------ | --------- | --------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| **app-identity**               | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/library/modules/app-identity.md)       | Canonical application metadata with discovery, validation, and caching (v0.1.10+)                             |
| **crucible-shim**              | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/library/modules/crucible-shim.md)      | Idiomatic Python access to Crucible schemas, docs, and config defaults via bridge API                         |
| **docscribe**                  | ✅ Stable | 95%             | [Spec](docs/crucible-py/standards/library/modules/docscribe.md)          | Frontmatter parsing, header extraction, and clean content access for markdown assets (v0.1.4+)                |
| **config-path-api**            | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/config/fulmen-config-paths.md)         | Platform-aware config/data/cache paths (XDG-compliant on Linux/macOS, Windows-aware)                          |
| **three-layer-config**         | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/library/modules/three-layer-config.md) | Crucible defaults → User overrides → Runtime config with YAML/JSON support                                    |
| **schema-validation**          | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/library/modules/schema-validation.md)  | JSON Schema validation helpers using jsonschema library                                                       |
| **observability-logging**      | ✅ Stable | 95%             | [Spec](docs/crucible-py/standards/observability/logging.md)              | Progressive logging with SIMPLE/STRUCTURED/ENTERPRISE profiles, policy enforcement                            |
| **error-handling-propagation** | ✅ Stable | 95%             | [Spec](docs/crucible-py/standards/error-handling/)                       | Pathfinder error wrapper with telemetry metadata, severity mapping, schema validation (v0.1.6+)               |
| **telemetry-metrics**          | ✅ Stable | 85%             | [Spec](docs/crucible-py/standards/observability/metrics/)                | Counter/gauge/histogram with Crucible taxonomy validation, logging integration (v0.1.6+)                      |
| **fulhash**                    | ✅ Stable | 95%             | [Spec](docs/crucible-py/standards/library/modules/fulhash.md)            | Fast, consistent hashing with xxh3-128/sha256, thread-safe streaming, cross-language fixtures (v0.1.6+)       |
| **signal-handling**            | ✅ Stable | 95%             | [Spec](docs/crucible-py/standards/library/modules/signal-handling.md)    | Cross-platform signal handling with Windows fallback, asyncio integration, and enterprise features (v0.1.11+) |
| **goneat-bootstrap**           | ✅ Stable | 90%             | [Spec](docs/crucible-py/guides/bootstrap-goneat.md)                      | Goneat tool installation and SSOT sync automation                                                             |
| **ssot-sync**                  | ✅ Stable | 90%             | -                                                                        | Automated sync of Crucible assets via goneat                                                                  |
| **foundry-patterns**           | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/library/foundry/interfaces.md)         | Pattern catalogs, MIME detection, HTTP status helpers                                                         |

### Extension Modules (Optional)

| Module ID         | Status     | Notes                                                                            |
| ----------------- | ---------- | -------------------------------------------------------------------------------- |
| **pathfinder**    | ✅ Stable  | Filesystem scanning with include/exclude patterns (47 tests, 90%+ coverage)      |
| **ascii-helpers** | ✅ Stable  | Console formatting utilities (tables, boxes, progress) (48 tests, 90%+ coverage) |
| **cloud-storage** | 📋 Planned | Unified S3/GCS/Azure Blob helpers                                                |

**Legend**: ✅ Stable | 🔄 Active Development | 📋 Planned | ⚠️ Deprecated

### Module Highlights: Application Identity (v0.1.10+)

**Purpose**: Canonical application metadata management with Crucible v0.2.4 compliance

**Core Features**:

- **Progressive Interface**: Zero-complexity defaults with enterprise power-ups
- **Auto-Discovery**: Environment override and ancestor search for `.fulmen/app.yaml`
- **Validation**: Schema-compliant validation with detailed error guidance
- **Caching**: Thread-safe process-level caching with test override support
- **CLI Tools**: Show and validate commands with JSON/text output

**APIs**:

- Discovery: `get_identity()`, `load_from_path()`, `reload()`
- Testing: `override_identity_for_testing()` context manager
- CLI: `pyfulmen appidentity show`, `pyfulmen appidentity validate`

**Integration**:

- Seamless config module integration for env prefixes and file names
- Backward-compatible APIs with optional identity parameters
- Cross-language parity preparation with gofulmen/tsfulmen

**Quality Metrics**:

- 64 comprehensive tests with 100% functionality coverage
- 87.14% total test coverage across all modules
- Enterprise-grade reliability with performance optimization
- Complete documentation with examples and troubleshooting

**Dependencies**: yaml (safe loading), jsonschema (validation)

### Module Highlights: Signal Handling (v0.1.11+)

**Purpose**: Cross-platform signal handling with Windows fallback, asyncio integration, and enterprise features

**Core Features**:

- **Cross-Platform Support**: Unix signals with Windows HTTP endpoint fallbacks
- **Asyncio Integration**: Safe async and sync signal handler execution
- **Progressive Interface**: Zero-complexity defaults with enterprise power-ups
- **Structured Logging**: Comprehensive logging with contextual information
- **Telemetry Emission**: Signal events with proper metadata and tags
- **Config Reload**: Restart-based configuration reload with validation
- **HTTP Helpers**: Windows fallback signal management via HTTP endpoints

**APIs**:

- Signal Registration: `on_shutdown()`, `on_reload()`, `on_force_quit()`
- Config Management: `reload_config()`, `register_shutdown_callback()`
- HTTP Helpers: `get_http_helper()`, `build_signal_request()`
- Platform Support: `supports_signal()`, `get_module_info()`

**Integration**:

- Seamless logging module integration with structured context
- Telemetry module integration for signal event emission
- Config module integration for reload workflows
- Application identity integration for validation

**Quality Metrics**:

- 143 comprehensive tests with 100% functionality coverage
- Cross-platform compatibility (Linux, macOS, Windows)
- Enterprise-grade reliability with fallback mechanisms
- Complete documentation with examples and migration guide

**Dependencies**: No additional runtime dependencies (uses only Python stdlib)

### Module Highlights: Enterprise Telemetry (v0.1.12+)

**Purpose**: Comprehensive enterprise telemetry with MetricRegistry, Prometheus export, and cross-module instrumentation implementing ADR-0008

**Core Features**:

- **MetricRegistry**: Thread-safe metrics collection with atomic operations and concurrent access support
- **Three Metric Types**: Counter (monotonic), Gauge (instantaneous), Histogram (distribution with buckets)
- **Prometheus Export**: `/metrics` endpoint with comprehensive metric formatting and metadata
- **Module-Level Helpers**: `counter()`, `gauge()`, `histogram()` for zero-complexity usage
- **Cross-Module Integration**: Foundry, Error Handling, and FulHash modules automatically instrumented
- **Performance Optimization**: <1ms typical overhead with import optimization for sensitive modules

**APIs**:

- Core Registry: `MetricRegistry`, `Counter`, `Gauge`, `Histogram`
- Helpers: `counter()`, `gauge()`, `histogram()`, `get_global_registry()`
- Export: `PrometheusExporter`, `export()` for Prometheus format
- CLI: `pyfulmen telemetry info`, `pyfulmen telemetry list`, `pyfulmen telemetry export`

**Integration**:

- **Foundry Module**: MIME detection telemetry (`foundry_mime_detections_total_*`, `foundry_mime_detection_ms_*`)
- **Error Handling**: Wrap operation telemetry (`error_handling_wraps_total`, `error_handling_wrap_ms`)
- **FulHash Module**: Algorithm-specific hashing telemetry (`fulhash_operations_total_*`, `fulhash_bytes_hashed_total`, `fulhash_operation_ms`)
- Thread-safe singleton pattern with automatic cleanup
- Performance-optimized histogram implementations

**Quality Metrics**:

- 26 comprehensive tests (17 unit + 9 integration, 100% pass rate)
- Thread safety validated with concurrent access patterns
- Performance benchmarks meeting enterprise requirements (<1ms overhead)
- Prometheus export compliance verified
- Memory efficiency validated with large-scale metric collection

**Dependencies**: No additional runtime dependencies (uses only Python stdlib)

### Module Highlights: FulHash (v0.1.6+)

**Purpose**: Fast, consistent hashing for checksums, content addressing, and integrity verification

**Algorithms**:

- xxh3-128 (default): Fast non-cryptographic hashing (5-10x faster than SHA-256)
- sha256: Cryptographic hashing for security-sensitive use cases

**APIs**:

- Block hashing: `hash_bytes()`, `hash_string()`, `hash_file()`, `hash()` dispatcher
- Streaming: `stream()` creates independent `StreamHasher` instances
- Metadata: `format_checksum()`, `parse_checksum()`, `validate_checksum_string()`, `compare_digests()`

**Thread Safety**: Independent instances by design (no singletons), validated with 14 concurrency tests

**Performance**: 121,051 ops/sec sustained throughput, memory-safe under concurrent load

**Cross-Language**: Shared fixtures with gofulmen and tsfulmen for consistent behavior

**Dependencies**: xxhash (fast hashing), hashlib (stdlib, sha256)

**Documentation**:

- [FulHash Thread Safety Guide](../fulhash_thread_safety.md)
- [ADR-0009: Independent Stream Instances](development/adr/ADR-0009-fulhash-independent-stream-instances.md)

## Observability Highlights

PyFulmen implements the **Progressive Logging Standard** with three profile levels designed to match application complexity:

### SIMPLE Profile

- **Use Case**: CLI tools, scripts, local development
- **Features**: Console-only output, minimal configuration
- **Configuration**: Service name only (`service: mycli`)
- **Output**: Human-readable text to stderr

### STRUCTURED Profile

- **Use Case**: API services, background jobs, dev/staging workloads
- **Features**: Multiple sinks (console, file, rolling-file), structured JSON output, correlation IDs
- **Configuration**: Service name + sink definitions
- **Output**: Newline-delimited JSON with full event envelope

### ENTERPRISE Profile

- **Use Case**: Production services, workhorses, regulated environments
- **Features**: Multiple sinks, middleware pipeline (redaction, correlation, throttling), policy enforcement, external log shipping
- **Configuration**: Service + sinks + middleware + optional policy file
- **Output**: Structured JSON with middleware transformations, compliance-ready

### Event Envelope

All structured log events emit JSON following the Crucible logging schema:

```json
{
  "timestamp": "2025-10-11T14:32:15.123456789Z",
  "severity": "INFO",
  "severityLevel": 20,
  "message": "Request processed successfully",
  "service": "myapp",
  "component": "api",
  "environment": "production",
  "correlationId": "01927d5c-8f4a-7890-b123-456789abcdef",
  "requestId": "req-abc123",
  "operation": "/api/v1/users",
  "durationMs": 45.2,
  "context": { "userId": "user-123" }
}
```

### Policy Enforcement

Organizations can define logging policies (`.goneat/logging-policy.yaml`) to enforce governance:

- **Allowed Profiles**: Restrict which profiles can be used (e.g., production must use ENTERPRISE)
- **Required Features**: Mandate middleware like secret redaction for compliance
- **Environment Rules**: Enforce profile selection based on deployment environment
- **Audit Settings**: Log policy violations and optionally fail-fast on non-compliance

Example policy:

```yaml
allowedProfiles: [STRUCTURED, ENTERPRISE]
requiredProfiles:
  workhorse: [ENTERPRISE]
environmentRules:
  production: [ENTERPRISE]
profileRequirements:
  ENTERPRISE:
    requiredFeatures: [correlation, middleware, throttling]
auditSettings:
  logPolicyViolations: true
  enforceStrictMode: true
```

### Middleware Pipeline

ENTERPRISE profile supports pluggable middleware for log event processing:

- **redact-secrets**: Remove sensitive data (API keys, tokens, passwords)
- **redact-pii**: Scrub personally identifiable information
- **correlation**: Inject correlation IDs (UUIDv7 for time-sortable identifiers)
- **throttle**: Apply rate limiting and backpressure protection
- **custom**: User-defined middleware for organization-specific requirements

### Severity Levels

Crucible logging severity enum maps to Python logging levels:

| Crucible | Numeric | Python   | Usage                                        |
| -------- | ------- | -------- | -------------------------------------------- |
| TRACE    | 0       | DEBUG    | Highly verbose diagnostics                   |
| DEBUG    | 10      | DEBUG    | Debug-level details                          |
| INFO     | 20      | INFO     | Core operational events                      |
| WARN     | 30      | WARNING  | Unusual but non-breaking conditions          |
| ERROR    | 40      | ERROR    | Request/operation failure (recoverable)      |
| FATAL    | 50      | CRITICAL | Unrecoverable failure, program exit expected |
| NONE     | 60      | -        | Explicitly disable emission                  |

## Docscribe Module APIs (v0.1.4+)

PyFulmen provides enhanced documentation processing with frontmatter parsing, header extraction, and clean content reads through the standalone `docscribe` module. These APIs enable tools to extract structured metadata (YAML headers), generate table of contents, and access clean markdown bodies, supporting runtime doc discovery and integration with rendering tools.

### Core APIs

All new documentation functions are exported at the top level of the `crucible` package:

```python
from pyfulmen import crucible

# Get clean markdown body (frontmatter stripped)
content = crucible.get_documentation('standards/observability/logging.md')
render_markdown(content)  # No YAML noise

# Get metadata only
metadata = crucible.get_documentation_metadata('standards/observability/logging.md')
print(f"Status: {metadata['status']}")
print(f"Tags: {metadata['tags']}")

# Get both together (more efficient)
content, metadata = crucible.get_documentation_with_metadata('guides/bootstrap-goneat.md')
if metadata:
    print(f"Reading guide by {metadata.get('author', 'Unknown')}")
    print(f"Last updated: {metadata.get('last_updated', 'N/A')}")
display(content)
```

### Error Handling

Documentation APIs provide helpful error messages with suggestions:

```python
from pyfulmen.crucible import AssetNotFoundError, ParseError

try:
    content = crucible.get_documentation('invalid/path.md')
except AssetNotFoundError as e:
    print(f"Not found: {e.asset_id}")
    print(f"Did you mean: {', '.join(e.suggestions)}")

try:
    metadata = crucible.get_documentation_metadata('malformed.md')
except ParseError as e:
    print(f"Invalid YAML: {e}")
```

### Frontmatter Format

Documentation files may include YAML frontmatter delimited by `---`:

```markdown
---
title: "My Document"
author: "Jane Doe"
date: "2025-10-20"
status: "stable"
tags: ["python", "documentation"]
---

# Document Content

The actual markdown content starts here...
```

The `get_documentation()` function returns only the markdown body (below the closing `---`), while `get_documentation_metadata()` returns the parsed YAML as a dictionary.

### Backward Compatibility

Legacy APIs remain available for code that needs raw content with frontmatter included:

```python
from pyfulmen.crucible import docs

# Legacy API - returns raw content WITH frontmatter
raw_content = docs.read_doc('standards/observability/logging.md')
assert raw_content.startswith('---')

# Enhanced API - returns clean content WITHOUT frontmatter
clean_content = crucible.get_documentation('standards/observability/logging.md')
assert not clean_content.startswith('---')
```

### Config Loading (Phase 2 - Coming in v0.1.5)

**Note**: `crucible.load_config()` wrapper with schema validation is planned for Phase 2. For now, use the existing Three-Layer Config system:

```python
from pyfulmen.config.loader import ConfigLoader

# Load config using three-layer system
loader = ConfigLoader()
config = loader.load('observability/logging/v1.0.0/logging-policy')

# Or load with metadata tracking
result = loader.load_with_metadata('observability/logging/v1.0.0/logging-policy')
print(f"Loaded from: {[s.layer for s in result.sources]}")
```

Phase 2 will add a convenience wrapper at `crucible.load_config()` that integrates frontmatter-aware config loading with schema validation.

### Performance

Frontmatter extraction is lightweight (~50 LOC parser using `pyyaml`):

- Average extraction: <10ms per document
- 100 iterations: <1s total
- Module-level caching for repeated access (future enhancement)

## Dependency Map

PyFulmen's dependency structure follows the Fulmen ecosystem model to prevent circular dependencies:

| Dependency Type    | Packages                                            | Notes                                                |
| ------------------ | --------------------------------------------------- | ---------------------------------------------------- |
| **Runtime**        | `jsonschema>=4.25.1`, `pyyaml>=6.0.3`               | Core validation and config parsing                   |
| **Development**    | `pytest>=8.0.0`, `pytest-cov>=4.1.0`, `ruff>=0.1.0` | Testing and quality tools                            |
| **Python Runtime** | Python 3.12+                                        | Type hints, pattern matching, modern stdlib features |
| **SSOT Assets**    | Crucible (synced via goneat)                        | Schemas, docs, config defaults (committed to repo)   |
| **Tooling**        | goneat (CLI tool)                                   | SSOT sync, version management, bootstrap             |

### Dependency Flow

```
┌─────────────┐
│  Crucible   │  (SSOT: schemas, docs, standards)
│   (synced)  │
└──────┬──────┘
       │
       ├─▶ docs/crucible-py/     (documentation)
       ├─▶ schemas/crucible-py/  (JSON/YAML schemas)
       └─▶ config/crucible-py/   (config defaults)
              │
              ▼
       ┌─────────────┐
       │  PyFulmen   │  (Python foundation library)
       └──────┬──────┘
              │
              ├─▶ Application code
              ├─▶ CLI tools
              └─▶ API services
```

### No Circular Dependencies

- **PyFulmen → Crucible**: One-way dependency (read-only sync)
- **PyFulmen → goneat**: Tool dependency (CLI invocation only, not imported)
- **Applications → PyFulmen**: Standard library import (`import pyfulmen`)

## Roadmap & Gaps

### Current Release (v0.1.12)

**Status**: Alpha - Core modules stable, Enterprise Telemetry system complete

**Completed**:

- ✅ Crucible shim with schema/doc/config access
- ✅ Config path API (XDG-compliant, Windows-aware)
- ✅ Three-layer config loading
- ✅ Schema validation utilities (catalog + CLI)
- ✅ Goneat bootstrap automation
- ✅ Progressive logging profiles (SIMPLE/STRUCTURED/ENTERPRISE)
- ✅ Logging policy enforcement
- ✅ Middleware pipeline implementation
- ✅ Throttling and backpressure management
- ✅ Foundry patterns module (pattern catalogs, MIME detection, HTTP status helpers)
- ✅ Foundry Similarity v2.0.0 (4 metrics, 4 normalization presets, 78 tests)
- ✅ Pathfinder module (filesystem scanning with glob patterns, 90 tests)
- ✅ ASCII helpers (console formatting, box drawing, 48 tests)
- ✅ Docscribe module (frontmatter parsing, header extraction, outline generation, 92 tests)
- ✅ Error Handling module (Pathfinder error wrapper, telemetry metadata, schema validation)
- ✅ Telemetry & Metrics module (counter/gauge/histogram, Crucible taxonomy validation)
- ✅ FulHash module (xxh3-128/sha256 hashing, thread-safe streaming, 156 tests)
- ✅ Telemetry Retrofit Complete (all 8 modules instrumented with 16 metrics, Phases 1.5-8)
- ✅ Application Identity module (canonical metadata, discovery, validation, caching, 64 tests)
- ✅ Signal Handling module (cross-platform, Windows fallback, asyncio integration, 143 tests)
- ✅ Enterprise Telemetry system (MetricRegistry, Prometheus export, cross-module integration, 26 tests)

**Test Coverage**: 268 tests passing (259 baseline + 9 new telemetry integration tests), 93% coverage across all modules

### Next Release (v0.2.0)

**Target**: Q1 2026

**Planned Features**:

- Enhanced correlation ID propagation (HTTP headers, gRPC metadata)
- Tracing integration (OpenTelemetry compatibility)
- External sink support (HTTP/HTTPS log shipping)
- Performance optimizations for high-throughput logging
- Async logging support for high-throughput services

### Future Releases

**v0.3.0+**:

- Cloud storage helpers (S3/GCS/Azure)
- Metrics and tracing modules (full observability stack)
- Enhanced CLI tooling integration
- Performance benchmarks and optimization

### Known Gaps

| Gap                         | Priority | Target Version | Notes                                   |
| --------------------------- | -------- | -------------- | --------------------------------------- |
| External sinks (HTTP/HTTPS) | High     | v0.2.0         | Required for enterprise log aggregation |
| Async logging support       | Medium   | v0.2.0         | For high-throughput services            |
| Windows path edge cases     | Low      | v0.2.0         | Best-effort Windows support             |
| Performance benchmarks      | Medium   | v0.2.0         | Establish baseline metrics              |
| Tracing integration         | Medium   | v0.2.0         | OpenTelemetry compatibility             |

### Breaking Changes Policy

Following semantic versioning:

- **Patch (0.1.x)**: Bug fixes, no breaking changes
- **Minor (0.x.0)**: New features, backward compatible
- **Major (x.0.0)**: Breaking API changes (rare, with migration guides)

Pre-1.0 releases may introduce breaking changes with minor version bumps. All breaking changes will be documented in CHANGELOG.md with migration guides.

## Getting Started

### Installation

```bash
pip install pyfulmen
```

### Quick Start with Bridge API (Recommended)

PyFulmen v0.1.4+ provides a unified bridge API for accessing Crucible assets. **This is the recommended pattern** for new code:

```python
from pyfulmen import crucible

# Discover available assets
categories = crucible.list_categories()  # ['docs', 'schemas', 'config']
schemas = crucible.list_assets('schemas', prefix='observability')

# Load schemas and documentation
schema = crucible.load_schema_by_id('observability/logging/v1.0.0/logger-config')
doc = crucible.get_documentation('standards/observability/logging.md')

# Stream large assets efficiently
with crucible.open_asset('architecture/fulmen-helper-library-standard.md') as f:
    content = f.read()

# Get version metadata
version = crucible.get_crucible_version()
print(f"Crucible v{version.version}")
```

### Legacy API (Still Supported)

Legacy APIs are maintained for backward compatibility but bridge API is recommended for new code:

```python
from pyfulmen import crucible, config, schema, logging

# Legacy Crucible access (still works)
schemas = crucible.schemas.list_available_schemas()
doc = crucible.docs.read_doc('guides/bootstrap-goneat.md')

# Config and schema validation (unchanged)
config_dir = config.paths.get_fulmen_config_dir()

loader = config.loader.ConfigLoader()
cfg = loader.load('terminal/v1.0.0/terminal-overrides-defaults')

schema.validator.validate_against_schema(
    data={
        'topLeft': '┌',
        'topRight': '┐',
        'bottomLeft': '└',
        'bottomRight': '┘',
        'horizontal': '─',
        'vertical': '│',
        'cross': '┼',
    },
    category='ascii',
    version='v1.0.0',
    name='box-chars'
)

logger = logging.logger.configure_logging(app_name='myapp', level='debug')
logger.info('Application started')
```

### Schema CLI (Experimental)

PyFulmen ships a lightweight Click-based CLI for exploring schemas and running ad-hoc validation locally. For CI/CD pipelines continue to use `goneat schema validate-*` as the authoritative validator.

```bash
# list schemas with a prefix filter
python -m pyfulmen.schema.cli list --prefix ascii/

# view metadata
python -m pyfulmen.schema.cli info ascii/v1.0.0/box-chars

# validate a payload using the built-in jsonschema engine
python -m pyfulmen.schema.cli validate ascii/v1.0.0/box-chars --file payload.json --no-goneat

# opt-in to goneat integration when the binary is available
python -m pyfulmen.schema.cli validate ascii/v1.0.0/box-chars --file payload.json --use-goneat

# pipeline helper (defaults to goneat, falls back to CLI)
./scripts/validate-schema.sh ascii/v1.0.0/box-chars --file payload.json
```

## References

- **Repository**: https://github.com/fulmenhq/pyfulmen
- **Documentation**: [README.md](../README.md)
- **Standards**: [Fulmen Helper Library Standard](docs/crucible-py/architecture/fulmen-helper-library-standard.md)
- **Logging Standard**: [Observability Logging](docs/crucible-py/standards/observability/logging.md)
- **Maintainers**: [MAINTAINERS.md](../MAINTAINERS.md)
- **Safety Protocols**: [REPOSITORY_SAFETY_PROTOCOLS.md](../REPOSITORY_SAFETY_PROTOCOLS.md)

## Support & Contribution

- **Issues**: https://github.com/fulmenhq/pyfulmen/issues
- **Discussions**: https://github.com/fulmenhq/pyfulmen/discussions
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)

---

_Generated by PyFulmen Architect (@pyfulmen-architect) under supervision of @3leapsdave_
