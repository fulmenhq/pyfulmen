---
id: "ADR-0001"
title: "FulmenCatalogModel populate_by_name=True"
status: "accepted"
date: "2025-10-15"
last_updated: "2025-10-15"
deciders:
  - "@pyfulmen-architect"
scope: "pyfulmen"
supersedes: []
tags:
  - "pydantic"
  - "api-design"
  - "developer-experience"
related_adrs: []
---

# ADR-0001: FulmenCatalogModel populate_by_name=True

## Status

**Current Status**: Accepted

**Context**: v0.1.2 Country code implementation

## Context

During Country code implementation, we discovered that `FulmenCatalogModel` used `extra='ignore'` but NOT `populate_by_name=True`. This meant fields with Pydantic aliases (like `official_name` with alias `officialName`) could only be set using the alias syntax, not the Pythonic field name.

```python
# Only this worked (before):
Country(..., officialName="United States")  # YAML/JSON alias

# This was silently ignored (before):
Country(..., official_name="United States")  # Pythonic field name
```

This created a poor developer experience where Python developers would naturally use snake_case field names but the values would be silently ignored due to `extra='ignore'`.

## Decision

Add `populate_by_name=True` to `FulmenCatalogModel.model_config` (v0.1.2).

```python
model_config = ConfigDict(
    frozen=True,
    extra="ignore",
    validate_assignment=True,
    populate_by_name=True,  # NEW: Allow both field names and aliases
    use_enum_values=True,
)
```

## Rationale

1. **Pythonic Ergonomics**: Python developers expect snake_case field names to work
2. **Least Surprise**: Silently ignoring the field name is confusing and error-prone
3. **Flexibility**: Supports both YAML/JSON (camelCase) and Python (snake_case) conventions
4. **Backward Compatible**: Existing code using aliases continues to work unchanged
5. **Consistency**: `FulmenConfigModel` already has `populate_by_name=True`
6. **Cross-Language Mapping**: Allows Crucible YAML schemas to map naturally to Python code

## Alternatives Considered

### Alternative 1: Status Quo (aliases only)

**Pros**:

- No changes needed
- Enforces strict alias usage
- Minimal validation overhead

**Cons**:

- Surprising to Python developers
- Less ergonomic API
- Silent failures when using field names
- Inconsistent with `FulmenConfigModel`

**Decision**: Rejected - Poor developer experience outweighs any benefits

### Alternative 2: Remove aliases entirely

**Pros**:

- Simpler, only one way to specify fields
- No ambiguity about which form to use

**Cons**:

- Breaks YAML/JSON deserialization from Crucible catalogs
- Would require renaming all YAML fields to snake_case
- Impacts cross-language consistency

**Decision**: Rejected - Would break Crucible integration

### Alternative 3: Document alias-only requirement

**Pros**:

- No code changes needed
- Clear documentation

**Cons**:

- Doesn't fix the underlying ergonomics issue
- Still surprising to developers
- Documentation doesn't prevent mistakes

**Decision**: Rejected - Doesn't address root cause

## Consequences

### Positive

- ✅ Both field names and aliases work for all catalog models
- ✅ More Pythonic API for library users
- ✅ No breaking changes (aliases still work)
- ✅ Consistent with `FulmenConfigModel` behavior
- ✅ Better developer experience and less surprise

### Negative

- ℹ️ Slight increase in Pydantic validation time (negligible, ~microseconds)
- ℹ️ Two ways to set the same field (but this is already standard Pydantic behavior)

### Neutral

- 📚 Enhanced docstring explains the feature with examples
- 📚 Added test to ensure both forms work

## Implementation

**Files Modified**:

- `src/pyfulmen/foundry/models.py:341` - Added `populate_by_name=True`
- `src/pyfulmen/foundry/models.py:295-334` - Enhanced docstring with 50+ lines explaining feature
- `tests/unit/foundry/test_catalog.py:682-693` - Added `test_country_creation_with_field_name`

**Test Coverage**:

```python
def test_country_creation_with_field_name(self):
    """Country should accept both field name and alias (populate_by_name=True)."""
    # Test using Pythonic field name (enabled by populate_by_name=True in v0.1.2)
    country = Country(
        alpha2="CA",
        alpha3="CAN",
        numeric="124",
        name="Canada",
        official_name="Canada",  # Pythonic field name - NOW WORKS
    )
    assert country.alpha2 == "CA"
    assert country.official_name == "Canada"
```

**Validation**: All 103 catalog tests pass including new test for populate_by_name behavior.

## References

- [Pydantic ConfigDict Documentation](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.populate_by_name)
- [FulmenConfigModel Implementation](../../src/pyfulmen/foundry/models.py#L240-247) - Already uses populate_by_name
- [Country Model Implementation](../../src/pyfulmen/foundry/catalog.py#L318-341)

## Notes

This change was retroactively applied to all catalog models (Pattern, MimeType, HttpStatusCode, HttpStatusGroup, Country) but only Country currently uses field aliases. If future catalog models add aliases, they will automatically benefit from this configuration.

---

_Last Updated: 2025-10-15_
