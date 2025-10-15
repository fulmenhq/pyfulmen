# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No unreleased changes.

---

## [0.1.2] - 2025-10-15

### Added

- **Architecture Decision Records (ADR) Infrastructure**: Two-tier ADR system for architectural governance
  - Local ADR infrastructure in `docs/development/adr/` with comprehensive index and template
  - Three foundry architectural decisions documented:
    - `ADR-0001`: FulmenCatalogModel populate_by_name=True (Python-specific implementation detail)
    - `ADR-0002`: validate_country_code() Three-Lookup Strategy (Alpha-2 → Alpha-3 → Numeric fallback)
    - `ADR-0003`: Country Catalog Preview Status (maturity communication for catalog lifecycle)
  - Four ecosystem ADRs synced from Crucible:
    - `ADR-0002`: Triple-Index Catalog Strategy (cross-language foundational pattern)
    - `ADR-0003`: Progressive Logging Profiles (SIMPLE/STRUCTURED/ENTERPRISE definitions)
    - `ADR-0004`: Schema-Driven Config Hydration (three-layer config pattern)
    - `ADR-0005`: CamelCase to Language Convention Mapping (field alias strategy)
  - +2,000 lines of architectural decision documentation

- **Country Code Support (Phase 2E)**: ISO 3166-1 country code lookups with full gofulmen v0.1.1 API parity
  - `Country` model with Alpha-2, Alpha-3, Numeric codes, name, and optional official name
  - O(1) lookups via triple-index lazy-loading catalog (precomputed Alpha-2, Alpha-3, Numeric indexes)
  - Case-insensitive matching: "us" → "US", "usa" → "USA"
  - Numeric zero-padding canonicalization: "76" → "076" (Brazil)
  - Five convenience functions: `validate_country_code()`, `get_country()`, `get_country_by_alpha3()`, `get_country_by_numeric()`, `list_countries()`
  - 5 sample countries from Crucible catalog (US, CA, JP, DE, BR)
  - 32 comprehensive tests covering model, catalog, convenience functions, and integration
  - Full behavioral parity with gofulmen v0.1.1 country code implementation

- **MIME Magic Number Detection (Phase 3)**: *(Coming in final v0.1.2 commit)*
  - Byte signature detection for MIME type identification
  - Stream-based detection for efficient processing
  - Integration with existing extension-based detection
  - *(Details to be added upon completion)*

- **Foundry Documentation Expansion**: Comprehensive README updates
  - Country code lookup section with catalog methods and convenience functions
  - Updated Crucible Standards Conformance section (moved Phase 2E from "Deferred" to "Implemented")
  - Expanded test count: 143+ tests covering all foundry features
  - Updated coverage metrics: 95% maintained on catalog module

### Changed

- **Version Synchronization**: Aligned VERSION, pyproject.toml, and __init__.py to 0.1.2
  - Fixed version mismatch between files
  - Ensures consistent version reporting across tooling

### Fixed

- **Code Style**: Normalized quote styles and list formatting in logging module
  - Single quotes → double quotes for consistency
  - Multi-line list formatting for sensitive_keys in RedactSecretsMiddleware

### Documentation

- **ADR System**: Established governance framework for architectural decisions
  - Clear distinction between local (Python-specific) and ecosystem (cross-language) ADRs
  - Promotion path from local → ecosystem when cross-language impact identified
  - Links to Crucible ecosystem ADRs for shared architectural patterns

---

## [0.1.1] - 2025-10-14

### Added

- **Progressive Logging System**: Complete enterprise-scale logging implementation
  - Four progressive profiles for different deployment scenarios:
    - **SIMPLE**: Zero-config console logging (text format, stderr, perfect for development)
    - **STRUCTURED**: JSON output with core envelope (configurable sinks, cloud-native ready)
    - **ENTERPRISE**: Full 20+ field Crucible envelope (policy enforcement, compliance-ready)
    - **CUSTOM**: User-defined configuration (full control for special requirements)
  - Unified `Logger()` factory with profile-based configuration
  - Full Crucible schema compliance with 20+ field log envelope
  - `LoggingConfig` and `LoggingPolicy` for organizational governance

- **Sink Implementations**: Flexible output destinations
  - `ConsoleSink`: stderr output with configurable formatting
  - `FileSink`: Write to specified file paths with directory creation
  - `RollingFileSink`: Automatic log rotation with size/age/backup limits
  - Sink-level filtering and formatting support

- **Middleware Pipeline**: Enterprise-grade log event processing
  - `CorrelationMiddleware`: Auto-generate/propagate UUIDv7 correlation IDs for distributed tracing
  - `RedactSecretsMiddleware`: Pattern-based secret detection (API keys, passwords, tokens)
  - `RedactPIIMiddleware`: PII detection and redaction (email, phone, SSN, credit cards)
  - `ThrottlingMiddleware`: Rate limiting with maxRate/burstSize/windowSize/dropPolicy
  - Ordered pipeline execution with event dropping support

- **Formatter System**: Multiple output formats
  - `JSONFormatter`: Compact single-line JSON for log aggregators (ELK, Splunk, Datadog)
  - `TextFormatter`: Human-readable text with service name and inline context
  - `ConsoleFormatter`: ANSI-colored output for terminal readability

- **Comprehensive Documentation**: Progressive logging guides and examples
  - `docs/guides/logging/README.md`: Progressive logging index with learning path
  - `docs/guides/logging/profiles.md`: SIMPLE, STRUCTURED, ENTERPRISE, CUSTOM profile documentation
  - `docs/guides/logging/middleware.md`: Middleware configuration and usage guide
  - Working examples: `logging_simple.py`, `logging_structured.py`, `logging_enterprise.py`

- **Example Validation Tests**: Automated testing ensuring examples always work
  - `tests/integration/logging/test_examples.py`: 17 tests validating all examples run correctly
  - Validates example output characteristics (text vs JSON, correlation IDs)
  - Ensures proper API usage in examples
  - Verifies examples complete in reasonable time

- **AGENTS.md Development Rule**: Added rule #5 for Python command invocation
  - Never invoke `python` directly as system command
  - Always use `uv run` or activated `.venv` for managed environments
  - Ensures consistent dependency management across development

### Changed

- **TextFormatter**: Updated default template to include service name
  - Format: `[{timestamp}] {severity:5} [{service}] {message}`
  - SIMPLE profile now shows service name in text output
  - Context automatically included when present

- **Logger Implementation**: Fixed SIMPLE profile event emission
  - Include service, component, and context in SIMPLE profile output
  - Better alignment with STRUCTURED/ENTERPRISE profiles

### Fixed

- **Component Kwarg Bug**: Resolved duplicate argument error in logger.py:317
  - Handle `component` parameter correctly when passed via kwargs
  - Prefer kwargs component over logger's default component
  - Prevents `TypeError: got multiple values for keyword argument 'component'`

- **Documentation Links**: Removed broken links to non-existent guide pages
  - Moved references to `configuration.md` to "Coming Soon" section
  - All documentation links now point to existing files only

- **Coverage Reports**: Added `coverage.json` to `.gitignore`
  - Prevent unintentional commit of coverage JSON files

### Documentation

- **Crucible Standards**: Synced latest cross-language coding standards
  - Updated Go, Python, TypeScript coding standards from Crucible
  - Updated logging observability standard

---

## [0.1.0] - 2025-10-13

### Added

- **Foundry Module (Phases 0-2)**: Complete pattern catalog system with Crucible integration
  - **Base Models**: `FulmenDataModel`, `FulmenConfigModel`, `FulmenCatalogModel` for ecosystem consistency
  - **Utilities**: `utc_now_rfc3339nano()` for RFC3339 timestamps, `generate_correlation_id()` for UUIDv7 correlation IDs
  - **Pattern Catalog**: `FoundryCatalog` with lazy loading of patterns, MIME types, HTTP status groups from Crucible
  - **Pattern Model**: Regex/glob/literal matching with Python magic methods (`__call__` for direct invocation)
  - **PatternAccessor**: Convenience methods for common patterns (email, slug, uuid_v4, semantic_version, etc.)
  - **MimeType**: File type identification by extension with `matches_extension()` method
  - **HttpStatusGroup**: Status code organization (1xx-5xx) with `contains()` and `get_reason()` methods
  - **HttpStatusHelper**: Convenience methods (`is_success()`, `is_client_error()`, `is_server_error()`, etc.)
  - **Global Catalog**: Singleton instance with convenience functions (`get_pattern()`, `get_mime_type()`, `is_success()`, etc.)
  - Computed field handling with exclusion by default for safe roundtripping
  - 104 comprehensive tests with 96% coverage on foundry module

- **Logging Module (Phase 1)**: Progressive logger interface with profile-based delegation
  - `Logger` class with unified interface across three profiles
  - `SimpleLogger`: Console-only, basic formatting (zero-complexity default)
  - `StructuredLogger`: JSON output with core envelope fields (cloud-native ready)
  - `EnterpriseLogger`: Full 20+ field envelope with policy enforcement (ready for Phase 2+)
  - Enhanced `Severity` enum: TRACE, DEBUG, INFO, WARN, ERROR, FATAL, NONE
  - `LogEvent`: Complete Pydantic model with 20+ enterprise fields
  - `LoggingConfig`, `LoggingPolicy`: Profile-based configuration and policy enforcement
  - 48 comprehensive tests with 96-100% coverage on logging module

- **Configuration Management**: Three-layer config loading with Crucible integration
  - Layer 1: Crucible defaults (embedded from sync)
  - Layer 2: User overrides from `~/.config/fulmen/`
  - Layer 3: Application-provided config (BYOC)
  - Deep merge support in `FulmenConfigModel`

- **Schema Validation**: JSON/YAML schema processing with Crucible schema registry
  - Schema validator with draft-07 and draft-2020-12 support
  - Integration with Crucible embedded schemas

### Changed

- **Pydantic Adoption**: Standardized on Pydantic v2.12+ for all data models (not dataclasses)
  - Better validation and error messages
  - Schema generation and cross-validation support
  - Computed fields with proper exclusion handling
  - Built-in serialization control (JSON, dict, custom encoders)

- **UUIDv7 Implementation**: Using `uuid6` library for Python 3.12+ compatibility
  - Python 3.13+ stdlib uuid7 support with fallback to uuid6 library
  - Consistent time-sortable correlation IDs across gofulmen, tsfulmen, pyfulmen ecosystem

- **Documentation**: Comprehensive developer documentation
  - Foundry README with usage examples and Python-specific features
  - Fulmen library requirements (correlation IDs, pattern catalogs, config management)
  - Cross-references to ecosystem standards
  - VS Code configuration for out-of-the-box developer experience

### Fixed

- Code quality: All linting and type checking passing
- Test coverage: 95%+ on all modules
- 104 tests passing across foundry module
- Ruff formatting and lint checks passing

---

_Note: This changelog tracks the progressive upscaling of PyFulmen through v0.1.x releases._
