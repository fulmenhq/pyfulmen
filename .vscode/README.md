# VS Code / VSCodium Configuration

This directory contains opinionated IDE configuration to provide a smooth development experience for pyfulmen library developers.

## What's Configured

### `settings.json`

- **Python Interpreter**: Points to `.venv/bin/python` (managed by `uv`)
- **Type Checking**: Basic type checking enabled via Pylance
- **Testing**: pytest integration configured
- **Formatting**: Ruff formatter with format-on-save
- **Import Organization**: Automatic import sorting on save
- **Code Actions**: Fix all issues on save
- **File Exclusions**: Hides `__pycache__`, `.pytest_cache`, build artifacts

### `extensions.json`

Recommended extensions for the best experience:

- `ms-python.python` - Python language support
- `ms-python.vscode-pylance` - Fast, feature-rich language server
- `charliermarsh.ruff` - Ruff linting and formatting

## Why We Commit This

**Problem**: Library developers see false positive import errors like:

```
Import "pydantic" could not be resolved
```

**Cause**: IDE/LSP not configured to use the project's virtual environment

**Solution**: Provide opinionated configuration that works out-of-the-box

## Important Notes

### 1. These Are IDE Settings Only

The **actual quality gates** are enforced via Makefile targets:

- `make test` - All tests must pass
- `make lint` - Ruff linting must pass
- `make test-cov` - Coverage requirements must be met

IDE warnings are just **developer experience improvements**, not authoritative.

### 2. You Can Override

VS Code supports user settings and workspace settings. If you prefer different configuration:

- User settings (global): `~/.config/Code/User/settings.json`
- Workspace settings (project-specific): `.vscode/settings.json` (this file)

Your user settings will override these workspace settings.

### 3. Not Required

You don't need VS Code to develop pyfulmen. The repository works with:

- Any IDE (PyCharm, Sublime, Vim, Emacs, etc.)
- Command line only (`make test`, `make lint`, etc.)
- CI/CD environments

## Troubleshooting

### "Import could not be resolved" Errors Persist

1. **Create Virtual Environment** (if missing):

   ```bash
   make bootstrap  # Creates .venv/ and installs dependencies
   ```

2. **Reload VS Code Window**: `Cmd+Shift+P` → "Developer: Reload Window"

3. **Verify Virtual Environment**: Check status bar shows `.venv` (bottom right)

4. **Select Interpreter Manually**:
   - `Cmd+Shift+P` → "Python: Select Interpreter"
   - Choose `.venv/bin/python`

5. **Check Python Path**:
   ```bash
   which python  # Should show /path/to/pyfulmen/.venv/bin/python
   ```

### Ruff Not Found

Install Ruff in the virtual environment:

```bash
uv sync --all-extras
```

Or install globally:

```bash
pipx install ruff
```

### Tests Not Discovered

Ensure pytest is installed:

```bash
uv run pytest --version
```

If missing:

```bash
uv sync --all-extras
```

## Philosophy

We provide these settings to make onboarding smooth and eliminate common friction points, while emphasizing that **passing the test suite and quality checks** are the true standards.

Think of this as "developer ergonomics" rather than mandatory requirements.
