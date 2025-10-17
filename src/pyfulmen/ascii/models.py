"""
Data models for pyfulmen.ascii module.

Defines box drawing characters and configuration models.
"""

from typing import Optional

from pydantic import Field

from pyfulmen.foundry import FulmenConfigModel, FulmenDataModel


class BoxChars(FulmenDataModel):
    """
    Unicode box drawing characters.

    Attributes:
        top_left: Top-left corner character
        top_right: Top-right corner character
        bottom_left: Bottom-left corner character
        bottom_right: Bottom-right corner character
        horizontal: Horizontal line character
        vertical: Vertical line character
        cross: Cross/intersection character
    """

    top_left: str = Field(default="┌", description="Top-left corner")
    top_right: str = Field(default="┐", description="Top-right corner")
    bottom_left: str = Field(default="└", description="Bottom-left corner")
    bottom_right: str = Field(default="┘", description="Bottom-right corner")
    horizontal: str = Field(default="─", description="Horizontal line")
    vertical: str = Field(default="│", description="Vertical line")
    cross: str = Field(default="┼", description="Cross/intersection")


class BoxOptions(FulmenDataModel):
    """
    Options for box drawing behavior.

    Attributes:
        min_width: Minimum box width (0 = auto-size to content)
        max_width: Maximum box width (0 = unlimited, content exceeding raises error)
        chars: Custom box characters (None = use defaults)
    """

    min_width: int = Field(default=0, description="Minimum width (0 = auto)")
    max_width: int = Field(default=0, description="Maximum width (0 = unlimited)")
    chars: Optional[BoxChars] = Field(default=None, description="Custom box characters")


class TerminalConfig(FulmenConfigModel):
    """
    Configuration for a specific terminal emulator.

    Attributes:
        name: Human-readable terminal name
        overrides: Character to width mapping (e.g., {"🔧": 2})
        notes: Additional notes about this terminal
    """

    name: str = Field(..., description="Terminal name")
    overrides: dict[str, int] = Field(
        default_factory=dict, description="Character width overrides"
    )
    notes: str = Field(default="", description="Additional notes")


class TerminalOverrides(FulmenConfigModel):
    """
    Terminal width overrides catalog.

    Attributes:
        version: Schema version
        last_updated: Last update date
        notes: Catalog-level notes
        terminals: Terminal-specific configurations keyed by TERM_PROGRAM value
    """

    version: str = Field(..., description="Schema version")
    last_updated: str = Field(default="", description="Last update date")
    notes: str = Field(default="", description="Catalog notes")
    terminals: dict[str, TerminalConfig] = Field(
        default_factory=dict, description="Terminal configurations"
    )
