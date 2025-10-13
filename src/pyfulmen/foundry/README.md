# Foundry Module

Foundation utilities and base models for pyfulmen following Fulmen conventions.

## Overview

The Foundry module provides:
- **Base Pydantic Models** - Consistent patterns for data, config, and catalog models
- **RFC3339Nano Timestamps** - Microsecond-precision UTC timestamps
- **UUIDv7 Correlation IDs** - Time-sortable correlation tracking
- **Pattern Catalogs** - Curated regex/glob/literal patterns from Crucible
- **MIME Type Detection** - File type identification by extension
- **HTTP Status Helpers** - Status code groups and classification

## Base Models

### FulmenDataModel

Immutable data model for events, messages, and structured data.

**Features:**
- Immutable (`frozen=True`) - prevents accidental mutation
- Strict schema (`extra='forbid'`) - rejects unknown fields
- JSON serialization helpers

**Use Cases:**
- Log events
- Trace events and spans
- Metric events
- API response models
- Domain events and messages

**Example:**
```python
from pyfulmen.foundry import FulmenDataModel, generate_correlation_id
from pydantic import Field, computed_field

class LogEvent(FulmenDataModel):
    message: str
    correlation_id: str = Field(default_factory=generate_correlation_id)
    timestamp: str = Field(default_factory=utc_now_rfc3339nano)
    
    @computed_field
    @property
    def message_length(self) -> int:
        """Computed field - excluded from serialization by default."""
        return len(self.message)

event = LogEvent(message="Request processed")

# Default serialization excludes computed fields (safe for roundtripping)
print(event.to_json_dict())
# {'message': 'Request processed', 'correlation_id': '...', 'timestamp': '...'}

# Include computed fields explicitly when needed
print(event.to_json_dict_with_computed())
# {'message': 'Request processed', ..., 'message_length': 17}
```

### FulmenConfigModel

Flexible configuration model for three-layer config loading.

**Features:**
- Mutable (`frozen=False`) - supports merge operations
- Flexible schema (`extra='allow'`) - accepts unknown fields
- Supports both camelCase and snake_case
- Deep merge helper

**Use Cases:**
- Application configuration
- Service configuration with environment overrides
- Three-layer merged configs (Crucible defaults → user → runtime)

**Example:**
```python
from pyfulmen.foundry import FulmenConfigModel

class LoggingConfig(FulmenConfigModel):
    service: str
    level: str = "INFO"
    sinks: list = []

base = LoggingConfig(service="myapp", sinks=[{"type": "console"}])
override = LoggingConfig(service="myapp", level="DEBUG")
merged = base.merge_with(override)
# merged.level == "DEBUG", merged.sinks == [{"type": "console"}]
```

### FulmenCatalogModel

Immutable catalog entry for reference data from Crucible.

**Features:**
- Immutable (`frozen=True`) - catalog entries never change
- Ignores unknown fields (`extra='ignore'`) - forward compatible
- Optimized for lookups and caching

**Use Cases:**
- Pattern definitions (regex, glob, literal)
- MIME type catalog entries
- HTTP status code definitions
- Country code mappings

**Example:**
```python
from pyfulmen.foundry import FulmenCatalogModel

class Pattern(FulmenCatalogModel):
    id: str
    pattern: str
    pattern_type: str

email_pattern = Pattern(
    id="email",
    pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    pattern_type="regex"
)
```

## Computed Fields (Pydantic v2.12+)

All Fulmen data models support computed fields using Pydantic's `@computed_field` decorator.

### Best Practices

**Default Behavior: Excluded from Serialization**

Computed fields are automatically excluded from `to_json_dict()` to enable safe roundtripping:

```python
from pydantic import computed_field
from pyfulmen.foundry import FulmenDataModel

class LogEvent(FulmenDataModel):
    message: str
    severity: str
    
    @computed_field
    @property
    def severity_level(self) -> int:
        """Map severity to numeric level."""
        levels = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
        return levels.get(self.severity, 0)

event = LogEvent(message="test", severity="INFO")

# Computed field accessible as attribute
assert event.severity_level == 20

# But excluded from serialization by default
data = event.to_json_dict()
assert "severity_level" not in data

# Safe roundtripping - no need to exclude computed fields manually
reconstructed = LogEvent(**data)
assert reconstructed.message == event.message
```

### Including Computed Fields

When you need computed fields in output (logging, debugging, API responses):

```python
# Option 1: Use convenience method
event.to_json_dict_with_computed()
# {'message': 'test', 'severity': 'INFO', 'severity_level': 20}

# Option 2: Use parameter
event.to_json_dict(include_computed=True)
# {'message': 'test', 'severity': 'INFO', 'severity_level': 20}

# Option 3: JSON string with computed fields
event.to_json_str(include_computed=True)
```

### Introspection

Query computed fields programmatically:

```python
# Get all computed field names
event.get_computed_field_names()
# {'severity_level'}

# Access Pydantic's computed field metadata
LogEvent.model_computed_fields
# {'severity_level': ComputedFieldInfo(...)}
```

### Why Exclude by Default?

1. **Roundtripping** - Deserializing with computed fields present would fail validation
2. **Data Integrity** - Computed values are derived, not stored
3. **API Contracts** - Clear separation between persisted and derived data
4. **Performance** - Skip computing values when not needed

## Utility Functions

### utc_now_rfc3339nano()

Generate RFC3339Nano timestamp with microsecond precision.

```python
from pyfulmen.foundry import utc_now_rfc3339nano

timestamp = utc_now_rfc3339nano()
# "2025-10-13T14:32:15.123456Z"
```

### generate_correlation_id()

Generate time-sortable UUIDv7 for correlation tracking.

```python
from pyfulmen.foundry import generate_correlation_id

correlation_id = generate_correlation_id()
# "0199dd68-a9de-75e8-811b-9ea72de82b73"
```

## Design Decisions

### Why Custom Base Classes?

Instead of everyone using `BaseModel` with slightly different `ConfigDict` settings, we provide:
- **Consistency** - Same configuration across all modules
- **Maintainability** - Change settings once, apply everywhere
- **Documentation** - Clear guidance on which base to use when
- **Testing** - Test foundation once, trust everywhere

### Why Pydantic?

- Enterprise Python users already have Pydantic (FastAPI, LangChain, data modeling)
- Pydantic v2 has excellent performance (Rust core)
- Type safety and validation out of the box
- Schema generation and cross-validation

### Why UUIDv7?

- Time-sortable (embeds timestamp)
- Cross-language consistency (gofulmen, tsfulmen, pyfulmen all use UUIDv7)
- Better for log aggregation systems (Splunk, Datadog)
- Crucible logging standard mandates UUIDv7

## Pattern Catalogs

### FoundryCatalog

Lazy-loading catalog for accessing curated patterns, MIME types, and HTTP status groups from Crucible configuration.

**Example:**
```python
from pyfulmen.config.loader import ConfigLoader
from pyfulmen.foundry import FoundryCatalog

loader = ConfigLoader(app_name="fulmen")
catalog = FoundryCatalog(loader)

# Get pattern by ID
email_pattern = catalog.get_pattern("ansi-email")
if email_pattern and email_pattern.match("user@example.com"):
    print("Valid email")

# Get MIME type by extension
mime = catalog.get_mime_type_by_extension("json")
print(mime.mime)  # "application/json"

# Get HTTP status group for code
group = catalog.get_http_status_group_for_code(404)
print(group.id)  # "client-error"
```

### Pattern

Immutable pattern definition with regex/glob/literal matching support.

**Features:**
- Regex, glob, and literal pattern types
- Python-specific magic methods (`__call__` for direct invocation)
- Lazy compilation and caching
- Pattern description with examples

**Example:**
```python
from pyfulmen.foundry import FoundryCatalog, PatternAccessor
from pyfulmen.config.loader import ConfigLoader

loader = ConfigLoader(app_name="fulmen")
catalog = FoundryCatalog(loader)
patterns = PatternAccessor(catalog)

# Access common patterns by name
email = patterns.email()
slug = patterns.slug()
uuid = patterns.uuid_v4()

# Pattern matching
if email.match("user@example.com"):
    print("Valid email")

# Direct invocation via __call__
if email("user@example.com"):
    print("Valid email")

# Search within string
if email.search("Contact: user@example.com for info"):
    print("Email found")

# Get pattern description
print(slug.describe())
```

**Available Patterns:**
- `email()` - Internationalized email (RFC 5322 with Unicode)
- `slug()` - Kebab-case or snake_case slugs
- `path_segment()` - URL path segments
- `identifier()` - CamelCase/snake_case identifiers
- `domain_name()` - Fully qualified domain names
- `ipv6()` - IPv6 addresses (full and compressed)
- `uuid_v4()` - RFC 4122 UUID v4
- `semantic_version()` - SemVer 2.0.0 versions
- `iso_date()` - ISO 8601 dates (YYYY-MM-DD)
- `iso_timestamp_utc()` - ISO 8601 UTC timestamps

### MimeType

Immutable MIME type definition with extension matching.

**Example:**
```python
mime = catalog.get_mime_type("json")
print(mime.mime)  # "application/json"
print(mime.extensions)  # ["json", "map"]

# Check if extension matches
if mime.matches_extension(".json"):
    print("JSON file")
```

### HttpStatusGroup

HTTP status code groups with lookup and classification.

**Example:**
```python
# Get status group by ID
success_group = catalog.get_http_status_group("success")
print(success_group.contains(200))  # True
print(success_group.get_reason(201))  # "Created"

# Get group for specific status code
group = catalog.get_http_status_group_for_code(404)
print(group.id)  # "client-error"
print(group.name)  # "Client Error Responses"
```

**Available Status Groups:**
- `informational` - 1xx responses
- `success` - 2xx responses
- `redirect` - 3xx responses
- `client-error` - 4xx responses
- `server-error` - 5xx responses

## Fulmen Library Requirements

PyFulmen implements the Fulmen Helper Library Standard for cross-language consistency:

### Correlation IDs (UUIDv7)
All Fulmen libraries use UUIDv7 for correlation tracking:
- **Time-sortable** - Embedded timestamp enables chronological ordering
- **Cross-language** - Same format in gofulmen, tsfulmen, pyfulmen
- **Log aggregation** - Better performance in Splunk, Datadog, ELK

### Pattern Catalogs
Centralized pattern definitions in Crucible ensure consistency:
- **Single source of truth** - Patterns defined once, used everywhere
- **Version controlled** - Pattern changes tracked in Crucible
- **Language-specific flags** - Python, Go, TypeScript, Rust flags supported

### Configuration Management
Three-layer config loading pattern:
1. **Crucible defaults** - Embedded standards from sync
2. **User overrides** - `~/.config/fulmen/` customizations
3. **Runtime config** - Application-provided settings (BYOC)

## Python-Specific Features

PyFulmen leverages Python's strengths for better developer experience:

### Pydantic Foundation
- **Type safety** - Runtime validation with static type hints
- **Performance** - Pydantic v2 with Rust core
- **FastAPI integration** - Models work directly in FastAPI endpoints
- **Schema generation** - Automatic JSON Schema for API contracts

### Magic Methods
Python-specific enhancements for natural usage:
- `Pattern.__call__()` - Use patterns as callables: `pattern(value)`
- `FulmenConfigModel.merge_with()` - Intuitive config merging
- `FulmenDataModel.to_json_dict()` - Clean serialization API

### Computed Fields
Pydantic v2.12+ computed fields with intelligent exclusion:
- Excluded from serialization by default (safe roundtripping)
- Explicit inclusion when needed (`include_computed=True`)
- Full introspection support

## Future Extensions

Planned enhancements for future versions:
- Global catalog instance with convenience functions
- HTTP status helper methods (is_success(), is_client_error(), etc.)
- Country code lookups (ISO alpha-2/alpha-3/numeric)
- MIME magic number detection from bytes
- Additional domain-specific utilities
