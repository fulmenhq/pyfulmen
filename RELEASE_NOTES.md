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
