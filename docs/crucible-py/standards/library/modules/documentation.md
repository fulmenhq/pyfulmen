---
title: "Documentation Module Standard"
description: "Cross-language helper contract for accessing and processing Crucible documentation assets, including frontmatter extraction and clean content reads"
author: "Fulmen Enterprise Architect (@fulmen-ea-steward)"
date: "2025-10-20"
last_updated: "2025-10-20"
status: "draft"
tags: ["standards", "library", "documentation", "frontmatter", "2025.10.2"]
---

# Documentation Module Standard

## Purpose
Provide a consistent helper API for accessing Crucible documentation assets embedded in Fulmen helper libraries. This module enables users to extract structured metadata (YAML frontmatter) and clean content (markdown body without frontmatter), supporting tool integrations and runtime doc discovery. It aligns with the Crucible Shim for indirect access and emphasizes lightweight processing to avoid bloat.

Every Fulmen helper library MUST implement this module as a core capability, ensuring API parity across languages (Go, Python, TypeScript, etc.). The module focuses on extraction and basic validation, deferring rendering/search to user tools.

## Responsibilities
1. **Asset Access**: Load documentation from synced Crucible paths (`docs/crucible-{lang}/`).
2. **Frontmatter Extraction**: Parse YAML headers (delimited by `---`) into structured dicts (title, author, date, status, tags, etc.).
3. **Clean Content**: Return markdown body stripped of frontmatter.
4. **Config Reads**: Load YAML/JSON configs with optional schema validation (integrate with Schema Validation module).
5. **Error Handling**: Provide helpful errors (e.g., `AssetNotFoundError` with suggestions) and integrate with Error Handling module.
6. **Performance**: Use caching for metadata/index; support streaming for large assets.
7. **Overrides**: Respect environment vars for custom doc roots (align with Config Path API).

## API Contract
Language bindings MUST provide the following surface (idiomatic naming allowed; expose under `crucible.documentation` or equivalent namespace):

### Core APIs (Mandatory - Phase 1)
| Function                          | Return Type                  | Description                                                                 |
|-----------------------------------|------------------------------|-----------------------------------------------------------------------------|
| `get_documentation(path)`         | str                          | Returns clean markdown body (frontmatter stripped). Raises `AssetNotFoundError`. |
| `get_documentation_metadata(path)`| dict[str, Any] \| None       | Extracts YAML frontmatter as dict. Returns `None` if absent.                |
| `get_documentation_with_metadata(path)` | tuple[str, dict[str, Any] \| None] | Combined: (clean_content, metadata). Convenience wrapper.                   |

- `path`: Relative to Crucible docs/config root (e.g., `standards/observability/logging.md`).
- Frontmatter keys: Standardize on `title`, `description`, `author`, `date`, `last_updated`, `status`, `tags`; preserve others.

### Config & Discovery APIs (Recommended - Phase 2)
| Function                          | Return Type                  | Description                                                                 |
|-----------------------------------|------------------------------|-----------------------------------------------------------------------------|
| `load_config(path, schema=None)`  | dict[str, Any]               | Loads YAML/JSON config; validates against schema if provided. Raises `ValidationError`. Integrates with Three-Layer Config system. |
| `list_documents(category=None, filter=None)` | list[DocumentMetadata] | Lists metadata; filters by category (e.g., `standards`) or metadata (e.g., `{"status": "stable"}`). |
| `find_documents(query, fields=["title", "tags"])` | list[DocumentMetadata] | Simple metadata search (no full-text).                                      |

- `load_config` integrates with existing Three-Layer Config module for cross-library consistency
- `schema`: Optional schema ID from Schema Validation module (e.g., `observability/logging/v1.0.0/logger-config`)
- `DocumentMetadata`: `{id: str, path: str, title: str, status: str, tags: list[str], checksum?: str}`.
- Filter: Dict for exact/partial matches (e.g., `{"tags": ["observability"]}`).

Language idioms:
- **Go**: Functions in `crucible/docs` package; return `string, error` or structs; use `embed.FS` for assets.
- **Python**: Module `pyfulmen.crucible.documentation`; return `str`/`dict`; use `pathlib` for paths; context managers for streaming.
- **TypeScript**: Namespace `@fulmenhq/crucible/documentation`; async where needed; return `string`/`Record<string, any>`.

## Implementation Notes
- **Frontmatter Parsing**: Detect `---` delimiters; use safe YAML loaders (e.g., Go `gopkg.in/yaml.v3`, Python `pyyaml.safe_load`, TS `js-yaml`). Limit depth/nesting to prevent DoS. ~50 LOC minimal parser if avoiding deps.
- **Content Stripping**: Slice markdown after closing `---`; trim whitespace.
- **Caching**: Module-level index for `list_documents` (build on sync or lazy-scan); invalidate via env var or API flag.
- **Validation**: Integrate `load_schema` from Schema Validation module for configs.
- **Edge Cases**: Handle no frontmatter, malformed YAML (raise `ParseError`), empty files, large assets (stream via `open_asset`).
- **Namespace**: Under Crucible Shim; e.g., `crucible.GetDocumentation(path)` for top-level access.
- **No Bloat**: Avoid markdown parsers (e.g., no CommonMark); users pipe to external tools for rendering.

## Testing Requirements
- Unit: Frontmatter extraction (valid/invalid/empty), content stripping, config loading (with/without schema).
- Integration: Load real Crucible assets; verify metadata matches expected (e.g., title from frontmatter).
- Performance: `list_documents` <50ms; cache hits instant.
- Coverage: 80%+; include platform-specific path handling.
- Errors: Test `AssetNotFoundError` suggestions (e.g., fuzzy match paths).

## Related Documents
- [Crucible Shim Standard](../crucible-shim.md)
- [Schema Validation Standard](../schema-validation.md)
- [Error Handling Standard](../error-handling-propagation.md)
- [Fulmen Helper Library Standard](../../../architecture/fulmen-helper-library-standard.md)
- `.plans/active/2025.10.2/documentation-module-proposal.md` (proposal details)

## Changelog
- **2025-10-20**: Initial draft based on ecosystem proposal.
- **2025-10-20**: Updated API Contract - moved `load_config` from Mandatory (Phase 1) to Recommended (Phase 2) to align with PyFulmen v0.1.4 implementation. Phase 1 focuses on core documentation access with frontmatter parsing; Phase 2 will add config loading with validation and discovery APIs.