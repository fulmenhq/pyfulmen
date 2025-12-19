---
title: "ADR-0011: App Identity Embedding Pattern for Python Packages"
description: "Architectural decision for how Python packages embed app identity for distributed artifacts without requiring repo-level file mirrors"
author: "PyFulmen Architect (@pyfulmen-architect)"
author_of_record: "Dave Thompson (https://github.com/3leapsdave)"
supervised_by: "@3leapsdave"
date: "2025-12-18"
last_updated: "2025-12-18"
status: "approved"
version: "v0.1.15"
tags: ["adr", "app-identity", "packaging", "embedding", "python", "wheels"]
---

# ADR-0011: App Identity Embedding Pattern for Python Packages

**Status**: Accepted
**Date**: 2025-12-18
**Authors**: PyFulmen Architect (@pyfulmen-architect)
**Deciders**: @3leapsdave
**Version**: v0.1.15
**Related ADRs**: None (ecosystem-level; see Crucible app-identity standard)

## Context

PyFulmen v0.1.15 introduces embedded identity fallback to ensure distributed Python packages (wheels, installed CLIs) can determine their identity without requiring `.fulmen/app.yaml` on disk at runtime.

### Problem

The standard `.fulmen/app.yaml` lives at the repository root, but Python wheels only include files from within the package directory tree (e.g., `src/pyfulmen/`). We need a pattern to make identity available in distributed packages.

### Cross-Language Context

**Go's constraint**: Go's `//go:embed` directive requires embedded files to be within the module tree. Since `.fulmen/` is a dot-directory at repo root, Go templates must maintain a synced mirror at `internal/assets/appidentity/app.yaml` and embed from there. This creates a permanent dual-copy in the repository.

**Python's opportunity**: Python build tools offer more flexibility. We can potentially avoid permanent dual-copies through build-time file mapping.

### Requirements

1. **Wheel must contain identity**: Built wheel includes identity for standalone execution
2. **SSOT remains `.fulmen/app.yaml`**: Developers edit only one file
3. **Drift prevention**: Mechanism to detect/prevent embedded vs source divergence
4. **Minimal repo clutter**: Avoid unnecessary committed files if possible
5. **Build reproducibility**: Same source produces same wheel
6. **Cross-language alignment**: Pattern should be documentable alongside Go/TS patterns

## Decision

**We choose: Build-Time Inclusion via pyproject.toml (No Repo-Level Mirror Required)**

Python packages SHOULD use build tool configuration to include `.fulmen/app.yaml` in the wheel at build time, mapping it to a package-internal location. No permanent mirror file needs to exist in the repository.

### Recommended Pattern (Hatch)

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mypackage"]

[tool.hatch.build.targets.wheel.force-include]
".fulmen/app.yaml" = "mypackage/_assets/app.yaml"
```

### Alternative Pattern (Setuptools)

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.package-data]
mypackage = ["_assets/app.yaml"]

# Requires: MANIFEST.in or custom build step to copy file
```

Note: Setuptools requires additional configuration (MANIFEST.in or custom script) to copy root-level files. Hatch's `force-include` is more elegant for this use case.

### Registration Pattern

```python
# src/mypackage/__init__.py
from importlib.resources import files
from pyfulmen.appidentity import register_embedded_identity_yaml

# Register embedded identity at package import
try:
    _identity_data = files("mypackage").joinpath("_assets/app.yaml").read_bytes()
    register_embedded_identity_yaml(_identity_data)
except Exception:
    pass  # Graceful degradation - filesystem discovery still works
```

### Directory Structure

```
myproject/
├── .fulmen/
│   └── app.yaml              # SSOT - developers edit THIS file
├── src/
│   └── mypackage/
│       ├── __init__.py       # Registers embedded identity
│       └── _assets/          # Created at build time only (NOT committed)
│           └── app.yaml      # Populated by hatch force-include
├── pyproject.toml            # Contains force-include directive
└── Makefile                  # Contains verify-embedded-identity target
```

**Key distinction from Go**: The `_assets/` directory does NOT need to exist in the repository. It's created during wheel build.

## Rationale

### 1. Single Source of Truth Preserved

Developers only edit `.fulmen/app.yaml`. No manual sync step, no risk of editing the wrong file.

```bash
# Developer workflow - edit SSOT only
vim .fulmen/app.yaml
make build  # force-include handles the rest
```

### 2. No Repo Clutter

Unlike Go's required `internal/assets/appidentity/app.yaml` mirror, Python repos don't need a committed copy. The `.gitignore` can exclude `src/*/\_assets/` entirely.

### 3. Build Tool Handles Mapping

Hatch's `force-include` (or equivalent) declaratively maps source to destination:

```toml
# Clear, auditable, version-controlled
[tool.hatch.build.targets.wheel.force-include]
".fulmen/app.yaml" = "mypackage/_assets/app.yaml"
```

### 4. Drift Prevention Still Possible

Even without a committed mirror, CI can verify the built wheel contains correct identity:

```makefile
.PHONY: verify-embedded-identity
verify-embedded-identity:  ## Verify wheel contains correct identity
	@uv build --wheel
	@unzip -p dist/*.whl "*/\_assets/app.yaml" | diff -q - .fulmen/app.yaml || \
		(echo "ERROR: Wheel identity differs from .fulmen/app.yaml" && exit 1)
	@echo "Embedded identity verified"
```

### 5. Cross-Language Documentation

The pattern is clearly distinct from Go, which is appropriate:

| Language   | Embedding Mechanism | Repo Mirror Required     | SSOT Location      |
| ---------- | ------------------- | ------------------------ | ------------------ |
| Go         | `//go:embed`        | Yes (`internal/assets/`) | `.fulmen/app.yaml` |
| Python     | `force-include`     | No                       | `.fulmen/app.yaml` |
| TypeScript | Package.json files  | TBD                      | `.fulmen/app.yaml` |

## Alternatives Considered

### Alternative 1: Committed Mirror (Go Pattern)

Maintain `src/mypackage/_assets/app.yaml` as a committed copy, synced via Make target.

```makefile
sync-embedded-identity:
	mkdir -p src/mypackage/_assets
	cp .fulmen/app.yaml src/mypackage/_assets/app.yaml
```

**Pros**:

- ✅ Cross-language consistency with Go
- ✅ Explicit file visible in repo
- ✅ Works with all build tools

**Cons**:

- ❌ Two copies in repo (drift risk)
- ❌ Requires manual sync step or pre-commit hook
- ❌ Additional committed files
- ❌ Developers might edit wrong file

**Decision**: Rejected for Python. Build-time inclusion is cleaner and Python tooling supports it.

### Alternative 2: Symlink

Create `src/mypackage/_assets/app.yaml` as symlink to `../../.fulmen/app.yaml`.

```bash
ln -s ../../.fulmen/app.yaml src/mypackage/_assets/app.yaml
```

**Pros**:

- ✅ Single file, no drift possible
- ✅ Changes instantly reflected

**Cons**:

- ❌ Symlinks in wheels are problematic (platform-dependent behavior)
- ❌ Windows compatibility issues
- ❌ Some build tools don't follow symlinks correctly
- ❌ `importlib.resources` behavior with symlinks is undefined

**Decision**: Rejected. Symlinks are unreliable for package distribution.

### Alternative 3: Runtime File Copy

Copy `.fulmen/app.yaml` to package location at runtime (first import).

```python
# __init__.py
import shutil
from pathlib import Path

_assets_dir = Path(__file__).parent / "_assets"
_ssot = Path(__file__).parents[2] / ".fulmen" / "app.yaml"
if _ssot.exists() and not (_assets_dir / "app.yaml").exists():
    _assets_dir.mkdir(exist_ok=True)
    shutil.copy(_ssot, _assets_dir / "app.yaml")
```

**Pros**:

- ✅ Automatic sync at import

**Cons**:

- ❌ Writes to package directory (may be read-only in installed packages)
- ❌ Race conditions on first import
- ❌ Unexpected filesystem writes
- ❌ Doesn't work for installed wheels (no `.fulmen/` nearby)

**Decision**: Rejected. Runtime file writes are inappropriate.

### Alternative 4: Environment Variable at Build Time

Inject identity path via environment variable during build.

**Pros**:

- ✅ Flexible

**Cons**:

- ❌ Not declarative (build depends on environment)
- ❌ Hard to reproduce builds
- ❌ Easy to forget

**Decision**: Rejected. Declarative `pyproject.toml` configuration is superior.

## Consequences

### Positive

- ✅ **Single SSOT**: Only `.fulmen/app.yaml` exists and is edited
- ✅ **Clean Repository**: No synced mirror files cluttering the repo
- ✅ **Zero Manual Sync**: Build tool handles file mapping automatically
- ✅ **Declarative**: Configuration in `pyproject.toml` is auditable
- ✅ **Reproducible**: Same source produces same wheel
- ✅ **Python-Native**: Leverages Python build tool capabilities

### Negative

- ⚠️ **Build Tool Dependency**: Requires Hatch or equivalent with `force-include`
  - **Mitigation**: Hatch is modern, well-supported, recommended by PyPA
  - **Fallback**: Setuptools users can use MANIFEST.in + custom build step
- ⚠️ **Verification Requires Build**: Can't diff committed files directly
  - **Mitigation**: CI target builds wheel and verifies contents
- ⚠️ **Cross-Language Divergence**: Pattern differs from Go's committed mirror
  - **Mitigation**: Document differences clearly; both achieve same goal

### Neutral

- 📝 **Documentation Needed**: Downstream consumers need guidance on this pattern
- 📝 **pyfulmen Itself**: pyfulmen library doesn't need embedded identity (it's a library, not a CLI), but documents the pattern for consumers

## Implementation

### For Downstream Consumers (e.g., percheron)

1. **Add force-include to pyproject.toml**:

```toml
[tool.hatch.build.targets.wheel.force-include]
".fulmen/app.yaml" = "percheron/_assets/app.yaml"
```

2. **Register in `__init__.py`**:

```python
from importlib.resources import files
from pyfulmen.appidentity import register_embedded_identity_yaml

try:
    _data = files("percheron").joinpath("_assets/app.yaml").read_bytes()
    register_embedded_identity_yaml(_data)
except Exception:
    pass
```

3. **Add CI verification**:

```makefile
.PHONY: verify-embedded-identity
verify-embedded-identity:
	@uv build --wheel
	@python -c "import zipfile; z=zipfile.ZipFile('dist/$(shell ls dist/*.whl)'); \
		embedded=z.read('percheron/_assets/app.yaml'); \
		ssot=open('.fulmen/app.yaml','rb').read(); \
		assert embedded==ssot, 'Identity drift detected'"
	@echo "Embedded identity verified"
```

4. **Update .gitignore**:

```gitignore
# Embedded assets (generated at build time)
src/*/_assets/
```

### Make Targets (Recommended)

```makefile
# Crucible CDRL compliance targets

.PHONY: sync-embedded-identity
sync-embedded-identity:  ## No-op for Python (build-time inclusion)
	@echo "Python uses build-time inclusion - no sync needed"
	@echo "Identity will be included via pyproject.toml force-include"

.PHONY: verify-embedded-identity
verify-embedded-identity:  ## Verify wheel contains correct identity
	@echo "Building wheel and verifying embedded identity..."
	@uv build --wheel --quiet
	@python scripts/verify_embedded_identity.py
	@echo "Embedded identity verified"
```

## When to Use Committed Mirror Instead

Some scenarios may warrant the Go-style committed mirror pattern:

1. **Setuptools without MANIFEST.in expertise**: If force-include isn't available
2. **Pre-build inspection required**: If you need to see the embedded file without building
3. **Non-Hatch build system**: Some build systems don't support force-include
4. **Organizational preference**: If cross-language consistency is paramount

In these cases, use:

```makefile
.PHONY: sync-embedded-identity
sync-embedded-identity:
	@mkdir -p src/mypackage/_assets
	@cp .fulmen/app.yaml src/mypackage/_assets/app.yaml
	@echo "Embedded identity synced"

.PHONY: verify-embedded-identity
verify-embedded-identity:
	@diff -q .fulmen/app.yaml src/mypackage/_assets/app.yaml || \
		(echo "ERROR: Run 'make sync-embedded-identity'" && exit 1)
	@echo "Embedded identity verified"
```

And remove `src/*/_assets/` from `.gitignore`.

## References

- **Feature Brief**: `.plans/active/v0.1.15/appidentity-embedded-fallback-feature-brief.md`
- **Crucible Standard**: `docs/crucible-py/standards/library/modules/app-identity.md`
- **Linked Memo**: `gofulmen/.plans/memos/fulmenhq/appidentity-embedding-fix-requirements.md`
- **Hatch force-include docs**: https://hatch.pypa.io/latest/config/build/#forced-inclusion
- **importlib.resources**: https://docs.python.org/3/library/importlib.resources.html

## Future Considerations

### When to Reconsider

1. **If Python packaging changes**: PEP changes to wheel format or package data
2. **If Hatch deprecates force-include**: Would need alternative build tool
3. **If cross-language CI requires committed files**: May need to adopt Go pattern

### Potential Enhancements

1. **pyfulmen CLI helper**: `pyfulmen appidentity verify-wheel dist/*.whl`
2. **Pre-commit hook**: Validate pyproject.toml has force-include configured
3. **Template generator**: Scaffold embedding configuration for new projects

## Revision History

| Date       | Version | Description      | Author             |
| ---------- | ------- | ---------------- | ------------------ |
| 2025-12-18 | 1.0     | Initial proposal | PyFulmen Architect |

---

**Decision**: Accepted
**Cross-Language Note**: This pattern intentionally differs from Go due to Python tooling capabilities
