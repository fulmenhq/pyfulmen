# ADR-0009: FulHash Independent Stream Instances

**Status**: Accepted
**Date**: 2025-10-23
**Authors**: PyFulmen Architect (@pyfulmen-architect)
**Deciders**: @3leapsdave
**Version**: v0.1.6
**Related ADRs**: None

## Context

PyFulmen v0.1.6 implements the FulHash module for fast, consistent hashing across the Fulmen ecosystem. A critical architectural decision is whether `StreamHasher` instances should use a singleton pattern or create independent instances for each `stream()` call.

### Requirements

1. **Thread Safety**: Support concurrent hashing in multi-threaded applications
2. **State Isolation**: Prevent state pollution between concurrent operations
3. **Developer Experience**: Intuitive API that works correctly by default
4. **Cross-Language Consistency**: Pattern must translate to gofulmen and tsfulmen
5. **Correctness**: Produce deterministic results regardless of execution order

### Background: TypeScript Singleton Bug

The original TypeScript FulHash implementation used a singleton hasher, which caused bugs in concurrent scenarios:

```typescript
// ❌ PROBLEMATIC: Singleton pattern
class FulHash {
  private static hasher = new XXH3(); // Shared singleton

  static stream(): Hasher {
    return this.hasher; // Returns same instance
  }
}

// Result: Concurrent calls corrupted each other's state
```

This experience highlighted the danger of shared mutable state in hashing utilities and informed the Python design.

### API Surface

```python
from pyfulmen.fulhash import stream, StreamHasher, Algorithm

# Question: Does stream() return singleton or new instance?
hasher = stream(Algorithm.XXH3_128)
hasher.update(b"chunk 1")
hasher.update(b"chunk 2")
digest = hasher.digest()
```

## Decision

**We choose: Independent Instances**

Each call to `stream()` creates a **new, independent `StreamHasher` instance** with isolated internal state. No singleton pattern.

### Implementation

```python
# src/pyfulmen/fulhash/_stream.py

def stream(algorithm: Algorithm = Algorithm.XXH3_128) -> StreamHasher:
    """Create a new independent streaming hasher.

    Each call returns a new instance with isolated state.
    Safe for concurrent use across multiple threads.
    """
    return StreamHasher(algorithm)  # New instance, not singleton


class StreamHasher:
    """Streaming hash computation with independent state."""

    def __init__(self, algorithm: Algorithm):
        """Initialize new hasher with isolated state."""
        self._algorithm = algorithm
        if algorithm == Algorithm.XXH3_128:
            self._hasher = xxhash.xxh3_128()  # New backend instance
        else:
            self._hasher = hashlib.sha256()   # New backend instance

    def update(self, data: bytes) -> None:
        """Update hash with data chunk."""
        self._hasher.update(data)  # Updates this instance's state only

    def digest(self) -> Digest:
        """Finalize and return digest."""
        return Digest(
            algorithm=self._algorithm.value,
            hex=self._hasher.hexdigest(),
            bytes=self._hasher.digest(),
        )

    def reset(self) -> None:
        """Reset hasher state for reuse."""
        # Creates fresh backend instance
        if self._algorithm == Algorithm.XXH3_128:
            self._hasher = xxhash.xxh3_128()
        else:
            self._hasher = hashlib.sha256()
```

## Rationale

### 1. Explicit Thread Safety Without Locking

Independent instances eliminate the need for locks or synchronization:

```python
# ✅ SAFE: Each thread gets independent hasher
import threading

def hash_in_thread(data):
    hasher = stream()  # New instance per thread
    hasher.update(data)
    return hasher.digest()

threads = [
    threading.Thread(target=hash_in_thread, args=(data,))
    for data in chunks
]
```

**Validation**: 14 concurrency tests, 1,200+ operations, zero state corruption.

### 2. Zero State Pollution Risk

No shared mutable state means concurrent operations cannot interfere:

```python
# ✅ SAFE: Concurrent streaming with independent hashers
hasher1 = stream()
hasher2 = stream()

# Thread 1
hasher1.update(b"thread 1 data")

# Thread 2 (concurrent)
hasher2.update(b"thread 2 data")

# Both produce correct results
digest1 = hasher1.digest()  # Correct for thread 1
digest2 = hasher2.digest()  # Correct for thread 2
```

**Test Evidence**: `test_no_state_pollution_streaming` with 20 threads and deliberate delays detected zero pollution.

### 3. Correct by Default

Developers don't need to think about thread safety or state management:

```python
# Works correctly in single-threaded code
hasher = stream()
hasher.update(b"data")
digest = hasher.digest()

# Works correctly in multi-threaded code (same API)
with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(hash_worker, data_chunks)
```

### 4. Learned from Ecosystem Experience

The TypeScript singleton bug provided clear evidence that shared state causes production issues. Python implementation explicitly avoids this anti-pattern.

### 5. Backend Support

Both `xxhash` and `hashlib` support independent instances:

```python
# xxhash: Each call creates new instance
hasher1 = xxhash.xxh3_128()
hasher2 = xxhash.xxh3_128()
# Independent state ✅

# hashlib: Each call creates new instance
hasher1 = hashlib.sha256()
hasher2 = hashlib.sha256()
# Independent state ✅
```

## Alternatives Considered

### Alternative 1: Singleton with Locking

Use a singleton hasher protected by locks:

```python
import threading

class StreamHasher:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, algorithm):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def update(self, data):
        with self._lock:
            self._hasher.update(data)
```

**Pros**:

- Single instance (minimal memory)

**Cons**:

- ❌ Performance bottleneck (locks serialize concurrent operations)
- ❌ Complex state management (need to track ownership)
- ❌ Reset() affects all users
- ❌ Hard to test (global state pollution)
- ❌ Not composable (can't use multiple algorithms concurrently)

**Rejected because**: Performance and correctness trade-offs unacceptable. Locking serializes concurrent operations, defeating the purpose of concurrency.

### Alternative 2: Thread-Local Storage

Use `threading.local()` for per-thread instances:

```python
import threading

_local = threading.local()

def stream(algorithm):
    if not hasattr(_local, 'hasher'):
        _local.hasher = StreamHasher(algorithm)
    return _local.hasher
```

**Pros**:

- Automatic per-thread isolation

**Cons**:

- ❌ Hidden state management (magic behavior)
- ❌ Doesn't work with async/await
- ❌ Can't have multiple concurrent hashers per thread
- ❌ Hard to test and debug
- ❌ Doesn't translate to Go/TypeScript

**Rejected because**: Hidden magic and limited flexibility. Developers should explicitly control instance lifecycle.

### Alternative 3: Context Manager Pattern

Require explicit context manager for streaming:

```python
with stream() as hasher:
    hasher.update(b"data")
    digest = hasher.digest()
```

**Pros**:

- Explicit lifecycle management
- Clear scope boundaries

**Cons**:

- ⚠️ More boilerplate for simple use cases
- ⚠️ Doesn't prevent state pollution (still need independent instances)
- ⚠️ Context manager doesn't add safety value

**Rejected because**: Adds complexity without safety benefits. Independent instances already provide thread safety.

## Consequences

### Positive

- ✅ **Thread-Safe by Design**: Zero synchronization needed, no locks
- ✅ **State Isolation**: Concurrent operations cannot interfere
- ✅ **Simple API**: Same code works in single and multi-threaded contexts
- ✅ **Testable**: Each test creates independent instances
- ✅ **Deterministic**: Results independent of execution order
- ✅ **Performance**: No lock contention, full parallelism
- ✅ **Cross-Language Pattern**: Translates directly to Go and TypeScript

### Negative

- ⚠️ **Memory Overhead**: Multiple instances use more memory than singleton
  - **Mitigation**: StreamHasher is lightweight (<100 bytes per instance)
  - **Analysis**: For 1,000 concurrent operations: ~100KB total (negligible)
- ⚠️ **Developer Education**: Must document that sharing instances is unsafe
  - **Mitigation**: Clear docs and examples showing correct patterns
  - **Prevention**: Thread safety guide with anti-patterns

### Neutral

- 📝 **Instance Lifecycle**: Developers responsible for instance management
- 📝 **Reuse Pattern**: Can reuse instance via `.reset()` if needed

## Validation

### Concurrency Test Coverage

**14 dedicated concurrency tests** validate thread safety:

1. **StreamHasher Independence** (3 tests):
   - `test_concurrent_independent_hashers`: 10 threads with independent instances
   - `test_concurrent_same_data_different_hashers`: 20 threads hashing same data
   - `test_concurrent_streaming_chunks`: 10 threads with multi-chunk streaming

2. **Block Hashing Concurrency** (3 tests):
   - `test_concurrent_hash_bytes`: 100 operations across 10 threads
   - `test_concurrent_hash_string`: 100 operations across 10 threads
   - `test_concurrent_mixed_algorithms`: 100 operations mixing algorithms

3. **File Hashing Concurrency** (2 tests):
   - `test_concurrent_file_hashing_different_files`: 10 files × 5 threads
   - `test_concurrent_file_hashing_same_file`: 20 threads reading same file

4. **State Pollution Detection** (2 tests):
   - `test_no_state_pollution_streaming`: 20 threads with deliberate delays
   - `test_no_pollution_with_reset`: Mixed reset() and non-reset() operations

5. **Digest Immutability** (1 test):
   - `test_digest_concurrent_reads`: 50 concurrent readers

6. **Universal Dispatcher** (1 test):
   - `test_concurrent_mixed_types`: Mixed bytes/string/file types

7. **Stress Tests** (2 tests):
   - `test_sustained_concurrent_hashing`: 1,000 operations sustained load
   - `test_memory_safety_under_load`: 200 operations with 1MB files

**Results**: All 156 tests passing, zero errors, zero state corruption

### Stress Test Results

```
Sustained Concurrent Hashing:
- Operations: 1,000 (10 threads × 100 ops)
- Throughput: 121,051 ops/sec
- Errors: 0
- State Corruption: None

Memory Safety Under Load:
- Operations: 200 (20 threads × 10 hashes)
- File Size: 1MB
- All Results Identical: ✅
- Memory Corruption: None
- File Handle Leaks: None
```

## Cross-Language Translation

### Go (gofulmen)

```go
package fulhash

// StreamHasher with independent state
type StreamHasher struct {
    algorithm Algorithm
    hasher    hash.Hash  // Independent backend
}

// Stream creates new independent hasher
func Stream(algorithm Algorithm) *StreamHasher {
    return &StreamHasher{
        algorithm: algorithm,
        hasher:    createBackend(algorithm),  // New instance
    }
}

// Update adds data to hash
func (s *StreamHasher) Update(data []byte) {
    s.hasher.Write(data)  // Updates this instance only
}
```

**Translation**: Direct mapping. Go's value semantics and pointer types make independence explicit.

### TypeScript (tsfulmen)

```typescript
// StreamHasher with independent state
class StreamHasher {
  private algorithm: Algorithm;
  private hasher: Hash; // Independent backend

  constructor(algorithm: Algorithm) {
    this.algorithm = algorithm;
    this.hasher = createBackend(algorithm); // New instance
  }

  update(data: Uint8Array): void {
    this.hasher.update(data); // Updates this instance only
  }
}

// stream creates new independent hasher
export function stream(
  algorithm: Algorithm = Algorithm.XXH3_128,
): StreamHasher {
  return new StreamHasher(algorithm); // New instance, not singleton
}
```

**Translation**: Direct mapping. Explicit `new` keyword makes independence clear. Fixes original TypeScript singleton bug.

## Anti-Patterns (What NOT to Do)

### ❌ UNSAFE: Sharing StreamHasher Across Threads

```python
# DON'T DO THIS
hasher = stream()  # Single shared instance

def worker(data):
    hasher.update(data)  # Race condition!
    return hasher.digest()

# Result: Undefined behavior, corrupted hashes
```

**Fix**: Create new hasher per thread or use stateless block hashing:

```python
# ✅ FIX 1: Independent hashers
def worker(data):
    hasher = stream()  # New instance per thread
    hasher.update(data)
    return hasher.digest()

# ✅ FIX 2: Stateless block hashing
def worker(data):
    return hash_bytes(data)  # Stateless, always safe
```

### ❌ UNSAFE: Module-Level Shared Hasher

```python
# DON'T DO THIS
_hasher = stream()  # Module-level singleton

def hash_data(data):
    _hasher.update(data)  # Shared state!
    return _hasher.digest()
```

**Fix**: Create hasher inside function or pass as parameter:

```python
# ✅ FIX: Create per-call
def hash_data(data):
    hasher = stream()
    hasher.update(data)
    return hasher.digest()
```

## Documentation Strategy

### 1. Thread Safety Guide

Created `docs/fulhash_thread_safety.md` with:

- Thread safety guarantees
- Implementation details explaining why it's safe
- Anti-patterns (what NOT to do)
- Stress test results
- Production recommendations

### 2. API Documentation

All public functions include thread safety notes:

```python
def stream(algorithm: Algorithm = Algorithm.XXH3_128) -> StreamHasher:
    """Create a new independent streaming hasher.

    Each call returns a new instance with isolated state.
    Safe for concurrent use across multiple threads.

    Thread Safety:
        This function creates independent instances. Each StreamHasher
        maintains isolated state and can be used concurrently without
        synchronization.

    Examples:
        Single-threaded streaming:
            >>> hasher = stream()
            >>> hasher.update(b"chunk 1")
            >>> hasher.update(b"chunk 2")
            >>> digest = hasher.digest()

        Multi-threaded (each thread gets independent hasher):
            >>> def worker(data):
            ...     hasher = stream()
            ...     hasher.update(data)
            ...     return hasher.digest()
    """
```

### 3. Examples

`examples/fulhash_demo.py` includes concurrency examples demonstrating correct patterns.

## References

- **Implementation**: `src/pyfulmen/fulhash/_stream.py`
- **Tests**: `tests/unit/fulhash/test_concurrency.py`
- **Thread Safety Doc**: `docs/fulhash_thread_safety.md`
- **Crucible Standard**: `docs/crucible-py/standards/library/modules/fulhash.md`
- **Related Work**: TypeScript singleton bug analysis (internal notes)

## Future Considerations

### When to Reconsider

Reconsider this decision if:

1. **Memory constraints** become critical (would need <1M concurrent operations)
2. **Object pooling** is needed for extreme performance (unlikely given current throughput)
3. **Backend changes** make independent instances prohibitively expensive

**Current Assessment**: None of these conditions are expected. Independent instances remain the correct choice.

### Potential Enhancements

Future non-breaking additions that preserve independence:

1. **Object Pooling**: Optional pool for high-frequency use cases:

   ```python
   with hasher_pool.get() as hasher:
       hasher.update(data)
       digest = hasher.digest()
   # Hasher returned to pool after reset
   ```

2. **Async Support**: Async streaming for I/O-bound scenarios:

   ```python
   async def stream_async(algorithm):
       return AsyncStreamHasher(algorithm)  # Still independent
   ```

3. **Batch API**: Convenience for multiple inputs:
   ```python
   digests = hash_batch([data1, data2, data3])  # Uses independent hashers
   ```

All enhancements would preserve the core principle: **independent instances by default**.

## Revision History

| Date       | Version | Description                         | Author             |
| ---------- | ------- | ----------------------------------- | ------------------ |
| 2025-10-23 | 1.0     | Initial decision and implementation | PyFulmen Architect |

---

**Decision**: Accepted and implemented in PyFulmen v0.1.6
**Validation**: 14 concurrency tests, 1,200+ operations, 100% passing
**Status**: Production-ready
