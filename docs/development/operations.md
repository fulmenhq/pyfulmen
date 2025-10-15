# PyFulmen Development Operations

> **Location**: `docs/development/operations.md` (standardized across all Fulmen helper libraries)

## 🎯 Mission

Enable developers to build enterprise-grade Python applications using PyFulmen library with comprehensive support, clear documentation, and reliable tooling.

This document provides operational guidance for PyFulmen maintainers and contributors.

## 📚 Documentation Structure

### Core Documentation

- **`README.md`**: Main project documentation with quick start guide
- **`CHANGELOG.md`**: Version history and migration notes
- **`CONTRIBUTING.md`**: Development guidelines and contribution process
- **`LICENSE`**: MIT License for open source use

### API Documentation

- **`docs/api/`**: Detailed API reference with examples
- **`docs/guides/`**: Usage guides and tutorials
- **`docs/examples/`**: Code examples and patterns
- **`docs/migration/`**: Upgrade guides between versions

### Architecture Documentation

- **`docs/architecture/`**: Design decisions and rationale
- **`docs/performance/`**: Benchmarks and optimization guides
- **`docs/integration/`**: Integration patterns with other libraries

## 🛠️ Development Workflow

### Getting Started

```bash
# Clone and setup
git clone https://github.com/fulmenhq/pyfulmen
cd pyfulmen
make bootstrap

# Start development
make sync-crucible
make test
make dev-server  # If applicable
```

### Daily Development

```bash
# Standard development cycle
make fmt             # Format code
make lint            # Check quality
make test            # Run tests
make test-cov        # With coverage
make build           # Build packages
```

### Quality Assurance

```bash
# Pre-commit checks
make fmt lint test

# Full quality suite
make check-all       # All quality checks
make test-all        # All test suites
make docs            # Generate documentation
```

### Git Hooks

PyFulmen uses goneat-managed git hooks for automated quality checks:

**Installed Hooks**:

- **pre-commit**: Runs `make precommit` (formatting + linting)
- **pre-push**: Runs `make prepush` (all checks + full test suite)

**Guardian Integration**:
Both hooks integrate with goneat guardian for approval workflows on protected operations. Guardian provides browser-based approval for high-risk git operations.

**Working with Hooks**:

```bash
# Test hooks manually before committing
goneat assess --hook pre-commit

# Test pre-push checks
goneat assess --hook pre-push

# Validate hook installation
bin/goneat hooks validate

# Regenerate hooks after configuration changes
bin/goneat hooks generate --with-guardian
bin/goneat hooks install
```

**Hook Configuration**:

- Configuration: `.goneat/hooks.yaml`
- Generated hooks: `.goneat/hooks/`
- Installed hooks: `.git/hooks/`
- Guardian config: `~/.goneat/guardian/config.yaml` (user-level)

**Bypassing Hooks** (not recommended):

```bash
# Skip pre-commit (emergency only)
git commit --no-verify -m "message"

# Skip pre-push (emergency only)
git push --no-verify
```

**Note**: Hooks are local-only and not committed to the repository. New contributors should run `make bootstrap` which sets up hooks automatically.

## 🚀 Release Process

### Version Management

- **Semantic Versioning**: Follow MAJOR.MINOR.PATCH for API changes
- **Changelog Maintenance**: Document all changes with impact notes
- **Tagging**: Use Git tags with signed releases
- **GitHub Releases**: Automated with comprehensive release notes

### Release Checklist

```bash
# Complete release preparation
make release-check   # Verify all requirements
make release-prepare # Update docs and sync
make release-build   # Build distribution
make test-release   # Test release artifacts
```

## 🔧 Tooling and Commands

### Development Tools

- **Bootstrap**: `make bootstrap` - Install dependencies and tools
- **Testing**: `make test` - Run test suite
- **Quality**: `make lint` - Code quality checks
- **Building**: `make build` - Create distribution packages
- **Documentation**: `make docs` - Generate documentation

### Make Targets Reference

- **`make help`**: Show all available targets
- **`make clean`**: Remove build artifacts
- **`make install`**: Install package locally
- **`make publish`**: Publish to PyPI (maintainers only)

## 🧪 Testing Strategy

### Test Coverage

- **Unit Tests**: 95%+ coverage on public API
- **Integration Tests**: Cross-module functionality
- **Performance Tests**: Benchmarks for enterprise features
- **Compatibility Tests**: Python version matrix testing

### Quality Gates

- **Code Style**: Ruff formatting and linting
- **Type Checking**: MyPy static analysis
- **Security**: Bandit security scanning
- **Documentation**: Docstring coverage and API docs

## 📊 Monitoring and Analytics

### Development Metrics

- **Test Coverage**: Track coverage trends over time
- **Performance**: Monitor benchmark performance
- **Quality**: Track lint and type check results
- **Dependencies**: Monitor for security updates

### Release Analytics

- **Download Stats**: PyPI download metrics
- **Usage Analytics**: Error reports and telemetry (opt-in)
- **Community Engagement**: GitHub stars, issues, PRs

## 🤝 Community Guidelines

### Contribution Process

1. **Fork Repository**: Create personal fork for development
2. **Create Branch**: Use descriptive branch names
3. **Make Changes**: Implement with tests and documentation
4. **Submit PR**: Pull request with comprehensive description
5. **Code Review**: Address feedback from maintainers
6. **Merge**: Maintainers merge after approval

### Code Standards

- **Python PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type hints for all public APIs
- **Documentation**: Comprehensive docstrings for all functions
- **Testing**: Unit tests for all functionality
- **Error Handling**: Proper exception handling and logging

### Support Channels

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Mattermost**: `#pyfulmen-development` for real-time discussion
- **Email**: maintainers@3leaps.net for private issues

## 🔐 Security

### Security Process

1. **Vulnerability Reporting**: Private disclosure to maintainers
2. **Security Reviews**: Regular dependency scanning
3. **Patch Management**: Prioritized security updates
4. **Security Documentation**: Security considerations and best practices

### Dependency Management

- **Regular Updates**: Keep dependencies current
- **Security Scanning**: Automated vulnerability scanning
- **License Compliance**: Verify all dependency licenses
- **Minimal Dependencies**: Reduce attack surface

---

_This documentation supports PyFulmen's mission to enable enterprise-grade Python development._
