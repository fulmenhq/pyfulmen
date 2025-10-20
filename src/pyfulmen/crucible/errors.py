"""Exception classes for Crucible asset access.

Provides specialized exceptions for asset discovery, parsing, and version
metadata errors with helpful error messages and suggestions.
"""

from __future__ import annotations


class AssetNotFoundError(Exception):
    """Raised when a requested Crucible asset cannot be found.

    Provides helpful suggestions for similar asset IDs to aid discovery.

    Attributes:
        asset_id: The asset ID that was not found
        category: Optional asset category for context ('docs', 'schemas', 'config')
        suggestions: List of similar asset IDs to suggest to the user
    """

    def __init__(
        self,
        asset_id: str,
        category: str | None = None,
        suggestions: list[str] | None = None,
    ):
        """Initialize AssetNotFoundError.

        Args:
            asset_id: The asset ID that was not found
            category: Optional asset category for context
            suggestions: List of similar asset IDs to suggest
        """
        self.asset_id = asset_id
        self.category = category
        self.suggestions = suggestions or []

        msg = f"Asset not found: {asset_id}"
        if category:
            msg += f" (category: {category})"
        if suggestions:
            msg += f"\nDid you mean: {', '.join(suggestions[:3])}"

        super().__init__(msg)


class ParseError(Exception):
    """Raised when YAML/JSON parsing fails.

    Used when frontmatter or config files contain malformed markup that
    cannot be parsed.
    """

    pass


class CrucibleVersionError(Exception):
    """Raised when Crucible version metadata cannot be determined.

    This may occur if the Crucible metadata directory is missing or
    the VERSION file cannot be read.
    """

    pass


__all__ = [
    "AssetNotFoundError",
    "ParseError",
    "CrucibleVersionError",
]
