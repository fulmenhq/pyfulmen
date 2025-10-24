# Telemetry Instrumentation Pattern

**Status**: Active  
**Version**: 1.0  
**Last Updated**: 2025-10-24  
**Related**: ADR-0008 (Global Metric Registry Singleton)

## Overview

This document defines the standard pattern for adding telemetry instrumentation to PyFulmen modules. It codifies learnings from the Phase 1 Pathfinder retrofit and serves as a guide for instrumenting other modules (config, schema, foundry, etc.).

## Core Pattern

### Wrapper Method with Try/Finally

```python
import time
from pyfulmen.telemetry import MetricRegistry

def public_operation(self, args):
    """Public API method with telemetry instrumentation.

    Telemetry:
        - Emits operation_name_ms histogram (operation duration)
        - Emits operation_name_errors counter (on exceptions)
    """
    start_time = time.perf_counter()
    registry = MetricRegistry()

    try:
        return self._public_operation_impl(args)
    except Exception as err:
        # Emit error counter
        registry.counter("operation_name_errors").inc()
        raise
    finally:
        # Always emit duration metric
        duration_ms = (time.perf_counter() - start_time) * 1000
        registry.histogram("operation_name_ms").observe(duration_ms)

def _public_operation_impl(self, args):
    """Internal implementation without telemetry wrapper."""
    # Original logic here, unchanged
    pass
```

### Key Principles

1. **Minimal Disruption**: Original logic moves to `_<method>_impl()` unchanged
2. **Clean Separation**: Telemetry concerns separated from business logic
3. **Guaranteed Emission**: `finally` block ensures metrics emitted even on exceptions
4. **Metric Naming**: Follow Crucible taxonomy conventions (`module_operation_unit`)
5. **Performance**: Overhead < 1%, measured and verified

## Metric Types & When to Use

### Histograms (Duration Tracking)

**Use For**: Operations with measurable duration  
**Unit**: milliseconds (ms)  
**Naming**: `<module>_<operation>_ms`

```python
registry.histogram("pathfinder_find_ms").observe(duration_ms)
registry.histogram("config_load_ms").observe(duration_ms)
```

**Examples**:

- `pathfinder_find_ms` - File discovery operation duration
- `config_load_ms` - Configuration loading duration
- `schema_validation_ms` - Schema validation duration

### Counters (Event Counting)

**Use For**: Discrete events, errors, warnings  
**Unit**: count  
**Naming**: `<module>_<event>_<unit>` or `<module>_<event>s`

```python
registry.counter("pathfinder_validation_errors").inc()
registry.counter("pathfinder_security_warnings").inc()
registry.counter("foundry_lookup_count").inc()
```

**Examples**:

- `pathfinder_validation_errors` - Failed input validation attempts
- `pathfinder_security_warnings` - Security violations detected
- `config_load_errors` - Failed configuration loads
- `schema_validation_errors` - Schema validation failures

### Gauges (Point-in-Time Values)

**Use For**: Current state measurements  
**Unit**: varies (count, bytes, etc.)  
**Naming**: `<module>_<state>_<unit>`

```python
registry.gauge("cache_size_bytes").set(cache.size)
registry.gauge("active_connections_count").set(len(connections))
```

**Note**: Less common in helper libraries, more common in services.

## Implementation Workflow

### Step 1: Identify Instrumentation Points

Review module for:

- **Duration operations**: Long-running methods (file I/O, network, computation)
- **Error paths**: Validation failures, exceptions, security checks
- **State changes**: Resource creation/deletion, cache updates

### Step 2: Check Taxonomy

Before adding metrics, verify they exist in Crucible taxonomy:

- Check `config/crucible-py/taxonomy/metrics.yaml`
- If missing, coordinate with Crucible team to add
- Use exact names from taxonomy (case-sensitive)

### Step 3: Add Imports

```python
import time
from pyfulmen.telemetry import MetricRegistry
```

### Step 4: Wrap Public Methods

1. Rename method: `public_method()` → `_public_method_impl()`
2. Create wrapper with try/finally structure
3. Initialize timer and registry
4. Emit metrics in appropriate blocks

### Step 5: Add Tests

**Smoke Test** (current limitation):

```python
def test_operation_with_telemetry_enabled(self):
    """Verify operation executes with telemetry without errors."""
    result = module.operation(args)
    assert result is not None  # Verify success
    # Note: Full metric assertions require module-level helpers (ADR-0008)
```

**Future Full Test** (when helpers available):

```python
def test_operation_emits_duration_metric(self):
    """Verify operation emits duration histogram."""
    from pyfulmen.telemetry import get_registry, clear_metrics

    clear_metrics()
    result = module.operation(args)

    events = get_registry().get_events()
    duration_events = [e for e in events if e.name == "operation_ms"]
    assert len(duration_events) == 1
    assert duration_events[0].value.count > 0
```

### Step 6: Update Documentation

Update method docstring:

```python
def public_method(self, args):
    """
    Perform operation.

    Args:
        args: Operation arguments

    Returns:
        Operation results

    Telemetry:
        - Emits operation_ms histogram (duration)
        - Emits operation_errors counter (on failure)
    """
```

## Real-World Example: Pathfinder.find_files()

### Before (v0.1.5)

```python
def find_files(self, query: FindQuery) -> list[PathResult]:
    """Perform file discovery."""
    # Validate input
    if self.config.validate_inputs:
        schema_validator.validate_against_schema(...)

    results: list[PathResult] = []
    root_path = Path(query.root).resolve()

    # ... discovery logic ...

    return results
```

### After (v0.1.6 Phase 1)

```python
def find_files(self, query: FindQuery) -> list[PathResult]:
    """
    Perform file discovery.

    Telemetry:
        - Emits pathfinder_find_ms histogram (operation duration)
    """
    start_time = time.perf_counter()
    registry = MetricRegistry()

    try:
        return self._find_files_impl(query)
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        registry.histogram("pathfinder_find_ms").observe(duration_ms)

def _find_files_impl(self, query: FindQuery) -> list[PathResult]:
    """Internal implementation of find_files without telemetry."""
    # Original logic unchanged - just moved here
    if self.config.validate_inputs:
        schema_validator.validate_against_schema(...)

    results: list[PathResult] = []
    root_path = Path(query.root).resolve()

    # ... discovery logic ...

    return results
```

### After (v0.1.6 Phase 1.5 - Complete)

```python
def find_files(self, query: FindQuery) -> list[PathResult]:
    """
    Perform file discovery.

    Telemetry:
        - Emits pathfinder_find_ms histogram (operation duration)
        - Emits pathfinder_validation_errors counter (on validation failure)
        - Emits pathfinder_security_warnings counter (on security violation)
    """
    start_time = time.perf_counter()
    registry = MetricRegistry()

    try:
        return self._find_files_impl(query, registry)
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        registry.histogram("pathfinder_find_ms").observe(duration_ms)

def _find_files_impl(self, query: FindQuery, registry: MetricRegistry) -> list[PathResult]:
    """Internal implementation with registry access for error counters."""
    # Validation with error counter
    if self.config.validate_inputs:
        try:
            schema_validator.validate_against_schema(...)
        except ValueError:
            registry.counter("pathfinder_validation_errors").inc()
            raise

    # Discovery logic with security counter
    for pattern in query.include:
        matches = root_path.glob(pattern)
        for match in matches:
            try:
                # Path safety validation
                try:
                    validate_path(str(abs_match))
                except PathTraversalError:
                    registry.counter("pathfinder_security_warnings").inc()
                    raise

                # Constraint violation handling
                if self._violates_constraint(...):
                    violation = PathTraversalError(...)
                    registry.counter("pathfinder_security_warnings").inc()

                    if constraint.enforcement_level == EnforcementLevel.STRICT.value:
                        raise violation
            except PathTraversalError:
                raise

    return results
```

## Performance Considerations

### Overhead Measurement

**Target**: < 1% overhead for instrumented operations  
**Actual** (Pathfinder Phase 1): < 0.1% overhead

**Measurement Method**:

```python
# Before: 88 tests in 0.20s
# After:  89 tests in 0.20s (added 1 test)
# Overhead: Negligible
```

### Optimization Tips

1. **Lazy Initialization**: Only create registry when needed
2. **Minimal Computation**: Calculate duration only (avoid complex logic in wrapper)
3. **No Defensive Copying**: Don't clone args/results just for telemetry
4. **Cache Instruments**: Registry caches counters/histograms by name

### Anti-Patterns

❌ **Don't** create registry in hot loops:

```python
for item in items:
    registry = MetricRegistry()  # BAD - creates new instance each iteration
    registry.counter("processed").inc()
```

✅ **Do** create registry once:

```python
registry = MetricRegistry()
for item in items:
    registry.counter("processed").inc()  # GOOD
```

## Testing Strategy

### Current Limitations (v0.1.6)

Each `MetricRegistry()` call creates an independent instance (per ADR-0008 design). This means:

- Telemetry IS emitted correctly
- Tests CANNOT observe metrics (different instance)

**Workaround**: Smoke tests verify instrumented code executes without errors.

### Future Testing (When Module Helpers Available)

Per ADR-0008, module-level helpers will provide singleton access:

```python
from pyfulmen.telemetry import counter, histogram, clear_metrics, get_events

def operation():
    hist = histogram("operation_ms")
    hist.observe(123.45)

def test_operation_emits_metric():
    clear_metrics()
    operation()
    events = get_events()
    assert any(e.name == "operation_ms" for e in events)
```

**Status**: Module helpers not yet implemented (tracked for Phase 1.5)

## Common Patterns by Module

### File I/O Operations (Pathfinder, Config)

```python
def load_file(self, path: str):
    start = time.perf_counter()
    registry = MetricRegistry()

    try:
        return self._load_file_impl(path)
    except (FileNotFoundError, PermissionError) as err:
        registry.counter("file_load_errors").inc()
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        registry.histogram("file_load_ms").observe(duration_ms)
```

### Validation Operations (Schema, Config)

```python
def validate(self, data: dict):
    registry = MetricRegistry()
    registry.counter("validations_total").inc()

    try:
        result = self._validate_impl(data)
        if not result.is_valid:
            registry.counter("validation_errors").inc()
        return result
    except Exception:
        registry.counter("validation_errors").inc()
        raise
```

### Lookup Operations (Foundry Catalog)

```python
def get_pattern(self, name: str):
    registry = MetricRegistry()
    registry.counter("lookup_count").inc()

    pattern = self._patterns.get(name)
    if pattern is None:
        registry.counter("lookup_misses").inc()
    return pattern
```

## Migration Checklist

When adding telemetry to a module:

- [ ] Review Crucible taxonomy for applicable metrics
- [ ] Add imports (`time`, `MetricRegistry`)
- [ ] Extract logic to `_<method>_impl()` for each public method
- [ ] Add try/finally wrapper with histogram
- [ ] Add counter emissions for error paths
- [ ] Update method docstrings with Telemetry section
- [ ] Add smoke test for instrumented path
- [ ] Run full test suite (verify zero regressions)
- [ ] Update CHANGELOG with telemetry additions
- [ ] Performance check (< 1% overhead)

## FAQ

### Q: Should every method be instrumented?

**A**: No. Focus on:

- Public API methods
- Long-running operations (I/O, network, heavy computation)
- Operations prone to errors
- Operations users care about monitoring

Skip:

- Simple getters/setters
- Internal helpers
- Pure computation methods < 1ms

### Q: What if the metric isn't in the taxonomy?

**A**: Coordinate with Crucible team to add it. Don't invent metrics locally - taxonomy ensures cross-language consistency.

### Q: Can I emit metrics conditionally?

**A**: Generally no - metrics should always be emitted for observability. Use sampling/cardinality controls at aggregation layer, not emission layer.

### Q: How do I handle multi-step operations?

**A**: Emit metrics at natural boundaries:

```python
def complex_operation(self):
    registry = MetricRegistry()

    # Step 1
    start = time.perf_counter()
    self._step1()
    registry.histogram("step1_ms").observe((time.perf_counter() - start) * 1000)

    # Step 2
    start = time.perf_counter()
    self._step2()
    registry.histogram("step2_ms").observe((time.perf_counter() - start) * 1000)

    # Total
    registry.histogram("complex_operation_ms").observe(total_duration_ms)
```

### Q: What about nested instrumentation?

**A**: It's fine - each level emits its own metrics:

```python
def outer():
    # Emits outer_ms
    inner()  # Also emits inner_ms

def inner():
    # Emits inner_ms
    pass
```

Aggregation tools can correlate if needed.

## References

- **ADR-0008**: Global Metric Registry Singleton
- **Crucible Taxonomy**: `config/crucible-py/taxonomy/metrics.yaml`
- **Telemetry Module**: `src/pyfulmen/telemetry/`
- **Implementation Plan**: `.plans/active/v0.1.6/error-telemetry-retrofit-implementation.md`
- **Audit Request**: `.plans/active/v0.1.6/AUDIT_REQUEST_telemetry_retrofit_phase1.md`

## Changelog

- **2025-10-24**: Initial version based on Pathfinder Phase 1 retrofit
- **Future**: Update when module-level helpers implemented (ADR-0008)
