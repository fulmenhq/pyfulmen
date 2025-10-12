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
doc = crucible.docs.read_doc('guides/bootstrap-fuldx.md')

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
- **uv** for Python package management
- **FulDX** for version management and SSOT sync
- **Crucible** for standards and schemas

### Quick Start

```bash
# Bootstrap development environment
make bootstrap

# Sync Crucible assets
make sync-crucible

# Run tests
make test

# Run linter
make lint

# Format code
make fmt

# Run all checks
make check-all
```

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

| Target | Description |
|--------|-------------|
| `make bootstrap` | Install tools and dependencies |
| `make tools` | Verify external tools |
| `make test` | Run full test suite |
| `make lint` | Run linting checks |
| `make fmt` | Apply code formatting |
| `make check-all` | Run all checks |
| `make build` | Build distributable package |
| `make release-build` | Build with checksums |
| `make version` | Print current version |
| `make version-bump-*` | Bump version |

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
├── .fuldx/                # FulDX configuration
│   └── sync-consumer.yaml # SSOT sync config
└── docs/                  # Documentation
    └── crucible-py/       # Synced Crucible docs
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

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
