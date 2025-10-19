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

## [0.1.2] - 2025-10-15

### Foundry Module Expansion: Country Codes & ADR Infrastructure

**Release Type**: Feature Release - Foundry Phase 2E + Phase 3 Complete + Architectural Governance
**Release Date**: October 15, 2025
**Status**: ✅ Released

#### Features

**Country Code Support (Phase 2E)**:

- ✅ **ISO 3166-1 Country Model**: Alpha-2, Alpha-3, Numeric codes with name and official name fields
- ✅ **Triple-Index Catalog**: O(1) lookups via precomputed Alpha-2, Alpha-3, Numeric indexes
- ✅ **Case-Insensitive Matching**: "us" → "US", "usa" → "USA", automatic normalization
- ✅ **Numeric Zero-Padding**: "76" → "076" (Brazil), automatic canonicalization
- ✅ **Five Convenience Functions**:
  - `validate_country_code()`: Three-lookup fallback strategy (Alpha-2 → Alpha-3 → Numeric)
  - `get_country()`: Lookup by Alpha-2 code
  - `get_country_by_alpha3()`: Lookup by Alpha-3 code
  - `get_country_by_numeric()`: Lookup by Numeric code (with zero-padding)
  - `list_countries()`: Enumerate all countries in catalog
- ✅ **Catalog Integration**: 5 sample countries from Crucible (US, CA, JP, DE, BR)
- ✅ **Full gofulmen v0.1.1 API Parity**: Identical API signatures and behavior
- ✅ **32 Comprehensive Tests**: Model, catalog, convenience functions, integration tests
- ✅ **95% Coverage**: Maintained on catalog module

**ADR Infrastructure (Architectural Governance)**:

- ✅ **Two-Tier ADR System**: Local (Python-specific) and Ecosystem (cross-language) decisions
- ✅ **Local ADR Infrastructure**: `docs/development/adr/` with comprehensive index and README
- ✅ **Three Foundry ADRs**:
  - ADR-0001: FulmenCatalogModel populate_by_name=True (Python-specific Pydantic config)
  - ADR-0002: validate_country_code() Three-Lookup Strategy (Alpha-2 → Alpha-3 → Numeric)
  - ADR-0003: Country Catalog Preview Status (lifecycle and maturity communication)
- ✅ **Four Ecosystem ADRs Synced from Crucible**:
  - ADR-0002: Triple-Index Catalog Strategy (foundational cross-language pattern)
  - ADR-0003: Progressive Logging Profiles (SIMPLE/STRUCTURED/ENTERPRISE)
  - ADR-0004: Schema-Driven Config Hydration (three-layer config pattern)
  - ADR-0005: CamelCase to Language Convention Mapping (field alias strategy)
- ✅ **Promotion Path**: Clear process for promoting local → ecosystem ADRs
- ✅ **+2,000 Lines of Documentation**: Architectural decision records

**MIME Magic Number Detection (Phase 3)** - _(Complete)_:

- ✅ **Byte Signature Detection**: Identify MIME types from file magic numbers
- ✅ **Stream-Based Detection**: Efficient processing for large files with reader preservation
- ✅ **BOM Handling**: UTF-8/UTF-16 byte order mark stripping
- ✅ **Format Support**: JSON, XML, YAML, CSV, plain text
- ✅ **Golden Fixtures**: 8 cross-language test fixtures under tests/fixtures/foundry/mime/
- ✅ **Parity Verification**: 100% behavioral parity with gofulmen v0.1.1 (28/28 features)

**Version Management Infrastructure**:

- ✅ **Single Source Pattern**: `__init__.py` now uses `importlib.metadata` to read from pyproject.toml
- ✅ **Version Propagation**: `.goneat/version-policy.yaml` enables automatic VERSION → pyproject.toml sync
- ✅ **Policy-Driven**: Semver scheme, branch guards, backup retention, workspace strategy configuration
- ✅ **Automated Workflow**: Makefile targets (version-set, version-bump-\*) auto-propagate to pyproject.toml
- ✅ **Manual Control**: New `version-propagate` target for explicit sync operations

#### Breaking Changes

- None (fully backward compatible with v0.1.1)

#### Migration Notes

- **Version Reading**: `__init__.py` now dynamically reads version from package metadata
  - No impact on users (transparent change)
  - Developers: Use `make version-bump-patch` or `make version-set VERSION=x.y.z` (auto-propagates)
- **Bootstrap**: `type:link` now creates symlinks (bin/goneat tracks source automatically)
  - Run `make bootstrap` to update existing installations
- **Country Codes**: New API, additive only (no existing APIs changed)
- **ADR System**: Documentation addition, no code impact

#### Known Limitations

- **5 Sample Countries**: Full 250+ country catalog will come in future Crucible sync

#### Quality Gates

- [x] Country code tests: 32/32 passing (model, catalog, convenience, integration)
- [x] Version sync test passing (importlib.metadata validation)
- [x] Code quality checks passing (ruff lint, ruff format)
- [x] ADR documentation complete and cross-referenced
- [x] Full gofulmen v0.1.1 behavioral parity verified
- [x] Magic numbers implementation complete
- [x] All tests passing (520 tests)
- [x] Final documentation review complete

#### Release Checklist

- [x] Version number set in VERSION (0.1.2)
- [x] pyproject.toml version updated (0.1.2)
- [x] **init**.py refactored to use importlib.metadata
- [x] CHANGELOG.md updated with v0.1.2 draft
- [x] RELEASE_NOTES.md updated with v0.1.2 draft
- [x] Country code implementation complete
- [x] ADR infrastructure complete
- [x] Magic numbers implementation complete
- [x] Version propagation infrastructure complete
- [x] Bootstrap symlink fix verified
- [x] All tests passing (520 tests)
- [x] Code quality checks passing
- [x] Final documentation review
- [x] Agentic attribution proper for all commits
- [ ] docs/releases/v0.1.2.md created
- [ ] Git tag created (v0.1.2) - pending final commit

---

## [Unreleased]

### v0.1.3+ - Additional Features (Planned)

- Additional ecosystem utilities
- Expanded catalog coverage

### v0.2.0 - Enterprise Complete (Planned)

- Full enterprise logging implementation
- Complete progressive interface features
- Cross-language compatibility verified
- Comprehensive documentation and examples
- Production-ready for FulmenHQ ecosystem

---

_Release notes will be updated as development progresses._
