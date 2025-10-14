# Release Notes

This document tracks release notes and checklists for PyFulmen releases.

## [0.1.0] - 2025-10-13

### Foundry Module Complete + Progressive Logger Foundation

**Release Type**: Foundation Release with Complete Foundry Module  
**Release Date**: October 13, 2025  
**Status**: ✅ Released

#### Features

**Foundry Module (Complete)**:

- ✅ **Base Pydantic Models**: FulmenDataModel, FulmenConfigModel, FulmenCatalogModel
- ✅ **Utility Functions**: RFC3339Nano timestamps, UUIDv7 correlation IDs
- ✅ **Pattern Catalog**: 20+ curated patterns (email, slug, UUID, semver, etc.) from Crucible
- ✅ **PatternAccessor**: Convenience methods for common patterns with Python magic methods
- ✅ **MIME Types**: File type detection by extension with 7+ common types
- ✅ **HTTP Status Helpers**: Status code groups (1xx-5xx) with is_success(), is_client_error(), etc.
- ✅ **Global Catalog**: Singleton with convenience functions (get_pattern, is_success, etc.)
- ✅ **Configuration Integration**: Three-layer config loading with Crucible
- ✅ **104 Tests**: 96% coverage on foundry module

**Logging Module (Phase 1)**:

- ✅ **Progressive Logger**: Three profiles (SimpleLogger, StructuredLogger, EnterpriseLogger)
- ✅ **Severity Enum**: TRACE, DEBUG, INFO, WARN, ERROR, FATAL, NONE with numeric levels
- ✅ **LogEvent Model**: Complete Pydantic model with 20+ enterprise fields
- ✅ **Policy Support**: LoggingPolicy and LoggingConfig for governance (ready for Phase 2+)
- ✅ **48 Tests**: 96-100% coverage on logging module

**Infrastructure**:

- ✅ **Repository Structure**: src/ layout with proper Python packaging
- ✅ **Bootstrap System**: Goneat-based tooling with SSOT synchronization
- ✅ **Quality Assurance**: Ruff linting, type checking, 95%+ coverage
- ✅ **AI Agent Framework**: PyFulmen Architect identity (@pyfulmen-architect)
- ✅ **Repository Governance**: Maintainers, safety protocols, agentic attribution

#### Breaking Changes

- None (initial release)

#### Migration Notes

- This is the foundation release with complete Foundry module
- Future v0.1.x releases will complete logging upscale (Phases 2-5)
- No breaking changes expected during v0.1.x series

#### Known Limitations

- Logging Phases 2-5 not yet implemented (severity mapping, redaction, throttling, middleware)
- Country code lookup not included (optional for most use cases)
- MIME magic number detection not included (extension-based detection sufficient for 95% of cases)

#### Quality Gates

- [x] All 104 tests passing (foundry) + 48 tests (logging) = 152+ total tests
- [x] 96% coverage on foundry module, 96-100% on logging module
- [x] Code quality checks passing (ruff lint, ruff format)
- [x] Documentation complete for Foundry and Logging Phase 1
- [x] Repository structure follows Python best practices
- [x] AI agent identity established and documented
- [x] Safety protocols in place with proper attribution
- [x] Cross-language coordination with gofulmen/tsfulmen teams

#### Release Checklist

- [x] Version number set in VERSION (0.1.0)
- [x] CHANGELOG.md updated with v0.1.0 release notes
- [x] RELEASE_NOTES.md updated
- [x] docs/releases/v0.1.0.md created
- [x] All tests passing
- [x] Code quality checks passing
- [x] Documentation generated and up to date
- [x] Agentic attribution proper for all commits
- [x] Git tag created (v0.1.0)

---

## [0.1.1] - 2025-10-14

### Enterprise-Scale Progressive Logging Implementation

**Release Type**: Major Feature Release - Progressive Logging Complete
**Release Date**: October 14, 2025
**Status**: ✅ Released

#### Features

**Progressive Logging System**:

- ✅ **Four Progressive Profiles**:
  - **SIMPLE**: Zero-config console logging (text format, stderr, perfect for development)
  - **STRUCTURED**: JSON output with core envelope (configurable sinks, cloud-native ready)
  - **ENTERPRISE**: Full 20+ field Crucible envelope (policy enforcement, compliance-ready)
  - **CUSTOM**: User-defined configuration (full control for special requirements)
- ✅ **Unified Logger Factory**: Profile-based configuration with LoggingConfig and LoggingPolicy
- ✅ **Crucible Schema Compliance**: Full 20+ field log envelope for enterprise logging
- ✅ **Policy Enforcement**: Organizational logging governance and validation

**Sink Implementations**:

- ✅ **ConsoleSink**: stderr output with configurable formatting
- ✅ **FileSink**: File output with directory creation
- ✅ **RollingFileSink**: Log rotation with size/age/backup limits
- ✅ **Sink-level filtering**: Per-sink log level configuration

**Middleware Pipeline**:

- ✅ **CorrelationMiddleware**: Auto-generate/propagate UUIDv7 correlation IDs for distributed tracing
- ✅ **RedactSecretsMiddleware**: Pattern-based secret detection (API keys, passwords, tokens)
- ✅ **RedactPIIMiddleware**: PII detection (email, phone, SSN, credit cards)
- ✅ **ThrottlingMiddleware**: Rate limiting with maxRate/burstSize/windowSize/dropPolicy
- ✅ **Pipeline ordering**: Configurable middleware execution order with event dropping

**Formatters**:

- ✅ **JSONFormatter**: Compact JSON for log aggregators (ELK, Splunk, Datadog)
- ✅ **TextFormatter**: Human-readable text with service name and context
- ✅ **ConsoleFormatter**: ANSI-colored terminal output

**Documentation & Testing**:

- ✅ **Progressive Logging Guides**: Comprehensive docs in docs/guides/logging/
- ✅ **Working Examples**: logging_simple.py, logging_structured.py, logging_enterprise.py
- ✅ **Example Validation Tests**: 17 integration tests ensuring examples work
- ✅ **95%+ Test Coverage**: Comprehensive unit and integration testing
- ✅ **Cross-language Standards**: Synced coding standards from Crucible

#### Breaking Changes

- None (fully backward compatible with v0.1.0)
- Old SimpleLogger/StructuredLogger/EnterpriseLogger classes replaced with unified ProgressiveLogger
- Public API maintained through Logger() factory function

#### Migration Notes

- No migration required for existing code using Logger() factory
- Internal implementation completely refactored but API unchanged
- Examples updated to demonstrate new features (correlation, middleware, profiles)
- TextFormatter default template enhanced to include service name

#### Quality Gates

- [x] All 17 example validation tests passing
- [x] All existing tests still passing
- [x] Code quality checks passing (ruff lint, ruff format)
- [x] Documentation links validated (no 404s)
- [x] Examples run successfully without errors
- [x] Cross-language standards synced

#### Release Checklist

- [x] Version number set (0.1.1)
- [x] CHANGELOG.md updated with v0.1.1 release notes
- [x] RELEASE_NOTES.md updated
- [x] docs/releases/v0.1.1.md created
- [x] All tests passing
- [x] Code quality checks passing
- [x] Documentation validated
- [x] Agentic attribution proper for all commits

---

## [Unreleased]

### v0.1.2+ - Additional Features (Planned)

- Country code lookup (optional)
- MIME magic number detection (optional)
- Additional ecosystem utilities

### v0.2.0 - Enterprise Complete (Planned)

- Full enterprise logging implementation
- Complete progressive interface features
- Cross-language compatibility verified
- Comprehensive documentation and examples
- Production-ready for FulmenHQ ecosystem

---

_Release notes will be updated as development progresses._
