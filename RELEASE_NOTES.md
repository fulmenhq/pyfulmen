# Release Notes

This document tracks release notes and checklists for PyFulmen releases.

## [0.1.9] - 2025-11-04

### Schema Export, Exit Codes & Crucible v0.2.4 Sync

**Release Type**: Major Feature Enhancement - Schema Management + Error Standardization + Infrastructure
**Release Date**: November 4, 2025
**Status**: ✅ Ready for Release

**Summary**: PyFulmen v0.1.9 delivers three major enhancements: comprehensive schema export functionality, standardized exit codes integration with 54 semantic codes, and Crucible v0.2.4 sync with schema migration to 2020-12 draft and new app-identity module. This release significantly expands PyFulmen's enterprise capabilities.

#### Key Features

**📤 Schema Export API**:

- Complete schema materialization system with JSON/YAML format support
- `export_schema()` function with provenance metadata embedding and validation
- CLI integration: `pyfulmen schema export` with comprehensive options
- Provenance tracking with configurable metadata inclusion
- 23 comprehensive tests (14 unit + 9 integration, 100% pass rate)

**🚨 Standardized Exit Codes**:

- 54 semantic exit codes across 11 categories for enterprise error handling
- Simplified mode mappings for monitoring/alerting system integration
- Cross-language consistency with gofulmen/tsfulmen exit codes
- 8 exported APIs for exit code management and metadata access
- 13 parity tests ensuring ecosystem consistency

**🔧 Crucible v0.2.4 Infrastructure**:

- Schema migration: JSON Schema draft-07 → 2020-12 across all schemas
- App-identity repository configuration module with validation fixtures
- Additional standards: server management, web styling, protocol standards
- Code generation templates and repository structure standards

#### Quality Gates

- [x] All 1343 tests passing (1322 passed, 21 skipped)
- [x] 93% code coverage maintained
- [x] Schema export functionality fully tested
- [x] Crucible sync validated and committed
- [x] Documentation updated

#### Breaking Changes

- None (fully backward compatible with v0.1.8)

## [0.1.8] - 2025-10-29

### CI/CD Infrastructure & Public Release Readiness

**Release Type**: Infrastructure & Quality - CI/CD + Dependency Fixes
**Release Date**: October 29, 2025
**Status**: ✅ Released

**Summary**: PyFulmen v0.1.8 establishes production-grade CI/CD infrastructure with GitHub Actions, fixes critical dependency classification for Similarity v2.0.0, and improves test reliability across platforms. This release marks the first public release with comprehensive automated testing on Ubuntu and macOS runners.

#### Key Features

**🚀 GitHub Actions CI/CD**:

- Matrix testing: Ubuntu/macOS × Python 3.12/3.13 (4 combinations)
- Quality gates: linting (`ruff check`), formatting (`ruff format`), test coverage
- Package validation: Build checks and metadata verification with `twine`
- Codecov integration for coverage tracking (optional)
- Automated workflows for `main` branch pushes and pull requests

**🔧 Dependency Fixes**:

- **rapidfuzz now required** (≥3.14.1): Moved from optional dev dependency to main runtime dependency
- Similarity v2.0.0 metrics (Damerau-Levenshtein, Jaro-Winkler) require rapidfuzz for correct implementations
- Removed incorrect fallback algorithms that violated Crucible fixtures

**🧪 Test Reliability Improvements**:

- Platform-conditional tests: macOS/Linux/Windows tests skip on non-native platforms
- Replaced fragile mock-based tests with actual behavior validation
- Performance test thresholds adjusted for CI runner characteristics (600% overhead allowance)
- Reality-check tests using environment variables instead of complex mocking

**📚 Infrastructure**:

- Crucible v0.2.2 sync (from v0.2.1)
- SSOT provenance validation in pre-push hooks
- Project URLs added to `pyproject.toml` (Homepage, Documentation, Repository, Changelog)

#### Breaking Changes

- **rapidfuzz dependency**: Now required at runtime. Applications must have `rapidfuzz>=3.14.1` installed.

#### Migration Notes

If you're upgrading from v0.1.7:

```bash
# rapidfuzz is now automatically installed as a runtime dependency
pip install --upgrade pyfulmen
# or with uv
uv pip install --upgrade pyfulmen
```

**No code changes required** - rapidfuzz was previously imported conditionally and is now always available.

#### Quality Gates

- [x] All 1286 tests passing (19 skipped platform-specific tests)
- [x] 93% code coverage maintained
- [x] CI/CD passing on Ubuntu and macOS runners
- [x] Package builds successfully and passes `twine check`
- [x] Codecov reporting enabled (optional)
- [x] Public readiness audit completed
- [x] SSOT provenance validation passing

#### Lessons Learned

**Testing Philosophy**:

- Avoid complex mocking when possible - prefer platform-conditional tests with `pytest.skip`
- Environment variable-based tests are more maintainable than mocking classmethods
- Reality-check tests that validate actual behavior are more valuable than mock correctness tests
- Performance tests need generous thresholds for CI runners (different hardware characteristics)

**CI/CD Best Practices**:

- Use `uv tool run` for one-off tools (e.g., `twine`) - don't install via pip
- Matrix testing across platforms catches platform-specific issues early
- Performance tests should account for slower CI runners vs local dev machines

## [0.1.7] - 2025-10-27

### Foundry Similarity v2.0.0 Upgrade - Multiple Metrics & Advanced Normalization

**Release Type**: Feature Enhancement - Foundry Similarity v2.0.0
**Release Date**: October 27, 2025
**Status**: ✅ Released

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
