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

### MIME Type Detection

Immutable MIME type definitions with multiple lookup methods per Crucible standard.

**Catalog Methods:**

```python
from pyfulmen.foundry import FoundryCatalog
from pyfulmen.config.loader import ConfigLoader

loader = ConfigLoader(app_name="fulmen")
catalog = FoundryCatalog(loader)

# Lookup by MIME type ID
mime = catalog.get_mime_type("json")
print(mime.mime)  # "application/json"
print(mime.extensions)  # ["json", "map"]

# Lookup by file extension
mime = catalog.get_mime_type_by_extension("json")
print(mime.mime)  # "application/json"

# Lookup by MIME string
mime = catalog.get_mime_type_by_mime_string("application/json")
print(mime.id)  # "json"

# List all MIME types
mime_types = catalog.get_all_mime_types()
for mime in mime_types.values():
    print(f"{mime.id}: {mime.mime}")
```

**Convenience Functions:**

For quick access without creating a catalog instance:

```python
from pyfulmen.foundry import (
    get_mime_type_by_extension,
    get_mime_type_by_mime_string,
    is_supported_mime_type,
    list_mime_types,
)

# Check if MIME type is supported
if is_supported_mime_type("application/json"):
    print("JSON is supported")

# Get MIME type by extension
mime = get_mime_type_by_extension("json")

# Get MIME type by MIME string (case-insensitive)
mime = get_mime_type_by_mime_string("application/json")

# List all available MIME types
for mime in list_mime_types():
    print(f"{mime.id}: {mime.mime}")
```

**Extension Matching:**

```python
mime = catalog.get_mime_type("json")

# Check if extension matches (with or without dot)
if mime.matches_extension(".json"):
    print("Matches .json extension")

if mime.matches_extension("json"):
    print("Matches json extension")
```

### HTTP Status Helpers

HTTP status code groups with lookup, classification, and convenience helpers per Crucible standard.

**Catalog Methods:**

```python
from pyfulmen.foundry import FoundryCatalog, HttpStatusHelper
from pyfulmen.config.loader import ConfigLoader

loader = ConfigLoader(app_name="fulmen")
catalog = FoundryCatalog(loader)

# Get status group by ID
success_group = catalog.get_http_status_group("success")
print(success_group.contains(200))  # True
print(success_group.get_reason(201))  # "Created"

# Get group for specific status code
group = catalog.get_http_status_group_for_code(404)
print(group.id)  # "client-error"
print(group.name)  # "Client Error Responses"

# Use HttpStatusHelper for classification
helper = HttpStatusHelper(catalog)
print(helper.is_success(200))  # True
print(helper.is_client_error(404))  # True
print(helper.is_server_error(500))  # True
```

**Convenience Functions:**

For quick status code classification without creating a catalog instance:

```python
from pyfulmen.foundry import (
    is_informational,
    is_success,
    is_redirect,
    is_client_error,
    is_server_error,
)

# Check status code categories
if is_success(200):
    print("Success response")

if is_client_error(404):
    print("Client error - not found")

if is_server_error(500):
    print("Server error")

if is_informational(100):
    print("Informational response")

if is_redirect(301):
    print("Redirect response")
```

**Available Status Groups:**

- `informational` - 1xx responses (100-199)
- `success` - 2xx responses (200-299)
- `redirect` - 3xx responses (300-399)
- `client-error` - 4xx responses (400-499)
- `server-error` - 5xx responses (500-599)

### Country Code Lookups

ISO 3166-1 country code support with Alpha-2, Alpha-3, and Numeric lookups.

**Catalog Methods:**

```python
from pyfulmen.foundry import FoundryCatalog
from pyfulmen.config.loader import ConfigLoader

loader = ConfigLoader(app_name="fulmen")
catalog = FoundryCatalog(loader)

# Lookup by Alpha-2 (case-insensitive)
country = catalog.get_country("US")
print(country.name)  # "United States of America"

# Lookup by Alpha-3 (case-insensitive)
country = catalog.get_country_by_alpha3("USA")
print(country.alpha2)  # "US"

# Lookup by Numeric (zero-padded automatically)
country = catalog.get_country_by_numeric("840")
print(country.name)  # "United States of America"

country = catalog.get_country_by_numeric("76")  # Brazil
print(country.numeric)  # "076" (zero-padded)

# List all countries
countries = catalog.list_countries()
for country in countries:
    print(f"{country.alpha2}: {country.name}")
```

**Convenience Functions:**

```python
from pyfulmen.foundry import (
    validate_country_code,
    get_country,
    get_country_by_alpha3,
    get_country_by_numeric,
    list_countries,
)

# Validate country codes (all formats)
if validate_country_code("US"):      # Alpha-2
    print("Valid")
if validate_country_code("usa"):     # Alpha-3 (case-insensitive)
    print("Valid")
if validate_country_code("76"):      # Numeric (Brazil)
    print("Valid")

# Quick lookups
country = get_country("US")
country = get_country_by_alpha3("USA")
country = get_country_by_numeric("840")

# List all
for country in list_countries():
    print(f"{country.alpha2}: {country.name}")
```

**Key Features:**

- **Case-insensitive** alpha code matching ("us" → "US")
- **Automatic zero-padding** for numeric codes ("76" → "076")
- **O(1) lookups** via precomputed indexes
- **5 sample countries**: US, CA, JP, DE, BR

## MIME Type Detection (Magic Numbers)

PyFulmen Foundry supports content-based MIME type detection using byte signatures (magic numbers). This complements extension-based detection and enables validation of file contents.

### Core Detection

```python
from pyfulmen.foundry import detect_mime_type

# Detect from bytes
data = b'{"key": "value"}'
mime = detect_mime_type(data)
print(mime.mime)  # application/json

# Handles BOM and whitespace
data = b"\xef\xbb\xbf  {\"key\": \"value\"}"
mime = detect_mime_type(data)
print(mime.id)  # json

# Returns None for unknown/binary
binary = b"\x00\x01\x02\xFF"
mime = detect_mime_type(binary)
print(mime)  # None
```

### Streaming Detection

```python
from pyfulmen.foundry import detect_mime_type_from_reader

# Detect from stream (preserves reader)
with open('upload.dat', 'rb') as f:
    mime, reader = detect_mime_type_from_reader(f)
    if mime and mime.id == 'json':
        # Continue processing with reader
        data = json.load(reader)

# HTTP request body detection
mime, body_reader = detect_mime_type_from_reader(request.body, max_bytes=512)
if mime and mime.id == 'json':
    process_json(body_reader)
```

### File Detection

```python
from pyfulmen.foundry import detect_mime_type_from_file

# Detect from file path
mime = detect_mime_type_from_file('config.json')
if mime:
    print(f'Detected: {mime.mime}')

# Handles large files (reads first 512 bytes)
mime = detect_mime_type_from_file('large_data.csv')
```

**Supported Formats**:

- **JSON**: Objects (`{...}`) and arrays (`[...]`)
- **XML**: Files with `<?xml` declaration
- **YAML**: Key-value documents (`key: value`)
- **CSV**: Comma-separated data (2+ commas)
- **Plain Text**: >80% printable ASCII/UTF-8

**Key Features**:

- **BOM stripping**: Handles UTF-8, UTF-16 LE/BE byte order marks
- **Whitespace trimming**: Accurate detection despite leading whitespace
- **Reader preservation**: Stream detection returns usable reader
- **Nil on unknown**: Returns None for binary/unknown (not exceptions)
- **gofulmen parity**: Full API compatibility with gofulmen v0.1.1

## Crucible Standards Conformance

PyFulmen Foundry implements the Crucible Foundry pattern catalog standard with the following conformance status:

### Implemented ✅

**Base Models (Phase 0)**

- `FulmenDataModel` - Immutable data models with JSON serialization
- `FulmenConfigModel` - Mutable config models with deep merge
- `FulmenCatalogModel` - Immutable catalog entries
- UUIDv7 correlation ID generation
- RFC3339Nano timestamp generation

**Pattern Catalog (Phase 1)**

- Regex, glob, and literal pattern matching
- Lazy loading with caching
- Python-specific magic methods (`__call__`)
- PatternAccessor for convenient pattern access
- Full pattern catalog from Crucible sync

**MIME Type Interface (Phase 2A)**

- `get_mime_type(id)` - Lookup by MIME type ID
- `get_mime_type_by_extension(ext)` - Lookup by file extension
- `get_mime_type_by_mime_string(mime)` - Lookup by MIME string (case-insensitive)
- `is_supported_mime_type(mime)` - Check if MIME type is supported
- `list_mime_types()` - Enumerate all MIME types
- Extension matching with or without dot prefix

**HTTP Status Helpers (Phase 2B)**

- `HttpStatusGroup` catalog entries
- `HttpStatusHelper` for classification
- Convenience functions: `is_informational()`, `is_success()`, `is_redirect()`, `is_client_error()`, `is_server_error()`
- Status code lookup and reason phrase access

**Country Code Catalog (Phase 2E)**

- ISO 3166-1 Alpha-2/Alpha-3/Numeric lookups
- Case-insensitive validation with `validate_country_code()`
- Numeric zero-padding canonicalization ("76" → "076")
- O(1) lookups via precomputed indexes
- 5 sample countries from Crucible catalog (US, CA, JP, DE, BR)

**Magic Number Detection (Phase 3)**

- `detect_mime_type(data: bytes)` - Byte signature detection from raw bytes
- `detect_mime_type_from_reader(reader, max_bytes)` - Streaming detection with reader preservation
- `detect_mime_type_from_file(path)` - File content detection
- BOM stripping (UTF-8, UTF-16 LE/BE)
- Detects: JSON, XML, YAML, CSV, plain text
- Full gofulmen v0.1.1 API parity
- 83+ comprehensive tests including golden fixtures
- Cross-language parity checklist with 100% compliance

### Testing Coverage

- **Unit Tests**: 167+ tests covering catalog loading, pattern matching, MIME lookups, HTTP status helpers, country code lookups, MIME detection
- **Coverage**: 95% on catalog module
- **Test Strategy**:
  - Positive and negative test cases for all interfaces
  - Case-insensitive MIME string lookup validation
  - Extension matching with/without dot prefix
  - Lazy loading and caching validation
  - Pydantic model validation and serialization

### Design Principles

Per Crucible standards, PyFulmen Foundry follows these principles:

1. **Read-Only Catalog** - Catalog entries are immutable (`frozen=True`)
2. **Single Source of Truth** - All patterns, MIME types, and status codes come from Crucible sync
3. **Lazy Loading** - Catalogs load on first access, not at import time
4. **Forward Compatibility** - Catalog models ignore unknown fields (`extra='ignore'`)
5. **Type Safety** - Pydantic validation for all catalog entries
6. **Cross-Language Consistency** - UUIDv7, RFC3339Nano match gofulmen/tsfulmen

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

## Text Similarity and Normalization (v2.0.0)

PyFulmen provides comprehensive text similarity utilities following the Foundry Similarity v2.0.0 standard. The module supports five distance metrics, four normalization presets, and ranked suggestion generation for typo correction, fuzzy matching, and text comparison.

### Quick Start

```python
from pyfulmen.foundry import similarity

# Basic similarity with default Levenshtein metric
similarity.distance("kitten", "sitting")  # 3
similarity.score("kitten", "sitting")     # 0.571...

# Typo correction with Damerau OSA (handles transpositions)
similarity.distance("teh", "the", metric="damerau_osa")  # 1

# CLI suggestions with Jaro-Winkler (rewards prefixes)
suggestions = similarity.suggest(
    "terrafrom",
    ["terraform", "format", "validate"],
    metric="jaro_winkler"
)

# Fuzzy matching with aggressive normalization
suggestions = similarity.suggest(
    "café!",
    ["Cafe", "CAFE"],
    normalize_preset="aggressive",
    min_score=0.8
)
```

### Similarity Metrics

The similarity module supports five metrics with different use cases:

```python
from pyfulmen.foundry import similarity

# Levenshtein (default) - insertions, deletions, substitutions
similarity.distance("kitten", "sitting")  # 3
similarity.score("kitten", "sitting")     # 0.5714285714285714

# Damerau-Levenshtein OSA - adds adjacent transpositions
# Best for: typo correction, spell checking, CLI fuzzy matching
similarity.distance("abcd", "abdc", metric="damerau_osa")  # 1
similarity.score("abcd", "abdc", metric="damerau_osa")     # 0.75

# Damerau-Levenshtein Unrestricted - unrestricted transpositions
# Best for: general similarity, DNA sequencing, complex transformations
similarity.distance("CA", "ABC", metric="damerau_unrestricted")  # 2
similarity.score("CA", "ABC", metric="damerau_unrestricted")     # 0.33333...

# Jaro-Winkler - similarity for short strings with common prefixes
# Best for: name matching, short text comparison, record linkage
similarity.score("martha", "marhta", metric="jaro_winkler")  # 0.9611111...
similarity.score("dixon", "dicksonx", metric="jaro_winkler")  # 0.8133333...

# Substring - longest common substring matching
# Best for: path matching, partial string search, document similarity
match_range, score = similarity.substring_match("world", "hello world")
# match_range = (6, 11), score = 0.4545454...
```

### Metric Selection Guide

**Choose Levenshtein when:**

- You need standard edit distance
- Performance is critical (fastest implementation)
- Transpositions should cost 2 operations

**Choose Damerau-Levenshtein OSA when:**

- Correcting common typos (transpositions)
- Building CLI autocomplete/suggestions
- Single-character swaps are common errors

**Choose Damerau-Levenshtein Unrestricted when:**

- Complex transformations are valid
- Need full transposition support
- Working with DNA/protein sequences

**Choose Jaro-Winkler when:**

- Comparing names or short strings
- Common prefixes are significant
- Record linkage or deduplication

**Choose Substring when:**

- Searching for partial matches
- Comparing file paths or URLs
- Need match location information

### Text Normalization

Unicode-aware text normalization with preset-based configuration:

```python
from pyfulmen.foundry import similarity

# Normalization presets (v2.0.0)
text = "  Café-Zürich! 🎉  "

similarity.apply_normalization_preset(text, "none")       # "  Café-Zürich! 🎉  "
similarity.apply_normalization_preset(text, "minimal")    # "Café-Zürich! 🎉"
similarity.apply_normalization_preset(text, "default")    # "café-zürich! 🎉"
similarity.apply_normalization_preset(text, "aggressive") # "cafezurich "

# Legacy API (backward compatible)
similarity.normalize("  Hello World  ")  # "hello world"
similarity.normalize("Café", strip_accents=True)  # "cafe"

# Case-insensitive comparison
similarity.equals_ignore_case("Hello", "HELLO")  # True
similarity.equals_ignore_case("Café", "cafe", strip_accents=True)  # True

# Unicode casefold with locale support
similarity.casefold("İstanbul", locale="tr")  # Turkish dotted I handling
```

**Preset Levels**:

- **`none`**: No changes (exact matching)
- **`minimal`**: NFC normalization + trim whitespace
- **`default`**: NFC + casefold + trim (recommended for most use cases)
- **`aggressive`**: NFKD + casefold + strip accents + remove punctuation + trim

### Suggestion Ranking

Rank candidate strings by similarity for typo correction:

```python
from pyfulmen.foundry import similarity

# CLI command suggestions with metric selection (v2.0.0)
suggestions = similarity.suggest(
    "terrafrom",
    ["terraform", "terraform-apply", "format"],
    metric="jaro_winkler",  # Best for prefix matching
    min_score=0.7,
    max_suggestions=3
)
# Returns terraform commands ranked by prefix similarity

# Fuzzy matching with normalization presets (v2.0.0)
suggestions = similarity.suggest(
    "café",
    ["Cafe", "CAFE", "cache"],
    normalize_preset="aggressive",  # Strip accents, case, punctuation
    min_score=0.8
)
# Returns: ["Cafe", "CAFE"] (cache excluded, too different)

# Basic usage (backward compatible)
suggestions = similarity.suggest(
    "cofnig",
    ["config", "configure", "confirm", "conflict"],
    min_score=0.6,
    max_suggestions=3
)
# [Suggestion(score=0.833..., value='config'),
#  Suggestion(score=0.625, value='configure'),
#  Suggestion(score=0.625, value='confirm')]

# Empty input defaults to alphabetical listing
suggestions = similarity.suggest("", ["zebra", "alpha", "beta"])
# [Suggestion(score=1.0, value='alpha'),
#  Suggestion(score=1.0, value='beta'),
#  Suggestion(score=1.0, value='zebra')]

# No matches returns empty list
suggestions = similarity.suggest("xyz", ["abc", "def"], min_score=0.8)
# []
```

### Advanced Usage

**Custom Jaro-Winkler parameters:**

```python
# Adjust prefix scaling (default: 0.1)
score = similarity.score(
    "testing", "test",
    metric="jaro_winkler",
    jaro_prefix_scale=0.15  # More weight to common prefixes
)

# Maximum prefix length (default: 4)
score = similarity.score(
    "testing", "test",
    metric="jaro_winkler",
    jaro_max_prefix=2  # Only consider first 2 characters
)
```

**Substring matching with location:**

```python
# Find substring and get location
match_range, score = similarity.substring_match("schemas", "schemas/foundry/patterns.yaml")
# match_range = (0, 7), score = 0.241379...

if match_range:
    start, end = match_range
    matched_text = haystack[start:end]  # "schemas"
```

### Performance Notes

**Computational Complexity:**

- **Levenshtein**: O(m×n) time, O(min(m,n)) space (two-row optimization)
- **Damerau OSA**: O(m×n) time, O(m×n) space
- **Damerau Unrestricted**: O(m×n) time, O(m×n) space
- **Jaro-Winkler**: O(m×n) time, O(1) space
- **Substring**: O(m×n) time, O(m×n) space

**Performance Targets** (from Foundry standard):

- ≤1ms for strings ≤128 characters
- ≤10ms for strings ≤1024 characters

**Substring Performance Consideration:**

The longest common substring implementation uses an O(m×n) dynamic programming matrix. This is appropriate for typical use cases (CLI suggestions, path matching, short documents), but performance may degrade with very large strings (>10KB).

**Recommended limits for substring matching:**

- ✅ **Optimal**: strings <1KB (instant results)
- ⚠️ **Acceptable**: strings 1-10KB (may take 10-100ms)
- ❌ **Not recommended**: strings >10KB (consider alternative approaches)

For very large text comparison, consider chunking strategies or alternative algorithms (e.g., suffix trees, rolling hashes).

### Dependency Notes

**RapidFuzz Integration:**

PyFulmen uses [rapidfuzz](https://github.com/maxbachmann/RapidFuzz) (≥3.14.1) for Damerau-Levenshtein and Jaro-Winkler implementations. RapidFuzz provides high-performance C++ implementations with Python bindings and is **required** for Similarity v2.0.0.

**Why Required:**

- **Damerau OSA** and **Damerau Unrestricted** have no pure Python implementations in PyFulmen
- **Jaro-Winkler** requires the rapidfuzz algorithm for accurate results
- **Crucible fixtures** validate exact algorithm behavior (46/46 fixtures passing)
- **PyFulmen is the reference implementation** for the Fulmen ecosystem

Rapidfuzz is automatically installed as a runtime dependency when you install pyfulmen:

```bash
pip install pyfulmen  # Includes rapidfuzz ≥3.14.1
```

### API Reference

**Core Functions (v2.0.0):**

```python
# Distance calculation (edit distance as integer)
distance(a: str, b: str, metric: MetricType = "levenshtein") -> int

# Similarity scoring (normalized 0.0-1.0)
score(
    a: str,
    b: str,
    metric: MetricType = "levenshtein",
    jaro_prefix_scale: float = 0.1,
    jaro_max_prefix: int = 4,
) -> float

# Substring matching with location
substring_match(needle: str, haystack: str) -> tuple[tuple[int, int] | None, float]

# Suggestion ranking (v2.0.0 enhanced)
suggest(
    input_value: str,
    candidates: list[str],
    min_score: float = 0.6,
    max_suggestions: int = 3,
    normalize_text: bool = True,
    metric: MetricType = "levenshtein",
    normalize_preset: NormalizationPreset | None = None,
    prefer_prefix: bool = False,
    jaro_prefix_scale: float = 0.1,
    jaro_max_prefix: int = 4,
) -> list[Suggestion]

# Text normalization (v2.0.0 presets)
apply_normalization_preset(text: str, preset: NormalizationPreset) -> str
normalize(
    value: str,
    preset: NormalizationPreset | None = None,
    strip_accents_flag: bool = False,
    locale: str = "",
) -> str
casefold(value: str, locale: str = "") -> str
strip_accents(value: str) -> str
equals_ignore_case(a: str, b: str, strip_accents_flag: bool = False) -> bool
```

**Metric Types:**

```python
MetricType = Literal[
    "levenshtein",
    "damerau_osa",
    "damerau_unrestricted",
    "jaro_winkler",
    "substring",
]
```

**Normalization Presets (v2.0.0):**

```python
NormalizationPreset = Literal[
    "none",
    "minimal",
    "default",
    "aggressive",
]
```

**Data Models:**

```python
@dataclass(frozen=True, order=True)
class Suggestion:
    score: float                          # Similarity score (0.0-1.0)
    value: str                            # Candidate string
    matched_range: tuple[int, int] | None = None  # v2.0.0: Substring match location
    reason: str | None = None             # v2.0.0: Match type explanation
    normalized_value: str | None = None   # v2.0.0: Normalized form
```

### Standards Compliance

- **Schema**: `schemas/crucible-py/library/foundry/v2.0.0/similarity.schema.json`
- **Fixtures**: `config/crucible-py/library/foundry/similarity-fixtures.yaml` (46 test cases)
- **Standard**: Foundry Similarity v2.0.0 (Crucible 2025.10.3)
- **Cross-language**: API parity with gofulmen and tsfulmen

### References

- **Implementation Guide**: `docs/crucible-py/standards/library/foundry/similarity.md`
- **Fixtures**: `config/crucible-py/library/foundry/similarity-fixtures.yaml`
- **Test Coverage**: 90%+ (55+ unit tests, 46 fixture validations)

## Future Extensions

Planned enhancements for future versions:

- **Pattern Validation Helpers** - Additional domain-specific pattern utilities
- **Catalog Versioning** - Track Crucible catalog version and sync status
- **Performance Optimizations** - Compiled regex caching, bloom filters for existence checks
- **Similarity Enhancements** - Phonetic algorithms (Soundex, Metaphone), n-gram similarity
