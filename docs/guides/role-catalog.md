# Role Catalog Guide

The Crucible role catalog provides typed access to agentic role definitions (devlead, devrev, secrev, etc.) synced from the Crucible SSOT. Use this when you need to programmatically inspect role definitions, build tooling around roles, or integrate role metadata into your application.

## Quick Start

```python
from pyfulmen.crucible import load_role, list_role_slugs, load_role_catalog

# List all available role slugs
slugs = list_role_slugs()
# ['cicd', 'cxotech', 'dataeng', 'deliverylead', 'devlead', 'devrev', ...]

# Load a single role by slug
role = load_role("devlead")
print(role.name)             # "Development Lead"
print(role.description)      # "Architecture, implementation, ..."
print(role.responsibilities)  # ["Implement features ...", ...]

# Load entire catalog as a dict keyed by slug
catalog = load_role_catalog()
for slug, role in catalog.items():
    print(f"{slug}: {role.name}")
```

## API Reference

### Functions

#### `list_role_slugs() -> list[str]`

Returns a sorted list of all available role slugs. README.md is excluded.

```python
slugs = list_role_slugs()
assert slugs == sorted(slugs)  # Always sorted
assert "devlead" in slugs       # Core roles always present
```

#### `load_role(slug: str) -> RolePrompt`

Loads and parses a single role by slug. Validates the slug format against the schema regex `^[a-z][a-z0-9]*$`.

```python
role = load_role("secrev")
print(role.name)        # "Security Review"
print(role.checklists)  # {"security_review": ["Credentials stored securely ...", ...]}
```

**Raises:**
- `ValueError` if slug format is invalid (uppercase, hyphens, digits-first)
- `AssetNotFoundError` if slug is valid but no matching role exists (includes similarity suggestions)

```python
from pyfulmen.crucible import AssetNotFoundError

try:
    load_role("devleadx")  # typo
except AssetNotFoundError as e:
    print(e.suggestions)  # ["devlead"]
```

#### `load_role_catalog() -> dict[str, RolePrompt]`

Loads all roles and returns a dict keyed by slug (from parsed YAML, not filename).

```python
catalog = load_role_catalog()
assert len(catalog) == len(list_role_slugs())  # Internal consistency
```

### Types

All types are dataclasses (not Pydantic). Import from `pyfulmen.crucible`.

#### `RolePrompt`

The top-level role definition. All roles have these required fields populated:

| Field | Type | Notes |
|-------|------|-------|
| `slug` | `str` | Unique identifier (e.g., `"devlead"`) |
| `name` | `str` | Human-readable name |
| `description` | `str` | Short description |
| `version` | `str` | Role version (semver) |
| `status` | `str` | e.g., `"approved"` |
| `scope` | `list[str]` | What the role covers |
| `responsibilities` | `list[str]` | What the role does |
| `escalates_to` | `list[RoleEscalation]` | When to hand off |
| `does_not` | `list[str]` | Explicit boundaries |

Optional fields (may be `None` or empty):

| Field | Type | Notes |
|-------|------|-------|
| `author` | `str \| None` | Role author |
| `category` | `str \| None` | Role category |
| `extends` | `str \| None` | Base role URL |
| `domains` | `list[str]` | Domain tags |
| `tags` | `list[str]` | Search tags |
| `context` | `str \| None` | When/how to use this role |
| `mindset` | `RoleMindset \| None` | Focus questions and principles |
| `examples` | `list[RoleExample]` | Example artifacts |
| `checklists` | `dict[str, list[str]]` | Named checklists |
| `pre_push_checklist` | `list[str]` | Pre-push checks |
| `required_reading` | `RequiredReading \| None` | Files to read first |
| `cross_role_note` | `str \| None` | Notes about role interactions |

#### `RoleMindset`

```python
role = load_role("devlead")
if role.mindset:
    for q in role.mindset.focus:
        print(f"  Ask: {q}")
    for p in role.mindset.principles:
        print(f"  Follow: {p}")
```

| Field | Type |
|-------|------|
| `focus` | `list[str]` |
| `principles` | `list[str]` |

#### `RoleEscalation`

```python
for esc in role.escalates_to:
    print(f"Escalate to {esc.target} when: {esc.when}")
```

| Field | Type |
|-------|------|
| `target` | `str` |
| `when` | `str` |

#### `RoleExample`

| Field | Type |
|-------|------|
| `type` | `str` |
| `title` | `str` |
| `content` | `str` |

#### `RequiredReading`

Some roles (e.g., `releng`) require specific files to be read before starting work.

```python
role = load_role("releng")
if role.required_reading:
    print(role.required_reading.description)
    for f in role.required_reading.files:
        print(f"  Read {f.path}: {f.reason}")
```

| Field | Type |
|-------|------|
| `description` | `str \| None` |
| `pattern` | `str \| None` |
| `files` | `list[RequiredReadingFile]` |

#### `RequiredReadingFile`

| Field | Type |
|-------|------|
| `path` | `str` |
| `reason` | `str` |

## Common Patterns

### Building a role selector

```python
from pyfulmen.crucible import load_role_catalog

catalog = load_role_catalog()

# Find roles by domain
dev_roles = {
    slug: role for slug, role in catalog.items()
    if "development" in role.domains
}
```

### Extracting checklists for tooling

```python
role = load_role("secrev")
for checklist_name, items in role.checklists.items():
    print(f"\n## {checklist_name}")
    for item in items:
        print(f"- [ ] {item}")
```

### Generating AGENTS.md role tables

```python
from pyfulmen.crucible import load_role_catalog

catalog = load_role_catalog()
print("| Role | Description |")
print("|------|-------------|")
for slug, role in sorted(catalog.items()):
    print(f"| `{slug}` | {role.description} |")
```

## Telemetry

Role loading is instrumented automatically:

- `crucible_load_role_ms` (histogram) — time to load and parse a role
- `crucible_role_not_found_count` (counter) — slug-not-found events

## Important Notes

- **Do not import from `crucible.agentic`** — the vendored `src/crucible/agentic.py` uses different path resolution and is not designed for pyfulmen consumers. Always use `from pyfulmen.crucible import ...`.
- Role YAML files live in `config/crucible-py/agentic/roles/` and are synced from the Crucible SSOT via `make sync`. Do not edit them directly.
- Slug validation uses the schema regex `^[a-z][a-z0-9]*$` — no hyphens, underscores, or uppercase.
