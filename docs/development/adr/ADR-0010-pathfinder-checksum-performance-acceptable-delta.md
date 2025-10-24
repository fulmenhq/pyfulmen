# ADR-0010: Pathfinder Checksum Performance - Acceptable Delta from Target

**Status**: Accepted  
**Date**: 2025-10-24  
**Deciders**: PyFulmen Architect (@pyfulmen-architect), @3leapsdave  
**Tags**: `performance`, `pathfinder`, `fulhash`, `implementation-decision`

## Context

The Pathfinder FulHash checksum integration (v0.1.6) aimed for <10% performance overhead when calculating checksums. Benchmarking revealed actual overhead of 38-88% for small files (1-10KB), significantly exceeding the target.

### Initial Performance Target

- **Goal**: <10% overhead for xxh3-128 checksums vs baseline file discovery
- **Rationale**: Minimize impact on file discovery operations
- **Measurement**: Comparative benchmarking (baseline vs checksums enabled)

### Measured Performance

```
Scenario: 100 files × 1KB
- Baseline (no checksums): 3.34ms (100 files)
- XXH3-128 checksums:      4.61ms (100 files)
- Measured overhead:       +38.2%

Scenario: 100 files × 10KB
- Baseline (no checksums): 2.57ms
- XXH3-128 checksums:      4.84ms
- Measured overhead:       +88.3%

Scenario: 500 files × 1KB
- Baseline (no checksums): 11.96ms
- XXH3-128 checksums:      21.49ms
- Measured overhead:       +79.6%
```

## Decision

**We accept the current performance characteristics as sufficient for v0.1.6**, despite not meeting the <10% overhead target, for the following reasons:

### 1. Absolute Performance Remains Excellent

The overhead is measured in **milliseconds**, not seconds:

- 100 files with checksums: 4-5ms total
- 500 files with checksums: 21ms total
- **Throughput: ~23,800 files/second with checksums**

Real-world impact is negligible for typical use cases (directory scanning, file discovery operations).

### 2. Overhead Source Analysis

Detailed profiling reveals the overhead breakdown per file:

```
Component Breakdown (1KB file):
- File I/O (open/read/close):   0.0132ms  (59%)
- XXH3-128 hashing (pure):      0.0051ms  (23%)
- PathMetadata construction:    0.0014ms  (6%)
- File stat:                    0.0026ms  (12%)
----------------------------------------
Total per-file:                 0.0224ms

Pathfinder Baseline Overhead:   0.0309ms per file
(Pattern matching, validation, model construction)
```

**Key insight**: The 0.02ms checksum overhead is small in absolute terms but large relative to the already-fast baseline (0.03ms Pathfinder overhead). This is a **percentage measurement artifact**, not a functional performance problem.

### 3. Fixed Cost Dominance

For small files (1-10KB), overhead is dominated by **fixed costs**:

- Python function call overhead
- File descriptor management
- Pydantic model construction and validation
- Object allocation (Digest, PathMetadata)

These fixed costs are **independent of file size** and don't scale with content. Larger files show better amortization:

```
File Size vs Pure Hash Time:
- 100 bytes:  0.0061ms (hash time)
- 1 KB:       0.0051ms
- 10 KB:      0.0065ms
- 100 KB:     0.0120ms (only 2× for 10× size)
```

The xxhash C extension is **extremely fast**; Python overhead is the bottleneck.

### 4. Cross-Language Comparison Context

- **tsfulmen**: Initially had similar issue, switched to WASM for browser performance
- **gofulmen**: Benefits from compiled language + minimal runtime overhead
- **pyfulmen**: Inherits Python's dynamic typing and memory management overhead

This is an **expected trade-off** for Python's developer experience and ecosystem integration benefits.

### 5. Production Use Case Alignment

Pathfinder checksums are designed for:

- **Discovery operations** (not hot-path serving)
- **Opt-in feature** (default: off)
- **CI/CD validation** (where 20ms is trivial)
- **Build tooling** (developer-facing, latency-tolerant)

Users requiring maximum performance can:

- Disable checksums (default behavior)
- Use larger batch sizes to amortize overhead
- Profile their specific workload

### 6. Functionality Correctness Verified

Despite performance delta:

- ✅ All 87 pathfinder tests passing
- ✅ Cross-language parity validated (checksums match FulHash reference)
- ✅ Both xxh3-128 and sha256 produce correct results
- ✅ Streaming works correctly for all file sizes
- ✅ Error handling robust

**Performance gap does not affect correctness.**

## Implications

### Documentation Requirements

1. **User-Facing Docs**: Document overhead characteristics
   - Note that overhead is higher for small files
   - Provide absolute time benchmarks (not just percentages)
   - Emphasize opt-in nature and use case alignment

2. **API Docs**: Clarify performance trade-offs
   - `calculateChecksums=False` (default) for maximum performance
   - `calculateChecksums=True` for integrity verification
   - Recommend batch operations for large repositories

3. **README**: Add performance section
   - Benchmark results table
   - Use case recommendations
   - Comparison to other implementations

### Future Optimization Opportunities (v0.2.0+)

If performance becomes critical:

1. **Batch Processing**: Amortize fixed costs across multiple files
2. **C Extension**: Inline Pathfinder logic into native code
3. **Caching**: Skip checksums for unchanged files (mtime-based)
4. **Parallel Processing**: Multi-threaded scanning for large directories
5. **Profiling**: py-spy analysis on real-world repositories

### Non-Requirements

We explicitly **do not** require:

- Matching gofulmen's compiled performance in Python
- Matching the <10% target for small files
- Optimizing for hot-path serving scenarios
- Competing with specialized native tools

## Alternatives Considered

### Alternative 1: Pure Python xxhash Implementation

- **Rejected**: Would be 10-100× slower than C extension
- No benefit over current approach

### Alternative 2: Inline C Extension for Pathfinder

- **Deferred**: Adds complexity, maintenance burden
- Not justified by current use cases
- Reconsider if users report performance issues

### Alternative 3: Async I/O

- **Deferred**: Adds API complexity
- Marginal benefit for synchronous file operations
- Most time is in Python overhead, not I/O wait

### Alternative 4: Loosen Performance Target

- **Accepted**: This ADR documents why current performance is acceptable
- Revise target to "acceptable absolute performance" vs "<10% overhead"

## Validation

### Acceptance Criteria Met

✅ Functionality correct (all tests passing)  
✅ Cross-language parity validated  
✅ Absolute performance acceptable (milliseconds for hundreds of files)  
✅ Overhead source understood and documented  
✅ Use case alignment confirmed

### Performance Baseline Established

Benchmark script (`scripts/benchmark_pathfinder_checksums.py`) provides reproducible measurements for:

- Regression detection
- Cross-version comparison
- User performance expectations

### Fixture Validation Available

Validation script (`scripts/validate_pathfinder_fixtures.py`) ensures:

- Checksum correctness maintained
- Cross-language consistency
- No silent performance optimizations that break parity

## References

- Original Performance Target: `.plans/active/v0.1.6/pathfinder_fulhash_extension.md` (Phase 4)
- Benchmark Script: `scripts/benchmark_pathfinder_checksums.py`
- Profiling Script: `scripts/profile_pathfinder_overhead.py`
- FulHash Integration: ADR-0009 (FulHash thread safety)
- Cross-Language Parity: `tests/fixtures/pathfinder/checksum-fixtures.yaml`

## Notes

- This decision applies to v0.1.6 (alpha phase, 93% coverage target)
- Performance requirements may be revisited for GA/LTS releases
- User feedback will inform future optimization priorities
- xxhash C extension performance is excellent; Python overhead is the bottleneck

---

**Decision Record**: Documenting performance reality vs aspirational target. Current implementation prioritizes correctness, maintainability, and developer experience over micro-optimization for a non-critical code path.
