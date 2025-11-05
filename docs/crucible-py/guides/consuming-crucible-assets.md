---
title: "Consuming Crucible Assets"
description: "Guidance for Fulmen templates and applications on using Crucible schemas, configs, and generated artifacts via helper libraries or dual-hosting workflows"
author: "Schema Cartographer"
date: "2025-11-03"
status: "approved"
tags: ["guides", "consumers", "schemas", "provenance", "dual-hosting"]
---

# Consuming Crucible Assets

Crucible is the SSOT for FulmenHQ schemas, configs, and generated bindings. Helper libraries (`gofulmen`, `pyfulmen`, `tsfulmen`, …) surface those assets so templates and applications can integrate without duplicating logic. This guide explains:

1. How to consume assets directly through helper-library APIs.
2. When and how to **dual-host** schemas/configs inside your own repo while preserving provenance.
3. Recommended checks to detect drift when Crucible versions advance.

> **Audience**: Template repositories (e.g., forge-codex-pulsar) and applications that depend on Fulmen helper libraries.

---

## 1. Library-First Consumption

Every helper library exposes Crucible catalogs via dedicated modules. Examples:

| Asset                  | Go (`gofulmen`)                                | Python (`pyfulmen`)           | TypeScript (`tsfulmen`)                |
| ---------------------- | ---------------------------------------------- | ----------------------------- | -------------------------------------- |
| Exit codes             | `github.com/fulmenhq/gofulmen/pkg/foundry`     | `pyfulmen.foundry.exit_codes` | `@fulmenhq/tsfulmen/foundry/exitCodes` |
| Signals (planned)      | `github.com/fulmenhq/gofulmen/pkg/signals`     | `pyfulmen.signals`            | `@fulmenhq/tsfulmen/signals`           |
| App identity | `github.com/fulmenhq/gofulmen/pkg/appidentity` | `pyfulmen.appidentity`        | `@fulmenhq/tsfulmen/appidentity`       |

Python consumers can introspect Crucible provenance and metadata without touching the filesystem:

```python
from pyfulmen.foundry import exit_codes

info = exit_codes.get_exit_code_info(exit_codes.ExitCode.EXIT_CONFIG_INVALID)
print(info["category"])          # => "configuration"
print(exit_codes.EXIT_CODES_VERSION)  # => e.g. "v1.0.0"
```

TypeScript consumers can retrieve the same metadata without leaving the helper boundary:

```typescript
import {
  exitCodes,
  getExitCodeInfo,
  EXIT_CODES_VERSION,
} from "@fulmenhq/tsfulmen/foundry/exitCodes";

const info = getExitCodeInfo(exitCodes.EXIT_CONFIG_INVALID);
console.log(info?.category); // => "configuration"
console.log(EXIT_CODES_VERSION); // => e.g. "v1.0.0"
```

For Go consumers, always import from the `pkg/...` path exposed by `gofulmen`. Crucible may generate root-level bindings for internal use, but the `pkg` re-exports are the compatibility layer we keep stable for templates and applications.

### Application Identity (v0.1.10+)

Application Identity provides canonical app metadata from `.fulmen/app.yaml` files with discovery, validation, and caching. This enables consistent configuration paths, environment variable prefixes, and telemetry namespaces across the Fulmen ecosystem.

```python
from pyfulmen.appidentity import get_identity, load_from_path, override_identity_for_testing

# Get current application identity (automatic discovery)
identity = get_identity()
print(f"Binary: {identity.binary_name}")
print(f"Vendor: {identity.vendor}")
print(f"Environment Prefix: {identity.env_prefix}")

# Load from explicit path
identity = load_from_path(Path("/path/to/.fulmen/app.yaml"))

# Testing with mock identity
test_identity = AppIdentity(
    binary_name="testapp",
    vendor="testvendor",
    env_prefix="TEST_",
    config_name="testapp",
    description="Test application",
    _raw_metadata={},
    _provenance={}
)

with override_identity_for_testing(test_identity):
    # All get_identity() calls return test_identity
    identity = get_identity()
```

**Integration with Config Module:**

The app identity integrates seamlessly with configuration loading:

```python
from pyfulmen.appidentity import get_identity
from pyfulmen.config import load_layered_config

identity = get_identity()

# Config loader automatically uses identity for:
# - Environment variable prefix (identity.env_prefix)
# - Configuration file names (identity.config_name)
config, diagnostics, sources = load_layered_config(
    category="myapp",
    version="1.0.0",
    identity=identity  # Optional - will use get_identity() if not provided
)
```

**Discovery Precedence:**

1. Environment variable `FULMEN_APP_IDENTITY_PATH`
2. Ancestor search for `.fulmen/app.yaml` from current directory
3. Raise `AppIdentityNotFoundError` if not found

**CLI Usage:**

```bash
# Show current identity
pyfulmen appidentity show

# Show identity in JSON format
pyfulmen appidentity show --format json

# Validate identity file
pyfulmen appidentity validate .fulmen/app.yaml
```

TypeScript validation helpers (e.g., `validateDataBySchemaId()` in `@fulmenhq/tsfulmen/schema/validator`) automatically capture provenance and emit telemetry. Prefer those over bespoke AJV instances so ecosystem metrics and migrations stay aligned.

When possible:

- Call the helper module to retrieve schemas/configs or typed bindings.
- Inspect provenance helpers (`foundry.ExitCodesVersion`, `signals.Version()`, etc.) to log catalog version, revision hash, or last-reviewed date.
- Use the helper’s validation utilities (AJV harness in TypeScript, `goneat` in Python, etc.) to enforce SSOT compliance in your build pipeline.

**Advantages**: No repo-level maintenance; automatic updates when you bump the helper library version; provenance recorded by the module.

---

## 2. Dual-Hosting Workflow

Sometimes you need the schema/config **in your repository** for visibility, auditing, or to run tools that require local files (e.g., static site builders, component demos). Follow this workflow to stay aligned with Crucible:

### Step 1 – Export the Asset

- Run the helper’s sync/export command if provided (e.g., `pyfulmen export-schema`, `tsfulmen scripts/sync-schemas`).
- If no helper command exists yet, fetch from Crucible directly:
  ```bash
  curl -sS https://raw.githubusercontent.com/fulmenhq/crucible/<version>/schemas/web/branding/v1.0.0/site-branding.schema.json \
    -o vendor/crucible/schemas/web/branding/v1.0.0/site-branding.schema.json
  ```
- TypeScript projects can wire a small Bun/tsx helper that exports **and validates** in one pass:
  ```bash
  bunx tsx scripts/export-schema.ts \
    --schema-id web/branding/v1.0.0/site-branding \
    --out vendor/crucible/schemas/web/branding/v1.0.0/site-branding.schema.json
  ```
  Inside `export-schema.ts`, call `validateDataBySchemaId()` from `@fulmenhq/tsfulmen/schema/validator` to guarantee the exported file still matches the SSOT snapshot.

### Step 2 – Preserve Provenance

For every dual-hosted file, store metadata alongside it. Options:

- YAML front-matter or comment header:
  ```yaml
  # x-crucible-source:
  #   catalog: web/site-branding
  #   version: v1.0.0
  #   revision: 5ae105bd (exit codes example)
  #   retrieved: 2025-11-03
  ```
- A companion `.provenance.yaml` file per directory summarizing source/version/hash.

### Step 3 – Track in Vendor Space

Keep dual-hosted files under a dedicated directory (`vendor/crucible/…`, `third_party/crucible/…`) so local changes do not blend with your primary SSOT.

Python packages that ship vendored Crucible assets must list those directories in `pyproject.toml` (`[tool.setuptools.package-data]` or equivalent) so `importlib.resources.files()` can locate them at runtime. Forgetting to mark the data files means your production wheels will serve stale or missing catalogs even if the repo copy looks correct.

### Step 4 – Wire Local Validation

Configure your repo to validate both the library-provided copy **and** your dual-hosted file:

- Add CI job (AJV, goneat, etc.) pointing at `vendor/crucible/...`.
- Ensure your build/test pipeline still imports via helper module to catch updates.
- In TypeScript, prefer `validateFileBySchemaId()` or `validateDataBySchemaId()` from `@fulmenhq/tsfulmen/schema/validator` instead of maintaining a parallel AJV instance:

  ```typescript
  import { validateFileBySchemaId } from "@fulmenhq/tsfulmen/schema/validator";

  await validateFileBySchemaId(
    "web/branding/v1.0.0/site-branding",
    "vendor/crucible/schemas/web/branding/v1.0.0/site-branding.schema.json",
  );
  ```

  This keeps telemetry, provenance, and future Crucible schema migrations consistent with the helper library.

```python
# Python CI example
from pathlib import Path

from pyfulmen.schema.validator import validate_file, format_diagnostics

result = validate_file(
    "web/branding/site-branding@v1.0.0",
    Path("vendor/crucible/schemas/web/branding/v1.0.0/site-branding.schema.json"),
    use_goneat=False,
)
if not result.is_valid:
    raise SystemExit(format_diagnostics(result.diagnostics))
```

**Go-specific tip**:

- If you vendor YAML catalogs for bootstrap tooling, embed them with Go’s `//go:embed` in a dedicated package (e.g., `internal/crucibleassets`). Keep the embed path aligned with the helper’s copy so `go test ./...` exercises the same data the helper exposes. Regenerate/refresh the vendored files before each release and document the expected Crucible tag in a `doc.go` header.

**TypeScript-specific tip**:

- Add a vitest (or Bun) parity test that loads the helper’s runtime catalog and compares it to your vendored copy. This catches drift without duplicating parsing logic:

  ```typescript
  import { loadPatternCatalog } from "@fulmenhq/tsfulmen/foundry/loader";
  import vendorCatalog from "../vendor/crucible/config/library/foundry/patterns.json";

  test("vendor catalog matches helper", async () => {
    const canonical = await loadPatternCatalog();
    expect(vendorCatalog).toStrictEqual(canonical);
  });
  ```

---

## 3. Drift Detection & Updates

When Crucible publishes an update (new version or schema change):

1. **Bump the helper library** in your repo (`go.mod`, `pyproject.toml`, `package.json`).
2. **Run sync/export** again to refresh dual-hosted files.
3. **Diff** your local copy against the helper/library view:
   - Use helper commands (`pyfulmen diff-schema` upcoming) or build your own script that compares your vendor copy to `tsfulmen`’s in-memory catalog.
   - For Go, add a parity check in `go test` that compares the embedded vendor bytes to `foundry.Catalog()` (when exposed) so CI fails if they diverge silently.
4. **Update provenance metadata** to reflect the new version and revision hash.

Consider adding a periodic CI job that:

- Downloads the latest Crucible schema (for the version you depend on).
- Compares it to your vendor copy and fails if they diverge.

---

## 4. Frequently Asked Questions

### Can we bypass helper libraries entirely?

Not recommended. Helper libraries encode language-specific behaviors (validation, code generation) and establish provenance. Dual-hosting is intended as a **cache**, not a replacement.

### How do we know when Crucible updates a catalog?

- Watch Crucible releases: new tags update the `VERSION` file.
- Helper modules expose version constants (`EXIT_CODES_VERSION`, `signals.Version()`).
- Consider subscribing to repository notifications or automation that checks `schemas/**` directories for changes.

### What about downstream forks/customizations?

If you alter the schema locally, you must:

- Rename your schema (e.g., `x-fulmen/…`) to avoid conflicting with SSOT paths.
- Document the divergence in your repo (README, changelog).
- Avoid upstreaming unless the change is intended for all consumers—submit a PR to Crucible instead.

---

## Next Steps

- Helper-library owners: audit modules to ensure they expose provenance (version/hash) and export commands.
- Templates/apps: integrate this guide into your onboarding docs so contributors know how to dual-host responsibly.
- Crucible maintainers: keep this guide updated as new helper commands or validation tooling ship.

For questions or suggestions, open an issue in Crucible and cc @schema-cartographer.
