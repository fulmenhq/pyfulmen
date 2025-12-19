# Fulmen Library Makefile
# Repository: pyfulmen
# Bootstrapped with: sfetch → goneat trust pyramid
# Compliant with: FulmenHQ Makefile Standard

# Read lifecycle phase for coverage gates
LIFECYCLE := $(shell cat LIFECYCLE_PHASE 2>/dev/null || echo experimental)
PREPUBLISH_SENTINEL := .artifacts/prepublish.json
CURRENT_VERSION := $(shell cat VERSION 2>/dev/null || echo "0.0.0")

# External tooling (bootstrap via sfetch trust pyramid)
BINDIR ?= ./bin
GONEAT_VERSION ?= v0.3.4
SFETCH_INSTALL_URL ?= https://github.com/3leaps/sfetch/releases/latest/download/install-sfetch.sh

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
	@echo "  make version-set       - Update version (VERSION=x.y.z) and propagate"
	@echo "  make version-propagate - Sync VERSION to package managers"
	@echo "  make version-bump-*    - Bump version (major/minor/patch) and propagate"
	@echo ""
	@echo "Release:"
	@echo "  make release-check     - Run release checklist validation"
	@echo "  make release-prepare   - Prepare for release"
	@echo "  make release-build     - Build release artifacts"
	@echo ""
	@echo "SSOT:"
	@echo "  make sync              - Sync SSOT artifacts (Crucible schemas and docs)"
	@echo "  make sync-crucible     - Alias for sync (deprecated, use sync)"

# Bootstrap tools and Python environment (sfetch → goneat trust pyramid)
.PHONY: bootstrap
bootstrap:
	@echo "Bootstrapping tools and Python environment..."
	@mkdir -p "$(BINDIR)"
	@if ! command -v sfetch >/dev/null 2>&1 && [ ! -x "$(BINDIR)/sfetch" ]; then \
		echo "→ Installing sfetch (trust pyramid bootstrap)..."; \
		if command -v curl >/dev/null 2>&1; then \
			curl -sSfL "$(SFETCH_INSTALL_URL)" | bash -s -- --dir "$(BINDIR)" --yes; \
		elif command -v wget >/dev/null 2>&1; then \
			wget -qO- "$(SFETCH_INSTALL_URL)" | bash -s -- --dir "$(BINDIR)" --yes; \
		else \
			echo "❌ curl or wget is required to bootstrap sfetch"; \
			exit 1; \
		fi; \
	else \
		echo "→ sfetch already installed"; \
	fi
	@SFETCH_BIN="$$(command -v sfetch 2>/dev/null || echo "$(BINDIR)/sfetch")"; \
	if [ ! -x "$(BINDIR)/goneat" ]; then \
		echo "→ Installing goneat $(GONEAT_VERSION) via sfetch..."; \
		"$$SFETCH_BIN" -repo fulmenhq/goneat -tag "$(GONEAT_VERSION)" -dest-dir "$(BINDIR)"; \
	else \
		echo "→ goneat already installed"; \
	fi
	@uv sync --all-extras
	@echo "✓ Bootstrap complete. Ensure $(BINDIR) is in PATH or use ./bin/goneat"

.PHONY: bootstrap-force
bootstrap-force:
	@echo "Force reinstalling tools..."
	@rm -f "$(BINDIR)/goneat" "$(BINDIR)/sfetch"
	@$(MAKE) bootstrap FORCE=1
	@echo "✓ Bootstrap complete"

# Ensure bin/goneat exists for targets that need it
bin/goneat:
	@echo "⚠️  Goneat not found. Run 'make bootstrap' first."
	@exit 1

.PHONY: tools
tools:
	@echo "Verifying external tools..."
	@SFETCH_BIN="$$(command -v sfetch 2>/dev/null || true)"; \
	if [ -z "$$SFETCH_BIN" ] && [ -x "$(BINDIR)/sfetch" ]; then SFETCH_BIN="$(BINDIR)/sfetch"; fi; \
	if [ -n "$$SFETCH_BIN" ]; then \
		echo "✓ sfetch: $$("$$SFETCH_BIN" -version 2>&1 | head -n1)"; \
	else \
		echo "❌ sfetch not found. Run 'make bootstrap' first."; \
		exit 1; \
	fi
	@if command -v goneat >/dev/null 2>&1; then \
		echo "✓ goneat: $$(goneat version 2>&1 | head -n1)"; \
	elif [ -x "$(BINDIR)/goneat" ]; then \
		echo "✓ goneat: $$("$(BINDIR)/goneat" version 2>&1 | head -n1)"; \
	else \
		echo "❌ goneat not found. Run 'make bootstrap' first."; \
		exit 1; \
	fi
	@uv --version > /dev/null && echo "✓ uv: $$(uv --version)" || (echo "❌ uv not found" && exit 1)
	@echo "✓ All tools verified"

# SSOT sync target (required by FulmenHQ Makefile Standard)
.PHONY: sync
sync: sync-crucible

.PHONY: sync-crucible
sync-crucible: bin/goneat
	@echo "Syncing Crucible assets..."
	@bin/goneat ssot sync
	@echo "✓ Crucible synced to .crucible/"

.PHONY: sync-ssot
sync-ssot: sync-crucible

.PHONY: fmt
fmt: bin/goneat
	@echo "Formatting code (ruff)..."
	@uv run ruff format src/ tests/ scripts/ --exclude tests/fixtures/
	@echo "Formatting docs and config (goneat)..."
	@bash -c './bin/goneat format --types yaml,json,markdown --folders . --finalize-eof --quiet 2>&1 | grep -v -E "(fixtures/invalid/malformed-yaml.yaml|encountered the following formatting errors)" || true'
	@echo "✓ All files formatted"

.PHONY: lint
lint:
	@echo "Running linter..."
	@uv run ruff check src/ tests/ scripts/ --exclude tests/fixtures/

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
check-all: fmt lint test
	@echo "✓ All checks passed"

.PHONY: version
version:
	@cat VERSION

.PHONY: version-set
version-set: bin/goneat
	@test -n "$(VERSION)" || (echo "❌ VERSION not set. Use: make version-set VERSION=x.y.z" && exit 1)
	@bin/goneat version set $(VERSION)
	@$(MAKE) version-propagate
	@echo "✓ Version set to $(VERSION) and propagated"

.PHONY: version-propagate
version-propagate: bin/goneat
	@bin/goneat version propagate
	@echo "✓ Version propagated to package managers"

.PHONY: version-bump-major
version-bump-major: bin/goneat
	@bin/goneat version bump major
	@$(MAKE) version-propagate
	@echo "✓ Version bumped (major) and propagated"

.PHONY: version-bump-minor
version-bump-minor: bin/goneat
	@bin/goneat version bump minor
	@$(MAKE) version-propagate
	@echo "✓ Version bumped (minor) and propagated"

.PHONY: version-bump-patch
version-bump-patch: bin/goneat
	@bin/goneat version bump patch
	@$(MAKE) version-propagate
	@echo "✓ Version bumped (patch) and propagated"

.PHONY: version-bump-calver
version-bump-calver: bin/goneat
	@bin/goneat version bump calver
	@$(MAKE) version-propagate
	@echo "✓ Version bumped (calver) and propagated"

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
	@if [ -n "$$(git status --porcelain)" ]; then echo "❌ Working tree dirty - commit or stash changes"; exit 1; fi
	@if [ ! -f $(PREPUBLISH_SENTINEL) ]; then echo "❌ Run 'make prepublish' before release-check"; exit 1; fi
	@uv run python scripts/prepublish_sentinel.py verify --sentinel $(PREPUBLISH_SENTINEL)
	@echo "✓ Release checks passed"

.PHONY: release-prepare
release-prepare: sync-crucible release-check
	@echo "✓ Release prepared"

.PHONY: release-build
release-build: build
	@echo "Generating checksums..."
	@cd dist && sha256sum * > SHA256SUMS.txt
	@echo "✓ Release artifacts ready in dist/"

.PHONY: verify-dist
verify-dist:
	@uv run python scripts/verify_dist_contents.py

.PHONY: verify-local-install
verify-local-install:
	@uv run python scripts/verify_local_install.py --installer uv

.PHONY: verify-local-install-pip
verify-local-install-pip:
	@uv run python scripts/verify_local_install.py --installer pip

.PHONY: verify-published-package
verify-published-package:
	@uv run python scripts/verify_published_package.py $(if $(VERIFY_PUBLISH_VERSION),--version $(VERIFY_PUBLISH_VERSION),) $(if $(VERIFY_INDEX_URL),--index-url $(VERIFY_INDEX_URL),)

.PHONY: release-verify
release-verify: release-build verify-dist verify-local-install verify-local-install-pip
	@echo "✓ Release verification suite passed"

.PHONY: prepublish
# Assumes `make prepush` has already succeeded; enforces clean repo and packaging gates
prepublish:
	@if [ -n "$$(git status --porcelain)" ]; then echo "❌ Working tree must be clean before prepublish"; exit 1; fi
	@$(MAKE) release-verify
	@uv run twine check dist/*.whl dist/*.tar.gz
	@uv run python scripts/prepublish_sentinel.py write --sentinel $(PREPUBLISH_SENTINEL) --version $(CURRENT_VERSION)
	@echo "✓ Prepublish checks completed"


.PHONY: release-publish-test
release-publish-test: prepublish
	@test -n "$$PYPI_TEST_TOKEN" || (echo "❌ Set PYPI_TEST_TOKEN before publishing" && exit 1)
	@uv run twine upload --repository-url https://test.pypi.org/legacy/ -u __token__ -p $$PYPI_TEST_TOKEN dist/*.whl dist/*.tar.gz
	@echo "✓ Uploaded artifacts to TestPyPI"

.PHONY: release-publish-prod
release-publish-prod: prepublish
	@test -n "$$PYPI_TOKEN" || (echo "❌ Set PYPI_TOKEN before publishing" && exit 1)
	@uv run twine upload --repository-url https://upload.pypi.org/legacy/ -u __token__ -p $$PYPI_TOKEN dist/*.whl dist/*.tar.gz
	@echo "✓ Uploaded artifacts to PyPI"

.PHONY: prepush
prepush: check-all validate-ssot-provenance
	@echo "Running goneat pre-push assessment..."
	@./bin/goneat assess --hook pre-push
	@echo "✓ Pre-push checks passed"

.PHONY: validate-ssot-provenance
validate-ssot-provenance:
	@echo "Validating SSOT provenance..."
	@uv run python scripts/validate_ssot_provenance.py

.PHONY: precommit
precommit: fmt lint test
	@echo "Running goneat pre-commit assessment..."
	@./bin/goneat assess --hook pre-commit
	@echo "✓ Pre-commit hooks passed"

.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf dist/ build/ *.egg-info __pycache__/ .pytest_cache/ .ruff_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Clean complete"

# Pathfinder fixture validation
.PHONY: validate-pathfinder-fixtures
validate-pathfinder-fixtures:
	@echo "Validating Pathfinder checksum fixtures..."
	@uv run python scripts/validate_pathfinder_fixtures.py
