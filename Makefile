# Fulmen Library Makefile
# Repository: pyfulmen
# Bootstrapped with: Goneat
# Compliant with: FulmenHQ Makefile Standard

# Read lifecycle phase for coverage gates
LIFECYCLE := $(shell cat LIFECYCLE_PHASE 2>/dev/null || echo experimental)

# Coverage thresholds by lifecycle phase
# experimental: 0%, alpha: 30%, beta: 60%, rc: 70%, ga: 75%, lts: 80%
ifeq ($(LIFECYCLE),alpha)
    COVERAGE_MIN := 30
else ifeq ($(LIFECYCLE),beta)
    COVERAGE_MIN := 60
else ifeq ($(LIFECYCLE),rc)
    COVERAGE_MIN := 70
else ifeq ($(LIFECYCLE),ga)
    COVERAGE_MIN := 75
else ifeq ($(LIFECYCLE),lts)
    COVERAGE_MIN := 80
else
    COVERAGE_MIN := 0
endif

.PHONY: help
help:
	@echo "PyFulmen Makefile - Standard Targets"
	@echo ""
	@echo "Core:"
	@echo "  make bootstrap         - Install tools and dependencies"
	@echo "  make tools             - Verify external tools are present"
	@echo "  make lint              - Run linting checks"
	@echo "  make fmt               - Apply code formatting"
	@echo "  make test              - Run full test suite"
	@echo "  make test-cov          - Run tests with coverage enforcement"
	@echo "  make check-all         - Run all checks (lint, test)"
	@echo "  make build             - Build distributable package"
	@echo "  make clean             - Remove build artifacts"
	@echo "  make lifecycle         - Show current lifecycle phase and requirements"
	@echo ""
	@echo "Version:"
	@echo "  make version           - Print current version"
	@echo "  make version-set       - Update version (VERSION=x.y.z)"
	@echo "  make version-bump-*    - Bump version (major/minor/patch)"
	@echo ""
	@echo "Release:"
	@echo "  make release-check     - Run release checklist validation"
	@echo "  make release-prepare   - Prepare for release"
	@echo "  make release-build     - Build release artifacts"
	@echo ""
	@echo "SSOT:"
	@echo "  make sync-crucible     - Sync Crucible schemas and docs"

# Bootstrap tools and Python environment
.PHONY: bootstrap
bootstrap:
	@echo "Bootstrapping tools and Python environment..."
	@uv run python scripts/bootstrap.py
	@uv sync --all-extras
	@echo "✓ Bootstrap complete"

.PHONY: bootstrap-force
bootstrap-force:
	@echo "Force reinstalling tools..."
	@uv run python scripts/bootstrap.py --force
	@uv sync --all-extras
	@echo "✓ Bootstrap complete"

# Ensure bin/goneat exists for targets that need it
bin/goneat:
	@echo "⚠️  Goneat not found. Run 'make bootstrap' first."
	@exit 1

.PHONY: tools
tools: bin/goneat
	@echo "Verifying external tools..."
	@bin/goneat version > /dev/null && echo "✓ Goneat: $$(bin/goneat version)" || (echo "❌ Goneat not functional" && exit 1)
	@uv --version > /dev/null && echo "✓ uv: $$(uv --version)" || (echo "❌ uv not found" && exit 1)
	@echo "✓ All required tools present"

.PHONY: sync-crucible
sync-crucible: bin/goneat
	@echo "Syncing Crucible assets..."
	@bin/goneat ssot sync
	@echo "✓ Crucible synced to .crucible/"

.PHONY: sync-ssot
sync-ssot: sync-crucible

.PHONY: fmt
fmt: bin/goneat
	@echo "Formatting code..."
	@uv run ruff format src/ tests/
	@echo "Formatting docs and config..."
	@bin/goneat format --types yaml,json,markdown
	@echo "✓ All files formatted"

.PHONY: lint
lint:
	@echo "Running linter..."
	@uv run ruff check src/ tests/

.PHONY: test
test:
	@echo "Running tests (lifecycle=$(LIFECYCLE), min coverage=$(COVERAGE_MIN)%)..."
	@uv run pytest tests/ -v

.PHONY: test-cov
test-cov:
	@echo "Running tests with coverage (lifecycle=$(LIFECYCLE), min=$(COVERAGE_MIN)%)..."
	@uv run pytest tests/ --cov=src/pyfulmen --cov-report=term-missing --cov-fail-under=$(COVERAGE_MIN)

.PHONY: lifecycle
lifecycle:
	@echo "Repository Lifecycle Phase: $(LIFECYCLE)"
	@echo "Required test coverage: $(COVERAGE_MIN)%"

.PHONY: check-all
check-all: lint test
	@echo "✓ All checks passed"

.PHONY: version
version:
	@cat VERSION

.PHONY: version-set
version-set: bin/goneat
	@test -n "$(VERSION)" || (echo "❌ VERSION not set. Use: make version-set VERSION=x.y.z" && exit 1)
	@bin/goneat version sync --version $(VERSION)
	@echo "✓ Version set to $(VERSION)"

.PHONY: version-bump-major
version-bump-major: bin/goneat
	@bin/goneat version bump major

.PHONY: version-bump-minor
version-bump-minor: bin/goneat
	@bin/goneat version bump minor

.PHONY: version-bump-patch
version-bump-patch: bin/goneat
	@bin/goneat version bump patch


.PHONY: version-bump-calver
version-bump-calver: bin/goneat
	@bin/goneat version bump calver

.PHONY: build
build:
	@echo "Building Python package..."
	@uv build
	@echo "✓ Package built in dist/"

.PHONY: build-all
build-all: build
	@echo "✓ Multi-platform build complete (Python wheel is platform-independent)"

.PHONY: release-check
release-check: check-all
	@echo "Running release checklist..."
	@test -f VERSION || (echo "❌ VERSION file missing" && exit 1)
	@echo "✓ Release checks passed"

.PHONY: release-prepare
release-prepare: sync-crucible release-check
	@echo "✓ Release prepared"

.PHONY: release-build
release-build: build
	@echo "Generating checksums..."
	@cd dist && sha256sum * > SHA256SUMS.txt
	@echo "✓ Release artifacts ready in dist/"

.PHONY: prepush
prepush: check-all
	@echo "✓ Pre-push checks passed"

.PHONY: precommit
precommit: fmt lint
	@echo "✓ Pre-commit hooks passed"

.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf dist/ build/ *.egg-info __pycache__/ .pytest_cache/ .ruff_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Clean complete"
