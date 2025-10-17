"""
Box drawing and string width utilities for pyfulmen.ascii.

Provides Unicode-aware box drawing with terminal-specific width adjustments.
"""

from typing import Optional

try:
    import wcwidth
    HAS_WCWIDTH = True
except ImportError:
    HAS_WCWIDTH = False

from .models import BoxChars, BoxOptions
from .terminal import get_terminal_config


def string_width(s: str) -> int:
    """
    Calculate the display width of a string, accounting for Unicode and terminal overrides.

    Uses wcwidth library if available, falls back to len() otherwise.
    Applies terminal-specific overrides from configuration.

    Args:
        s: String to measure

    Returns:
        Display width in terminal columns

    Example:
        >>> string_width("Hello")
        5
        >>> string_width("Café")
        4
        >>> string_width("🚀")  # May be 1 or 2 depending on terminal
        2
    """
    # Get terminal-specific overrides
    terminal_config = get_terminal_config()

    # Calculate base width
    if HAS_WCWIDTH:
        base_width = wcwidth.wcswidth(s)
        # wcswidth returns -1 for control characters
        if base_width < 0:
            base_width = len(s)
    else:
        # Fallback: simple character count
        base_width = len(s)

    # Apply terminal-specific overrides if available
    if terminal_config and terminal_config.overrides:
        adjustment = 0
        for char, expected_width in terminal_config.overrides.items():
            count = s.count(char)
            if count > 0:
                if HAS_WCWIDTH:
                    current_width = wcwidth.wcwidth(char)
                    if current_width >= 0:
                        adjustment += count * (expected_width - current_width)
                else:
                    # Fallback: assume char is 1 wide
                    adjustment += count * (expected_width - 1)

        if adjustment != 0:
            return base_width + adjustment

    return base_width


def max_content_width(contents: list[str]) -> int:
    """
    Calculate the maximum display width across multiple content strings.

    Useful for aligning multiple boxes to the same width.

    Args:
        contents: List of content strings

    Returns:
        Maximum width across all strings

    Example:
        >>> contents = ["Short", "Medium length", "Very long content"]
        >>> max_content_width(contents)
        18
    """
    max_width = 0
    for content in contents:
        lines = content.split("\n")
        for line in lines:
            width = string_width(line)
            if width > max_width:
                max_width = width
    return max_width


def draw_box(content: str, width: int = 0) -> str:
    """
    Draw a box around the given content with a minimum width.

    The box will expand to fit content, but never be smaller than the width parameter.

    Args:
        content: Multi-line string to box
        width: Minimum width (0 = auto-size to content)

    Returns:
        Boxed content as a string with newlines

    Example:
        >>> box = draw_box("Hello\\nWorld", 20)
        >>> print(box)
        ┌──────────────────────┐
        │ Hello                │
        │ World                │
        └──────────────────────┘
    """
    return draw_box_with_options(content, BoxOptions(min_width=width))


def draw_box_with_options(content: str, options: BoxOptions) -> str:
    """
    Draw a box with advanced options for width constraints and styling.

    Args:
        content: Multi-line string to box
        options: BoxOptions configuring behavior

    Returns:
        Boxed content as a string with newlines

    Raises:
        ValueError: If content exceeds max_width (when max_width > 0)

    Example - Aligned boxes:
        >>> boxes = ["Short", "Medium length", "Very long content"]
        >>> max_w = max_content_width(boxes)
        >>> for content in boxes:
        ...     print(draw_box_with_options(content, BoxOptions(min_width=max_w)))

    Example - Width limits:
        >>> box = draw_box_with_options(
        ...     content,
        ...     BoxOptions(min_width=40, max_width=80)
        ... )
    """
    # Get box characters (use defaults if not specified)
    chars = options.chars if options.chars else BoxChars()

    lines = content.split("\n")

    # Find content width
    content_width = 0
    for line in lines:
        line_width = string_width(line)
        if line_width > content_width:
            content_width = line_width

    # Apply width constraints
    box_width = content_width
    if options.min_width > 0 and box_width < options.min_width:
        box_width = options.min_width
    if options.max_width > 0 and content_width > options.max_width:
        # Content exceeds max width - this is an error condition
        raise ValueError(
            f"Content width {content_width} exceeds maximum width {options.max_width}"
        )

    # Build the box
    result = []

    # Top border
    top_border = chars.top_left + (chars.horizontal * (box_width + 2)) + chars.top_right
    result.append(top_border)

    # Content lines
    for line in lines:
        line_width = string_width(line)

        # Handle truncation if max_width exceeded (shouldn't happen after check above)
        if options.max_width > 0 and line_width > options.max_width:
            # Truncate at character boundaries (simple truncation)
            truncated_line = line[:options.max_width]
            line = truncated_line
            line_width = string_width(truncated_line)

        # Padding to reach box width
        padding = box_width - line_width
        padding_str = " " * padding if padding > 0 else ""

        content_line = chars.vertical + " " + line + padding_str + " " + chars.vertical
        result.append(content_line)

    # Bottom border
    bottom_border = chars.bottom_left + (chars.horizontal * (box_width + 2)) + chars.bottom_right
    result.append(bottom_border)

    return "\n".join(result) + "\n"
