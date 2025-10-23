# ADR-0008: Global Metric Registry Singleton Pattern

**Status**: Accepted
**Date**: 2025-10-23
**Authors**: PyFulmen Architect (@pyfulmen-architect)
**Deciders**: @3leapsdave
**Version**: v0.1.6
**Note**: Renumbered from ADR-0010 after original ADR-0008 and ADR-0009 promoted to Crucible 2025.10.3

## Context

PyFulmen implements telemetry-metrics with a `MetricRegistry` class that manages metric instruments (counters, gauges, histograms) and records metric events. A key architectural decision is whether to use a global singleton registry or require explicit registry instantiation and dependency injection.

### Requirements

1. **Simple API**: Minimize boilerplate for common use cases
2. **Thread Safety**: Support concurrent metric recording across multiple threads
3. **Testability**: Enable test isolation with separate registries
4. **Cross-Module**: Allow metrics to be recorded from multiple modules
5. **Cross-Language Consistency**: API patterns should translate to gofulmen and tsfulmen

### Metric Registry Responsibilities

```python
class MetricRegistry:
    def counter(self, name: str) -> Counter:
        """Get or create a counter instrument."""

    def gauge(self, name: str) -> Gauge:
        """Get or create a gauge instrument."""

    def histogram(self, name: str, buckets: Optional[list[float]] = None) -> Histogram:
        """Get or create a histogram instrument."""

    def get_events(self) -> list[MetricEvent]:
        """Get all recorded events."""

    def clear(self) -> None:
        """Clear all events and instruments."""
```

## Options Considered

### Option 1: Explicit Registry (Dependency Injection)

Require users to create and pass registry instances explicitly:

```python
# User code
registry = telemetry.MetricRegistry()
counter = registry.counter("schema_validations")
counter.inc()

# Pass registry to functions
def process_config(registry: MetricRegistry):
    histogram = registry.histogram("config_load_ms")
    histogram.observe(42.5)
```

**Pros**:

- Explicit dependencies (testable, clear)
- No global state
- Multiple independent registries

**Cons**:

- Boilerplate for simple use cases
- Registry must be passed through function chains
- Harder to adopt in existing code

### Option 2: Global Singleton Only

Provide only a global singleton registry:

```python
# Built-in singleton
_registry = MetricRegistry()

def counter(name: str) -> Counter:
    return _registry.counter(name)

# User code
telemetry.counter("schema_validations").inc()
```

**Pros**:

- Zero boilerplate for simple use cases
- Easy adoption
- Cross-module metrics work automatically

**Cons**:

- Global state makes testing harder
- Cannot have multiple independent registries
- Test isolation requires manual cleanup

### Option 3: Global Singleton + Custom Registry Support (Hybrid)

Provide a global default registry with helper functions, but allow custom registries when needed:

```python
# Global default registry (internal)
_default_registry = MetricRegistry()

# Helper functions use default registry
def counter(name: str) -> Counter:
    return _default_registry.counter(name)

def gauge(name: str) -> Gauge:
    return _default_registry.gauge(name)

# Export MetricRegistry class for custom instances
class MetricRegistry:
    # ... implementation

# User code - Simple case (default registry)
telemetry.counter("schema_validations").inc()

# User code - Testing (custom registry)
test_registry = telemetry.MetricRegistry()
test_counter = test_registry.counter("test_metric")
test_counter.inc()
events = test_registry.get_events()  # Isolated from default registry
```

**Pros**:

- Simple API for common cases
- Testable via custom registries
- Explicit when needed
- Best of both worlds

**Cons**:

- Two patterns to understand (default vs custom)
- Default registry cleanup needed in some tests

## Decision

**We choose Option 3: Global Singleton + Custom Registry Support**

Provide module-level helper functions that use a global default registry, while also exporting the `MetricRegistry` class for users who need explicit control or test isolation.

### API Design

```python
# src/pyfulmen/telemetry/__init__.py
from ._registry import MetricRegistry
from .models import MetricEvent, HistogramSummary, HistogramBucket
from ._validate import validate_metric_event, validate_metric_events

# Export class for custom registries
__all__ = [
    "MetricRegistry",          # Explicit registry for advanced use
    "MetricEvent",
    "HistogramSummary",
    "HistogramBucket",
    "validate_metric_event",
    "validate_metric_events",
]

# src/pyfulmen/telemetry/_registry.py
# Internal default singleton
_default_registry = MetricRegistry()

# NOT exported - internal only for simple API
# Users get instruments directly from MetricRegistry instances
```

### Usage Patterns

#### Pattern 1: Simple Application (Default Registry)

```python
from pyfulmen import telemetry

# Create registry and use it
registry = telemetry.MetricRegistry()

# Record metrics
registry.counter("requests").inc()
registry.histogram("latency_ms").observe(42.5)

# Get events
events = registry.get_events()
```

#### Pattern 2: Testing (Custom Registry)

```python
import pytest
from pyfulmen import telemetry

def test_metric_recording():
    # Create isolated test registry
    registry = telemetry.MetricRegistry()

    # Record test metrics
    counter = registry.counter("test_metric")
    counter.inc()
    counter.inc()

    # Assert on isolated events
    events = registry.get_events()
    assert len(events) == 2
    assert events[0].name == "test_metric"
    assert events[0].value == 1.0
    assert events[1].value == 2.0
```

#### Pattern 3: Module-Level Metrics

```python
# src/myapp/database.py
from pyfulmen import telemetry

# Module-level registry
_db_metrics = telemetry.MetricRegistry()

def query(sql: str):
    histogram = _db_metrics.histogram("db_query_ms")
    start = time.time()
    # ... execute query
    histogram.observe((time.time() - start) * 1000)

def get_metrics():
    """Export database metrics."""
    return _db_metrics.get_events()
```

## Rationale

1. **Simple Default**: Creating `registry = telemetry.MetricRegistry()` is straightforward for common use cases:

   ```python
   registry = telemetry.MetricRegistry()
   registry.counter("requests").inc()
   ```

2. **Test Isolation**: Tests can create independent registries without global state pollution:

   ```python
   test_registry = telemetry.MetricRegistry()
   # Test metrics isolated from production metrics
   ```

3. **Explicit Dependencies**: Users control registry lifecycle and can inject registries where needed:

   ```python
   class MyService:
       def __init__(self, registry: telemetry.MetricRegistry):
           self.registry = registry
   ```

4. **Cross-Language Consistency**: This pattern translates well to Go and TypeScript:
   - Go: `registry := telemetry.NewRegistry()`
   - TypeScript: `const registry = new MetricRegistry()`

5. **Progressive Complexity**: Start simple with single registry, graduate to multiple registries as needs evolve.

## Consequences

### Positive

- ✅ **Simple Adoption**: Creating a registry is one line of code
- ✅ **Test Isolation**: Each test can have its own registry
- ✅ **Explicit Control**: Users manage registry lifecycle
- ✅ **Thread Safety**: Registry is thread-safe via internal locking
- ✅ **No Magic**: Clear where metrics are stored (explicit registry instance)

### Negative

- ⚠️ **Pattern Clarity**: Need to document when to use single vs multiple registries
  - **Mitigation**: Provide clear examples in documentation and README

- ⚠️ **Discoverability**: Users might expect global helper functions
  - **Mitigation**: Document pattern clearly with examples

### Neutral

- 📝 **Registry Management**: Users responsible for registry cleanup if needed
- 📝 **Cross-Module**: Modules can share a registry or use independent registries

## Cross-Language Translation

### Go (gofulmen)

```go
package telemetry

// Registry manages metric instruments and events
type Registry struct {
    mu         sync.Mutex
    counters   map[string]*Counter
    gauges     map[string]*Gauge
    histograms map[string]*Histogram
    events     []MetricEvent
}

// NewRegistry creates a new metric registry
func NewRegistry() *Registry {
    return &Registry{
        counters:   make(map[string]*Counter),
        gauges:     make(map[string]*Gauge),
        histograms: make(map[string]*Histogram),
        events:     make([]MetricEvent, 0),
    }
}

// Usage
registry := telemetry.NewRegistry()
counter := registry.Counter("requests")
counter.Inc()
```

### TypeScript (tsfulmen)

```typescript
// MetricRegistry manages metric instruments and events
export class MetricRegistry {
  private counters: Map<string, Counter> = new Map();
  private gauges: Map<string, Gauge> = new Map();
  private histograms: Map<string, Histogram> = new Map();
  private events: MetricEvent[] = [];

  counter(name: string): Counter {
    if (!this.counters.has(name)) {
      this.counters.set(name, new Counter(name, this));
    }
    return this.counters.get(name)!;
  }

  // ... other methods
}

// Usage
const registry = new MetricRegistry();
const counter = registry.counter("requests");
counter.inc();
```

## Alternatives Considered but Rejected

### Context-Based Registry (Python Context Variables)

Use Python's `contextvars` to manage registry per-context:

```python
import contextvars

_registry_context = contextvars.ContextVar('metric_registry', default=MetricRegistry())

def get_registry() -> MetricRegistry:
    return _registry_context.get()
```

**Rejected because**:

- Overly complex for the use case
- Doesn't translate to Go/TypeScript
- Context propagation can be confusing
- Harder to test and debug

### Thread-Local Registry

Use `threading.local()` for per-thread registries:

```python
import threading

_local = threading.local()

def get_registry() -> MetricRegistry:
    if not hasattr(_local, 'registry'):
        _local.registry = MetricRegistry()
    return _local.registry
```

**Rejected because**:

- Metrics should be aggregated across threads
- Complicates metric export (need to collect from all threads)
- Not compatible with async/await patterns

## Migration Path

If future needs require additional patterns (e.g., dependency injection frameworks), we can add helper utilities without breaking changes:

```python
# Future: Optional DI helpers
from pyfulmen.telemetry import MetricRegistry, with_registry

@with_registry
def my_function(registry: MetricRegistry):
    registry.counter("calls").inc()
```

## References

- [Crucible Metrics Taxonomy](../../config/crucible-py/taxonomy/metrics.yaml)
- [OpenTelemetry Metrics API](https://opentelemetry.io/docs/specs/otel/metrics/api/)
- [Prometheus Client Python](https://github.com/prometheus/client_python)
- [FulmenHQ Helper Library Standard](../crucible-py/architecture/fulmen-helper-library-standard.md)

## Related Standards

- **Crucible 2025.10.3**: Error Handling as Data Models (promoted from PyFulmen ADR-0008)
- **Crucible 2025.10.3**: Telemetry Default Histogram Buckets (promoted from PyFulmen ADR-0009)

## Revision History

| Date       | Version | Description      | Author             |
| ---------- | ------- | ---------------- | ------------------ |
| 2025-10-23 | 1.0     | Initial decision | PyFulmen Architect |
