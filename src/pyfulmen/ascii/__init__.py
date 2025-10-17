"""
ASCII Helpers - Box drawing and terminal utilities for pyfulmen.

This module provides Unicode-aware box drawing for console output with
terminal-specific width adjustments. Follows gofulmen conventions for
consistent cross-language behavior.

Key Features:
- Box drawing with customizable characters
- Unicode-aware string width calculation
- Terminal-specific character width overrides
- Three-layer configuration (defaults, user, BYOC)

Example - Simple box:
    >>> from pyfulmen.ascii import draw_box
    >>> print(draw_box("Hello, World!"))
    ┌───────────────┐
    │ Hello, World! │
    └───────────────┘

Example - Advanced options:
    >>> from pyfulmen.ascii import draw_box_with_options, BoxOptions, BoxChars
    >>> custom_chars = BoxChars(
    ...     top_left="╔", top_right="╗",
    ...     bottom_left="╚", bottom_right="╝",
    ...     horizontal="═", vertical="║"
    ... )
    >>> options = BoxOptions(min_width=30, chars=custom_chars)
    >>> print(draw_box_with_options("Hello!", options))
    ╔════════════════════════════════╗
    ║ Hello!                         ║
    ╚════════════════════════════════╝

Example - Terminal configuration:
    >>> from pyfulmen.ascii import get_terminal_config
    >>> config = get_terminal_config()
    >>> if config:
    ...     print(f"Terminal: {config.name}")
    ...     print(f"Overrides: {config.overrides}")
"""

from .ascii import draw_box, draw_box_with_options, max_content_width, string_width
from .models import BoxChars, BoxOptions, TerminalConfig, TerminalOverrides
from .terminal import (
    get_all_terminal_configs,
    get_terminal_config,
    reload_terminal_overrides,
    set_terminal_config,
    set_terminal_overrides,
)

__all__ = [
    # Box drawing functions
    "draw_box",
    "draw_box_with_options",
    "string_width",
    "max_content_width",
    # Data models
    "BoxChars",
    "BoxOptions",
    "TerminalConfig",
    "TerminalOverrides",
    # Terminal configuration
    "get_terminal_config",
    "get_all_terminal_configs",
    "set_terminal_overrides",
    "set_terminal_config",
    "reload_terminal_overrides",
]
