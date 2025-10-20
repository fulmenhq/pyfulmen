---
title: "PyFulmen Overview"
description: "Python foundation library for the Fulmen ecosystem"
author: "PyFulmen Architect"
date: "2025-10-11"
last_updated: "2025-10-17"
status: "active"
lifecycle_phase: "alpha"
version: "0.1.3"
tags: ["python", "library", "fulmen", "enterprise"]
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

## Module Catalog

PyFulmen implements the mandatory core modules defined in the [Module Manifest](config/crucible-py/library/v1.0.0/module-manifest.yaml). Each module follows the progressive interface pattern and targets 90%+ test coverage.

| Module ID                 | Status    | Coverage Target | Specification                                                            | Description                                                                          |
| ------------------------- | --------- | --------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| **crucible-shim**         | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/library/modules/crucible-shim.md)      | Idiomatic Python access to Crucible schemas, docs, and config defaults               |
| **config-path-api**       | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/config/fulmen-config-paths.md)         | Platform-aware config/data/cache paths (XDG-compliant on Linux/macOS, Windows-aware) |
| **three-layer-config**    | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/library/modules/three-layer-config.md) | Crucible defaults → User overrides → Runtime config with YAML/JSON support           |
| **schema-validation**     | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/library/modules/schema-validation.md)  | JSON Schema validation helpers using jsonschema library                              |
| **observability-logging** | ✅ Stable | 95%             | [Spec](docs/crucible-py/standards/observability/logging.md)              | Progressive logging with SIMPLE/STRUCTURED/ENTERPRISE profiles, policy enforcement   |
| **goneat-bootstrap**      | ✅ Stable | 90%             | [Spec](docs/crucible-py/guides/bootstrap-goneat.md)                      | Goneat tool installation and SSOT sync automation                                    |
| **ssot-sync**             | ✅ Stable | 90%             | -                                                                        | Automated sync of Crucible assets via goneat                                         |
| **foundry-patterns**      | ✅ Stable | 90%             | [Spec](docs/crucible-py/standards/library/foundry/interfaces.md)         | Pattern catalogs, MIME detection, HTTP status helpers                                |

### Extension Modules (Optional)

| Module ID         | Status     | Notes                                                                            |
| ----------------- | ---------- | -------------------------------------------------------------------------------- |
| **pathfinder**    | ✅ Stable  | Filesystem scanning with include/exclude patterns (47 tests, 90%+ coverage)      |
| **ascii-helpers** | ✅ Stable  | Console formatting utilities (tables, boxes, progress) (48 tests, 90%+ coverage) |
| **cloud-storage** | 📋 Planned | Unified S3/GCS/Azure Blob helpers                                                |

**Legend**: ✅ Stable | 🔄 Active Development | 📋 Planned | ⚠️ Deprecated

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

### Current Release (v0.1.3)

**Status**: Alpha - Core modules stable, two extension modules added

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
- ✅ Pathfinder module (filesystem scanning with glob patterns, 47 tests)
- ✅ ASCII helpers (console formatting, box drawing, 48 tests)

**Test Coverage**: 615 tests passing, 90%+ coverage across all modules

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

### Quick Start

```python
from pyfulmen import crucible, config, schema, logging

schemas = crucible.schemas.list_available_schemas()

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
