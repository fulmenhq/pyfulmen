# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Foundry Telemetry Instrumentation (Phase 4 - Complete)**: Comprehensive telemetry in Foundry module
  - `FoundryCatalog.get_pattern()` emits `foundry_lookup_count` counter (catalog lookups)
  - `FoundryCatalog.get_mime_type()` emits `foundry_lookup_count` counter (catalog lookups)
  - Simple counter increments on each catalog operation
  - 290 foundry tests passing (288 original + 2 new telemetry tests)
  - Zero performance overhead confirmed
  - Follows same pattern as previous phases (simplified for counter-only)
  - **Rationale**: Continuing telemetry dogfooding across all modules

- **Schema Telemetry Instrumentation (Phase 3 - Complete)**: Comprehensive telemetry in Schema module
  - `validate_against_schema()` emits `schema_validation_ms` histogram (validation duration)
  - `validate_against_schema()` emits `schema_validation_errors` counter (validation failures)
  - Try/finally pattern ensures metrics emitted even on errors
  - 22 schema tests passing (20 original + 2 new telemetry tests)
  - Zero performance overhead confirmed
  - Follows same pattern as Pathfinder Phase 1.5 and Config Phase 2
  - **Rationale**: Continuing telemetry dogfooding across all modules

- **Config Telemetry Instrumentation (Phase 2 - Complete)**: Comprehensive telemetry in Config module
  - `ConfigLoader.load_with_metadata()` emits `config_load_ms` histogram (operation duration)
  - `ConfigLoader` emits `config_load_errors` counter (YAML parse failures, file read errors)
  - Try/finally pattern ensures metrics emitted even on errors
  - 36 config tests passing (34 original + 2 new telemetry tests)
  - Zero performance overhead confirmed
  - Follows same pattern as Pathfinder Phase 1.5
  - **Rationale**: Continuing telemetry dogfooding across all modules

- **Pathfinder Telemetry Instrumentation (Phase 1.5 - Complete)**: Comprehensive telemetry in Pathfinder module
  - `Finder.find_files()` emits `pathfinder_find_ms` histogram (operation duration)
  - `Finder.find_files()` emits `pathfinder_validation_errors` counter (schema validation failures)
  - `Finder.find_files()` emits `pathfinder_security_warnings` counter (path traversal attempts)
  - Try/finally pattern ensures metrics emitted even on errors
  - 90 pathfinder tests passing (87 original + 3 new telemetry tests)
  - Zero performance overhead confirmed
  - Pattern documented in `docs/development/telemetry-instrumentation-pattern.md`
  - **Rationale**: Dogfooding our own telemetry/error-handling modules before ecosystem-wide adoption

- **Telemetry Taxonomy Update**: Synced four new metrics from Crucible taxonomy (2025.10.3)
  - `config_load_errors` (count) - Failed configuration load attempts
  - `pathfinder_find_ms` (ms) - Duration of pathfinder file discovery operations
  - `pathfinder_validation_errors` (count) - Failed pathfinder validation attempts
  - `pathfinder_security_warnings` (count) - Pathfinder security warnings (path traversal, etc.)
  - Added test coverage for new metrics in `test_validate.py`
  - Validation ensures correct units and schema compliance
  - Coordinated with gofulmen Phase 3 telemetry implementation

- **Pathfinder Checksum Support**: Optional FulHash integration for file integrity verification
  - `FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128" | "sha256")` configuration
  - Case-insensitive algorithm names (XXH3-128, Sha256, etc. normalized to lowercase)
  - `PathMetadata.checksum`, `checksumAlgorithm`, `checksumError` fields
  - Streaming hash calculation via FulHash for memory efficiency
  - 87 pathfinder tests (62 unit + 25 integration)
  - 15 new tests: 12 cross-language parity + 3 case-insensitive validation
  - Performance: ~23,800 files/sec with checksums enabled
  - Cross-language test fixtures in `tests/fixtures/pathfinder/`
  - Validation tool: `make validate-pathfinder-fixtures` for CI/CD
  - ADR-0010 documents performance characteristics vs <10% aspirational target
  - Binary fixture protection via .gitattributes (prevents Windows CRLF corruption)

## [0.1.6] - 2025-10-23

### Added

- **FulHash Module**: Fast, consistent hashing for the Fulmen ecosystem
  - Two algorithms: xxh3-128 (default, fast) and sha256 (cryptographic)
  - Block hashing: `hash_bytes(data)`, `hash_string(text, encoding)`, `hash_file(path)`
  - Streaming API: `stream(algorithm)` returns independent `StreamHasher` instance
  - Universal dispatcher: `hash(bytes | str | Path)` with automatic type detection
  - Metadata helpers: `format_checksum()`, `parse_checksum()`, `validate_checksum_string()`, `compare_digests()`
  - Schema compliance: Digest and checksum-string validation against Crucible schemas
  - Thread-safe by design: Independent instances, no singletons (ADR-0009)
  - 156 tests including 14 dedicated concurrency tests
  - Stress tested: 121,051 ops/sec sustained throughput (1,000 operations)
  - Memory safety: 200 concurrent file hashing operations (1MB files), zero corruption
  - Cross-language fixtures: Shared test vectors in `config/crucible-py/library/fulhash/fixtures.yaml`
  - Dependencies: Added xxhash library for fast non-cryptographic hashing
  - 95%+ test coverage on all fulhash APIs
  - **Ecosystem Impact**: First language to implement fulhash module
  - **Architecture Decision**: ADR-0009 documents independent instance pattern (learned from TypeScript singleton bug)

- **Error Handling Module**: Pathfinder error envelope with telemetry extensions
  - `PathfinderError` model: Base error structure (code, message, details, path, timestamp)
  - `FulmenError` model: Extended error with telemetry metadata (severity, correlation_id, trace_id, exit_code, context, original)
  - `wrap(base_error, severity, context, ...)` - Wrap errors with telemetry metadata
  - `validate(error)` - Validate against Crucible error-handling schema
  - `exit_with_error(exit_code, error, logger)` - Severity-aware logging before sys.exit()
  - Schema compliance with `schemas/error-handling/v1.0.0/error-response.schema.json`
  - Automatic correlation_id propagation from logging context
  - Python exception serialization with traceback capture
  - 95% test coverage with 4 test methods
  - **Ecosystem Impact**: First language to implement error-handling-propagation module
  - **Crucible Standard**: Error handling as data models (Crucible 2025.10.3)

- **Telemetry Module**: OpenTelemetry-compatible metrics with Crucible taxonomy validation
  - `MetricRegistry` class: Thread-safe metric instrument management
  - Three metric types: Counter (monotonic), Gauge (instantaneous), Histogram (distribution)
  - `counter(name)`, `gauge(name)`, `histogram(name, buckets)` - Instrument accessors
  - `validate_metric_event(event)` - Validate against Crucible metrics schema and taxonomy
  - `validate_metric_events(events)` - Batch validation with detailed error reporting
  - Default histogram buckets: `[1, 5, 10, 50, 100, 500, 1000, 5000, 10000]` milliseconds
  - Taxonomy-aware validation: metric names, units, histogram structure
  - Thread-safe event recording via threading.Lock
  - 85% test coverage with 6 test methods
  - **Ecosystem Impact**: First language to implement telemetry-metrics module
  - **Crucible Standard**: Default histogram buckets (Crucible 2025.10.3)

- **Logging Integration**: Telemetry metrics routing through progressive logging
  - `emit_metrics_to_log(logger, events)` - Route metric events through logging pipeline
  - Structured JSON output with metric_event context
  - Compatible with SIMPLE/STRUCTURED/ENTERPRISE profiles

- **Cross-Language Fixtures**: JSON fixtures for schema validation
  - `tests/fixtures/errors/` - valid_error.json, invalid_error_missing_code.json
  - `tests/fixtures/metrics/` - scalar_counter.json, histogram_ms.json, invalid_metric_bad_name.json
  - Terminal histogram bucket uses 1e9 (numeric sentinel) for cross-language compatibility
  - All fixtures schema-validated (valid pass, invalid fail as expected)

- **Example Integration**: Complete error/telemetry demonstration
  - `examples/error_telemetry_demo.py` - Working demo with structured JSON output
  - Demonstrates error wrapping, validation, metrics recording, logging integration

- **Architecture Decision Records**: PyFulmen metric registry pattern
  - `ADR-0008`: Metric Registry Pattern - Explicit instantiation over global singleton
  - Documents registry lifecycle, usage patterns, cross-language translation

### Changed

- **Module Exports**: Enhanced public APIs
  - `error_handling.__all__`: Added `exit_with_error`
  - `telemetry.__all__`: Added `validate_metric_event`, `validate_metric_events`
  - `logging.__all__`: Added `emit_metrics_to_log`

- **Documentation**: Comprehensive module documentation
  - `README.md`: Added Error Handling and Telemetry & Metrics sections with examples
  - `docs/pyfulmen_overview.md`: Updated module catalog with error-handling-propagation and telemetry-metrics (✅ Stable)

### Architectural Impact

- **First Language Implementation**: PyFulmen implements error-handling and telemetry modules before gofulmen and tsfulmen
- **Crucible Standards Promotion**: Two PyFulmen ADRs promoted to Crucible 2025.10.3 ecosystem standards
  - Error handling as data models (not language-native exceptions)
  - Default histogram buckets `[1, 5, 10, 50, 100, 500, 1000, 5000, 10000]` ms for `*_ms` metrics
- **Cross-Language Pattern Establishment**: Pydantic models translate to Go structs and TypeScript interfaces
- **Registry Pattern**: Explicit instantiation pattern aligns with Go and TypeScript idioms

### Test Coverage

- **Total Tests**: 1,058 passing (18 skipped)
- **New Tests**: 100 tests added for error_handling + telemetry + validation
- **Coverage**: 93% overall, 95% error_handling, 85% telemetry
- **Schema Validation**: All fixtures validated correctly

## [0.1.5] - 2025-10-22

### Breaking Changes

- **crucible**: `CrucibleVersion.sync_date` renamed to `synced_at` for Crucible Shim Standard compliance

### Added

- **crucible**: New `find_schema(id)` function returning `(dict, AssetMetadata)` tuple with full metadata
- **crucible**: New `find_config(id)` function returning `(dict, AssetMetadata)` tuple with full metadata
- **crucible**: New `get_doc(id)` function returning `(str, AssetMetadata)` with raw markdown (frontmatter preserved)
- **crucible**: `AssetMetadata` now includes `format`, `size`, and `modified` fields
- **crucible**: `CrucibleVersion` now parses `commit` and `synced_at` from sync metadata (`.crucible/metadata/sync-keys.yaml`)
- **crucible**: Full metadata computation - SHA-256 checksums, file sizes, ISO-8601 timestamps
- **crucible**: JSON-first, YAML-fallback schema resolution per Crucible Shim Standard
- **crucible**: 23 new unit tests for metadata utilities (100% pass rate)
- **crucible**: 9 new integration tests for shim helpers (checksums, metadata, Docscribe delegation)

### Changed

- **crucible**: `list_assets()` now populates all metadata fields (format, size, checksum, modified) for every asset
- **crucible**: `get_crucible_version()` docstring updated (`sync_date` → `synced_at`)
- **crucible**: Docscribe wrappers now delegate to `get_doc()` for single read path
  - `get_documentation()` calls `get_doc()` then strips frontmatter via Docscribe
  - `get_documentation_metadata()` calls `get_doc()` then extracts frontmatter
  - `get_documentation_with_metadata()` calls `get_doc()` then parses with Docscribe

### Deprecated

- **crucible**: `load_schema_by_id()` deprecated in favor of `find_schema()` (removal in v0.2.0)
  - Emits `DeprecationWarning` with migration guidance
  - Still functional, delegates to `find_schema()` internally
- **crucible**: `get_config_defaults()` deprecated in favor of `find_config()` (removal in v0.2.0)
  - Emits `DeprecationWarning` with migration guidance
  - Still functional, delegates to `find_config()` internally

### Documentation

- **README.md**: Updated Crucible Bridge API section with v0.1.5 examples showing metadata-bearing helpers
- **README.md**: Added migration guide from legacy APIs
- **README.md**: Version badge updated to 0.1.5, coverage 92%

### Testing

- **Test Coverage**: 92% for crucible module (exceeds 90% target)
- **Test Count**: 165 crucible tests passing (123 unit + 42 integration)
- **New Tests**: Metadata computation, version parsing, shim helpers, Docscribe integration

## [0.1.4] - 2025-10-21

### Added

- **Crucible Bridge API**: Unified interface for accessing embedded Crucible assets
  - `crucible.list_categories()` - Discover available asset categories (docs, schemas, config)
  - `crucible.list_assets(category, prefix)` - List assets with optional prefix filtering
  - `crucible.load_schema_by_id(schema_id)` - Load schemas by full ID path
  - `crucible.get_config_defaults(category, version)` - Access config defaults by path
  - `crucible.open_asset(asset_id)` - Stream large assets efficiently via context manager
  - `crucible.get_crucible_version()` - Get embedded Crucible version metadata
  - `AssetMetadata` model with ID, category, path, size, and modification tracking
  - `CrucibleVersion` model with version, commit hash, and sync timestamp
  - Recursive category discovery for nested schema/config structures
  - Similarity-based suggestions in `AssetNotFoundError` (up to 3 suggestions)
  - 21 integration tests against real synced Crucible assets
  - 321 unit tests for bridge models and APIs
  - **Recommended pattern** for new code accessing Crucible assets

- **Docscribe Module**: Standalone documentation processing with frontmatter parsing and header extraction
  - `docscribe.parse_frontmatter(content)` - Extract YAML frontmatter and clean markdown body
  - `docscribe.extract_metadata(content)` - Get frontmatter dict only (None if absent)
  - `docscribe.strip_frontmatter(content)` - Remove frontmatter, return clean markdown
  - `docscribe.has_frontmatter(content)` - Check for frontmatter presence
  - `docscribe.detect_format(content)` - Detect format (json, yaml, markdown, toml, multi-document)
  - `docscribe.split_documents(content)` - Split multi-document streams (YAML/markdown)
  - `docscribe.inspect_document(content)` - Get document metadata (format, line count, header count, sections)
  - `docscribe.extract_headers(content)` - Extract markdown headers with anchors and line numbers
  - `docscribe.generate_outline(content, max_depth)` - Generate nested table of contents structure
  - `docscribe.search_headers(content, pattern)` - Find headers matching search pattern
  - `DocumentHeader` model with level, text, anchor, and line_number
  - `DocumentInfo` model with format, line count, header count, and section estimation
  - Crucible bridge integration: `crucible.get_documentation()`, `crucible.get_documentation_metadata()`
  - GitHub-compatible anchor generation (preserves double-hyphens for special chars)
  - Smart format detection distinguishes frontmatter from YAML document separators
  - 92 comprehensive unit tests (frontmatter, formats, headers, edge cases)
  - 12 integration tests against real Crucible documentation
  - 95% test coverage across docscribe module

- **Synced Crucible Assets**: Module standards and architecture documentation
  - `docs/crucible-py/standards/library/modules/docscribe.md` - Docscribe module standard (411 lines)
  - `docs/crucible-py/architecture/fulmen-forge-workhorse-standard.md` - Workhorse standard (282 lines)
  - Updated `docs/crucible-py/architecture/fulmen-helper-library-standard.md` - Added Crucible Overview requirement
  - Updated `docs/crucible-py/architecture/modules/README.md` - Module index
  - Updated `config/crucible-py/library/v1.0.0/module-manifest.yaml` - Added docscribe module entry
  - Updated `schemas/crucible-py/library/module-manifest/v1.0.0/module-manifest.schema.json` - Schema updates

### Changed

- **Crucible Package Exports**: Enhanced API surface with bridge and docscribe
  - Bridge API: `list_categories()`, `list_assets()`, `load_schema_by_id()`, `get_config_defaults()`, `open_asset()`, `get_crucible_version()`
  - Docscribe API: `get_documentation()`, `get_documentation_metadata()`, `get_documentation_with_metadata()`
  - Error types: `AssetNotFoundError`, `ParseError`, `CrucibleVersionError`
  - Models: `AssetMetadata`, `CrucibleVersion`
  - **Recommended pattern**: Use bridge API for new code, legacy APIs maintained for compatibility

- **Crucible Docs Module**: Delegates to docscribe for frontmatter processing
  - `crucible.docs.get_documentation()` - Delegates to `docscribe.parse_frontmatter()` for clean markdown
  - `crucible.docs.get_documentation_metadata()` - Extracts YAML frontmatter using docscribe
  - `crucible.docs.get_documentation_with_metadata()` - Combined access via docscribe
  - Legacy functions (`read_doc`, `list_available_docs`, `get_doc_path`) unchanged
  - All documentation comments updated to reference docscribe module

- **PyFulmen Overview**: Added mandatory Crucible Overview section
  - "What is Crucible?" - Explains SSOT role and ecosystem consistency
  - "Why the Shim & Docscribe Module?" - Describes idiomatic asset access pattern
  - "Where to Learn More" - Links to Crucible repo, manifesto, and sync standard
  - Updated Module Catalog: docscribe listed as ✅ Stable with 95% coverage target
  - Updated test counts: 845 passing tests (92 docscribe tests)
  - Version metadata: v0.1.4, last_updated 2025-10-21

### Fixed

- **Crucible Bridge Asset Discovery**: Fixed recursive discovery and prefix filtering
  - Recursively walks schema/config directory trees to find all nested categories
  - Prefix filtering now applies to full asset ID (e.g., `library/foundry/v1.0.0/mime-types`)
  - Asset ID suggestions use full paths instead of just top-level categories

- **Crucible Bridge Asset IDs**: Corrected documentation examples
  - Doc asset IDs no longer include `docs/` prefix (correct: `architecture/...`)
  - Fixed docstring examples in bridge.py and **init**.py
  - All user-facing docs teach correct asset ID format

### Documentation

- **README.md**: Added Crucible Bridge API section with recommended usage patterns
- **PyFulmen Overview**: Comprehensive docscribe module section
  - "Docscribe Module APIs (v0.1.4+)" with frontmatter, format detection, header extraction examples
  - Crucible Overview section (mandatory per helper library standard)
  - Updated Module Catalog and Roadmap sections
  - Bridge API quick start examples

- **Integration Tests**: Comprehensive test coverage
  - `tests/integration/crucible/test_bridge_integration.py` - 21 tests for bridge API
  - `tests/integration/crucible/test_documentation_integration.py` - 12 tests for docscribe
  - Tests verify recursive discovery, prefix filtering, frontmatter parsing, header extraction
  - Performance benchmarks: <10ms per frontmatter extraction, <5ms average

### Test Coverage

- **Total Tests**: 845 passing (18 skipped)
- **New Tests**: 113 tests added for bridge API and docscribe module
  - Bridge: 21 integration tests, 321 unit tests
  - Docscribe: 92 unit tests, 12 integration tests
- **Coverage**: 90%+ maintained across all modules, 95% on docscribe

## [0.1.3] - 2025-10-20

### Added

- **Pathfinder Extension Module** (Phase 1-2 Complete): Safe filesystem discovery with .fulmenignore support and schema compliance
  - `Finder` class with configuration-based discovery (maxWorkers, caching, validation)
  - `FindQuery` model with include/exclude patterns, maxDepth, followSymlinks, includeHidden options
  - `PathResult` model with relativePath, sourcePath, logicalPath, loaderType, metadata
  - Path safety validation with traversal attack prevention (`validate_path()`)
  - Proper `pathlib.Path` usage throughout (no string manipulation - addresses Go implementation bugs)
  - Recursive `**` glob pattern support via pathlib.rglob()
  - Convenience methods: `find_go_files()`, `find_config_files()`, `find_schema_files()`, `find_by_extension()`
  - **Phase 1-2 Enhancements**:
    - `.fulmenignore` support with gitignore-style pattern matching (`IgnoreMatcher` class)
    - `PathConstraint` model with enforcement levels (strict/warn/permissive)
    - Metadata collection for discovered files (size, modified, permissions via `Path.stat()`)
    - CamelCase field aliases for schema compatibility (`_to_camel` generator)
    - Schema validation for FindQuery/PathResult inputs/outputs when configured
    - Fixed recursive glob handling to preserve intermediate path segments
    - Fixed symlink detection to check before resolution when follow_symlinks=False
    - Enhanced test coverage with constraint enforcement and ignore pattern tests
  - Schema validation support for FindQuery and PathResult against Crucible schemas
  - Error handlers and progress callbacks for streaming discovery
  - 54 comprehensive tests with 88% coverage (249 statements)
  - Phase 1-2 complete per pathfinder-remediation-feature-brief.md

- **ASCII Helpers Extension Module**: Unicode-aware console formatting with terminal-specific width overrides
  - `string_width()`: wcwidth-based display width calculation with terminal overrides
  - Padding functions: `pad_right()`, `pad_left()`, `pad_center()` with Unicode awareness
  - `truncate()`: Width-aware string truncation with ellipsis support
  - Box drawing with `draw_box()` supporting 4 box styles (SINGLE, DOUBLE, ROUNDED, BOLD)
  - Three-layer terminal configuration (Crucible defaults → User overrides → BYOC)
  - Auto-detection of terminal type via `TERM_PROGRAM` environment variable
  - Terminal-specific character width overrides for proper alignment (VSCode, Apple Terminal, iTerm2)
  - `get_terminal_config()`: Access current terminal configuration
  - wcwidth library integration for accurate Unicode width calculation
  - 48 comprehensive tests with 90%+ coverage
  - 100% gofulmen ASCII implementation alignment

- **Config Three-Layer System** (Complete Implementation): Production-ready configuration loading with metadata tracking
  - `ConfigLoader` class with three-layer merge (Crucible defaults → User overrides → Application config)
  - `ConfigLoadResult` with source tracking metadata for diagnostics
  - `ConfigSource` dataclass tracking layer, source path, and application status
  - Vendor/app namespace support with kebab-case normalization
  - `FULMEN_CONFIG_HOME`, `FULMEN_DATA_HOME`, `FULMEN_CACHE_HOME` environment overrides
  - YAML/JSON format auto-detection for user overrides (.yaml, .yml, .json)
  - `ensure` parameter for automatic directory creation
  - `get_config_search_paths()` alias for standard compliance
  - Platform-specific path resolution (macOS, Linux, Windows)
  - `load()` method for simple merged config access
  - `load_with_metadata()` method for full diagnostics
  - 34 comprehensive tests with 93% coverage
  - Full compliance with Three-Layer Configuration Standard

- **Schema Catalog & Validation** (Enhanced Implementation): Discovery and validation with optional goneat integration
  - `SchemaInfo` dataclass with schema metadata (id, category, version, name, path, description)
  - `list_schemas()` for discovery with optional prefix filtering
  - `get_schema()` for metadata retrieval by schema ID
  - `parse_schema_id()` for identifier parsing (category/version/name)
  - `validate_data()` function with `ValidationResult` and `Diagnostic` tracking
  - `validate_file()` function supporting JSON/YAML auto-detection
  - Optional goneat CLI integration with automatic fallback to jsonschema
  - `format_diagnostics()` helper with text/json output modes
  - Click-based CLI with `list`, `info`, `validate` commands
  - `validate-schema.sh` helper script (defaults to goneat, falls back to PyFulmen CLI)
  - `--use-goneat`/`--no-goneat` flags for integration control
  - Test fixtures for schema validation (box-chars valid/invalid payloads)
  - 20 comprehensive tests with 78% coverage (283 statements)
  - Catalog module: 93% coverage (75 statements)
  - Validator module: 92% coverage (106 statements)

- **Ecosystem ADR Adoption Tracking**: Comprehensive architectural decision tracking
  - `docs/development/adr/ecosystem-adoption-status.md`: New comprehensive adoption status document
  - Adoption status levels defined: not-applicable (0), deferred (5), planned (10), in-progress (20), implemented (30), verified (40)
  - Tracking for 5 ecosystem ADRs with test evidence and coverage metrics
  - Module maturity tracking: 7 modules tracked (Foundry, Logging, Config, Crucible Shim, Schema, Pathfinder, ASCII)
  - 4 ecosystem ADRs at "verified" status (40), 1 at "implemented" status (30)
  - Total test count tracking: 615 tests passing across all modules
  - Coverage summary by module with Ecosystem ADR mappings

### Changed

- **Documentation**: Comprehensive updates for v0.1.3 release
  - `docs/pyfulmen_overview.md`: Updated all module statuses to "✅ Stable"
  - Updated version metadata to 0.1.3 and last_updated to 2025-10-17
  - Updated module catalog with current statuses: observability-logging and foundry-patterns now stable
  - Updated extension modules table: pathfinder and ascii-helpers now stable with test counts
  - Updated roadmap: Current Release section reflects v0.1.3 status with 615 tests passing
  - Updated Next Release target to Q1 2026 for v0.2.0
  - Removed completed items from Known Gaps (middleware plugin system completed)
  - `docs/development/adr/README.md`: Updated ecosystem ADR adoption statuses from "In Progress" to "Verified"
  - Added link to ecosystem-adoption-status.md with adoption status level definitions

- **Development Tooling**: Enhanced code quality and demo script support
  - `Makefile`: Added `scripts/` directory to `fmt` and `lint` targets
  - `ruff.toml`: Added `scripts/demos/*.py` exception for E402 (imports not at top)
  - Enables proper formatting and linting of demo scripts while allowing necessary sys.path manipulation
  - Demo scripts now included in quality gates (make prepush)

- **Test Organization**: Renamed pathfinder test file to avoid pytest collection errors
  - Renamed `tests/unit/pathfinder/test_models.py` to `test_pathfinder_models.py`
  - Prevents collision with `tests/unit/foundry/test_models.py`
  - Fixes pytest "imported module has this **file** attribute" error

- **Version Alignment**: Updated version to 0.1.3 across all files
  - `VERSION`: 0.1.3
  - `pyproject.toml`: version = "0.1.3"
  - `tests/test_basic.py`: Updated version assertion to "0.1.3"

### Fixed

- **ASCII Emoji Crash**: Fixed TypeError in string_width() with multi-codepoint emoji (✌️, ☠️, ⚠️)
  - wcwidth.wcwidth() only accepts single characters, now using wcwidth.wcswidth() for multi-codepoint grapheme clusters
  - Added 7 regression tests covering emoji variation selectors and CJK/emoji truncation

- **ASCII SSOT Drift**: Terminal defaults now load from Crucible asset instead of embedded YAML
  - Changed from embedded DEFAULT_TERMINAL_OVERRIDES to load_config_defaults("terminal", "v1.0.0")
  - Ensures terminal configuration stays in sync with ecosystem standards

- **ASCII max_width Parity**: Changed max_width behavior to truncate instead of raising ValueError
  - Matches gofulmen behavior (lines 31-35, 51-54 of gofulmen/ascii/ascii.go)
  - Cross-language behavioral consistency maintained

- **ASCII Width-Aware Truncation**: Fixed truncation to respect display width for CJK/emoji characters
  - Added \_truncate_to_width() helper that accumulates display width character-by-character
  - Prevents misaligned boxes when truncating double-width characters

- **Path Traversal Detection**: Fixed to check for ".." BEFORE normalization
  - os.path.normpath() resolves ".." sequences, hiding traversal attempts
  - Now checks for ".." in original path first, then normalizes

- **Import Paths**: Fixed config module import for ASCII terminal configuration
  - Changed from pyfulmen.config to pyfulmen.config.paths for get_fulmen_config_dir()

### Dependencies

- **wcwidth**: Added `wcwidth>=0.2.0` for Unicode character width calculation
  - Enables accurate terminal width calculation for CJK, emojis, box-drawing characters
  - Required for ASCII helpers module
- **click**: Added `click>=8.1.0` for CLI framework
  - Powers schema catalog CLI (list/info/validate commands)
  - Provides argument parsing, help generation, and error handling

### Documentation

- **Release Notes**: Comprehensive v0.1.3 release documentation
  - `docs/releases/v0.1.3.md`: Complete release notes with feature descriptions, examples, migration guide
  - Pathfinder and ASCII module documentation
  - Config three-layer system documentation with examples
  - Schema catalog and validation CLI documentation
  - Ecosystem ADR adoption tracking documentation
  - `docs/pyfulmen_overview.md`: Updated with schema CLI usage examples and current module statuses
  - Quality metrics: 613 tests, 90%+ coverage across all modules
  - Cross-language parity verification with gofulmen

- **Logging Demo Script**: Comprehensive progressive logging demonstration
  - `scripts/demos/logging_demo.py`: Interactive demo showcasing all logging capabilities
  - Demonstrates all three progressive profiles (SIMPLE, STRUCTURED, ENTERPRISE)
  - Shows all severity levels (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
  - Examples of context propagation and correlation IDs
  - Error handling with exception details
  - Profile comparison showing same log event across profiles
  - Executable with shebang (`#!/usr/bin/env -S uv run python`) for direct invocation
  - Includes comprehensive inline documentation and usage instructions

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

- **MIME Magic Number Detection (Phase 3)**: Content-based MIME type identification with full gofulmen v0.1.1 API parity
  - `detect_mime_type(data: bytes)` - Core byte signature detection from raw bytes
  - `detect_mime_type_from_reader(reader, max_bytes)` - Streaming detection with reader preservation (ChainedReader pattern)
  - `detect_mime_type_from_file(path)` - File content detection (reads first 512 bytes)
  - BOM stripping: UTF-8 (EF BB BF), UTF-16 LE (FF FE), UTF-16 BE (FE FF)
  - Leading whitespace trimming for accurate signature detection
  - Format detection: JSON (objects/arrays), XML (<?xml declaration), YAML (key: value), CSV (2+ commas), plain text (>80% printable)
  - Returns None for binary/unknown content (not exceptions)
  - 83 comprehensive tests including golden fixtures
  - 8 cross-language golden fixtures: valid-json-object.json, valid-json-array.json, valid-xml.xml, valid-yaml.yaml, valid-csv.csv, valid-text.txt, binary-unknown.bin, json-with-utf8-bom.json
  - Full behavioral parity with gofulmen v0.1.1 verified via parity checklist (28/28 features, 100% compliance)

- **Foundry Documentation Expansion**: Comprehensive README updates
  - Country code lookup section with catalog methods and convenience functions
  - MIME Type Detection (Magic Numbers) section with Core Detection, Streaming Detection, File Detection
  - Updated Crucible Standards Conformance section (moved Phase 2E and Phase 3 from "Deferred" to "Implemented")
  - Expanded test count: 520 tests covering all pyfulmen features (227 foundry tests)
  - Updated coverage metrics: 95% maintained on catalog and mime_detection modules

- **Version Propagation Infrastructure**: Policy-driven VERSION management
  - `.goneat/version-policy.yaml` configuration for automatic pyproject.toml sync
  - VERSION file as single source of truth with goneat version propagate
  - Policy controls: semver scheme, branch guards, backup retention, workspace strategy
  - Safety features: dirty worktree checks, required branches (main, release/\*)

### Changed

- **Version Synchronization**: Aligned VERSION, pyproject.toml, and **init**.py to 0.1.2
  - Fixed version mismatch between files
  - Ensures consistent version reporting across tooling

- **Makefile Version Targets**: Enhanced version management workflow
  - `version-set` now auto-propagates VERSION to pyproject.toml
  - All bump targets (major/minor/patch/calver) auto-propagate after bumping
  - Added `version-propagate` target for manual sync operations
  - Fixed `version-set` command (was using non-existent `goneat version sync`)

### Fixed

- **Code Style**: Normalized quote styles and list formatting in logging module
  - Single quotes → double quotes for consistency
  - Multi-line list formatting for sensitive_keys in RedactSecretsMiddleware

- **Bootstrap Symlink**: Fixed type:link tools to use symlinks instead of copies
  - `bin/goneat` now symlinks to source, tracking rebuilds automatically
  - No more stale binaries requiring `make bootstrap-force` after goneat rebuilds
  - Addresses Pitfall 6 from Fulmen Helper Library Standard

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
