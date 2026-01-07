# Fulmen Library Makefile
# Repository: pyfulmen
# Bootstrapped with: sfetch → goneat trust pyramid
# Compliant with: FulmenHQ Makefile Standard

# Read lifecycle phase for coverage gates
LIFECYCLE := $(shell cat LIFECYCLE_PHASE 2>/dev/null || echo experimental)
PREPUBLISH_SENTINEL := .artifacts/prepublish.json
CURRENT_VERSION := $(shell cat VERSION 2>/dev/null || echo "0.0.0")

# Tool installation (user-space bin dir; overridable with BINDIR=...)
# Defaults to $HOME/.local/bin on macOS/Linux
BINDIR ?= $(HOME)/.local/bin
GONEAT_VERSION ?= v0.4.2
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
bootstrap: ## Install external tools (sfetch, goneat + foundation tools)
	@echo "Bootstrapping pyfulmen development environment..."
	@mkdir -p "$(BINDIR)"
	@echo ""
	@echo "Step 1: Installing sfetch (trust anchor)..."
	@if ! command -v sfetch >/dev/null 2>&1 && [ ! -x "$(BINDIR)/sfetch" ]; then \
		echo "→ Installing sfetch into $(BINDIR)..."; \
		if command -v curl >/dev/null 2>&1; then \
			curl -sSfL "$(SFETCH_INSTALL_URL)" | bash -s -- --dir "$(BINDIR)" --yes; \
		elif command -v wget >/dev/null 2>&1; then \
			wget -qO- "$(SFETCH_INSTALL_URL)" | bash -s -- --dir "$(BINDIR)" --yes; \
		else \
			echo "❌ curl or wget is required to bootstrap sfetch"; \
			exit 1; \
		fi; \
	else \
		echo "✅ sfetch already installed"; \
	fi
	@echo ""
	@echo "Step 2: Installing goneat via sfetch..."
	@SFETCH_BIN="$$(command -v sfetch 2>/dev/null || true)"; \
	if [ -z "$$SFETCH_BIN" ] && [ -x "$(BINDIR)/sfetch" ]; then SFETCH_BIN="$(BINDIR)/sfetch"; fi; \
	if [ -z "$$SFETCH_BIN" ]; then echo "❌ sfetch not found after bootstrap"; exit 1; fi; \
	if [ "$(FORCE)" = "1" ] || [ "$(FORCE)" = "true" ]; then \
		echo "→ Force installing goneat $(GONEAT_VERSION) into $(BINDIR)..."; \
		"$$SFETCH_BIN" -repo fulmenhq/goneat -tag "$(GONEAT_VERSION)" -dest-dir "$(BINDIR)"; \
	else \
		if ! command -v goneat >/dev/null 2>&1 && [ ! -x "$(BINDIR)/goneat" ]; then \
			echo "→ Installing goneat $(GONEAT_VERSION) into $(BINDIR)..."; \
			"$$SFETCH_BIN" -repo fulmenhq/goneat -tag "$(GONEAT_VERSION)" -dest-dir "$(BINDIR)"; \
		else \
			echo "✅ goneat already installed: $$(goneat --version 2>&1 | head -1)"; \
		fi; \
	fi
	@echo ""
	@echo "Step 3: Installing foundation tools via goneat..."
	@GONEAT_BIN="$$(command -v goneat 2>/dev/null || true)"; \
	if [ -z "$$GONEAT_BIN" ] && [ -x "$(BINDIR)/goneat" ]; then GONEAT_BIN="$(BINDIR)/goneat"; fi; \
	if [ -n "$$GONEAT_BIN" ]; then \
		"$$GONEAT_BIN" doctor tools --scope foundation --install --yes --no-cooling 2>/dev/null || \
		echo "⚠️  Some foundation tools may need manual installation"; \
	fi
	@echo ""
	@echo "Step 4: Syncing Python dependencies with uv..."
	@if command -v uv >/dev/null 2>&1; then \
		uv sync --all-extras; \
		echo "✅ Python dependencies synced"; \
	else \
		echo "⚠️  uv not found - skipping Python dependency sync"; \
		echo "   Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
	fi
	@echo ""
	@echo "✅ Bootstrap completed"
	@echo ""
	@echo "💡 Ensure $(BINDIR) is in your PATH:"
	@echo "   export PATH=\"$(BINDIR):\$$PATH\""

.PHONY: bootstrap-force
bootstrap-force: ## Force reinstall external tools
	@$(MAKE) bootstrap FORCE=1

# Goneat resolution (finds goneat in BINDIR or PATH)
GONEAT_RESOLVE = \
	GONEAT=""; \
	if [ -x "$(BINDIR)/goneat" ]; then GONEAT="$(BINDIR)/goneat"; fi; \
	if [ -z "$$GONEAT" ]; then GONEAT="$$(command -v goneat 2>/dev/null || true)"; fi; \
	if [ -z "$$GONEAT" ]; then echo "goneat not found. Run 'make bootstrap' first."; exit 1; fi

# Sfetch resolution (finds sfetch in BINDIR or PATH)
SFETCH_RESOLVE = \
	SFETCH=""; \
	if [ -x "$(BINDIR)/sfetch" ]; then SFETCH="$(BINDIR)/sfetch"; fi; \
	if [ -z "$$SFETCH" ]; then SFETCH="$$(command -v sfetch 2>/dev/null || true)"; fi

.PHONY: tools
tools: ## Verify external tools are available
	@echo "Verifying external tools..."
	@$(SFETCH_RESOLVE); if [ -n "$$SFETCH" ]; then echo "sfetch: $$("$$SFETCH" -version 2>&1 | head -n1)"; else echo "sfetch not found (optional for day-to-day)"; fi
	@$(GONEAT_RESOLVE); echo "goneat: $$($$GONEAT --version 2>&1 | head -n1 || true)"
	@uv --version > /dev/null && echo "uv: $$(uv --version)" || (echo "uv not found" && exit 1)
	@uv run ruff --version > /dev/null && echo "ruff: $$(uv run ruff --version)" || echo "ruff not available"
	@echo "All required tools verified"

# SSOT sync target (required by FulmenHQ Makefile Standard)
.PHONY: sync
sync: sync-crucible

.PHONY: sync-crucible
sync-crucible: ## Sync assets from Crucible SSOT
	@echo "Syncing Crucible assets..."
	@$(GONEAT_RESOLVE); $$GONEAT ssot sync
	@echo "Crucible synced to .crucible/"

.PHONY: sync-ssot
sync-ssot: sync-crucible

.PHONY: fmt
fmt: ## Format code with ruff and goneat
	@echo "Formatting code (ruff)..."
	@uv run ruff format src/ tests/ scripts/ --exclude tests/fixtures/
	@echo "Formatting docs and config (goneat)..."
	@$(GONEAT_RESOLVE); bash -c '$$GONEAT format --types yaml,json,markdown --folders . --finalize-eof --quiet 2>&1 | grep -v -E "(fixtures/invalid/malformed-yaml.yaml|encountered the following formatting errors)" || true'
	@echo "All files formatted"

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
check-all: fmt lint test license-audit ## Run all quality checks (fmt, lint, test, license)
	@echo "All quality checks passed"

.PHONY: version
version:
	@cat VERSION

.PHONY: version-set
version-set: ## Set version to specific value (usage: make version-set VERSION=x.y.z)
	@test -n "$(VERSION)" || (echo "VERSION not set. Use: make version-set VERSION=x.y.z" && exit 1)
	@$(GONEAT_RESOLVE); $$GONEAT version set $(VERSION)
	@$(MAKE) version-propagate
	@echo "Version set to $(VERSION) and propagated"

.PHONY: version-propagate
version-propagate: ## Sync VERSION to package managers
	@$(GONEAT_RESOLVE); $$GONEAT version propagate
	@echo "Version propagated to package managers"

.PHONY: version-bump-major
version-bump-major: ## Bump major version
	@$(GONEAT_RESOLVE); $$GONEAT version bump major
	@$(MAKE) version-propagate
	@echo "Version bumped (major) and propagated"

.PHONY: version-bump-minor
version-bump-minor: ## Bump minor version
	@$(GONEAT_RESOLVE); $$GONEAT version bump minor
	@$(MAKE) version-propagate
	@echo "Version bumped (minor) and propagated"

.PHONY: version-bump-patch
version-bump-patch: ## Bump patch version
	@$(GONEAT_RESOLVE); $$GONEAT version bump patch
	@$(MAKE) version-propagate
	@echo "Version bumped (patch) and propagated"

.PHONY: version-bump-calver
version-bump-calver: ## Bump to CalVer
	@$(GONEAT_RESOLVE); $$GONEAT version bump calver
	@$(MAKE) version-propagate
	@echo "Version bumped (calver) and propagated"

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
prepush: check-all validate-ssot-provenance ## Run pre-push hooks (comprehensive)
	@echo "Running goneat pre-push assessment..."
	@$(GONEAT_RESOLVE); $$GONEAT assess --hook pre-push --hook-manifest .goneat/hooks.yaml
	@echo "Pre-push checks passed"

.PHONY: validate-ssot-provenance
validate-ssot-provenance: ## Verify SSOT provenance files
	@echo "Validating SSOT provenance..."
	@uv run python scripts/validate_ssot_provenance.py

.PHONY: precommit
precommit: fmt lint test ## Run pre-commit hooks (fast, critical issues)
	@echo "Running goneat pre-commit assessment..."
	@$(GONEAT_RESOLVE); $$GONEAT assess --hook pre-commit --hook-manifest .goneat/hooks.yaml
	@echo "Pre-commit hooks passed"

# License compliance
# Only audits runtime dependencies (excludes dev tools like mypy, twine, pytest)
# Dev tools may use GPL/MPL licenses which is acceptable - they don't ship in the wheel
.PHONY: license-audit
license-audit: ## Audit runtime dependencies for forbidden licenses (excludes dev tools)
	@echo "Auditing runtime dependency licenses (excluding dev tools)..."
	@mkdir -p dist/reports
	@# Extract runtime package names from pyproject.toml (direct + transitive)
	@RUNTIME_PKGS=$$(uv pip compile pyproject.toml 2>/dev/null | grep -E "^[a-z]" | cut -d'=' -f1 | tr '\n' ' '); \
	if [ -z "$$RUNTIME_PKGS" ]; then \
		echo "Failed to resolve runtime dependencies"; \
		exit 1; \
	fi; \
	echo "Runtime packages: $$RUNTIME_PKGS"; \
	uv run pip-licenses --packages $$RUNTIME_PKGS --format=csv --output-file=dist/reports/license-inventory.csv 2>/dev/null || \
		(uv pip install pip-licenses && uv run pip-licenses --packages $$RUNTIME_PKGS --format=csv --output-file=dist/reports/license-inventory.csv); \
	forbidden='GPL|LGPL|AGPL|MPL|CDDL'; \
	if grep -E "$$forbidden" dist/reports/license-inventory.csv >/dev/null 2>&1; then \
		echo "Forbidden license detected in runtime dependencies. See dist/reports/license-inventory.csv"; \
		grep -E "$$forbidden" dist/reports/license-inventory.csv; \
		exit 1; \
	else \
		echo "No forbidden licenses in runtime dependencies"; \
	fi

# Full license inventory (includes dev tools - informational only, no enforcement)
.PHONY: license-inventory
license-inventory: ## Generate full license inventory including dev tools (informational)
	@echo "Generating full license inventory (all packages)..."
	@mkdir -p dist/reports
	@uv run pip-licenses --format=csv --output-file=dist/reports/license-inventory-full.csv 2>/dev/null || \
		(uv pip install pip-licenses && uv run pip-licenses --format=csv --output-file=dist/reports/license-inventory-full.csv)
	@echo "Full inventory: dist/reports/license-inventory-full.csv"
	@wc -l dist/reports/license-inventory-full.csv | awk '{print $$1 - 1 " packages total"}'

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
