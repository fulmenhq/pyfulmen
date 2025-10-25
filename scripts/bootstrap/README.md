# Bootstrap Scripts

This directory contains scripts for computing authoritative fixture values that are synced to Crucible (the FulmenHQ SSOT repository).

## Purpose

Crucible is language-agnostic and cannot compute language-specific values (hashes, similarity scores, etc.). PyFulmen serves as the **canonical reference implementation** for computing these values, which are then synced to Crucible and used for cross-language validation.

## Pattern

Each bootstrap script:

1. **Reads** a fixture YAML file from `config/crucible-py/library/`
2. **Computes** authoritative values using PyFulmen's implementation
3. **Updates** the YAML with computed values
4. **Writes** the updated YAML back to the same location
5. **Reports** summary and next steps

## Available Scripts

### `compute_fulhash_fixtures.py`

Computes authoritative hash values (xxh3-128, sha256) for FulHash test fixtures.

**Input**: `config/crucible-py/library/fulhash/fixtures.yaml`  
**Computes**: xxh3-128 and sha256 digests for block and streaming fixtures  
**Dependencies**: `xxhash>=3.6.0`, `pyyaml>=6.0.3`

**Usage**:
```bash
uv run python scripts/bootstrap/compute_fulhash_fixtures.py
```

**Status**: ✅ Complete (v0.1.6)

### `compute_similarity_fixtures.py`

**Status**: ✅ Complete (v0.1.7) - Bootstrap phase only

⚠️  **BOOTSTRAP ONLY**: This script overwrites files with PyYAML formatting. Use `validate_similarity_fixtures.py` for ongoing validation.

Computes authoritative similarity scores for Foundry similarity test fixtures.

**Input**: `config/crucible-py/library/foundry/similarity-fixtures.yaml`  
**Computes**: 
- Levenshtein distance and scores (using `rapidfuzz.distance.Levenshtein`)
- Damerau-Levenshtein OSA distance with transposition support (using `rapidfuzz.distance.OSA`)
- Jaro-Winkler similarity scores (using `rapidfuzz.distance.JaroWinkler`)
- Substring matching scores (longest common substring algorithm)
- Normalization preset outputs (none/minimal/default/aggressive)
- Suggestion ranking results (multi-metric with normalization)

**Dependencies**: `rapidfuzz>=3.10.0` (cross-validated against Rust strsim 0.11.x)

**Usage**:
```bash
# Initial bootstrap (overwrites file, changes formatting):
uv run python scripts/bootstrap/compute_similarity_fixtures.py

# Ongoing validation (preserves Crucible formatting):
uv run python scripts/bootstrap/validate_similarity_fixtures.py
```

**Output**: 33 test cases across 6 categories (levenshtein, damerau_osa, jaro_winkler, substring, normalization_presets, suggestions)

### `validate_similarity_fixtures.py`

**Status**: ✅ Complete (v0.1.7)

Validates similarity fixture values WITHOUT modifying the file or changing its formatting. Use this after Crucible owns the fixture format.

**Input**: `config/crucible-py/library/foundry/similarity-fixtures.yaml`  
**Validates**: All computed values match expected values from rapidfuzz  
**Output**: Validation report showing any mismatches

**Usage**:
```bash
uv run python scripts/bootstrap/validate_similarity_fixtures.py
```

**Benefits**:
- Preserves Crucible's YAML formatting (indentation, comments, order)
- Non-destructive validation for CI/CD pipelines
- Clear error reporting with expected vs. actual values

## Workflow

### When Creating New Fixtures

1. **Crucible creates YAML template** with placeholder values marked `# PYFULMEN_COMPUTE`
2. **PyFulmen computes values** using bootstrap script
3. **Updated YAML is synced back** to Crucible via `make sync`
4. **Other languages validate** against PyFulmen's computed values

### When Updating Algorithms

1. **Update PyFulmen implementation** (e.g., change hash algorithm version)
2. **Re-run bootstrap script** to recompute all values
3. **Sync to Crucible** for ecosystem-wide update
4. **Other languages update** to match new reference values

## Design Philosophy

### Why PyFulmen is Canonical

- **First Implementation**: PyFulmen implements new modules before gofulmen/tsfulmen
- **Rich Ecosystem**: Python has mature libraries (xxhash, rapidfuzz) for validation
- **Rapid Iteration**: Python enables quick prototyping and fixture computation
- **Developer Tools**: Scripts can use full PyFulmen API for computation

### Why Not Manual Computation

- **Consistency**: Automated computation eliminates manual errors
- **Reproducibility**: Anyone can verify values by re-running scripts
- **Version Tracking**: Scripts document exact library versions used
- **Maintenance**: Algorithm changes only require script re-run, not manual recalculation

### Why Not Crucible-Native

- **Language Agnostic**: Crucible is YAML/JSON, not a programming language
- **No Dependencies**: Crucible avoids language-specific dependencies
- **Reference Implementation**: PyFulmen provides the "source of truth" computation

## Contributing

When adding new fixture computation scripts:

1. **Follow naming convention**: `compute_<module>_fixtures.py`
2. **Document dependencies**: Specify exact library versions in docstring
3. **Include usage instructions**: Clear `uv run python` command
4. **Report summary**: Print fixture counts and next steps
5. **Update this README**: Add script to "Available Scripts" section

## Cross-Language Validation

After computing fixtures:

1. **PyFulmen tests**: Validate computed values against PyFulmen implementation
2. **Sync to Crucible**: `make sync` pushes updates to SSOT
3. **gofulmen validates**: Rust implementation must match PyFulmen values
4. **tsfulmen validates**: TypeScript implementation must match PyFulmen values
5. **Report discrepancies**: Cross-language bugs revealed by fixture mismatches

---

_Bootstrap scripts are part of PyFulmen's role as the canonical reference implementation for the Fulmen ecosystem._
