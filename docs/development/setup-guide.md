---
title: "PyFulmen Development Setup Guide"
description: "Quick start guide for pyfulmen library developers"
author: "PyFulmen Architect"
date: "2025-10-13"
status: "active"
---

# PyFulmen Development Setup Guide

Quick start guide for setting up a pyfulmen development environment.

## TL;DR

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and bootstrap
git clone https://github.com/fulmenhq/pyfulmen.git
cd pyfulmen
make bootstrap

# Verify
make test  # Should see 136 tests passing
```

## Prerequisites

- **Python 3.12+** - Required for stdlib features
- **uv** - Fast Python package manager ([install](https://github.com/astral-sh/uv#installation))

## Bootstrap Process

`make bootstrap` performs these steps automatically:

1. **Creates `.venv/`** - Virtual environment (via `uv sync`)
2. **Installs Dependencies** - All packages from `pyproject.toml`
3. **Installs Tools** - goneat CLI for SSOT sync
4. **Syncs Assets** - Crucible schemas, docs, configs

### Virtual Environment

The `.venv/` directory is created automatically by `uv sync` (no manual `uv venv` needed).

```bash
# After bootstrap, .venv contains:
.venv/
├── bin/
│   ├── python      # Python 3.12+ interpreter
│   ├── pytest      # Test runner
│   └── ruff        # Linter/formatter
└── lib/python3.12/site-packages/  # Installed packages
```

**Using the environment:**
```bash
# Automatic (recommended)
uv run pytest tests/
uv run ruff check src/

# Manual activation
source .venv/bin/activate  # Linux/macOS
pytest tests/
```

## IDE Setup

### VS Code / VSCodium ✅ Recommended

The repository includes `.vscode/settings.json` with optimal configuration:

1. Open project: `code .`
2. Check status bar shows `.venv` interpreter (bottom right)
3. Install recommended extensions (when prompted)

See [.vscode/README.md](../../.vscode/README.md) for details.

### Other IDEs

Point your IDE to: `/path/to/pyfulmen/.venv/bin/python`

## Development Workflow

```bash
# Format code
make fmt

# Check linting
make lint

# Run tests
make test

# All checks (before commit)
make check-all
```

## Troubleshooting

### Virtual Environment Not Created

```bash
# Manually create it
uv venv
uv sync --all-extras
```

### Import Errors in IDE

1. Reload IDE/window
2. Verify interpreter: Check `.venv/bin/python` is selected
3. Re-bootstrap: `make bootstrap`

### Tests Fail

```bash
# Install in editable mode
uv pip install -e .

# Re-run tests
make test
```

## Quality Standards

Before submitting changes:

- ✅ `make lint` - Must pass
- ✅ `make test` - All 136 tests pass
- ✅ `make test-cov` - 93% coverage maintained

## More Information

- [bootstrap.md](./bootstrap.md) - Historical bootstrap journal
- [operations.md](./operations.md) - Detailed development workflows
- [.vscode/README.md](../../.vscode/README.md) - IDE configuration details
