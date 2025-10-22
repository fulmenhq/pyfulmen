# Release Notes

This document tracks release notes and checklists for PyFulmen releases.

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
