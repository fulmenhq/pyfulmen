# PyFulmen Bootstrap Journal

> **⚠️ HISTORICAL DOCUMENT**: This journal describes the original bootstrap process using FulDX.
> **FulDX has been succeeded by goneat**. For current setup instructions, see [setup-guide.md](./setup-guide.md).

This document chronicles how the pyfulmen repository was bootstrapped from scratch using FulDX and the Fulmen ecosystem tools.

**Date:** 2025-10-08  
**Status:** Historical reference only  
**Current Bootstrap Guide:** [setup-guide.md](./setup-guide.md)  
**Original Bootstrap Guide:** [Fulmen Library Bootstrap Guide](../crucible-py/guides/fulmen-library-bootstrap-guide.md)

## Overview

PyFulmen is the third in a series of Fulmen helper libraries, following the Go and TypeScript implementations. This bootstrap process adapts the standard Fulmen bootstrap pattern for Python with `uv` as the package manager.

## Prerequisites Met

- ✅ Python 3.13.7 (CPython)
- ✅ uv 0.8.22 installed
- ✅ make available
- ✅ Access to sibling repositories: ../crucible, ../gofulmen, ../fuldx

## Bootstrap Steps Completed

### 1. FulDX Binary Setup

```bash
mkdir -p bin
cp ../fuldx/dist/fuldx bin/fuldx
chmod +x bin/fuldx
bin/fuldx --version  # 0.1.4
```

**Note:** Since FulDX isn't public yet, we copied the binary from the local build.

### 2. Version Management

```bash
echo "0.1.0" > VERSION
```

Following SemVer for initial development (0.x.y).

### 3. FulDX Configuration

Created `.fuldx/sync-consumer.yaml`:

```yaml
version: 1.0
sources:
  - name: crucible
    repo: fulmenhq/crucible
    ref: main
    output: .
    sync_path_base: "lang/go" # Temporary: lang/python not yet available
    assets:
      - type: doc
        paths:
          - "docs/architecture/**/*.md"
          - "docs/standards/**/*.md"
          - "docs/guides/**/*.md"
          - "docs/sop/**/*.md"
        subdir: docs/crucible-py
      - type: schema
        paths: ["schemas/**/*"]
        subdir: schemas/crucible-py
      - type: config
        paths: ["config/**/*.yaml"]
        subdir: config/crucible-py
      - type: metadata
        paths:
          - "config/sync/**/*"
          - "schemas/config/sync-consumer-config.yaml"
        subdir: .crucible/metadata
```

**Important:** ~~Currently using `sync_path_base: 'lang/go'` because `lang/python` doesn't exist yet in Crucible.~~ Updated to `sync_path_base: 'lang/python'` as of 2025-10-08.

Created `.fuldx/sync-consumer.local.yaml` for local development:

```yaml
version: 1.0
sources:
  - name: crucible
    localPath: ../crucible
```

**Critical:** This file is **machine-specific and gitignored** (`.gitignore` includes `.fuldx/*.local.yaml`). It should **never be committed** to the repository. Each developer can create their own local override pointing to their Crucible clone location. The `.fuldx/sync-consumer.yaml` contains the canonical GitHub repo configuration that works for everyone, while `.fuldx/sync-consumer.local.yaml` overrides it for faster local development.

This pattern enables:

- Fast syncing from the sibling Crucible repository (filesystem copy vs GitHub API)
- Machine-specific paths without polluting the repository
- Team members can use different Crucible locations

### 4. Python Project Files

**pyproject.toml:**

```toml
[project]
name = "pyfulmen"
version = "0.1.0"
description = "Python Fulmen libraries"
authors = [{name = "3 Leaps Team", email = "dev@3leaps.net"}]
requires-python = ">=3.11"
license = {text = "MIT"}
readme = "README.md"

dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

**Package Structure:**

```
src/pyfulmen/__init__.py   # Main package with __version__
tests/conftest.py           # Pytest configuration
tests/test_basic.py         # Initial smoke test
```

### 5. Makefile with uv Integration

Created `Makefile` based on the Fulmen template, **adapted for uv**:

Key changes from standard pip-based approach:

- `make bootstrap`: Uses `uv sync --all-extras` instead of `pip install -e .[dev]`
- `make lint`: Uses `uv run ruff check` to run in virtual environment
- `make test`: Uses `uv run pytest` to run in virtual environment

This leverages uv's speed and automatic virtual environment management.

### 6. Gitignore Configuration

Updated `.gitignore` with:

- FulDX binary exclusions (`/bin/fuldx`)
- Crucible sync asset exclusions (regenerated from source)
- FulDX local overrides (`.fuldx/*.local.yaml`)
- Python-specific artifacts
- uv virtual environment (`.venv/`)

### 7. Crucible Sync

```bash
make sync-crucible
```

**Result:** Successfully synced 185 assets from local Crucible repository:

- Standards documentation → `docs/crucible-py/`
- Schemas → `schemas/crucible-py/`
- Config files → `config/crucible-py/`
- Metadata → `.crucible/metadata/`

### 8. uv Bootstrap

```bash
uv sync --all-extras
```

**Result:**

- Created virtual environment at `.venv/`
- Installed dependencies: pytest, pytest-cov, ruff
- Built and installed pyfulmen package in editable mode
- Using CPython 3.13.7

**Note:** Initial attempt failed due to missing README.md (referenced in pyproject.toml). Created basic README.md and sync succeeded.

### 9. Verification

```bash
make test
```

**Result:** ✅ 1 test passed - basic version check confirms package setup

## Key Deviations from Standard Bootstrap

1. **Package Manager:** Using `uv` instead of `pip`
   - Faster dependency resolution
   - Automatic virtual environment management
   - Better lock file support

2. **Crucible Language Path:** Using `lang/go` temporarily
   - `lang/python` not yet available in Crucible
   - TODO: Update to `lang/python` once available

3. **Python Version:** Using Python 3.13.7
   - Newer than bootstrap guide example (3.11)
   - Fully compatible with pyproject.toml requirement (>=3.11)

## Current State

✅ Repository fully bootstrapped and ready for development
✅ FulDX integration working (version management, SSOT sync)
✅ Crucible standards and schemas synced
✅ uv package management configured
✅ Basic tests passing

## Next Steps

1. ~~Wait for `lang/python` in Crucible, then update sync config~~ ✅ Complete (2025-10-08)
2. Draft Python-specific environment standards for Crucible
3. Add Python-specific Fulmen library functionality
4. Implement proper project structure following Crucible standards
5. Add comprehensive test suite
6. Consider adding Goneat for release automation (when ready)

## Commands Reference

```bash
# Bootstrap environment
make bootstrap

# Sync Crucible assets
make sync-crucible

# Run tests
make test

# Run linter
make lint

# Version bumping
make version-bump-patch    # 0.1.0 → 0.1.1
make version-bump-minor    # 0.1.0 → 0.2.0
make version-bump-major    # 0.1.0 → 1.0.0
make version-bump-calver   # → YYYY.MM.PATCH

# Clean build artifacts
make clean

# FulDX commands
bin/fuldx --version
bin/fuldx info
bin/fuldx docs --list
bin/fuldx ssot keys crucible
```

## Notes for Future Bootstrappers

- Always use `uv` for Python projects in the Fulmen ecosystem
- Keep `.fuldx/sync-consumer.local.yaml` for local Crucible development
- Run `make sync-crucible` weekly or before major changes
- The bootstrap guide is available offline: `bin/fuldx docs --file docs/crucible-py/guides/fulmen-library-bootstrap-guide.md`
- Check sibling repositories (gofulmen, tsfulmen) for implementation patterns

## Attribution

This bootstrap was performed with assistance from Claude Code, following the Fulmen Library Bootstrap Guide and adapting it for Python with uv.

---

## Phase 2: Implementing Fulmen Helper Library (2025-10-08)

### Goal

Transform from bootstrapped skeleton into a proper Fulmen helper library following the **Fulmen Helper Library Standard**.

### Documentation Review

**Read**:

- ✅ `docs/crucible-py/architecture/fulmen-helper-library-standard.md`
- ✅ `docs/crucible-py/guides/bootstrap-fuldx.md`
- ✅ Reference implementation: `../gofulmen/`

**Key Findings**:

#### 1. FulDX Bootstrap Pattern (Critical Gap)

**Current State**: We manually copied `bin/fuldx` from `../fuldx/dist/fuldx`

**Should Be**:

- `.crucible/tools.yaml` with FulDX download URLs + checksums
- `.crucible/tools.local.yaml.example` as template
- Bootstrap script that:
  - Prefers `.crucible/tools.local.yaml` if present (local dev)
  - Falls back to `tools.yaml` (CI/CD)
  - Installs to `./bin/fuldx`

**Reference**:

- `../gofulmen/.crucible/tools.yaml` - Shows manifest structure
- `../gofulmen/.crucible/tools.local.yaml` - Local override with `type: link`
- Schema: `schemas/crucible-py/tooling/external-tools/v1.0.0/`

**Discovery**: gofulmen uses Go for bootstrap (`go run ./cmd/bootstrap`), we need Python equivalent

#### 2. Mandatory Capabilities Checklist

From helper library standard, we need:

1. **FulDX Bootstrap Pattern** ❌
   - Tools manifest
   - Bootstrap script
   - Local override support

2. **SSOT Synchronization** ✅ (Mostly Done)
   - `.fuldx/sync-consumer.yaml` ✅
   - `.fuldx/sync-consumer.local.yaml` ✅
   - Synced assets committed ✅
   - `make sync` target ✅

3. **Crucible Shim** ❌ (Not Started)
   - Access to synced docs, schemas, configs
   - Version exposure
   - Discovery APIs

4. **Config Path API** ❌ (Not Started)
   - XDG-compliant path resolution
   - Platform-aware (Linux/macOS/Windows)
   - Fulmen-specific helpers

5. **Three-Layer Config Loading** ❌ (Not Started)
   - Crucible defaults → User overrides → BYOC

6. **Schema Validation Utilities** ❌ (Not Started)
   - jsonschema integration
   - Helpers for Crucible schemas

7. **Observability Integration** ❌ (Not Started)
   - Logging based on Crucible patterns
   - Severity mapping

#### 3. Documentation Gaps Identified

**bootstrap-fuldx.md** is helpful but could be enhanced:

**✅ What's Clear**:

- Local override pattern with `tools.local.yaml`
- `type: link` for local binaries
- Gitignore requirements

**⚠️ Could Be Clearer**:

1. **Missing**: Complete tools.yaml example with FulDX
   - Currently only shows tools.local.yaml
   - Need production example with checksums
   - **Suggestion**: Add example for FulDX v0.1.4 with actual checksums

2. **Missing**: Python-specific bootstrap script guidance
   - gofulmen uses `go run ./cmd/bootstrap`
   - tsfulmen would use Bun/Node
   - Python needs guidance on:
     - PyYAML for manifest parsing
     - Platform detection (os.name, platform.system())
     - Download + checksum verification
     - File permissions (chmod +x)

3. **Missing**: Schema reference for manifest
   - Mentions schema location but doesn't explain structure
   - **Suggestion**: Add inline example showing all install types:
     - `type: verify` (existing command)
     - `type: download` (URL with checksums)
     - `type: link` (local copy)
     - `type: go` (go install)

4. **Missing**: Error handling guidance
   - What if checksum fails?
   - What if download fails?
   - Retry logic?

5. **Missing**: Progress indication
   - Should bootstrap show progress?
   - Quiet mode for CI?

**Specific Requests for Crucible**:

1. **Add to bootstrap-fuldx.md**:

   ```markdown
   ## Example: FulDX in tools.yaml

   \`\`\`yaml
   version: v1.0.0
   binDir: ./bin
   tools:

   - id: fuldx
     description: Fulmen Developer Experience CLI
     required: true
     install:
     type: download
     url: https://github.com/fulmenhq/fuldx/releases/download/v0.1.4/fuldx-{{os}}-{{arch}}
     binName: fuldx
     destination: ./bin
     checksum:
     darwin-arm64: <actual-sha256>
     darwin-amd64: <actual-sha256>
     linux-amd64: <actual-sha256>
     linux-arm64: <actual-sha256>
     \`\`\`
   ```

2. **Add Python bootstrap script template** to guides:

   ```markdown
   ## Python Bootstrap Script Example

   \`\`\`python
   #!/usr/bin/env python3
   """Bootstrap script for installing tools from .crucible/tools.yaml"""

   import hashlib
   import os
   import platform
   import shutil
   import sys
   import urllib.request
   from pathlib import Path

   import yaml

   # ... implementation ...

   \`\`\`
   ```

3. **Add to helper library standard**: Language-specific bootstrap patterns section
   - Go: `go run ./cmd/bootstrap`
   - TypeScript: `bun run scripts/bootstrap.ts`
   - Python: `python scripts/bootstrap.py`
   - Each language shows minimal example

#### 4. Implementation Plan Created

Created comprehensive plan: `.plans/active/v0.1.0/bootstrap.md`

**10 Phases**:

1. FulDX Bootstrap Pattern ← **STARTING HERE**
2. Version Management
3. Crucible Shim
4. Config Path API
5. Three-Layer Config Loading
6. Schema Validation
7. Observability/Logging
8. Documentation & Examples
9. Testing & Quality
10. v0.1.0 Release

**First Commit**: Phases 1 + 2 (Bootstrap + Version)

#### 5. Questions for FulDX Team

1. **FulDX Published Binaries**:
   - Are v0.1.4 binaries published to GitHub releases?
   - What are the actual SHA256 checksums for each platform?
   - If not published yet, should we continue using `type: link` in production?

2. **Bootstrap Script Requirements**:
   - Should we vendor PyYAML or require it pre-installed?
   - Error handling: Fail fast or continue with warnings?
   - Should bootstrap be idempotent (skip if tool exists)?

3. **Platform Support**:
   - Primary: darwin-arm64, darwin-amd64, linux-amd64
   - Secondary: linux-arm64, windows-amd64?
   - Should we error on unsupported platforms?

4. **Schema Validation**:
   - Should bootstrap script validate tools.yaml against schema?
   - Or trust that humans/CI got it right?

### Next Steps

1. **Wait for feedback** on documentation gaps
2. **Get FulDX checksums** (or confirm we should use `type: link` for now)
3. **Implement Phase 1**:
   - Create `.crucible/tools.yaml`
   - Create `.crucible/tools.local.yaml.example`
   - Create `scripts/bootstrap.py`
   - Update `Makefile`
   - Update `.gitignore`
4. **Test bootstrap** on macOS (current), Linux (VM/CI)
5. **Make first commit** with working bootstrap

### Documentation Dogfooding Success

✅ **What Worked**:

- Helper library standard is comprehensive and clear
- bootstrap-fuldx.md gives good overview
- gofulmen provides excellent reference implementation
- Schema location is documented

⚠️ **What Could Be Better**:

- More Python-specific examples
- Complete tools.yaml example with FulDX
- Bootstrap script template/skeleton
- Error handling guidance
- Language-specific patterns in helper library standard

**Overall Assessment**: Documentation is 85% there, just needs language-specific details filled in. Excellent foundation!

---

**Last Updated:** 2025-10-08
**Status:** Phase 2 Planning Complete - Awaiting Guidance on FulDX Binaries
