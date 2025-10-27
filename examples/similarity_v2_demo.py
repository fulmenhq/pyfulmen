"""
Similarity v2.0.0 Feature Demonstration

Demonstrates the new capabilities in Foundry Similarity v2.0.0:
- Multiple distance metrics (Levenshtein, Damerau variants, Jaro-Winkler, substring)
- Normalization presets (none, minimal, default, aggressive)
- Enhanced suggestion API with metric selection
- Real-world use cases for each feature

Usage:
    uv run python examples/similarity_v2_demo.py
"""

from pyfulmen.foundry.similarity import (
    distance,
    score,
    suggest,
    normalize,
    apply_normalization_preset,
    substring_match,
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print("=" * 70)


def demo_distance_metrics() -> None:
    """Demonstrate different distance metrics for various use cases."""
    print_section("1. Distance Metrics - Choose the Right Algorithm")

    # Example 1: Simple typos (Levenshtein)
    print("\n📝 Example 1: Simple Typos (use Levenshtein)")
    word1, word2 = "python", "pyton"
    print(f'  Input: "{word1}" vs "{word2}"')
    print(f"  Levenshtein distance: {distance(word1, word2, metric='levenshtein')}")
    print(f"  Levenshtein score: {score(word1, word2, metric='levenshtein'):.3f}")
    print("  → Best for: Simple typos (insertions, deletions, substitutions)")

    # Example 2: Transpositions (Damerau OSA)
    print("\n🔄 Example 2: Adjacent Transpositions (use Damerau OSA)")
    word1, word2 = "algorithm", "lagorithm"
    print(f'  Input: "{word1}" vs "{word2}"')
    print(f"  Damerau OSA distance: {distance(word1, word2, metric='damerau_osa')}")
    print(f"  Damerau OSA score: {score(word1, word2, metric='damerau_osa'):.3f}")
    print("  → Best for: Typos with character swaps (teh → the)")

    # Example 3: Complex transpositions (Damerau Unrestricted)
    print("\n🔀 Example 3: Complex Transpositions (use Damerau Unrestricted)")
    word1, word2 = "CA", "ABC"
    print(f'  Input: "{word1}" vs "{word2}"')
    print(f"  Damerau OSA: {distance(word1, word2, metric='damerau_osa')}")
    print(f"  Damerau Unrestricted: {distance(word1, word2, metric='damerau_unrestricted')}")
    print("  → OSA restricts edits; Unrestricted allows more transformations")

    # Example 4: Prefix matching (Jaro-Winkler)
    print("\n🎯 Example 4: Prefix Matching (use Jaro-Winkler)")
    word1, word2 = "terraform", "terra"
    print(f'  Input: "{word1}" vs "{word2}"')
    print(f"  Jaro-Winkler score: {score(word1, word2, metric='jaro_winkler'):.3f}")
    print(f"  Levenshtein score: {score(word1, word2, metric='levenshtein'):.3f}")
    print("  → Best for: CLI command suggestions (rewards common prefixes)")

    # Example 5: Substring finding
    print("\n🔍 Example 5: Substring Matching")
    needle, haystack = "world", "hello world!"
    match_range, match_score = substring_match(needle, haystack)
    print(f'  Needle: "{needle}", Haystack: "{haystack}"')
    print(f"  Match range: {match_range}, Score: {match_score:.3f}")
    print("  → Best for: Finding common substrings in documents")


def demo_normalization_presets() -> None:
    """Demonstrate normalization presets for different matching scenarios."""
    print_section("2. Normalization Presets - Control Matching Behavior")

    text = "  Café-Zürich! 🎉  "

    print(f'\n📋 Original text: "{text}"')
    print("  (leading/trailing spaces, accents, punctuation, emoji)")

    # None preset
    normalized = apply_normalization_preset(text, "none")
    print(f'\n  none:       "{normalized}"')
    print("  → No changes (exact matching)")

    # Minimal preset
    normalized = apply_normalization_preset(text, "minimal")
    print(f'  minimal:    "{normalized}"')
    print("  → NFC normalization + trim (Unicode consistency)")

    # Default preset
    normalized = apply_normalization_preset(text, "default")
    print(f'  default:    "{normalized}"')
    print("  → NFC + casefold + trim (recommended for most use cases)")

    # Aggressive preset
    normalized = apply_normalization_preset(text, "aggressive")
    print(f'  aggressive: "{normalized}"')
    print("  → NFKD + casefold + strip accents + remove punctuation")
    print("  → Best for: Fuzzy matching, search, typo tolerance")


def demo_normalization_impact() -> None:
    """Show how normalization affects similarity scores."""
    print_section("3. Normalization Impact on Matching")

    word1, word2 = "Café", "cafe"

    print(f'\n🔤 Comparing: "{word1}" vs "{word2}"')

    # Without normalization
    dist_raw = distance(word1, word2)
    print(f"\n  Without normalization:")
    print(f"    Distance: {dist_raw} (different)")

    # With normalization (default)
    norm1 = normalize(word1, preset="default")
    norm2 = normalize(word2, preset="default")
    dist_normalized = distance(norm1, norm2)
    print(f"\n  With 'default' normalization:")
    print(f"    '{word1}' → '{norm1}'")
    print(f"    '{word2}' → '{norm2}'")
    print(f"    Distance: {dist_normalized} (still different - accents preserved)")

    # With aggressive normalization
    norm1_agg = normalize(word1, preset="aggressive")
    norm2_agg = normalize(word2, preset="aggressive")
    dist_aggressive = distance(norm1_agg, norm2_agg)
    print(f"\n  With 'aggressive' normalization:")
    print(f"    '{word1}' → '{norm1_agg}'")
    print(f"    '{word2}' → '{norm2_agg}'")
    print(f"    Distance: {dist_aggressive} (same - accents stripped)")


def demo_cli_suggestions() -> None:
    """Demonstrate CLI command suggestion use case."""
    print_section("4. CLI Command Suggestions with Jaro-Winkler")

    commands = [
        "terraform",
        "terraform-apply",
        "terraform-destroy",
        "format",
        "validate",
        "plan",
    ]

    typo = "terrafrom"

    print(f'\n💻 User typed: "{typo}"')
    print(f"  Available commands: {commands}")

    # Using Levenshtein (default)
    suggestions_lev = suggest(typo, commands, metric="levenshtein", max_suggestions=3)
    print(f"\n  With Levenshtein (edit distance):")
    for sug in suggestions_lev:
        print(f"    {sug.value:<20} (score: {sug.score:.3f})")

    # Using Jaro-Winkler (prefix-aware)
    suggestions_jw = suggest(typo, commands, metric="jaro_winkler", max_suggestions=3)
    print(f"\n  With Jaro-Winkler (prefix-aware):")
    for sug in suggestions_jw:
        print(f"    {sug.value:<20} (score: {sug.score:.3f})")

    print("\n  → Jaro-Winkler better for CLI: rewards 'terra' prefix match")


def demo_document_similarity() -> None:
    """Demonstrate document similarity with multiline text."""
    print_section("5. Document Similarity - Multiline Handling")

    doc1 = """Hello World!
This is a test document.
It has multiple lines."""

    doc2 = """Hello World!
This is a test document.
It has multiple lines."""

    doc3 = """Hello World!
This is a different document.
It has multiple lines."""

    print("\n📄 Comparing documents:")
    print(f"  Doc1 vs Doc2 (identical): {score(doc1, doc2):.3f}")
    print(f"  Doc1 vs Doc3 (one line different): {score(doc1, doc3):.3f}")

    # Find common substring
    common_range, common_score = substring_match("test document", doc1)
    print(f'\n  Finding "test document" in Doc1:')
    print(f"    Range: {common_range}, Score: {common_score:.3f}")


def demo_error_handling() -> None:
    """Demonstrate error handling for invalid inputs."""
    print_section("6. Error Handling - Clear Messages")

    print("\n❌ Example 1: Invalid metric for distance()")
    try:
        distance("hello", "world", metric="jaro_winkler")
    except ValueError as e:
        print(f"  ValueError: {e}")

    print("\n❌ Example 2: Invalid normalization preset")
    try:
        normalize("hello", preset="invalid")
    except ValueError as e:
        print(f"  ValueError: {e}")

    print("\n✅ Error messages are clear and actionable")


def demo_real_world_typos() -> None:
    """Demonstrate real-world typo correction scenarios."""
    print_section("7. Real-World Typo Correction")

    # Programming language names
    print("\n🔧 Programming Languages:")
    languages = ["python", "javascript", "typescript", "rust", "golang"]
    typos = ["pyton", "javascrpt", "typscript"]

    for typo in typos:
        suggestions = suggest(typo, languages, max_suggestions=2, min_score=0.6)
        print(f'  "{typo}" → ', end="")
        if suggestions:
            print(f"{suggestions[0].value} (score: {suggestions[0].score:.3f})")
        else:
            print("no suggestions")

    # AWS service names with normalization
    print("\n☁️  AWS Services (with normalization):")
    services = ["EC2-Instance", "S3-Bucket", "Lambda-Function"]
    typo = "s3 bucket"  # lowercase, space instead of hyphen

    print(f'  "{typo}"')
    # Use suggest with aggressive normalization preset
    suggestions = suggest(
        typo,
        services,
        max_suggestions=2,
        min_score=0.5,
        normalize_preset="aggressive",
        metric="levenshtein",
    )
    for sug in suggestions:
        print(f"    → {sug.value} (score: {sug.score:.3f})")


def main() -> None:
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  PyFulmen Similarity v2.0.0 Feature Demonstration")
    print("=" * 70)
    print("\n  This demo showcases the new v2.0.0 capabilities:")
    print("  • Multiple distance metrics for different use cases")
    print("  • Normalization presets for flexible matching")
    print("  • Enhanced suggestion API")
    print("  • Real-world typo correction examples")

    demo_distance_metrics()
    demo_normalization_presets()
    demo_normalization_impact()
    demo_cli_suggestions()
    demo_document_similarity()
    demo_real_world_typos()
    demo_error_handling()

    print("\n" + "=" * 70)
    print("  Demo Complete!")
    print("=" * 70)
    print("\n  Next Steps:")
    print("  • Read docs: src/pyfulmen/foundry/similarity/")
    print("  • Run tests: uv run pytest tests/unit/foundry/ -k similarity")
    print("  • Check fixtures: config/crucible-py/library/foundry/similarity-fixtures.yaml")
    print()


if __name__ == "__main__":
    main()
