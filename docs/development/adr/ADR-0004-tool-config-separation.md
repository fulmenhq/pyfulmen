---
id: "ADR-0004"
title: "Tool Configuration Separation (ruff.toml not pyproject.toml)"
status: "accepted"
date: "2025-10-15"
last_updated: "2025-10-15"
deciders:
  - "@pyfulmen-architect"
  - "@3leapsdave"
scope: "pyfulmen"
supersedes: []
tags:
  - "devops"
  - "tooling"
  - "code-quality"
  - "dry-principle"
related_adrs: []
---

# ADR-0004: Tool Configuration Separation (ruff.toml not pyproject.toml)

## Status

**Current Status**: Accepted

**Context**: v0.1.2 MIME detection implementation revealed DRY violation in Ruff configuration

## Context

During v0.1.2 MIME detection implementation, we discovered Ruff configuration was split between two files:

1. **pyproject.toml** - Had `[tool.ruff]` and `[tool.ruff.lint]` sections with line-length, select rules, and per-file-ignores
2. **ruff.toml** - Had separate configuration with additional settings (target-version, exclude, format)

This violated DRY (Don't Repeat Yourself) principles and created confusion:

```toml
# pyproject.toml (incomplete configuration)
[tool.ruff]
line-length = 100  # Duplicate!

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM"]  # Missing "C4"

# ruff.toml (more complete configuration)
line-length = 100  # Duplicate!
target-version = "py312"  # Only here
exclude = [...]  # Only here

[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]  # Has "C4"
```

The duplication led to:

- Uncertainty about which file was the source of truth
- Risk of inconsistent settings
- Maintenance burden when updating configuration
- Potential for settings to drift apart

## Decision

**Use dedicated tool configuration files (ruff.toml, pytest.ini, etc.) instead of embedding everything in pyproject.toml.**

**Specifically for Ruff**:

- Remove all `[tool.ruff]` sections from pyproject.toml
- Maintain ruff.toml as the single source of truth for all Ruff configuration
- Keep only project metadata in pyproject.toml (name, version, dependencies, build system)

## Rationale

### 1. Single Source of Truth (DRY)

One file per tool eliminates duplication and confusion:

```toml
# pyproject.toml - ONLY project metadata
[project]
name = "pyfulmen"
version = "0.1.2"
dependencies = [...]

# NO [tool.ruff] sections!

# ruff.toml - ALL Ruff configuration
line-length = 100
target-version = "py312"
exclude = [...]
[lint]
select = [...]
```

### 2. Separation of Concerns

- **pyproject.toml**: Project definition (PEP 518) - what the package is
- **Tool configs**: Tool behavior - how tools process the code

This mirrors how other ecosystems separate concerns:

- Go: `go.mod` (project) + `.golangci.yml` (linter)
- Node: `package.json` (project) + `.eslintrc` (linter)
- Rust: `Cargo.toml` (project) + `clippy.toml` (linter)

### 3. Discoverability

When developers need to adjust linting rules, they look for `ruff.toml` (or `.ruff.toml`). This is intuitive and matches tool documentation.

### 4. Flexibility

Some tools have complex configuration that doesn't fit well in pyproject.toml's `[tool.*]` namespace. Dedicated files allow:

- Tool-native configuration syntax
- Better editor support (syntax highlighting, validation)
- Easier copying between projects

### 5. Future-Proofing

As we add more tools (mypy, black, isort alternatives), each gets its own configuration file without bloating pyproject.toml.

## Alternatives Considered

### Alternative 1: Everything in pyproject.toml

**Pros**:

- Single file for all configuration
- PEP 518 supports `[tool.*]` namespace
- Reduces file count

**Cons**:

- Violates separation of concerns
- pyproject.toml becomes unwieldy (100+ lines for large projects)
- Harder to copy tool config between projects
- Risk of configuration drift when tools are configured in multiple places

**Decision**: Rejected - DRY violation discovered in practice, separation is cleaner

### Alternative 2: Split by category (tooling.toml)

**Pros**:

- Groups all dev tools together
- Still separates from project metadata

**Cons**:

- Non-standard (tools expect their own config files)
- Harder to discover ("where's the linter config?")
- Would need tool-specific flags to point to custom location

**Decision**: Rejected - Goes against tool conventions

### Alternative 3: Keep both, but synchronize

**Pros**:

- Maintains backward compatibility
- Allows flexibility

**Cons**:

- Requires manual synchronization (error-prone)
- Doesn't solve root problem
- Maintenance burden

**Decision**: Rejected - Doesn't address DRY violation

## Consequences

### Positive

- ✅ Single source of truth for each tool (DRY)
- ✅ Clear separation: pyproject.toml = project, tool configs = tooling
- ✅ Easier to update tool settings (one place)
- ✅ Matches ecosystem conventions (Go, Node, Rust patterns)
- ✅ Prevents configuration drift
- ✅ Better editor support for tool configs

### Negative

- ℹ️ Slightly more files in repository root (but organized)
- ℹ️ Developers need to know which file to edit (but naming is intuitive)

### Neutral

- 📚 pyproject.toml only contains: project metadata, build system, pytest (until pytest.ini needed)
- 📚 ruff.toml contains: all Ruff configuration (lint, format, exclude)
- 📚 Pattern applies to future tools (mypy.ini, .coveragerc, etc.)

## Implementation

### Files Modified

**Removed from pyproject.toml**:

```toml
# REMOVED - was lines 50-60
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM"]

[tool.ruff.lint.per-file-ignores]
"src/pyfulmen/logging/config.py" = ["N815"]
"tests/**/*.py" = ["B017", "F841"]
```

**ruff.toml** (single source of truth):

```toml
# Ruff configuration for pyfulmen
# See: https://docs.astral.sh/ruff/

line-length = 100
target-version = "py312"

exclude = [
    "tests/fixtures/",  # Test data, not code
]

[lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]

[lint.per-file-ignores]
"src/pyfulmen/logging/config.py" = ["N815"]
"tests/**/*.py" = ["S101", "B017", "F841"]

[format]
quote-style = "double"
indent-style = "space"
```

### Validation

```bash
# Verify Ruff uses ruff.toml
uv run ruff check .  # Should use ruff.toml settings

# Verify pyproject.toml has no [tool.ruff]
grep -A 5 "\[tool.ruff\]" pyproject.toml  # Should return nothing

# Verify all tests pass
make test  # 520 tests passing
```

**Result**: All quality checks passing with consolidated configuration.

## Tool Configuration Policy

### When to Use pyproject.toml

Only for project definition:

- ✅ `[project]` - Package metadata (name, version, dependencies)
- ✅ `[build-system]` - Build backend (hatchling, setuptools)
- ✅ `[tool.hatch.*]` - Build tool configuration
- ✅ `[tool.pytest.ini_options]` - Simple pytest settings (if no pytest.ini)

### When to Use Dedicated Tool Config

Use dedicated config files for:

- ✅ **Ruff**: ruff.toml (this ADR)
- ✅ **MyPy**: mypy.ini or .mypy.ini
- ✅ **Coverage**: .coveragerc or pyproject.toml `[tool.coverage.*]` (acceptable)
- ✅ **Pre-commit**: .pre-commit-config.yaml (goneat in our case)

### Migration Path for Existing Tools

If we discover similar duplication in the future:

1. Check for configuration in both pyproject.toml and dedicated file
2. Consolidate to dedicated file (prefer tool-native format)
3. Remove from pyproject.toml
4. Update this ADR with new tool
5. Document in CONTRIBUTING.md or DEVELOPMENT.md

## References

- [PEP 518 - pyproject.toml Specification](https://peps.python.org/pep-0518/) - Defines project metadata
- [Ruff Configuration Documentation](https://docs.astral.sh/ruff/configuration/) - Recommends ruff.toml
- [Python Packaging Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) - Best practices
- DRY Principle: "Every piece of knowledge must have a single, unambiguous, authoritative representation"

## Future Considerations

### When to Reconsider

This decision should be revisited if:

1. **Tool standardization changes**: If Python ecosystem moves to "everything in pyproject.toml"
2. **Tooling improves**: If tools gain better multi-file config merging
3. **Complexity grows**: If number of config files becomes overwhelming (10+)

### Tools to Watch

- **mypy**: Currently uses mypy.ini, may migrate to pyproject.toml
- **pytest**: Currently allows both, evaluate if pytest.ini needed
- **coverage**: Currently allows both, ruff.toml pattern preferred

### Automation Opportunities

Consider automating config validation:

- Pre-commit hook: Check for `[tool.ruff]` in pyproject.toml (should fail)
- CI check: Verify single source of truth
- Goneat integration: Validate tool config separation

## Notes

This ADR was created retroactively during v0.1.2 MIME detection implementation when we discovered the DRY violation. The consolidation to ruff.toml was necessary to add fixture exclusion and revealed the broader configuration duplication issue.

**Key Insight**: The need for this ADR emerged from practical development work, not theoretical planning. This demonstrates the value of ADRs for capturing lessons learned during implementation.

---

_Last Updated: 2025-10-15_
