# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No unreleased changes.

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

## [0.1.1] - Planned

### Planned (Logging Upscale - Phases 2-5)

- **Enhanced Logging Features**: Complete enterprise logging implementation
  - Severity mapping and level filtering
  - Context propagation with correlation IDs
  - Redaction and PII protection
  - Throttling and rate limiting
  - Custom middleware pipeline
  - Performance optimizations

### Planned (Additional Foundry Features)

- **Country Code Lookup** (Optional): ISO country codes with multiple format support
- **MIME Magic Numbers** (Optional): Byte-level MIME type detection from file headers

---

_Note: This changelog tracks the progressive upscaling of PyFulmen through v0.1.x releases._
