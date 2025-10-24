# Pathfinder Module Guide

**Module**: `pyfulmen.pathfinder`  
**Since**: v0.1.0 (checksums added v0.1.6)  
**Status**: Stable

## Overview

Pathfinder provides fast, pattern-based file discovery with optional FulHash checksum calculation. Designed for build tools, CI/CD pipelines, and development workflows requiring file integrity verification.

## Quick Start

```python
from pyfulmen.pathfinder import Finder, FindQuery, FinderConfig

# Basic usage
finder = Finder()
results = finder.find_files(FindQuery(
    root="/path/to/project",
    include=["**/*.py"]
))

for result in results:
    print(f"{result.relative_path}: {result.metadata.size} bytes")
```

## Checksum Calculation (v0.1.6+)

### Enabling Checksums

```python
# Configure finder with checksums
config = FinderConfig(
    calculateChecksums=True,
    checksumAlgorithm="xxh3-128"  # or "sha256"
)
finder = Finder(config)

results = finder.find_files(FindQuery(
    root="/path/to/project",
    include=["**/*.py", "**/*.json"]
))

for result in results:
    if result.metadata.checksum:
        print(f"{result.relative_path}: {result.metadata.checksum}")
```

### Algorithm Selection

**xxh3-128 (default):**

- Fast non-cryptographic hash
- Suitable for content addressing, deduplication, integrity checks
- 5-10× faster than SHA256 for large files
- Cross-language parity with gofulmen/tsfulmen

**sha256:**

- Cryptographic hash
- Use when security properties required
- Slower but provides tamper detection

**Case-insensitive:** Algorithm names accept any case (`XXH3-128`, `Sha256`, etc.)

```python
# Both work identically
FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128")
FinderConfig(calculateChecksums=True, checksumAlgorithm="XXH3-128")  # Normalized to lowercase
```

### Error Handling

If checksum calculation fails, the error is captured in metadata:

```python
for result in results:
    if result.metadata.checksum_error:
        print(f"Failed to checksum {result.relative_path}: {result.metadata.checksum_error}")
    elif result.metadata.checksum:
        print(f"{result.relative_path}: {result.metadata.checksum}")
```

Common errors:

- `"Unsupported checksum algorithm: md5"` - Invalid algorithm
- File read errors (permissions, deleted files)

## Performance

### Benchmarks (v0.1.6)

```
Scenario: 100 files × 1KB
- Without checksums: 3.34ms
- With xxh3-128:    4.61ms (+38% overhead)
- With sha256:      4.77ms (+43% overhead)

Throughput: ~23,800 files/sec with checksums
```

**Notes:**

- Overhead higher for small files (fixed Python/IO costs)
- Absolute performance remains excellent (milliseconds)
- Checksums optional (off by default)

📖 See [ADR-0010](../development/adr/ADR-0010-pathfinder-checksum-performance-acceptable-delta.md) for detailed performance analysis.

## Pattern Matching

### Include Patterns

```python
FindQuery(
    root="/project",
    include=[
        "**/*.py",          # All Python files recursively
        "*.json",           # JSON files in root only
        "src/**/*.ts",      # TypeScript in src/
        "**/__init__.py"    # Specific filename recursively
    ]
)
```

### Exclude Patterns

```python
FindQuery(
    root="/project",
    include=["**/*.py"],
    exclude=[
        "**/__pycache__/**",
        "**/node_modules/**",
        "**/.venv/**",
        "**/test_*.py"
    ]
)
```

## Advanced Usage

### Helper Methods

```python
finder = Finder()

# Find Python files specifically
results = finder.find_python_files(root="/project")

# Find by extension
results = finder.find_by_extension(root="/project", extensions=["json", "yaml"])
```

### Metadata Access

```python
for result in results:
    meta = result.metadata
    print(f"Path: {result.relative_path}")
    print(f"  Size: {meta.size} bytes")
    print(f"  Modified: {meta.modified}")  # ISO8601 timestamp
    print(f"  Permissions: {meta.permissions}")  # Octal string

    # Checksum fields (v0.1.6+)
    if meta.checksum:
        print(f"  Checksum: {meta.checksum}")
        print(f"  Algorithm: {meta.checksum_algorithm}")
```

## Cross-Language Parity

Pathfinder checksums are validated against shared test vectors:

```bash
# Validate fixture integrity
make validate-pathfinder-fixtures
```

Checksums match across:

- `pyfulmen` (Python)
- `gofulmen` (Go)
- `tsfulmen` (TypeScript/WASM)

See `tests/fixtures/pathfinder/checksum-fixtures.yaml` for test vectors.

## Schema Validation

Pathfinder results conform to Crucible schemas:

- **Config**: `schemas/crucible-py/pathfinder/v1.0.0/finder-config.schema.json`
- **Query**: `schemas/crucible-py/pathfinder/v1.0.0/find-query.schema.json`
- **Result**: `schemas/crucible-py/pathfinder/v1.0.0/path-result.schema.json`
- **Metadata**: `schemas/crucible-py/pathfinder/v1.0.0/metadata.schema.json`

## Examples

### Build Tool Integration

```python
# Find all source files that changed
finder = Finder(FinderConfig(calculateChecksums=True))
current = finder.find_files(FindQuery(root="src", include=["**/*.py"]))

# Compare against previous checksums
changed_files = [
    r for r in current
    if r.metadata.checksum != previous_checksums.get(r.relative_path)
]
```

### CI/CD Validation

```python
# Verify distribution integrity
finder = Finder(FinderConfig(calculateChecksums=True, checksumAlgorithm="sha256"))
results = finder.find_files(FindQuery(root="dist", include=["**/*"]))

for result in results:
    expected = manifest.get(result.relative_path)
    if result.metadata.checksum != expected:
        raise ValueError(f"Checksum mismatch: {result.relative_path}")
```

## Testing

Comprehensive test coverage (87 tests):

- 62 unit tests (pattern matching, config validation)
- 25 integration tests (checksums, parity validation)

Run tests:

```bash
pytest tests/unit/pathfinder/ tests/integration/test_pathfinder_*.py -v
```

## Telemetry (v0.1.6+)

Pathfinder emits telemetry metrics for observability:

- **`pathfinder_find_ms`**: File discovery operation duration (histogram)
- **`pathfinder_validation_errors`**: Schema validation failures (counter)
- **`pathfinder_security_warnings`**: Path traversal attempts and security violations (counter)

All metrics follow the [Telemetry Instrumentation Pattern](../development/telemetry-instrumentation-pattern.md).

## See Also

- [FulHash Thread Safety](../fulhash_thread_safety.md)
- [ADR-0010: Pathfinder Checksum Performance](../development/adr/ADR-0010-pathfinder-checksum-performance-acceptable-delta.md)
- [Telemetry Instrumentation Pattern](../development/telemetry-instrumentation-pattern.md)
- [Checksum Fixtures](../../tests/fixtures/pathfinder/checksum-fixtures.yaml)
