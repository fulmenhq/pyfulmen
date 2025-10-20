"""
Box drawing and string width utilities for pyfulmen.ascii.

Provides Unicode-aware box drawing with terminal-specific width adjustments.
"""

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
                    # Handle multi-codepoint characters (emoji with variation selectors)
                    # wcwidth.wcwidth() only accepts single characters, so use wcswidth()
                    # for multi-codepoint grapheme clusters
                    if len(char) > 1:
                        # Multi-codepoint character (e.g., '✌️' = base + variation selector)
                        current_width = wcwidth.wcswidth(char)
                        if current_width < 0:
                            # Unprintable or invalid - skip this override
                            continue
                    else:
                        # Single codepoint - use wcwidth()
                        current_width = wcwidth.wcwidth(char)
                        if current_width < 0:
                            # Unprintable or invalid - skip this override
                            continue

                    adjustment += count * (expected_width - current_width)
                else:
                    # Fallback: assume char is len(char) wide (handles multi-codepoint)
                    current_width_fallback = len(char)
                    adjustment += count * (expected_width - current_width_fallback)

        if adjustment != 0:
            return base_width + adjustment

    return base_width


def _truncate_to_width(s: str, max_width: int) -> str:
    """
    Truncate string to fit within max_width display columns.

    Iterates through characters and accumulates display width until
    adding the next character would exceed max_width.

    Args:
        s: String to truncate
        max_width: Maximum display width in columns

    Returns:
        Truncated string that fits within max_width

    Example:
        >>> _truncate_to_width("中文测试", 3)
        "中"  # One CJK char = 2 width, second would exceed 3
    """
    if max_width <= 0:
        return ""

    current_width = 0
    result = []

    for char in s:
        # Calculate width of this character
        if HAS_WCWIDTH:
            # Use wcswidth for multi-codepoint characters (emoji with variation selectors)
            if len(char) > 1:
                char_width = wcwidth.wcswidth(char)
                if char_width < 0:
                    char_width = len(char)
            else:
                char_width = wcwidth.wcwidth(char)
                if char_width < 0:
                    char_width = 1
        else:
            char_width = len(char)

        # Check if adding this character would exceed max_width
        if current_width + char_width > max_width:
            break

        result.append(char)
        current_width += char_width

    return "".join(result)


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
        # Content exceeds max width - truncate to max_width (matches gofulmen behavior)
        box_width = options.max_width

    # Build the box
    result = []

    # Top border
    top_border = chars.top_left + (chars.horizontal * (box_width + 2)) + chars.top_right
    result.append(top_border)

    # Content lines
    for line in lines:
        # Truncate line if it exceeds max_width (width-aware truncation for CJK/emoji)
        if options.max_width > 0:
            line_width = string_width(line)
            if line_width > options.max_width:
                # Use width-aware truncation to handle double-width characters
                line = _truncate_to_width(line, options.max_width)
                line_width = string_width(line)
        else:
            line_width = string_width(line)

        # Padding to reach box width
        padding = box_width - line_width
        padding_str = " " * padding if padding > 0 else ""

        content_line = chars.vertical + " " + line + padding_str + " " + chars.vertical
        result.append(content_line)

    # Bottom border
    bottom_border = chars.bottom_left + (chars.horizontal * (box_width + 2)) + chars.bottom_right
    result.append(bottom_border)

    return "\n".join(result) + "\n"
