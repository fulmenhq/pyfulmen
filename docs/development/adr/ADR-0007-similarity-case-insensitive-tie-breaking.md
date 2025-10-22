# ADR-0007: Similarity Suggestion Case-Insensitive Tie-Breaking

**Status**: Accepted  
**Date**: 2025-10-22  
**Author**: PyFulmen Architect (@pyfulmen-architect)  
**Supervised by**: @3leapsdave

## Context

The `foundry.similarity.suggest()` function returns ranked suggestions sorted by similarity score (descending). When multiple candidates have identical scores (e.g., all 1.0 for exact matches after normalization), we need a deterministic tie-breaking strategy.

The Crucible SSOT fixtures expect case-insensitive alphabetical ordering with lowercase-first preference:
- "docscribe" before "Docscribe" before "DocScribe"

Standard Python string sorting uses lexicographic (ASCII) ordering where uppercase letters come before lowercase:
- "DocScribe" before "Docscribe" before "docscribe"

## Decision

We implement **case-insensitive alphabetical tie-breaking with lowercase preference** using a multi-key sort:

```python
scored_candidates.sort(
    key=lambda s: (
        -s.score,                                    # Primary: score descending
        s.value.lower(),                             # Secondary: case-insensitive alpha
        sum(1 for c in s.value if c.isupper()),     # Tertiary: uppercase count
        s.value                                      # Quaternary: exact value
    )
)
```

This produces the ordering:
1. Highest similarity score first
2. Case-insensitive alphabetical order (e.g., "docscribe" groups with "Docscribe")
3. Within same case-folded value, prefer fewer uppercase letters (lowercase → Title Case → camelCase)
4. If all else equal, use exact string as final tie-breaker

## Rationale

### Why Case-Insensitive?

1. **User Experience**: When suggestions have identical scores after normalization, users expect alphabetical ordering that matches their mental model (where "apple", "Apple", and "APPLE" are treated as the same word).

2. **Fixture Compliance**: Crucible SSOT fixtures explicitly expect this behavior for cross-language consistency.

3. **Predictability**: Case-sensitive lexicographic ordering (ASCII) is surprising to users unfamiliar with character encoding details.

### Why Lowercase First?

Within case-insensitive groups, preferring lowercase → Title Case → CamelCase provides:

1. **Convention Alignment**: Most documentation and user-facing text uses lowercase or Title Case over ALL CAPS or camelCase.

2. **Readability**: Lowercase text is generally more readable in "Did you mean...?" prompts.

3. **Consistency**: Matches common sorting behavior in tools like `sort -f` (fold case, prefer lowercase).

## Examples

```python
from pyfulmen.foundry import similarity

# All have score 1.0 after normalization
suggestions = similarity.suggest(
    "DOCSCRIBE",
    ["DocScribe", "docscribe", "Docscribe", "DOCSCRIBE"],
    min_score=0.9,
    normalize_text=True
)

# Result order: docscribe, Docscribe, DocScribe, DOCSCRIBE
# ✓ Case-insensitive: all "docscribe" variants grouped
# ✓ Lowercase first: "docscribe" before capitalized variants
# ✓ Uppercase count: Docscribe (1 upper) before DocScribe (2 upper) before DOCSCRIBE (9 upper)
```

## Consequences

### Positive

- **Fixture Compliance**: Passes all Crucible SSOT suggestion fixtures with case-insensitive tie-breaking.
- **User Experience**: More intuitive suggestion ordering for CLI tools and error messages.
- **Cross-Language Consistency**: Matches behavior expected by gofulmen and tsfulmen implementations.

### Negative

- **Complexity**: Sort key is more complex than simple lexicographic ordering.
- **Performance**: Minimal overhead (O(n) for uppercase counting on each string during sort).
- **Deviation from Python Default**: Differs from Python's built-in string sorting (but this is intentional).

### Neutral

- **Case Sensitivity Preserved**: Original casing is preserved in returned values; only tie-breaking logic is case-insensitive.
- **Scope Limited**: Only affects tie-breaking when scores are equal. Primary sort by score is unaffected.

## Alternatives Considered

### 1. Lexicographic (ASCII) Ordering

```python
scored_candidates.sort(key=lambda s: (-s.score, s.value))
```

**Rejected**: Fails Crucible fixtures and produces counter-intuitive ordering for users.

### 2. Simple Case-Insensitive

```python
scored_candidates.sort(key=lambda s: (-s.score, s.value.lower(), s.value))
```

**Rejected**: Without uppercase count, "DocScribe" would come before "Docscribe" due to ASCII values, failing fixtures.

### 3. Locale-Aware Collation

Use `locale.strcoll()` or `PyICU` for locale-aware sorting.

**Rejected**: 
- Adds complexity and dependency
- Locale behavior varies by system
- Crucible fixtures don't specify locale requirements beyond Turkish casefold
- Overkill for tie-breaking edge case

## References

- Crucible Fixture: `config/crucible-py/library/foundry/similarity-fixtures.yaml` (Case-insensitive exact match test)
- Foundry Standard: `docs/crucible-py/standards/library/foundry/similarity.md` (Section: Suggestion API)
- Implementation: `src/pyfulmen/foundry/similarity/_suggest.py` (Lines 88-95)

## Status: Accepted

This decision is accepted and implemented in v0.1.5.

---

_Generated by PyFulmen Architect (@pyfulmen-architect) ([OpenCode](https://github.com/sst/opencode)) under supervision of @3leapsdave_

Co-Authored-By: PyFulmen Architect <noreply@3leaps.net>  
Committer-of-Record: Dave Thompson <dave.thompson@3leaps.net> [@3leapsdave]
