# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Foundry Module (Phase 0)**: Base Pydantic models for PyFulmen ecosystem
  - `FulmenDataModel`: Immutable data models (frozen, strict schema) for events and messages
  - `FulmenConfigModel`: Mutable config models with deep merge support for three-layer config pattern
  - `FulmenCatalogModel`: Immutable catalog entries for pattern/MIME/country data
  - `utc_now_rfc3339nano()`: RFC3339 timestamps with microsecond precision
  - `generate_correlation_id()`: UUIDv7 generation for time-sortable correlation tracking
  - Computed field handling with exclusion by default for safe roundtripping
  - 41 comprehensive tests with 98% coverage

- **Logging Module (Phase 1)**: Progressive logger interface with profile-based delegation
  - `Logger` class with unified interface across three profiles
  - `SimpleLogger`: Console-only, basic formatting (zero-complexity default)
  - `StructuredLogger`: JSON output with core envelope fields (cloud-native ready)
  - `EnterpriseLogger`: Full 20+ field envelope with policy enforcement
  - Enhanced `Severity` enum: TRACE, DEBUG, INFO, WARN, ERROR, FATAL, NONE
  - `LogEvent`: Complete Pydantic model with 20+ enterprise fields
  - `LoggingConfig`, `LoggingPolicy`: Profile-based configuration and policy enforcement
  - 48 comprehensive tests (20 new logger tests + 28 severity tests) with 96-100% coverage

### Changed

- **Pydantic Adoption**: Standardized on Pydantic v2.12+ for all data models (not dataclasses)
  - Better validation and error messages
  - Schema generation and cross-validation support
  - Computed fields with proper exclusion handling
  - Built-in serialization control

- **UUIDv7 Implementation**: Using `uuid6` library for Python 3.12+ compatibility
  - Python 3.13+ stdlib uuid7 support with fallback to uuid6 library
  - Consistent time-sortable correlation IDs across ecosystem

- **Documentation Updates**:
  - Updated Foundry feature brief with Phase 0 complete status and Pydantic clarification
  - Removed dataclass references, standardized on Pydantic models
  - Added VS Code configuration for better developer experience
  - Updated bootstrap documentation with FulDX → Goneat migration notes

### Fixed

- **VS Code Configuration**: Committed `.vscode/` directory for out-of-the-box developer experience
  - Python interpreter, Ruff, pytest integration
  - Configuration philosophy documented in `.vscode/README.md`

- **Code Quality**: All linting and type checking passing
  - Fixed line length issues (100 character limit)
  - Simplified comparison expressions
  - Removed outdated version blocks
  - 156 tests passing, 95% overall coverage

---

## [0.1.0] - 2025-10-10

### Added

- **Enterprise Library Foundation**: Initial release with complete PyFulmen library structure
  - Core modules: logging, config, schemas, crucible integration
  - Bootstrap system with Goneat tooling and SSOT synchronization
  - Progressive logging interface design (ready for enterprise upscaling)
  - Cross-language coordination with gofulmen and tsfulmen teams
  - Comprehensive documentation and development operations setup
  - AI agent framework with PyFulmen Architect identity
  - Repository governance with maintainers, safety protocols, and communication channels

### Changed

- **Repository Initialization**: Established complete foundation for enterprise-grade Python library
- **Standards Compliance**: Aligned with FulmenHQ ecosystem standards and helper library requirements
- **Documentation**: Complete setup for developers and contributors
- **Tooling**: Full Makefile with standard targets and bootstrap scripts

---

## [0.2.0] - Planned

### Planned (Enterprise Logging Upscale)

- **Progressive Logging Implementation**: Full enterprise logging with structured JSON output
- **Policy Enforcement**: YAML-based organizational governance for logging standards
- **Foundry Module**: Pattern catalogs, MIME detection, HTTP status helpers
- **Correlation & Context**: UUIDv7 correlation IDs, request tracing, context propagation
- **Middleware Pipeline**: Redaction, throttling, and custom processing capabilities
- **Performance Optimization**: Enterprise-grade performance with comprehensive testing

### Planned (Foundry Module Addition)

- **Pattern Catalogs**: Curated regex, glob, and literal patterns from Crucible
- **MIME Type Detection**: File type identification from bytes and extensions
- **HTTP Status Helpers**: Status code grouping and validation utilities
- **Country Code Lookup**: ISO country codes with multiple format support
- **Schema Integration**: Full integration with Crucible configuration system

---

*Note: This changelog will be updated as enterprise upscaling work progresses through v0.2.x releases.*