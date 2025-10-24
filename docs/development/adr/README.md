# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for PyFulmen. ADRs document significant architectural and design decisions made during development, including context, alternatives considered, and consequences.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision along with its context and consequences. ADRs help:

- **Future Maintainers**: Understand why decisions were made
- **New Contributors**: Learn the architectural philosophy
- **Decision Review**: Re-evaluate choices as requirements evolve
- **Knowledge Transfer**: Preserve institutional knowledge

## ADR Format

Each ADR follows this structure:

```markdown
# ADR-XXXX: Title

**Status**: [Proposed | Accepted | Deprecated | Superseded by ADR-YYYY]
**Date**: YYYY-MM-DD
**Context**: Brief description of what prompted this
**Decision Maker**: Who made the decision
**Related ADRs**: Links to related decisions

## Context

[Background, constraints, requirements]

## Decision

[What we decided, with code examples if relevant]

## Rationale

[Why this is the right choice]

## Alternatives Considered

### Alternative 1: Name

**Pros**: ...
**Cons**: ...
**Decision**: [Accepted | Rejected] - Reason

## Consequences

### Positive

- ✅ Benefits

### Negative

- ⚠️ Trade-offs

### Neutral

- ℹ️ Neutral impacts

## Implementation

[Files modified, tests added, validation results]

## References

[Links to docs, specs, related code]

## Future Considerations

[When to reconsider this decision]
```

## When to Write an ADR

Record an architecture decision when:

- ✅ It affects public API design
- ✅ It involves performance trade-offs
- ✅ It impacts cross-language consistency (gofulmen, tsfulmen, pyfulmen)
- ✅ It requires explaining "why not X?"
- ✅ Future maintainers would ask "why did we do it this way?"
- ✅ It establishes a pattern for similar future decisions

**Don't write an ADR for**:

- ❌ Trivial implementation details
- ❌ Routine bug fixes
- ❌ Stylistic preferences covered by linter
- ❌ Temporary/experimental code

## ADR Lifecycle

### Statuses

- **Proposed**: Under discussion, not yet implemented
- **Accepted**: Approved and implemented
- **Deprecated**: No longer recommended, but not yet replaced
- **Superseded**: Replaced by a newer ADR (link to successor)

### Updating ADRs

ADRs are **immutable** once accepted. Instead of editing:

1. **Add a "Superseded by" note** to the old ADR
2. **Create a new ADR** explaining the change
3. **Link between old and new** for traceability

**Exception**: Typo fixes and clarifications are OK without new ADR.

## ADR Index

### PyFulmen Local ADRs

| ADR                                                              | Title                                         | Date       | Status   |
| ---------------------------------------------------------------- | --------------------------------------------- | ---------- | -------- |
| [ADR-0001](ADR-0001-fulmencatalogmodel-populate-by-name.md)      | FulmenCatalogModel populate_by_name=True      | 2025-10-15 | Accepted |
| [ADR-0002](ADR-0002-validate-country-code-lookup-strategy.md)    | validate_country_code() Three-Lookup Strategy | 2025-10-15 | Accepted |
| [ADR-0003](ADR-0003-country-catalog-preview-status.md)           | Country Code Catalog Preview Status           | 2025-10-15 | Accepted |
| [ADR-0004](ADR-0004-tool-config-separation.md)                   | Tool Configuration Separation                 | 2025-10-15 | Accepted |
| [ADR-0007](ADR-0007-similarity-case-insensitive-tie-breaking.md) | Similarity Case-Insensitive Tie Breaking      | 2025-10-15 | Accepted |
| [ADR-0008](ADR-0008-global-metric-registry-singleton.md)         | Global Metric Registry Singleton Pattern      | 2025-10-23 | Accepted |
| [ADR-0009](ADR-0009-fulhash-independent-stream-instances.md)     | FulHash Independent Stream Instances          | 2025-10-23 | Accepted |

| [ADR-0010](ADR-0010-pathfinder-checksum-performance-acceptable-delta.md) | Pathfinder Checksum Performance Acceptable Delta | 2025-10-24 | Accepted |

### Ecosystem ADRs (Reference)

PyFulmen implements these cross-language architectural decisions from Crucible. See [`docs/crucible-py/architecture/decisions/`](../../crucible-py/architecture/decisions/) for complete ecosystem ADRs.

**📊 Detailed adoption tracking**: See [Ecosystem Adoption Status](ecosystem-adoption-status.md) for comprehensive implementation status, test coverage, and related local ADRs.

| ADR                                                                                                | Title                             | Status   | PyFulmen Adoption |
| -------------------------------------------------------------------------------------------------- | --------------------------------- | -------- | ----------------- |
| [ADR-0001](../../crucible-py/architecture/decisions/ADR-0001-two-tier-adr-system.md)               | Two-Tier ADR System               | Accepted | Verified          |
| [ADR-0002](../../crucible-py/architecture/decisions/ADR-0002-triple-index-catalog-strategy.md)     | Triple-Index Catalog Strategy     | Proposal | Verified          |
| [ADR-0003](../../crucible-py/architecture/decisions/ADR-0003-progressive-logging-profiles.md)      | Progressive Logging Profiles      | Proposal | Verified          |
| [ADR-0004](../../crucible-py/architecture/decisions/ADR-0004-schema-driven-config-hydration.md)    | Schema-Driven Config Hydration    | Proposal | Implemented       |
| [ADR-0005](../../crucible-py/architecture/decisions/ADR-0005-camelcase-to-language-conventions.md) | CamelCase to Language Conventions | Proposal | Verified          |

**Adoption Status Levels**:

- **Verified** (40): Implemented and validated through tests/production use
- **Implemented** (30): Fully implemented, ready for validation
- **In Progress** (20): Active implementation underway
- **Planned** (10): Implementation planned but not started

**Note**: Ecosystem ADR-0002 was promoted from PyFulmen's original local ADR-0003 (Triple-Index Catalog Strategy). The local version has been removed as superseded by the ecosystem version.

### By Category

#### API Design

- [ADR-0001](ADR-0001-fulmencatalogmodel-populate-by-name.md) - Field naming flexibility (populate_by_name)
- [ADR-0002](ADR-0002-validate-country-code-lookup-strategy.md) - Multi-format validation strategy

#### Performance & Scalability

- [ADR-0002](ADR-0002-validate-country-code-lookup-strategy.md) - Sequential lookup performance analysis
- [Ecosystem ADR-0002](../../crucible-py/architecture/decisions/ADR-0002-triple-index-catalog-strategy.md) - Index structure and memory trade-offs

#### Data & Catalogs

- [Ecosystem ADR-0002](../../crucible-py/architecture/decisions/ADR-0002-triple-index-catalog-strategy.md) - Country catalog index design
- [ADR-0003](ADR-0003-country-catalog-preview-status.md) - Catalog completeness and roadmap

#### Cross-Language Consistency

- [ADR-0002](ADR-0002-validate-country-code-lookup-strategy.md) - Parity with gofulmen v0.1.1
- [Ecosystem ADR-0002](../../crucible-py/architecture/decisions/ADR-0002-triple-index-catalog-strategy.md) - gofulmen implementation match

#### DevOps & Tooling

- [ADR-0004](ADR-0004-tool-config-separation.md) - Tool configuration separation (DRY principle)

## Architectural Principles

These ADRs reflect PyFulmen's core architectural principles:

### 1. Developer Experience First

- Pythonic APIs (snake_case, intuitive behavior)
- Least surprise principle
- Clear documentation and examples

### 2. Performance Through Simplicity

- O(1) operations where possible
- Lazy loading to defer work
- Bounded complexity (no premature optimization)

### 3. Maintainability

- Clear intent in code
- Easy to test and verify
- Future-proof without over-engineering

### 4. Cross-Language Consistency

- API parity with gofulmen, tsfulmen
- Same data structures and algorithms
- Standards compliance (ISO, Crucible)

## Contributing

### Proposing a New ADR

1. **Discuss First**: Open a GitHub issue or discuss in development channel
2. **Create Draft**: Copy template, fill in context and alternatives
3. **Review**: Share with maintainers for feedback
4. **Number**: Maintainers assign next ADR number
5. **Commit**: Add to repository with descriptive commit message

### ADR Numbering

- Use 4-digit zero-padded numbers (0001, 0002, ...)
- Numbers assigned sequentially by maintainers
- Gaps are OK (if ADRs are rejected/withdrawn)

### File Naming

Format: `ADR-XXXX-kebab-case-title.md`

**Good**:

- `ADR-0001-fulmencatalogmodel-populate-by-name.md`
- `ADR-0002-validate-country-code-lookup-strategy.md`

**Bad**:

- `adr-1.md` (no zero-padding)
- `0001.md` (missing ADR- prefix and descriptive title)
- `ADR-0001-some-decision-about-a-thing.md` (too vague)

## References

### ADR Philosophy

- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) - Michael Nygard (original ADR concept)
- [ADR GitHub Organization](https://adr.github.io/) - Tools and templates

### Fulmen Standards

- [Fulmen Helper Library Standard](../../crucible-py/architecture/fulmen-helper-library-standard.md)
- [PyFulmen Overview](../../pyfulmen_overview.md)
- [Operations Guide](../operations.md)

### Related Practices

- [Architectural Decision Records at GoCardless](https://github.com/gocardless/developer-handbook/blob/master/architectural-decision-records.md)
- [Architecture Decision Record (ADR) at Spotify](https://engineering.atspotify.com/2020/04/architecture-decision-records/)

---

_This ADR index is maintained by the PyFulmen Architect team. Last updated: 2025-10-15_
