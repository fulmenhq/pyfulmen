# pyfulmen

Python Fulmen libraries for enterprise-scale development.

**Lifecycle Phase**: `alpha` | **Version**: 0.1.0 | **Coverage**: 93%

## Overview

PyFulmen is part of the Fulmen ecosystem, providing templates, processes, and tools for enterprise-scale development in Python.

📖 **[Read the full PyFulmen Overview](docs/pyfulmen_overview.md)** for a comprehensive guide to modules, observability features, and the roadmap.

> **Alpha Status**: Early adopters; rapidly evolving features. Minimum coverage: 30%. See [Repository Lifecycle Standard](docs/crucible-py/standards/repository-lifecycle.md) for quality expectations.

**Key Features:**

- **Crucible Shim** - Idiomatic Python access to Crucible schemas, docs, and config defaults
- **Config Path API** - XDG-compliant, platform-aware configuration paths
- **Three-Layer Config Loading** - Crucible defaults → User overrides → App config
- **Schema Validation** - Helpers for validating data against Crucible JSON schemas
- **Observability Integration** - Structured logging with Crucible severity mapping
- **Version Management** - Utilities for reading and validating repository versions

## Installation

### From PyPI (when published)

```bash
pip install pyfulmen
# or with uv
uv add pyfulmen
```

### From Local Wheel (for testing/development)

```bash
# Build the wheel
make build

# Install in another project
cd /path/to/your/project
pip install /path/to/pyfulmen/dist/pyfulmen-0.1.0-py3-none-any.whl

# Or with uv
uv add /path/to/pyfulmen/dist/pyfulmen-0.1.0-py3-none-any.whl
```

### Editable Install (for library development)

```bash
# Install pyfulmen in editable mode
cd /path/to/your/project
pip install -e /path/to/pyfulmen

# Or with uv
uv add --editable /path/to/pyfulmen
```

This allows you to modify PyFulmen code and see changes immediately without rebuilding.

## Usage

### Basic Example

```python
from pyfulmen import crucible, config, schema, logging

# Access Crucible assets
schemas = crucible.schemas.list_available_schemas()
doc = crucible.docs.read_doc('guides/bootstrap-goneat.md')

# Get platform-aware config paths
config_dir = config.paths.get_fulmen_config_dir()

# Load config with three-layer merge
loader = config.loader.ConfigLoader()
cfg = loader.load('terminal/v1.0.0/terminal-overrides-defaults')

# Validate data against schemas
schema.validator.validate_against_schema(
    data={'severity': 'info'},
    category='observability/logging',
    version='v1.0.0',
    name='log-event'
)

# Configure logging
logger = logging.logger.configure_logging(app_name='myapp', level='debug')
logger.info('Application started')
```

### Version Management

```python
from pyfulmen import version

# Read version from VERSION file
ver = version.read_version()  # "0.1.0"

# Get detailed version info
info = version.get_version_info()
# {'version': '0.1.0', 'source': 'VERSION', 'valid': True}

# Validate version sync across files
sync = version.validate_version_sync()
# {'synced': True, 'version_file': '0.1.0', ...}
```

## Development

This repository uses:

- **uv** for Python package management (fast, modern alternative to pip/virtualenv)
- **goneat** for version management and SSOT sync (successor to FulDX)
- **Crucible** for standards and schemas

### Prerequisites

Install `uv` (Python package manager):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv

# Or via pipx
pipx install uv
```

See [uv installation docs](https://github.com/astral-sh/uv#installation) for other platforms.

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/fulmenhq/pyfulmen.git
cd pyfulmen

# 2. Bootstrap development environment (creates .venv, installs tools and dependencies)
make bootstrap

# This command:
# - Creates .venv/ virtual environment (if not exists)
# - Installs goneat CLI tool
# - Installs all Python dependencies via uv
# - Syncs Crucible assets

# 3. Verify setup
make tools  # Check that goneat and other tools are available
make test   # Run test suite (should see 136 tests passing)

# 4. Development cycle
make fmt              # Format code with Ruff
make lint             # Check linting
make test             # Run tests
make check-all        # Run all checks (lint + test)
```

### Manual Virtual Environment Setup (Optional)

The `make bootstrap` command handles this automatically, but if you need to create the virtual environment manually:

```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv sync --all-extras

# Verify installation
uv run pytest --version
uv run ruff --version
```

**Note**: `uv` manages the virtual environment automatically when you run `uv run <command>`, so you typically don't need to activate it manually.

### Building & Releasing

```bash
# Build wheel
make build

# Build with checksums
make release-build

# Run release checks
make release-check

# Bump version
make version-bump-patch  # or -minor, -major
```

### Makefile Targets

See `make help` for all available targets. Key commands:

| Target                | Description                    |
| --------------------- | ------------------------------ |
| `make bootstrap`      | Install tools and dependencies |
| `make tools`          | Verify external tools          |
| `make test`           | Run full test suite            |
| `make lint`           | Run linting checks             |
| `make fmt`            | Apply code formatting          |
| `make check-all`      | Run all checks                 |
| `make build`          | Build distributable package    |
| `make release-build`  | Build with checksums           |
| `make version`        | Print current version          |
| `make version-bump-*` | Bump version                   |

## Project Structure

```
pyfulmen/
├── src/pyfulmen/           # Main package
│   ├── crucible/          # Crucible shim (schemas, docs, config)
│   ├── config/            # Config paths and loading
│   ├── schema/            # Schema validation utilities
│   ├── logging/           # Observability integration
│   └── version.py         # Version management
├── tests/                 # Test suite
├── scripts/               # Build scripts
│   └── bootstrap.py       # Tool installation script
├── .crucible/             # Crucible integration
│   ├── tools.yaml         # Tool definitions
│   └── tools.local.yaml.example
├── .goneat/               # Goneat configuration
│   ├── tools.yaml         # Tool definitions
│   └── ssot-consumer.yaml # SSOT sync config
└── docs/                  # Documentation
    └── crucible-py/       # Synced Crucible docs
```

## Library Developers

**Note**: This section is for developers working on pyfulmen itself. Library users can skip this section.

### First-Time Setup

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and bootstrap
git clone https://github.com/fulmenhq/pyfulmen.git
cd pyfulmen
make bootstrap

# 3. Verify setup
make test  # Should see 136 tests passing
```

The `.venv/` virtual environment is created automatically by `make bootstrap` (via `uv sync`).

### IDE Setup (VS Code / VSCodium)

We provide opinionated `.vscode/settings.json` configuration to eliminate false positive linter errors and configure the development environment optimally. This is a **convenience only** - the actual quality gates are enforced via:

- `make test` - Test suite (currently 143 tests, 93% coverage)
- `make lint` - Ruff linting
- `make fmt` - Code formatting
- `make check-all` - All quality checks

The `.vscode/` configuration:

- Points Python interpreter to `.venv/bin/python`
- Configures Ruff as the formatter
- Enables format-on-save
- Sets up pytest integration
- Hides build artifacts and cache directories

**Recommended VS Code Extensions** (see `.vscode/extensions.json`):

- `ms-python.python` - Python language support
- `ms-python.vscode-pylance` - Fast, feature-rich language server
- `charliermarsh.ruff` - Ruff linting and formatting

### Development Workflow

```bash
# 1. Bootstrap environment (first time only)
make bootstrap

# 2. Sync Crucible assets (when schemas/docs update)
make sync-crucible

# 3. Development cycle
make fmt              # Format code
make lint             # Check linting
make test             # Run tests
make check-all        # Run all checks (lint + test)

# 4. Before commit
make precommit        # Runs fmt + lint
make prepush          # Runs check-all
```

### Quality Gates

**All contributions must pass**:

1. ✅ `make lint` - No linting errors
2. ✅ `make test` - All tests passing
3. ✅ `make test-cov` - Minimum coverage maintained (30% alpha, target 93%)
4. ✅ Type hints present for public APIs
5. ✅ Docstrings for all public functions/classes

**Note**: IDE linter warnings (e.g., "Import could not be resolved") are often false positives. The actual quality gate is `make lint` and `make test` passing.

### Testing

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
uv run pytest tests/unit/foundry/test_models.py -v

# Run specific test class
uv run pytest tests/unit/logging/test_severity.py::TestSeverityComparison -v
```

### Code Style

- **Formatter**: Ruff (line length: 100)
- **Linter**: Ruff with pyproject.toml configuration
- **Type Hints**: Required for public APIs (Python 3.12+)
- **Docstrings**: Google style
- **Imports**: Organized automatically by Ruff

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Ensure all quality gates pass (`make check-all`).
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
5. Push to the branch (`git push origin feature/AmazingFeature`).
6. Open a Pull Request.

PyFulmen follows the [Fulmen Helper Library Standard](docs/crucible-py/architecture/fulmen-helper-library-standard.md).

See [Python Coding Standards](docs/crucible-py/standards/coding/python.md) for code style guidelines.

### Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for more information.

### Attribution

AI-assisted contributions should be attributed in commits:

```
feat: add schema validation utilities

Co-authored-by: Agent Name <noreply@3leaps.net>
```

For more details, see [MAINTAINERS.md](MAINTAINERS.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Licensing

[pyfulmen](https://github.com/fulmenhq/pyfulmen) is licensed under MIT license - see [LICENSE](LICENSE) for complete details.

**Trademarks**: "Fulmen" and "3 Leaps" are trademarks of 3 Leaps, LLC. While code is open source, please use distinct names for derivative works to prevent confusion.

### OSS Policies (Organization-wide)

- Authoritative policies repository: https://github.com/3leaps/oss-policies/
- Code of Conduct: https://github.com/3leaps/oss-policies/blob/main/CODE_OF_CONDUCT.md
- Security Policy: https://github.com/3leaps/oss-policies/blob/main/SECURITY.md
- Contributing Guide: https://github.com/3leaps/oss-policies/blob/main/CONTRIBUTING.md

## Status

**Lifecycle Phase**: `alpha` ([Repository Lifecycle Standard](docs/crucible-py/standards/repository-lifecycle.md))

- **Quality Bar**: 30% minimum test coverage (currently: 93%)
- **Stability**: Early adopters; rapidly evolving features
- **Breaking Changes**: Expected without deprecation warnings
- **Documentation**: Major gaps documented; kept current

See `LIFECYCLE_PHASE` file and [CHANGELOG.md](CHANGELOG.md) for version history.

---

<div align="center">

⚡ **Python Foundation for the Fulmen Ecosystem** ⚡

_Idiomatic Python access to Crucible schemas, platform-aware config paths, and three-layer configuration loading_

<br><br>

**Built with 🔨 by the 3 Leaps team**
**Part of the [Fulmen Ecosystem](https://fulmenhq.dev) - Lightning-fast enterprise development**

**Crucible Integration** • **Config Management** • **Schema Validation** • **Observability**

</div>
