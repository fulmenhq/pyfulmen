# PyFulmen Development Documentation

This directory contains documentation for PyFulmen maintainers and contributors.

## 📁 Documentation Index

### [Bootstrap Guide](bootstrap.md)
Complete guide to bootstrapping PyFulmen development environment, including:
- Tool installation (goneat, uv, Python)
- Dependency management
- SSOT sync setup
- Initial development workflow

### [Operations Guide](operations.md)
Development operations documentation covering:
- Development workflow and daily commands
- Testing strategy and quality gates
- Release process and version management
- Community guidelines and support channels
- Security and dependency management

## 🎯 Quick Start for Contributors

```bash
# 1. Bootstrap development environment
make bootstrap

# 2. Sync Crucible assets
make sync-crucible

# 3. Run tests
make test

# 4. Start developing
make fmt lint test
```

## 📚 Additional Resources

- **[PyFulmen Overview](../pyfulmen_overview.md)**: Comprehensive library overview
- **[Crucible Standards](../crucible-py/standards/)**: Coding standards and best practices
- **[Architecture Docs](../crucible-py/architecture/)**: Fulmen ecosystem architecture
- **[Repository Safety Protocols](../../REPOSITORY_SAFETY_PROTOCOLS.md)**: Operational safety guidelines
- **[Maintainers](../../MAINTAINERS.md)**: Maintainer team and contact info

## 🤝 Contributing

See [operations.md](operations.md) for detailed contribution guidelines and development workflow.

---

*Part of the FulmenHQ ecosystem - standardized across all helper libraries*
