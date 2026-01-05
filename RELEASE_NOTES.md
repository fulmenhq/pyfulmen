# Release Notes

This document tracks release notes for recent PyFulmen releases.

**Retention Policy**: This file maintains notes for the last 3 releases only. For complete release history, see [CHANGELOG.md](./CHANGELOG.md).

---

## [0.2.0] - Crucible v0.3.2 Integration & CI/CD Modernization - 2026-01-05

**Release Type**: Minor - Role-Based Model & Dependency Protection
**Status**: Ready for Release

**Summary**: PyFulmen v0.2.0 aligns with Crucible v0.3.2's role-based agentic model, modernizes the bootstrap and CI/CD infrastructure to match gofulmen/rsfulmen patterns, and adds dependency protection (license compliance and supply chain security).

### Highlights

**Role-Based Agentic Model**:

- Migrated from identity scheme to Crucible v0.3.2 role catalog
- AGENTS.md and MAINTAINERS.md updated with role-based model
- Commit attribution now includes `Role:` trailer (devlead, devrev, infoarch, secrev)

**License Audit & Dependency Protection**:

- `make license-audit` checks for forbidden licenses (GPL, LGPL, AGPL, MPL, CDDL)
- `.goneat/dependencies.yaml` with cooling policy for supply chain security
- Integrated into `make check-all` dependency chain

**Bootstrap Modernization**:

- New `scripts/make-bootstrap.sh` for sfetch -> goneat trust pyramid
- BINDIR defaults to `$HOME/.local/bin` (aligned with gofulmen/rsfulmen)
- Uses `goneat doctor tools --scope foundation`
- Updated to goneat v0.4.1

**Crucible Sync (v0.2.26 -> v0.3.2)**:

- New agentic role configs (devlead, devrev, entarch, cicd, dataeng, infoarch, secrev)
- Agentic-interface-adoption guide
- Updated ai-agents and agentic-attribution standards

### Breaking Changes

- None (fully backward compatible)

---

## [0.1.15] - Embedded Identity Fallback - 2025-12-19

**Release Type**: Feature Enhancement - Distributed Package Support
**Status**: ✅ Ready for Release

**Summary**: PyFulmen v0.1.15 implements embedded identity fallback, enabling Python wheels and installed CLIs to determine their identity without requiring `.fulmen/app.yaml` on the filesystem. This addresses a critical gap for distributed artifacts.

### Highlights

**App Identity Embedded Fallback**:

- `register_embedded_identity_yaml(data: bytes)` - Register identity at package import time
- First-wins semantics prevents hidden overrides in complex import chains
- Validation on registration (fail-fast)
- Updated discovery precedence: explicit → env → filesystem → **embedded** → error

**ADR-0011: Python Embedding Pattern**:

- Documents build-time inclusion via `pyproject.toml` `force-include`
- No repo mirror required (unlike Go's `//go:embed` constraint)
- Downstream guidance for percheron and other packages

**Infrastructure Fixes**:

- Pre-commit hooks now use `goneat assess` (~1s) instead of `make precommit` (timeout)
- Bootstrap updated to sfetch trust pyramid pattern

**Crucible Sync (v0.2.20 → v0.2.26)**:

- Updated `app-identity.md` standard with embedded identity fallback requirements
- New `enact` module standards and schemas
- Updated repository category standards
- New publishing standards

### Usage Example

```python
# In downstream package's __init__.py
from importlib.resources import files
from pyfulmen.appidentity import register_embedded_identity_yaml

try:
    _data = files("mypackage").joinpath("_assets/app.yaml").read_bytes()
    register_embedded_identity_yaml(_data)
except Exception:
    pass  # Graceful degradation
```

### Quality Gates

- [x] **Tests**: 107 appidentity tests passing (91 existing + 16 new)
- [x] **Thread Safety**: Validated with concurrent registration tests
- [x] **Documentation**: ADR-0011, feature brief, continuation prompt
- [x] **Hooks**: Pre-commit validation in ~1s

### Breaking Changes

- None (fully backward compatible)

---

## [0.1.14] - Packaging Fix for Crucible Assets - 2025-11-29

**Release Type**: Critical Packaging Fix
**Status**: ✅ Released

**Summary**: Resolves a `ModuleNotFoundError` by including the `src/crucible` package in the wheel distribution. This ensures that synced assets (schemas, configs, exit codes) are available to downstream consumers.

### Highlights

- Fixed exclusion of `src/crucible` in `tool.hatch.build.targets.wheel.packages`
- Added regression test `tests/integration/crucible/test_consumer_usage.py`

### Breaking Changes

- None

---

_For releases prior to v0.1.14, see [CHANGELOG.md](./CHANGELOG.md)._
