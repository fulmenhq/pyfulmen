#!/usr/bin/env -S uv run python
"""ASCII Helpers Demo - Showcasing Unicode-aware console formatting.

This demo script showcases PyFulmen's ASCII helpers module capabilities:
- Box drawing with customizable characters
- Unicode-aware string width calculation
- Terminal detection and configuration
- Custom box styling (single, double, rounded, bold)

Prerequisites:
    1. Clone the pyfulmen repository
    2. Install uv package manager: https://docs.astral.sh/uv/
    3. Run from repository root directory

Setup (one-time):
    # Install uv if not already installed
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Clone and setup repository
    cd /path/to/pyfulmen
    uv sync  # Creates .venv and installs dependencies

Usage:
    # From repository root (recommended - uses shebang)
    ./scripts/demos/ascii_demo.py

    # Or explicitly with uv run (works from any directory in repo)
    uv run python scripts/demos/ascii_demo.py

    # Or with activated virtual environment
    source .venv/bin/activate
    python scripts/demos/ascii_demo.py

Note:
    - This script adds src/ to Python path for development environment
    - Does NOT require pyfulmen to be installed via pip
    - Designed for developers working on the library itself
"""

import os
import sys
from pathlib import Path

# Add src to path for development environment
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

from pyfulmen.ascii import (
    BoxChars,
    BoxOptions,
    draw_box,
    draw_box_with_options,
    get_terminal_config,
    max_content_width,
    string_width,
)


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def demo_terminal_detection() -> None:
    """Demonstrate terminal detection capabilities."""
    print_section("Terminal Detection")

    config = get_terminal_config()
    if config:
        term_program = os.environ.get("TERM_PROGRAM", "unknown")
        print(f"Terminal Detected: {term_program}")
        print(f"Terminal Name: {config.name}")
        print(f"Character Overrides: {len(config.overrides)} characters")
        if config.overrides:
            print("\nSample overrides:")
            for char, width in list(config.overrides.items())[:5]:
                print(f"  '{char}' → width {width}")
        if config.notes:
            print(f"\nNotes: {config.notes}")
    else:
        print("Terminal: Generic (no specific configuration)")
        print(f"TERM_PROGRAM: {os.environ.get('TERM_PROGRAM', 'not set')}")


def demo_string_width() -> None:
    """Demonstrate Unicode-aware width calculation."""
    print_section("String Width Calculation")

    test_strings = [
        ("Hello World", "Basic ASCII"),
        ("Hello 世界", "CJK characters (double-width)"),
        ("Café ☕", "Accents and emoji"),
        ("┌─┐│└┘", "Box drawing characters"),
        ("🎉🎊🎈", "Emoji (may vary by terminal)"),
    ]

    for string, description in test_strings:
        width = string_width(string)
        print(f"{description:40} | '{string}' = {width} cells")


def demo_basic_boxes() -> None:
    """Demonstrate basic box drawing."""
    print_section("Basic Box Drawing")

    # Simple box with auto-sizing
    content = "Hello, World!"
    box = draw_box(content)
    print("Auto-sized box:")
    print(box)

    # Box with minimum width
    box = draw_box(content, width=30)
    print("Box with minimum width (30 cells):")
    print(box)

    # Multi-line content
    content = "Line 1\nLine 2\nLine 3"
    box = draw_box(content, width=25)
    print("Multi-line content:")
    print(box)


def demo_custom_box_chars() -> None:
    """Demonstrate custom box characters."""
    print_section("Custom Box Characters")

    content = "Custom Styling"

    # Double-line box
    double_chars = BoxChars(
        top_left="╔",
        top_right="╗",
        bottom_left="╚",
        bottom_right="╝",
        horizontal="═",
        vertical="║",
    )
    box = draw_box_with_options(content, BoxOptions(min_width=30, chars=double_chars))
    print("Double-line box:")
    print(box)

    # Rounded corner box
    rounded_chars = BoxChars(
        top_left="╭",
        top_right="╮",
        bottom_left="╰",
        bottom_right="╯",
        horizontal="─",
        vertical="│",
    )
    box = draw_box_with_options(content, BoxOptions(min_width=30, chars=rounded_chars))
    print("Rounded corner box:")
    print(box)

    # Bold/heavy box
    bold_chars = BoxChars(
        top_left="┏",
        top_right="┓",
        bottom_left="┗",
        bottom_right="┛",
        horizontal="━",
        vertical="┃",
    )
    box = draw_box_with_options(content, BoxOptions(min_width=30, chars=bold_chars))
    print("Bold/heavy box:")
    print(box)


def demo_unicode_content() -> None:
    """Demonstrate boxes with Unicode content."""
    print_section("Unicode Content")

    # CJK content
    content = "English: Hello World\n中文: 你好世界\n日本語: こんにちは世界"
    box = draw_box(content, width=35)
    print("International content:")
    print(box)

    # Box drawing characters in content
    content = "Nested: ┌─┐\n        │ │\n        └─┘"
    box = draw_box(content, width=20)
    print("Box characters in content:")
    print(box)


def demo_aligned_boxes() -> None:
    """Demonstrate aligned boxes using max_content_width."""
    print_section("Aligned Boxes")

    contents = [
        "Short",
        "Medium length",
        "Very long content line",
        "Multi\nLine\nContent",
    ]

    # Find maximum width
    max_width = max_content_width(contents)
    print(f"Maximum content width: {max_width} cells\n")

    # Draw all boxes with same width
    for content in contents:
        box = draw_box(content, width=max_width)
        print(box)


def demo_status_dashboard() -> None:
    """Demonstrate a practical status dashboard."""
    print_section("Practical Example: Status Dashboard")

    # System status with double-line box
    status_chars = BoxChars(
        top_left="╔",
        top_right="╗",
        bottom_left="╚",
        bottom_right="╝",
        horizontal="═",
        vertical="║",
    )

    status_content = (
        "SYSTEM STATUS\n"
        "─────────────────────────────────\n"
        "Database:    ✓ Connected\n"
        "API Server:  ✓ Running (port 8080)\n"
        "Cache:       ✓ Healthy (95% hit)\n"
        "Queue:       ⚠ 42 messages pending"
    )

    box = draw_box_with_options(
        status_content, BoxOptions(min_width=40, chars=status_chars)
    )
    print(box)


def demo_error_message() -> None:
    """Demonstrate error message formatting."""
    print_section("Practical Example: Error Message")

    error_chars = BoxChars(
        top_left="┏",
        top_right="┓",
        bottom_left="┗",
        bottom_right="┛",
        horizontal="━",
        vertical="┃",
    )

    error_content = (
        "❌ ERROR\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "File: config.yaml\n"
        "Line: 42\n"
        "Issue: Invalid YAML syntax\n"
        "\n"
        "Expected: key: value\n"
        "Got: key value (missing colon)"
    )

    box = draw_box_with_options(
        error_content, BoxOptions(min_width=45, chars=error_chars)
    )
    print(box)


def main() -> None:
    """Run all ASCII demos."""
    print("\n" + "=" * 80)
    print("  PyFulmen ASCII Helpers - Demo")
    print("  Unicode-aware console formatting for enterprise applications")
    print("=" * 80)

    demo_terminal_detection()
    demo_string_width()
    demo_basic_boxes()
    demo_custom_box_chars()
    demo_unicode_content()
    demo_aligned_boxes()
    demo_status_dashboard()
    demo_error_message()

    print("\n" + "=" * 80)
    print("  Demo Complete!")
    print("=" * 80)
    print("\nFor more information, see:")
    print("  - src/pyfulmen/ascii/README.md")
    print("  - docs/releases/v0.1.3.md (ASCII Helpers section)")
    print()


if __name__ == "__main__":
    main()
