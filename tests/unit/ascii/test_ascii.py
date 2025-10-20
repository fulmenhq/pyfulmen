"""
Tests for pyfulmen.ascii box drawing functionality.

Tests box drawing, string width calculation, and Unicode handling.
"""


from pyfulmen.ascii import (
    BoxChars,
    BoxOptions,
    draw_box,
    draw_box_with_options,
    max_content_width,
    string_width,
)


class TestStringWidth:
    """Test string width calculation."""

    def test_ascii_string(self):
        """ASCII strings should have width equal to length."""
        assert string_width("Hello") == 5
        assert string_width("Test") == 4

    def test_empty_string(self):
        """Empty string should have width 0."""
        assert string_width("") == 0

    def test_unicode_string(self):
        """Unicode strings should be measured correctly."""
        # Most ASCII-like characters
        assert string_width("Café") == 4

    def test_emoji(self):
        """Emoji width depends on terminal (usually 2)."""
        # Without terminal overrides, wcwidth gives us the standard width
        width = string_width("🚀")
        assert width >= 1  # Could be 1 or 2 depending on wcwidth

    def test_multiline_not_supported(self):
        """string_width measures single line (newlines counted as chars)."""
        # Note: string_width doesn't split lines, it measures the raw string
        result = string_width("Hello\nWorld")
        assert result >= 10  # At minimum, the character count

    def test_emoji_with_variation_selector(self):
        """Emoji with variation selectors should not crash (multi-codepoint)."""
        # These emoji have variation selectors (U+FE0F) making them multi-codepoint
        # Regression test for TypeError: ord() expected a character
        assert string_width("✌️") == 2
        assert string_width("☠️") == 2
        assert string_width("⚠️") == 2
        assert string_width("🛠️") == 2

    def test_string_with_emoji_variation_selector(self):
        """Strings containing emoji with variation selectors should work."""
        # test✌️test should be: t(1) + e(1) + s(1) + t(1) + ✌️(2) + t(1) + e(1) + s(1) + t(1) = 10
        assert string_width("test✌️test") == 10

    def test_multiple_emoji_with_variation_selectors(self):
        """Multiple emoji with variation selectors in one string."""
        # Each emoji is width 2
        result = string_width("✌️☠️⚠️")
        assert result == 6  # 3 emoji * 2 width each


class TestMaxContentWidth:
    """Test max content width calculation."""

    def test_single_string(self):
        """Single string should return its width."""
        assert max_content_width(["Hello"]) == 5

    def test_multiple_strings(self):
        """Should return width of longest string."""
        contents = ["Short", "Medium length", "Long"]
        assert max_content_width(contents) == 13  # "Medium length"

    def test_empty_list(self):
        """Empty list should return 0."""
        assert max_content_width([]) == 0

    def test_multiline_content(self):
        """Should handle multiline strings correctly."""
        contents = ["Line 1\nLonger line 2", "Short"]
        # Should find the longest line across all content
        width = max_content_width(contents)
        assert width >= 13  # "Longer line 2"


class TestDrawBox:
    """Test simple box drawing."""

    def test_simple_box(self):
        """Should draw a basic box around content."""
        result = draw_box("Hello")
        assert "Hello" in result
        assert "┌" in result  # Top-left
        assert "┐" in result  # Top-right
        assert "└" in result  # Bottom-left
        assert "┘" in result  # Bottom-right
        assert "─" in result  # Horizontal
        assert "│" in result  # Vertical

    def test_box_structure(self):
        """Box should have proper structure."""
        result = draw_box("Test")
        lines = result.strip().split("\n")
        assert len(lines) == 3  # Top border, content, bottom border

    def test_multiline_content(self):
        """Should handle multiline content."""
        result = draw_box("Line 1\nLine 2")
        lines = result.strip().split("\n")
        assert len(lines) == 4  # Top border, 2 content lines, bottom border

    def test_minimum_width(self):
        """Should respect minimum width parameter."""
        result = draw_box("Hi", width=20)
        lines = result.strip().split("\n")
        # Check that the box is at least 20 chars wide (plus borders)
        assert len(lines[0]) >= 22  # 20 content + 2 for borders

    def test_empty_content(self):
        """Should handle empty content."""
        result = draw_box("")
        assert "┌" in result
        assert "└" in result


class TestDrawBoxWithOptions:
    """Test advanced box drawing with options."""

    def test_custom_characters(self):
        """Should use custom box characters."""
        custom_chars = BoxChars(
            top_left="╔",
            top_right="╗",
            bottom_left="╚",
            bottom_right="╝",
            horizontal="═",
            vertical="║",
        )
        options = BoxOptions(chars=custom_chars)
        result = draw_box_with_options("Test", options)

        assert "╔" in result
        assert "╗" in result
        assert "╚" in result
        assert "╝" in result
        assert "═" in result
        assert "║" in result

    def test_min_width(self):
        """Should enforce minimum width."""
        options = BoxOptions(min_width=30)
        result = draw_box_with_options("Short", options)
        lines = result.strip().split("\n")
        # Box should be at least 30 chars wide
        assert len(lines[0]) >= 32  # 30 + 2 for borders

    def test_max_width_truncates(self):
        """Should truncate content if it exceeds max_width (matches gofulmen)."""
        options = BoxOptions(max_width=5)
        result = draw_box_with_options("This is a very long string", options)
        # Should truncate to max_width, not raise error
        assert result  # Box should be created
        lines = result.strip().split("\n")
        # Content line should be truncated
        content_line = lines[1]
        assert len(content_line) <= 5 + 4  # max_width + border/padding chars

    def test_max_width_with_cjk(self):
        """Truncation should respect CJK character width (regression test)."""
        # CJK characters are width-2, so max_width=3 should fit only 1 char
        options = BoxOptions(max_width=3)
        result = draw_box_with_options("中文测试", options)
        lines = result.strip().split("\n")

        # Box width should be 3 (max_width)
        top_border = lines[0]
        content_line = lines[1]
        bottom_border = lines[2]

        # All lines should have same DISPLAY WIDTH (not character count)
        # "中" is 1 character but 2 display width, so char counts will differ
        assert string_width(top_border) == string_width(content_line) == string_width(bottom_border)

        # Content should be "中" (width 2) with 1 space padding to reach width 3
        assert "中" in content_line
        assert "文" not in content_line  # Second char should be truncated

    def test_max_width_with_emoji(self):
        """Truncation should respect emoji width (regression test)."""
        # Emoji are typically width-2, so max_width=3 should fit only 1 emoji
        options = BoxOptions(max_width=3)
        result = draw_box_with_options("🎉🎊🎈", options)
        lines = result.strip().split("\n")

        content_line = lines[1]
        # Should contain first emoji but not the others
        assert "🎉" in content_line
        assert "🎊" not in content_line
        assert "🎈" not in content_line

    def test_max_width_mixed_width_chars(self):
        """Truncation should handle mixed ASCII and CJK correctly."""
        # "test中文" = t(1) + e(1) + s(1) + t(1) + 中(2) + 文(2) = 8 total
        # max_width=5 should give us "test中" = 1+1+1+1+2 = 6, but that exceeds
        # Actually: "test" = 4, can't fit "中" (would be 6), so just "test"
        options = BoxOptions(max_width=5)
        result = draw_box_with_options("test中文", options)
        lines = result.strip().split("\n")

        content_line = lines[1]
        assert "test" in content_line
        # Whether 中 fits depends on exact width calculation
        # With max_width=5, "test"=4, "中"=2, total would be 6 which exceeds 5
        # So 中 should NOT be included
        assert "中" not in content_line

    def test_max_width_with_short_content(self):
        """Short content should work fine with max_width."""
        options = BoxOptions(max_width=20)
        result = draw_box_with_options("Short", options)
        assert "Short" in result

    def test_min_and_max_width(self):
        """Should handle both min and max width."""
        options = BoxOptions(min_width=10, max_width=20)
        result = draw_box_with_options("Medium", options)
        lines = result.strip().split("\n")
        # Should be at least min_width
        assert len(lines[0]) >= 12  # 10 + 2 for borders

    def test_multiline_with_options(self):
        """Should handle multiline content with options."""
        options = BoxOptions(min_width=15)
        result = draw_box_with_options("Line 1\nLine 2\nLine 3", options)
        lines = result.strip().split("\n")
        assert len(lines) == 5  # Top border, 3 content lines, bottom border


class TestBoxAlignment:
    """Test box alignment for multiple boxes."""

    def test_align_multiple_boxes(self):
        """Should be able to align multiple boxes to same width."""
        contents = ["Short", "Medium length", "Long"]
        max_w = max_content_width(contents)

        results = []
        for content in contents:
            box = draw_box_with_options(content, BoxOptions(min_width=max_w))
            results.append(box)

        # All boxes should have the same width
        widths = [len(box.strip().split("\n")[0]) for box in results]
        assert len(set(widths)) == 1  # All widths are the same


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_unicode_content(self):
        """Should handle Unicode content correctly."""
        result = draw_box("Café ☕")
        assert "Café" in result
        assert "☕" in result

    def test_very_long_single_line(self):
        """Should handle very long single lines."""
        long_content = "A" * 100
        result = draw_box(long_content)
        assert long_content in result

    def test_many_short_lines(self):
        """Should handle many short lines."""
        content = "\n".join(["Line"] * 20)
        result = draw_box(content)
        lines = result.strip().split("\n")
        assert len(lines) == 22  # Top border, 20 content lines, bottom border

    def test_mixed_width_lines(self):
        """Should handle lines of different widths."""
        content = "Short\nMedium sized line\nX"
        result = draw_box(content)
        lines = result.strip().split("\n")

        # All content lines should be padded to the same width
        content_lines = lines[1:-1]  # Exclude borders
        # Check that padding is applied (right side has spaces before │)
        for line in content_lines:
            assert line.endswith("│")
            assert line.startswith("│")


class TestBoxCharsModel:
    """Test BoxChars data model."""

    def test_default_chars(self):
        """Default box chars should use Unicode box drawing."""
        chars = BoxChars()
        assert chars.top_left == "┌"
        assert chars.top_right == "┐"
        assert chars.bottom_left == "└"
        assert chars.bottom_right == "┘"
        assert chars.horizontal == "─"
        assert chars.vertical == "│"

    def test_custom_chars(self):
        """Should allow custom characters."""
        chars = BoxChars(
            top_left="+",
            top_right="+",
            bottom_left="+",
            bottom_right="+",
            horizontal="-",
            vertical="|",
        )
        assert chars.top_left == "+"
        assert chars.horizontal == "-"


class TestBoxOptionsModel:
    """Test BoxOptions data model."""

    def test_default_options(self):
        """Default options should have sensible defaults."""
        opts = BoxOptions()
        assert opts.min_width == 0
        assert opts.max_width == 0
        assert opts.chars is None

    def test_custom_options(self):
        """Should allow custom options."""
        chars = BoxChars()
        opts = BoxOptions(min_width=10, max_width=50, chars=chars)
        assert opts.min_width == 10
        assert opts.max_width == 50
        assert opts.chars == chars
