---
id: "ADR-0003"
title: "Country Code Catalog Preview Status"
status: "accepted"
date: "2025-10-15"
last_updated: "2025-10-15"
deciders:
  - "@pyfulmen-architect"
scope: "pyfulmen"
supersedes: []
tags:
  - "catalog"
  - "foundry"
  - "roadmap"
  - "data"
related_adrs: []
---

# ADR-0003: Country Code Catalog Preview Status

## Status

**Current Status**: Accepted

**Context**: v0.1.2 Country code implementation

## Related ADRs

- [ADR-0002: validate_country_code() Strategy](ADR-0002-validate-country-code-lookup-strategy.md) (local)
- [Ecosystem ADR-0002: Triple-Index Catalog Strategy](../../crucible-py/architecture/decisions/ADR-0002-triple-index-catalog-strategy.md)

## Context

PyFulmen v0.1.2 implements full ISO 3166-1 support with complete API for Alpha-2, Alpha-3, and Numeric country code lookups. However, the shipped catalog contains only 5 sample countries (US, CA, JP, DE, BR) from the Crucible catalog.

Users need clear documentation about:

1. Current scope (5 countries is intentional, not a bug)
2. API stability (production-ready despite limited data)
3. Future plans (full catalog expansion)

## Decision

Document country code catalog as "preview" status with explicit communication:

1. **README states clearly**: "**5 sample countries**: US, CA, JP, DE, BR"
2. **Implementation is complete**: Full ISO 3166-1 standard support (ready for expansion)
3. **API is stable**: Production-ready, no breaking changes planned
4. **Preview mode**: Sufficient for testing, validation, and early adopters

## Rationale

1. **API Validation**: 5 countries sufficient to test all three lookup formats and edge cases
2. **Minimal Bundle Size**: Small catalog keeps library lightweight (<1KB data)
3. **Future-Proof**: Implementation ready for full catalog when available
4. **Transparency**: Clear documentation prevents user confusion and bug reports
5. **Rapid Iteration**: Can expand catalog without API changes

## Alternatives Considered

### Alternative 1: Wait for Full Catalog Before Release

**Pros**:

- Complete dataset from day one
- No "preview" designation needed

**Cons**:

- Delays v0.1.2 release significantly
- Requires Crucible team to compile full catalog first
- Blocks other features waiting on country codes

**Decision**: Rejected - Perfect is enemy of good; API value delivered sooner

### Alternative 2: Ship Empty Catalog, Let Users Provide Data

**Pros**:

- Zero bundle size
- Maximum flexibility for users

**Cons**:

- Poor developer experience (BYOD - Bring Your Own Data)
- No out-of-box functionality
- Defeats purpose of helper library

**Decision**: Rejected - Counter to Fulmen Helper Library philosophy

### Alternative 3: Embed Full 250+ Country Catalog Now

**Pros**:

- Complete dataset
- No future migration needed

**Cons**:

- Requires manual data compilation (~250 countries)
- Risk of data errors without proper validation
- Licensing concerns for ISO data (need research)
- Larger bundle size (~20-30KB for full catalog)

**Decision**: Deferred - Planned for 2025.10.3 with proper ISO licensing research

### Alternative 4: Silent Limitation (No Preview Designation)

**Pros**:

- Simpler messaging
- Implies completeness

**Cons**:

- Misleading to users
- Will generate bug reports ("Why can't I find Finland?")
- Lacks transparency

**Decision**: Rejected - Transparency is a Fulmen core value

## Consequences

### Positive

- ✅ Users understand current scope (no confusion)
- ✅ API is stable (no breaking changes planned)
- ✅ Implementation ready for catalog expansion (no rework needed)
- ✅ Faster time-to-market for v0.1.2
- ✅ Enables testing and validation with real data

### Negative

- ⚠️ Limited utility for production use cases requiring full country list
- ⚠️ Users may need to wait for full catalog or bring their own data
- ℹ️ "Preview" designation may deter some early adopters

### Neutral

- 📚 Documentation clearly states preview status
- 📅 Future expansion planned with timeline
- 🔬 Sufficient for testing, demos, and POCs

## Future Plans

### Roadmap (2025.10.3)

**Planned Enhancements**:

1. **Full Country Catalog**: 250+ countries with complete metadata
2. **Currency Codes**: ISO 4217 support (Alpha-3, numeric, symbol, decimal places)
3. **Language Codes**: ISO 639 support (Alpha-2, Alpha-3, language names)

**Research Required**:

- ISO standard data licensing compatibility with OSS (Apache 2.0)
- Source data validation and quality assurance
- Crucible catalog structure for multi-standard support

**Preliminary Assessment**:

- Plenty of OSS tools and files reference ISO standards
- Wikipedia and other open sources provide ISO data
- Need legal/licensing review before shipping full datasets

### Migration Path

**Current (v0.1.2)**:

```python
countries = list_countries()  # Returns 5 countries
len(countries)  # 5
```

**Future (v0.2.x)**:

```python
countries = list_countries()  # Returns 250+ countries
len(countries)  # 250+

# No API changes, same methods work
country = get_country("FI")  # Finland - NEW
country = get_country_by_alpha3("FIN")  # NEW
country = get_country_by_numeric("246")  # NEW
```

**Migration Required**: None - API is stable, data expands seamlessly

## Implementation

**Files Modified**:

- `src/pyfulmen/foundry/README.md:548` - Key Features list states "5 sample countries"
- `src/pyfulmen/foundry/README.md:589` - Crucible conformance notes Phase 2E completion
- `docs/crucible-py/library/foundry/country-codes.yaml` - Data source (5 entries)

**Documentation Examples**:

README Key Features section:

```markdown
**Key Features:**

- **Case-insensitive** alpha code matching ("us" → "US")
- **Automatic zero-padding** for numeric codes ("76" → "076")
- **O(1) lookups** via precomputed indexes
- **5 sample countries**: US, CA, JP, DE, BR
```

Crucible Standards Conformance section:

```markdown
**Country Code Catalog (Phase 2E)**

- ISO 3166-1 Alpha-2/Alpha-3/Numeric lookups
- Case-insensitive validation with `validate_country_code()`
- Numeric zero-padding canonicalization ("76" → "076")
- O(1) lookups via precomputed indexes
- 5 sample countries from Crucible catalog (US, CA, JP, DE, BR)
```

## User Communication

### For Users Needing Full Catalog Now

**Option 1: Wait for v0.2.x**

- Timeline: 2025 Q4 (estimated)
- Includes full catalog + currency codes + language codes

**Option 2: Extend Catalog Locally**

- Create custom YAML file with additional countries
- Use ConfigLoader override mechanism
- Maintain private catalog until official release

**Option 3: Use Alternative Library**

- pycountry (full ISO data)
- Trade-off: No Fulmen integration, different API

### Setting Expectations

Clear communication in:

- README (Key Features section)
- API documentation (module docstrings)
- GitHub Issues (pinned note about catalog status)
- Release notes (v0.1.2 changelog)

## References

- [ISO 3166-1 Standard](https://www.iso.org/iso-3166-country-codes.html)
- [pycountry](https://github.com/flyingcircusio/pycountry) - Reference for full ISO data
- [Wikipedia ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1) - Open data source
- Crucible Feature Planning: 2025.10.3 discussion

## Success Metrics

**v0.1.2 Goals (Met)**:

- ✅ API surface fully defined and stable
- ✅ All three lookup formats working (Alpha-2, Alpha-3, Numeric)
- ✅ Comprehensive test coverage (33 tests)
- ✅ Documentation complete with examples
- ✅ Cross-language parity with gofulmen v0.1.1

**v0.2.x Goals (Planned)**:

- ⏳ Full 250+ country catalog
- ⏳ Currency code support
- ⏳ Language code support
- ⏳ ISO data licensing research complete

---

_Last Updated: 2025-10-15_
