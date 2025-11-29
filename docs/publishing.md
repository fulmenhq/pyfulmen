---
title: "PyFulmen Publishing Guide"
description: "Authoritative checklist for publishing pyfulmen to TestPyPI and PyPI."
---

# PyFulmen Publishing Guide

This guide documents the uv-focused workflow for publishing PyFulmen. Follow the
steps below exactly before tagging or pushing release branches. The process
keeps git history clean, guarantees that artifacts are validated locally, and
mirrors the rigor in tsfulmen’s npm workflow.

> **Prerequisites**
>
> - uv installed (run `make bootstrap` to provision tools)
> - Clean working tree (`git status` must show no staged/unstaged files)
> - Goneat bootstrap completed (`bin/goneat` present)
> - PyPI credentials stored as `PYPI_TEST_TOKEN` and `PYPI_TOKEN` (1Password)

## 1. Version bump and docs

1. Update the version via Goneat (example for patch bump):
   ```bash
   make version-bump-patch
   ```
2. Update `CHANGELOG.md`, `RELEASE_NOTES.md`, and any docs describing the
   release. Commit all changes.

## 2. Quality gates

Run the standard pre-push suite:

```bash
make prepush
```

`prepush` runs formatting, lint, pytest, SSOT provenance validation, and the
Goneat pre-push hook. The tree must stay clean afterwards.

## 3. Build + verify artifacts

Build the distributables and run the full verification stack:

```bash
make release-verify
```

`release-verify` executes:

1. `make release-build` – builds sdists + wheels via `uv build` and records
   SHA256 sums.
2. `scripts/verify_dist_contents.py` – ensures wheels/sdists include `py.typed`,
   README, license, and other required files.
3. `scripts/verify_local_install.py --installer uv` – installs the wheel with
   `uv pip install --target …` and imports key modules.
4. `scripts/verify_local_install.py --installer pip` – re-runs the install using
   `python -m pip` (still executed under `uv run`) to confirm compatibility with
   pure pip environments.

## 4. Twine metadata check

Run the metadata validation step:

```bash
uv run twine check dist/*.whl dist/*.tar.gz
```

This ensures the generated `PKG-INFO`/metadata is acceptable for PyPI.

## 5. Record the prepublish sentinel

Run the consolidated command **after** `make prepush` has already passed:

```bash
make prepublish
```

`prepublish` enforces a clean working tree, runs the full `release-verify`
workflow, executes `uv run twine check dist/*`, and records a JSON sentinel at
`.artifacts/prepublish.json`. It no longer re-runs `make prepush`, so treat
the earlier quality gates as a prerequisite. `release-check` will refuse to
continue unless this sentinel exists and matches the current version.

## 6. Final release check

Immediately before tagging:

```bash
make release-check
```

`release-check` re-runs the lightweight checks, confirms the git tree is clean,
validates the sentinel version, and blocks if `make prepublish` has not been run
for the current `VERSION`.

## 7. Tag and push

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

Wait for CI to complete before publishing to PyPI.

## 8. Publish to TestPyPI

```bash
PYPI_TEST_TOKEN=… make release-publish-test
```

This wraps `uv run twine upload --repository-url https://test.pypi.org/legacy/ …`
and only runs if `make prepublish` has completed. Use this stage for final smoke
checks in staging environments.

## 9. Publish to PyPI

```bash
PYPI_TOKEN=… make release-publish-prod
```

This uploads the artifacts to the production index via `uv run twine upload`.

## 10. Post-publish validation

Verify the published package from the registry:

```bash
make verify-published-package                     # uses version in VERSION
VERIFY_PUBLISH_VERSION=0.1.12 make verify-published-package
```

`verify_published_package.py` installs through `uv pip install --index-url …`
so it does not depend on the system interpreter. Extend the `DEFAULT_IMPORTS`
list in the script when new public modules are added.

## 11. Release communication

1. Create a GitHub release referencing changelog entries and include
   `dist/SHA256SUMS.txt`.
2. Announce in `#pyfulmen-development`, `#fulmen-releases`, and any template
   repositories that consume PyFulmen.
3. Update downstream templates (Percheron, Forge) to reference the new PyPI
   version.

---

**Quick reference:** `make prepublish` → `make release-check` → tag/push →
`make release-publish-test` → `make release-publish-prod` →
`make verify-published-package`.
