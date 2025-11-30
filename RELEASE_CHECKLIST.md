# PyFulmen Release Checklist

Reference: `docs/publishing.md` for full details. This file captures the
high-level order of operations for each release.

1. **Bump version + docs**
   - `make version-bump-<type>`
   - Update CHANGELOG / RELEASE_NOTES
   - Commit changes
2. **Run quality gates** – `make prepush`
3. **Build + verify artifacts** – `make release-verify`
4. **Twine metadata check** – `uv run twine check dist/*.whl dist/*.tar.gz`
5. **Consolidated gate** – `make prepublish` (records `.artifacts/prepublish.json`)
6. **Final release sanity** – `make release-check` (requires clean tree + sentinel)
7. **Tag + push** – `git tag -a vX.Y.Z …`, `git push origin main`, `git push origin vX.Y.Z`
8. **Publish**
   - TestPyPI: `PYPI_TEST_TOKEN=… make release-publish-test`
   - PyPI: `PYPI_TOKEN=… make release-publish-prod`
9. **Post-publish verification** – `make verify-published-package`
10. **Announce + update consumers** – GitHub release, Mattermost, templates

Never skip `make prepublish`. If any step fails, fix the issue, re-run from the
failed command, and ensure the sentinel is regenerated so `make release-check`
passes for the target version.
