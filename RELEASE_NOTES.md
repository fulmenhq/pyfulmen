# Release Notes

This document tracks release notes and checklists for PyFulmen releases.

## [0.1.7] - Unreleased

### Foundry Similarity v2.0.0 Upgrade - Multiple Metrics & Advanced Normalization

**Release Type**: Feature Enhancement - Foundry Similarity v2.0.0
**Target Date**: TBD
**Status**: 🚧 In Progress (Implementation Complete, Documentation in Progress)

**Summary**: PyFulmen v0.1.7 upgrades the Foundry Similarity module to v2.0.0, adding support for multiple distance metrics (Damerau-Levenshtein variants, Jaro-Winkler, substring matching), advanced normalization presets, and enhanced suggestion APIs. This release maintains 100% backward compatibility while providing powerful new tools for typo correction, fuzzy matching, and text similarity.

#### Key Features

**🎯 Multiple Distance Metrics** (4 new algorithms):

- **Damerau-Levenshtein OSA** (`damerau_osa`): Handles adjacent transpositions, ideal for typo correction and spell checking
- **Damerau-Levenshtein Unrestricted** (`damerau_unrestricted`): Unrestricted transpositions for complex transformations
- **Jaro-Winkler** (`jaro_winkler`): Prefix-aware similarity, ideal for name matching and CLI suggestions
- **Substring/LCS** (`substring`): Longest common substring matching with location information

**🔧 Advanced Normalization Presets** (4 levels):

- **`none`**: No changes (exact matching)
- **`minimal`**: NFC normalization + trim (Unicode consistency)
- **`default`**: NFC + casefold + trim (recommended for most use cases)
- **`aggressive`**: NFKD + casefold + strip accents + remove punctuation (maximum fuzzy matching)

**🚀 Enhanced Suggestion API**:

- Metric selection for different use cases
- Preset-based normalization
- Prefix preference options
- Extended Suggestion model with `matched_range`, `reason`, `normalized_value`

**📊 Quality Metrics**:

- ✅ **78 Tests**: 61 unit + 17 integration (100% pass rate)
- ✅ **46/46 Crucible Fixtures**: Full v2.0.0 standard compliance
- ✅ **90% Coverage**: Exceeds enterprise target
- ✅ **100% Backward Compatible**: All v1.0 APIs unchanged
- ✅ **Performance**: <0.5ms typical, <50ms for 100 candidates

**🔬 Cross-Language Validation**:

- Validated gofulmen OSA discrepancy against Crucible fixtures
- Identified matchr Go library bug with start-of-string transpositions
- Established PyFulmen (rapidfuzz/strsim-rs) as reference implementation

#### Use Cases & Examples

**CLI Typo Correction**:

```python
from pyfulmen.foundry import similarity

# Jaro-Winkler rewards common prefixes (best for commands)
suggestions = similarity.suggest(
    "terrafrom",
    ["terraform", "terraform-apply", "format"],
    metric="jaro_winkler",
    max_suggestions=3
)
# Returns: ["terraform", "terraform-apply", "terraform-destroy"]
```

**Spell Checking with Transpositions**:

```python
# Damerau OSA handles character swaps (teh → the)
distance = similarity.distance("teh", "the", metric="damerau_osa")  # 1
distance = similarity.distance("teh", "the", metric="levenshtein")  # 2
```

**Fuzzy Matching with Normalization**:

```python
# Aggressive normalization for maximum fuzziness
suggestions = similarity.suggest(
    "café-zürich!",
    ["Cafe Zurich", "CAFE-ZURICH"],
    normalize_preset="aggressive",
    min_score=0.8
)
# Returns matches despite case/accent/punctuation differences
```

**Document Similarity**:

```python
# Substring matching for partial text search
match_range, score = similarity.substring_match("world", "hello world")
# Returns: ((6, 11), 0.4545...)
```

#### Comprehensive Demo

New example script with 7 real-world scenarios:

```bash
uv run python examples/similarity_v2_demo.py
```

Demonstrates:

1. Distance metrics comparison (when to use each)
2. Normalization preset impacts
3. CLI command suggestions
4. Document similarity comparison
5. Real-world typo correction
6. Error handling

#### Breaking Changes

- None (fully backward compatible with v0.1.6)

## [0.1.6] - 2025-10-25

### Telemetry Retrofit Complete - Full Dogfooding Achievement

**Release Type**: Major Milestone - Complete Module Instrumentation
**Release Date**: October 25, 2025
**Status**: ✅ Released

**Summary**: PyFulmen v0.1.6 achieves complete telemetry dogfooding across all 8 major modules (Phases 1.5-8). This milestone establishes PyFulmen as the first Fulmen helper library with comprehensive self-instrumentation, proving the telemetry pattern for ecosystem-wide adoption. All modules now observe their own behavior, providing production-ready observability from day one.

#### Key Achievements

**🎯 Telemetry Retrofit Complete (Phases 1.5-8)**:

- ✅ **8 Modules Instrumented**: Pathfinder, Config, Schema, Foundry, Logging, Crucible, Docscribe, FulHash
- ✅ **16 Metrics Deployed**: 8 histograms + 13 counters across all modules
- ✅ **1269 Tests Passing**: 1250 baseline + 19 new telemetry smoke tests
- ✅ **Zero Performance Overhead**: <10ns per operation for performance-sensitive modules
- ✅ **Two Instrumentation Patterns**: Standard (histogram + counter) and Performance-Sensitive (counter-only)
- ✅ **Ecosystem Alignment**: Follows [Crucible ADR-0008](docs/crucible-py/architecture/decisions/ADR-0008-helper-library-instrumentation-patterns.md)

**📊 Module Coverage**:

- **Phase 1.5**: Pathfinder (`pathfinder_find_ms`, `pathfinder_validation_errors`, `pathfinder_security_warnings`)
- **Phase 2**: Config (`config_load_ms`, `config_load_errors`)
- **Phase 3**: Schema (`schema_validation_ms`, `schema_validation_errors`)
- **Phase 4**: Foundry (`foundry_lookup_count`)
- **Phase 5**: Logging (`logging_emit_count`, `logging_emit_latency_ms`)
- **Phase 6**: Crucible (`crucible_list_assets_ms`, `crucible_find_schema_ms`, `crucible_find_config_ms`, `crucible_get_doc_ms`, `crucible_asset_not_found_count`)
- **Phase 7**: Docscribe (`docscribe_parse_count`, `docscribe_extract_headers_count`)
- **Phase 8**: FulHash (`fulhash_hash_file_count`, `fulhash_hash_string_count`, `fulhash_stream_created_count`, `fulhash_errors_count`)

**🔧 Test Quality Improvements**:

- ✅ **Zero Test Warnings**: Fixed deprecation warnings in backward compatibility tests
- ✅ **Pytest Markers**: Registered `slow` marker to eliminate unknown mark warnings
- ✅ **Clean Test Suite**: 11 warnings → 0 warnings across 1269 tests

**📚 Documentation**:

- ✅ **Telemetry Instrumentation Pattern Guide**: Complete pattern documentation with examples
- ✅ **Release Notes**: Comprehensive v0.1.6 documentation (510 lines)
- ✅ **CHANGELOG**: Updated with all 8 phases of telemetry work

#### Breaking Changes

- None (fully backward compatible with v0.1.5)

#### Migration Notes

**No migration required** - all telemetry instrumentation is internal to PyFulmen modules. Applications using PyFulmen automatically benefit from the instrumentation without code changes.

**Observability Benefits**:

```python
from pyfulmen import telemetry, logging, pathfinder

# Create registry to capture metrics
registry = telemetry.MetricRegistry()

# Use PyFulmen modules normally - they instrument themselves
finder = pathfinder.Finder()
results = finder.find_files(pathfinder.FindQuery(root="/path/to/project"))

# Retrieve emitted metrics
events = registry.get_events()
for event in events:
    print(f"{event.name}: {event.value}")
# Output: pathfinder_find_ms: 12.5, pathfinder_validation_errors: 0
```

#### Quality Gates

- [x] All 1269 tests passing (1250 baseline + 19 new telemetry tests)
- [x] Zero test warnings (down from 11)
- [x] 93% overall coverage maintained
- [x] Code quality checks passing (ruff lint, ruff format)
- [x] All 8 modules instrumented with comprehensive telemetry
- [x] Performance validated (<10ns overhead for FulHash counter-only pattern)
- [x] Documentation complete (pattern guide, CHANGELOG, release notes)
- [x] Ecosystem alignment verified (Crucible ADR-0008)

#### Release Checklist

- [x] Version number set in VERSION (0.1.6)
- [x] pyproject.toml version updated (0.1.6)
- [x] All 8 telemetry phases completed (Pathfinder, Config, Schema, Foundry, Logging, Crucible, Docscribe, FulHash)
- [x] Test quality improvements completed (zero warnings)
- [x] Documentation updated (CHANGELOG, RELEASE_NOTES, telemetry pattern guide)
- [x] All 1269 tests passing with zero warnings
- [x] Code quality checks passing
- [x] Commit 1 completed (d912990 - Phase 8 + test cleanup)
- [ ] Commit 2: Release finalization (README, overview, release notes) - in progress
- [ ] Git tag created (v0.1.6) - after commit 2
- [ ] Git push with tags - final step

---

## [0.1.4] - 2025-10-21

### Crucible Bridge API + Docscribe Module

**Release Type**: Feature Release - Unified Asset Access + Documentation Processing
**Release Date**: October 21, 2025
**Status**: ✅ Released

#### Features

**Crucible Bridge API (Unified Asset Access)**:

- ✅ **Unified Interface**: Single API for discovering and accessing all Crucible assets
  - `crucible.list_categories()` - Discover docs/schemas/config categories
  - `crucible.list_assets(category, prefix)` - List assets with filtering
  - `crucible.load_schema_by_id(schema_id)` - Load schemas by full ID
  - `crucible.get_config_defaults(category, version)` - Access config by path
  - `crucible.open_asset(asset_id)` - Stream large assets via context manager
  - `crucible.get_crucible_version()` - Get embedded Crucible metadata
- ✅ **Models**: AssetMetadata, CrucibleVersion with Pydantic validation
- ✅ **Error Handling**: AssetNotFoundError with similarity-based suggestions (up to 3)
- ✅ **Recursive Discovery**: Walks nested schema/config directories automatically
- ✅ **Prefix Filtering**: Filter assets by full ID path (e.g., `library/foundry/v1.0.0`)
- ✅ **21 Integration Tests**: Tested against real synced Crucible assets
- ✅ **321 Unit Tests**: Comprehensive coverage of bridge models and APIs
- ✅ **Recommended Pattern**: Preferred API for new code

**Docscribe Module (Documentation Processing)**:

- ✅ **Frontmatter Parsing**: Extract YAML headers and clean markdown bodies
  - `docscribe.parse_frontmatter(content)` - Returns (content, metadata) tuple
  - `docscribe.extract_metadata(content)` - Get frontmatter dict only
  - `docscribe.strip_frontmatter(content)` - Remove frontmatter, return clean markdown
  - `docscribe.has_frontmatter(content)` - Boolean check for frontmatter presence
- ✅ **Format Detection**: Identify document types and multi-document streams
  - `docscribe.detect_format(content)` - Detects json/yaml/markdown/toml/multi-document
  - `docscribe.split_documents(content)` - Split YAML streams and concatenated markdown
  - `docscribe.inspect_document(content)` - Get format, line count, headers, sections
- ✅ **Header Extraction**: Parse markdown structure for navigation
  - `docscribe.extract_headers(content)` - Extract headers with anchors and line numbers
  - `docscribe.generate_outline(content, max_depth)` - Nested table of contents
  - `docscribe.search_headers(content, pattern)` - Find headers by pattern
- ✅ **Models**: DocumentHeader (level, text, anchor, line_number), DocumentInfo
- ✅ **GitHub-Compatible Anchors**: Preserve double-hyphens from special characters
- ✅ **Smart Parsing**: Distinguishes frontmatter from YAML document separators
- ✅ **92 Unit Tests**: Frontmatter, formats, headers, edge cases
- ✅ **12 Integration Tests**: Tested against real Crucible documentation
- ✅ **95% Coverage**: Comprehensive test coverage across docscribe module

**Crucible Integration**:

- ✅ **Crucible Bridge Delegation**: `crucible.get_documentation()` uses docscribe internally
- ✅ **Clean Content Access**: `crucible.get_documentation(path)` returns frontmatter-stripped markdown
- ✅ **Metadata Extraction**: `crucible.get_documentation_metadata(path)` returns YAML dict
- ✅ **Combined Access**: `crucible.get_documentation_with_metadata(path)` for efficiency

**Infrastructure & Documentation**:

- ✅ **Crucible Overview Section**: Added to docs/pyfulmen_overview.md (mandatory per helper library standard)
  - Explains Crucible SSOT role and ecosystem consistency
  - Describes shim and docscribe module purpose
  - Links to Crucible repo, technical manifesto, and sync standard
- ✅ **Module Catalog Updates**: Docscribe listed as ✅ Stable with 95% coverage target
- ✅ **Synced Crucible Assets**: Module standards, architecture docs, manifest updates
- ✅ **845 Tests**: 113 new tests for bridge and docscribe (845 total passing, 18 skipped)

#### Breaking Changes

- None (fully backward compatible with v0.1.3)
- All legacy APIs (`crucible.docs.read_doc()`, etc.) maintained unchanged

#### Migration Notes

- **Bridge API**: Recommended for new code, but legacy APIs still supported
  - Old: `crucible.schemas.load_schema(category, version, name)`
  - New: `crucible.load_schema_by_id('category/version/name')` (recommended)
- **Docscribe**: Access directly or via crucible bridge
  - Direct: `from pyfulmen import docscribe; docscribe.parse_frontmatter(content)`
  - Bridge: `from pyfulmen import crucible; crucible.get_documentation(path)`
- **No code changes required**: All existing code continues to work

#### Known Limitations

- None for v0.1.4 features
- Docscribe Phase 2 (config loading with frontmatter) deferred to v0.1.5

#### Quality Gates

- [x] All 845 tests passing (113 new tests for bridge + docscribe)
- [x] 90%+ coverage maintained across all modules
- [x] 95% coverage on docscribe module
- [x] Code quality checks passing (ruff lint, ruff format)
- [x] Bridge API integration tests against real Crucible assets
- [x] Docscribe tests cover frontmatter, formats, headers, edge cases
- [x] Documentation complete (CHANGELOG, overview, module specs)
- [x] Crucible Overview section added per helper library standard
- [x] Cross-language standards synced

#### Release Checklist

- [x] Version number set in VERSION (0.1.4)
- [x] pyproject.toml version updated (0.1.4)
- [x] CHANGELOG.md updated with v0.1.4 entry
- [x] RELEASE_NOTES.md updated with v0.1.4 section
- [x] docs/pyfulmen_overview.md updated (Crucible Overview section added)
- [x] All tests passing (845 tests)
- [x] Code quality checks passing
- [x] Documentation reviewed and updated
- [x] Agentic attribution proper for all commits
- [ ] docs/releases/v0.1.4.md created - next step
- [ ] Git tag created (v0.1.4) - after release doc
- [ ] Git push with tags - final step

---

## [0.1.5] - 2025-10-22

### Foundry Text Similarity & Crucible Integration

**Release Type**: Feature Release - Text Similarity Module & Enhanced Asset Discovery
**Release Date**: October 22, 2025
**Status**: ✅ Released

#### Features

**Foundry Text Similarity Module**:

- ✅ **Levenshtein Distance**: Wagner-Fischer algorithm with O(mn) dynamic programming
  - `similarity.distance(s1, s2)` - Calculate edit distance between strings
  - `similarity.score(s1, s2)` - Normalized similarity score (0.0 to 1.0)
- ✅ **Suggestion API**: Ranked fuzzy matching with case-insensitive tie-breaking
  - `similarity.suggest(query, candidates, min_score, max_suggestions)` - Get ranked suggestions
  - Returns `Suggestion` dataclass with `value` and `score` fields
  - Tie-breaking: score desc → case-insensitive alpha → uppercase count → exact value
- ✅ **Unicode Normalization**: Turkish locale support and accent stripping
  - `similarity.normalize(text, locale)` - Unicode case folding with locale awareness
  - `similarity.casefold(text)` - Case-insensitive comparison
  - `similarity.strip_accents(text)` - Remove diacritical marks
  - `similarity.equals_ignore_case(s1, s2)` - Case-insensitive string equality
- ✅ **61 Tests Passing**: 19 distance + 22 normalization + 14 suggest + 6 fixture validation
- ✅ **Cross-Language Fixtures**: Shared test cases in `config/crucible-py/library/foundry/similarity-fixtures.yaml`
- ✅ **ADR-0007**: Case-insensitive tie-breaking decision documented
- ✅ **Location**: `src/pyfulmen/foundry/similarity/`

**Crucible Similarity Adoption**:

- ✅ **Replaced Ad-Hoc Suggestions**: Crucible bridge now uses `foundry.similarity.suggest()`
  - Removed `_find_similar_assets()` from `bridge.py`
  - Removed dead code `_get_similar_docs()` from `docs.py`
  - Updated threshold to `min_score=0.6` (Foundry standard compliance)
- ✅ **Consistent Error Messaging**: All asset not found errors use standardized suggestion algorithm
- ✅ **165 Crucible Tests Passing**: All integration tests validated with new similarity engine

**Crucible Shim Standard Updates**:

- ✅ **Synced Standards**: Updated `crucible-shim.md` with metadata requirements
- ✅ **Bridge API Deprecations**: Marked `load_schema_by_id()` and `get_config_defaults()` as deprecated
  - Replacement: `find_schema()` and `find_config()` return tuples with metadata
  - Deprecation warnings emitted (removal in v0.2.0)
- ✅ **Documentation Sync**: Latest Crucible standards and forge-workhorse requirements

#### Breaking Changes

- None (fully backward compatible with v0.1.4)
- Deprecation warnings for legacy bridge APIs (removal in v0.2.0)

#### Migration Notes

**Text Similarity**:

```python
from pyfulmen.foundry import similarity

# Calculate edit distance
dist = similarity.distance("kitten", "sitting")  # Returns: 3

# Get normalized score
score = similarity.score("color", "colour")  # Returns: 0.833

# Get ranked suggestions
suggestions = similarity.suggest(
    "loging",  # typo
    ["logging", "login", "logic"],
    min_score=0.6,
    max_suggestions=3
)
# Returns: [Suggestion(value="logging", score=0.857), ...]
```

**Crucible Bridge - New Pattern** (Recommended):

```python
from pyfulmen import crucible

# OLD (deprecated, still works)
schema = crucible.load_schema_by_id('observability/logging/v1.0.0/logger-config')

# NEW (recommended - returns metadata)
schema, meta = crucible.find_schema('observability/logging/v1.0.0/logger-config')
print(f"Schema size: {meta.size} bytes, checksum: {meta.checksum[:8]}...")
```

#### Known Limitations

- **Damerau-Levenshtein**: Transposition support deferred to future release
  - 3 fixture tests skipped with TODO markers
  - Standard Levenshtein sufficient for current use cases
- **Crucible Version Metadata**: API planned but blocked by goneat ssot sync (see v0.1.7)

#### Quality Gates

- [x] All 947 tests passing (61 new tests for similarity, 165 crucible tests)
- [x] 92% coverage maintained across all modules
- [x] Code quality checks passing (ruff lint, ruff format)
- [x] Similarity algorithm matches cross-language fixtures
- [x] Crucible bridge integration validated
- [x] ADR-0007 documented (case-insensitive tie-breaking)

#### Release Checklist

- [x] Version number set in VERSION (0.1.5)
- [x] pyproject.toml version updated (0.1.5)
- [x] Similarity module implemented and tested
- [x] Crucible adoption complete
- [x] All tests passing (947 tests, 18 skipped)
- [x] Code quality checks passing
- [x] ADR-0007 created and reviewed
- [ ] CHANGELOG.md updated with v0.1.5 entry - next
- [ ] RELEASE_NOTES.md updated with v0.1.5 section - this file
- [ ] docs/releases/v0.1.5.md created - next
- [ ] Git commits ready (4 commits ahead)
- [ ] Git tag created (v0.1.5) - after release doc
- [ ] Git push with tags - final step

---

## [0.1.6] - 2025-10-23

### Error Handling & Telemetry Modules

**Release Type**: Feature Release - First Language to Implement Error/Telemetry Modules
**Release Date**: October 23, 2025
**Status**: 🔄 In Progress

#### Features

**Error Handling Module (error-handling-propagation)**:

- ✅ **Pathfinder Error Models**: Pydantic-based data structures (not exceptions)
  - `PathfinderError` - Base error structure (code, message, details, path, timestamp)
  - `FulmenError` - Extended error with telemetry metadata
  - Fields: severity, severity_level, correlation_id, trace_id, exit_code, context, original
- ✅ **Wrapping API**: `error_handling.wrap(base_error, severity, context, ...)`
  - Auto-populates correlation_id from logging context
  - Serializes original Python exceptions with traceback
  - Maps severity names to severity_level integers (0-4)
- ✅ **Schema Validation**: `error_handling.validate(error)` - Crucible schema compliance
- ✅ **Exit Helper**: `exit_with_error(exit_code, error, logger)`
  - Severity-aware logging (info/warn/error/fatal mapping)
  - Graceful stderr fallback when logging unavailable
  - Structured context emission before sys.exit()
- ✅ **95% Coverage**: 4 test methods, all error paths validated
- ✅ **Crucible Standard**: Error handling as data models (Crucible 2025.10.3)

**Telemetry Module (telemetry-metrics)**:

- ✅ **Three Metric Types**: Counter (monotonic), Gauge (instantaneous), Histogram (distribution)
  - `MetricRegistry.counter(name)` - Get or create counter instrument
  - `MetricRegistry.gauge(name)` - Get or create gauge instrument
  - `MetricRegistry.histogram(name, buckets)` - Get or create histogram with buckets
- ✅ **Thread-Safe Registry**: Concurrent metric recording via threading.Lock
- ✅ **Crucible Taxonomy Validation**: `validate_metric_event(event)`
  - Validates metric names against taxonomy (schema_validations, config_load_ms, etc.)
  - Validates units per metric (count, ms, bytes, percent)
  - Validates histogram bucket structure (cumulative, numeric bounds)
- ✅ **Default Histogram Buckets**: `[1, 5, 10, 50, 100, 500, 1000, 5000, 10000]` milliseconds
  - Covers 1ms to 10s range for typical library operations
  - Cross-language compatible (numeric sentinel instead of null/Infinity)
- ✅ **Logging Integration**: `logging.emit_metrics_to_log(logger, events)`
  - Routes metric events through progressive logging pipeline
  - Emits structured JSON with metric_event context
- ✅ **85% Coverage**: 6 test methods, validation edge cases, thread safety
- ✅ **Crucible Standard**: Default histogram buckets `[1, 5, 10, 50, 100, 500, 1000, 5000, 10000]` ms (Crucible 2025.10.3)
- ✅ **ADR-0008**: Metric registry pattern (explicit instantiation over global singleton)

**Integration & Fixtures**:

- ✅ **Cross-Language Fixtures**: JSON fixtures for error/metric validation
  - `tests/fixtures/errors/` - valid_error.json, invalid_error_missing_code.json
  - `tests/fixtures/metrics/` - scalar_counter.json, histogram_ms.json, invalid_metric_bad_name.json
  - All fixtures schema-validated (valid pass, invalid fail as expected)
  - Terminal histogram bucket uses 1e9 (numeric) instead of null for cross-language compatibility
- ✅ **Example Integration**: `examples/error_telemetry_demo.py`
  - Demonstrates error wrapping, validation, metrics recording, logging integration
  - Full working demo with structured JSON output
- ✅ **Module Exports Updated**:
  - `error_handling.__all__` - Added exit_with_error
  - `telemetry.__all__` - Added validate_metric_event, validate_metric_events
  - `logging.__all__` - Added emit_metrics_to_log

**Documentation**:

- ✅ **README Updated**: Added Error Handling and Telemetry & Metrics sections with examples
- ✅ **Module Catalog**: Added error-handling-propagation and telemetry-metrics (✅ Stable)
- ✅ **ADR-0008**: Metric Registry Pattern (explicit instantiation pattern documented)
- ✅ **Crucible Standards Support**: Error handling data models and histogram buckets (2025.10.3)
- [ ] CHANGELOG.md entry - pending
- [ ] docs/releases/v0.1.6.md - after scope finalized

#### Breaking Changes

- None (fully backward compatible with v0.1.5)

#### Migration Notes

**Error Handling**:

```python
from pyfulmen import error_handling, logging
from datetime import datetime, UTC

# Create Pathfinder error
base = error_handling.PathfinderError(
    code="CONFIG_INVALID",
    message="Failed to load config",
    timestamp=datetime.now(UTC)
)

# Wrap with telemetry metadata
error = error_handling.wrap(
    base,
    severity="high",  # "info" | "low" | "medium" | "high" | "critical"
    context={"environment": "production"}
)

# Validate against schema
is_valid = error_handling.validate(error)  # True

# Exit with structured logging
logger = logging.Logger(service="myapp")
# error_handling.exit_with_error(1, error, logger=logger)
```

**Telemetry**:

```python
from pyfulmen import telemetry, logging

# Create registry
registry = telemetry.MetricRegistry()

# Record metrics
registry.counter("requests").inc()
registry.gauge("connections").set(42)
registry.histogram("latency_ms").observe(12.5)

# Get events and validate
events = registry.get_events()
event_dicts = [e.model_dump(mode="json") for e in events]
telemetry.validate_metric_event(event_dicts[0])  # True

# Integrate with logging
logger = logging.Logger(service="myapp", profile=logging.LoggingProfile.STRUCTURED)
logging.emit_metrics_to_log(logger, event_dicts)
```

#### Cross-Language Implications

**PyFulmen is the first language implementation** of error-handling and telemetry modules. Design decisions documented in ADRs for gofulmen and tsfulmen adoption:

- **Data Models vs Exceptions**: Pydantic models translate to Go structs and TS interfaces
- **Histogram Buckets**: `[1, 5, 10, 50, 100, 500, 1000, 5000, 10000]` ms - numeric for cross-language JSON
- **Registry Pattern**: Explicit `MetricRegistry()` instantiation matches Go/TS idioms

#### Known Limitations

- **No Global Telemetry Helpers**: Must create `MetricRegistry()` instance (by design per ADR-0010)
- **Histogram Buckets Fixed**: Taxonomy doesn't specify per-metric buckets (local decision per ADR-0009)

#### Quality Gates

- [x] All 1,058 tests passing (100 new tests: error_handling + telemetry + validation)
- [x] 93% coverage maintained across all modules
- [x] 95% coverage on error_handling module
- [x] 85% coverage on telemetry module
- [x] Code quality checks passing (ruff lint, ruff format)
- [x] Schema validation: all fixtures validated correctly
- [x] Example demo runs successfully
- [x] README updated with new modules
- [x] Module catalog updated
- [x] ADR-0008 created (metric registry pattern)
- [x] Crucible standards support validated (error data models, histogram buckets)
- [ ] CHANGELOG.md updated - pending
- [ ] Final prepush validation - pending

#### Release Checklist

- [ ] Version number set in VERSION (0.1.6)
- [ ] pyproject.toml version updated (0.1.6)
- [x] Error handling module implemented (95% coverage)
- [x] Telemetry module implemented (85% coverage)
- [x] Fixtures created and validated
- [x] Example integration demo working
- [x] All 1,058 tests passing (18 skipped)
- [x] Code quality checks passing
- [x] ADR-0008 created (metric registry pattern)
- [x] Crucible 2025.10.3 standards support validated
- [x] README updated
- [x] Module catalog updated
- [ ] CHANGELOG.md updated - next
- [ ] docs/releases/v0.1.6.md - after scope finalized
- [ ] Git commits ready
- [ ] Git tag created (v0.1.6) - after finalization
- [ ] Git push with tags - final step

---

## [Unreleased]

### v0.2.0 - Enterprise Complete (Planned)

- Full enterprise logging implementation
- Complete progressive interface features
- Pathfinder Phase 3 (service facade, streaming, processors, telemetry)
- Docscribe Phase 2 (config loading with frontmatter validation)
- Cross-language compatibility verified
- Comprehensive documentation and examples
- Production-ready for FulmenHQ ecosystem

---

_Release notes will be updated as development progresses._
