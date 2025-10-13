"""Tests for severity enum and mapping functions."""

import logging

from pyfulmen.logging.severity import (
    Severity,
    from_numeric_level,
    from_python_level,
    to_numeric_level,
    to_python_level,
)


class TestSeverityEnum:
    """Test Severity enum values and properties."""

    def test_severity_values(self):
        """Severity enum should have all required values."""
        assert Severity.TRACE.value == "TRACE"
        assert Severity.DEBUG.value == "DEBUG"
        assert Severity.INFO.value == "INFO"
        assert Severity.WARN.value == "WARN"
        assert Severity.ERROR.value == "ERROR"
        assert Severity.FATAL.value == "FATAL"
        assert Severity.NONE.value == "NONE"

    def test_severity_numeric_levels(self):
        """Severity enum should have correct numeric levels."""
        assert Severity.TRACE.numeric_level == 0
        assert Severity.DEBUG.numeric_level == 10
        assert Severity.INFO.numeric_level == 20
        assert Severity.WARN.numeric_level == 30
        assert Severity.ERROR.numeric_level == 40
        assert Severity.FATAL.numeric_level == 50
        assert Severity.NONE.numeric_level == 60

    def test_severity_python_levels(self):
        """Severity enum should map to Python logging levels."""
        assert Severity.TRACE.python_level == logging.DEBUG
        assert Severity.DEBUG.python_level == logging.DEBUG
        assert Severity.INFO.python_level == logging.INFO
        assert Severity.WARN.python_level == logging.WARNING
        assert Severity.ERROR.python_level == logging.ERROR
        assert Severity.FATAL.python_level == logging.CRITICAL
        assert Severity.NONE.python_level == logging.CRITICAL + 10

    def test_severity_is_string_enum(self):
        """Severity should be a string enum."""
        assert isinstance(Severity.INFO, str)
        assert Severity.INFO == "INFO"


class TestSeverityComparison:
    """Test severity comparison operators."""

    def test_severity_less_than(self):
        """Severity should support less than comparison."""
        assert Severity.TRACE < Severity.DEBUG
        assert Severity.DEBUG < Severity.INFO
        assert Severity.INFO < Severity.WARN
        assert Severity.WARN < Severity.ERROR
        assert Severity.ERROR < Severity.FATAL
        assert Severity.FATAL < Severity.NONE

    def test_severity_less_than_equal(self):
        """Severity should support less than or equal comparison."""
        assert Severity.INFO <= Severity.INFO
        assert Severity.INFO <= Severity.WARN
        assert Severity.DEBUG <= Severity.ERROR

    def test_severity_greater_than(self):
        """Severity should support greater than comparison."""
        assert Severity.FATAL > Severity.ERROR
        assert Severity.ERROR > Severity.WARN
        assert Severity.WARN > Severity.INFO
        assert Severity.INFO > Severity.DEBUG
        assert Severity.DEBUG > Severity.TRACE

    def test_severity_greater_than_equal(self):
        """Severity should support greater than or equal comparison."""
        assert Severity.WARN >= Severity.WARN
        assert Severity.ERROR >= Severity.WARN
        assert Severity.FATAL >= Severity.DEBUG

    def test_severity_equality(self):
        """Severity should support equality comparison."""
        assert Severity.INFO == Severity.INFO
        assert Severity.ERROR == Severity.ERROR
        assert Severity.INFO != Severity.WARN

    def test_severity_inequality(self):
        """Severity should support inequality comparison."""
        assert Severity.INFO != Severity.WARN
        assert Severity.DEBUG != Severity.ERROR
        assert Severity.INFO == Severity.INFO

    def test_severity_comparison_chain(self):
        """Severity comparisons should work in chains."""
        assert Severity.TRACE < Severity.DEBUG < Severity.INFO < Severity.WARN
        assert Severity.ERROR > Severity.WARN > Severity.INFO > Severity.DEBUG

    def test_severity_comparison_with_non_severity(self):
        """Comparing Severity with non-Severity should return NotImplemented."""
        result = Severity.INFO.__lt__("INFO")
        assert result == NotImplemented


class TestToPythonLevel:
    """Test to_python_level conversion function."""

    def test_to_python_level_from_enum(self):
        """Should convert Severity enum to Python logging level."""
        assert to_python_level(Severity.DEBUG) == logging.DEBUG
        assert to_python_level(Severity.INFO) == logging.INFO
        assert to_python_level(Severity.WARN) == logging.WARNING
        assert to_python_level(Severity.ERROR) == logging.ERROR
        assert to_python_level(Severity.FATAL) == logging.CRITICAL

    def test_to_python_level_from_string(self):
        """Should convert string to Python logging level."""
        assert to_python_level("DEBUG") == logging.DEBUG
        assert to_python_level("INFO") == logging.INFO
        assert to_python_level("WARN") == logging.WARNING
        assert to_python_level("ERROR") == logging.ERROR
        assert to_python_level("FATAL") == logging.CRITICAL

    def test_to_python_level_case_insensitive(self):
        """Should handle lowercase strings."""
        assert to_python_level("debug") == logging.DEBUG
        assert to_python_level("info") == logging.INFO
        assert to_python_level("warn") == logging.WARNING

    def test_to_python_level_trace_maps_to_debug(self):
        """TRACE should map to DEBUG (Python has no TRACE level)."""
        assert to_python_level(Severity.TRACE) == logging.DEBUG
        assert to_python_level("TRACE") == logging.DEBUG

    def test_to_python_level_invalid_string_defaults_to_info(self):
        """Invalid severity string should default to INFO."""
        assert to_python_level("INVALID") == logging.INFO
        assert to_python_level("unknown") == logging.INFO


class TestToNumericLevel:
    """Test to_numeric_level conversion function."""

    def test_to_numeric_level_from_enum(self):
        """Should convert Severity enum to numeric level."""
        assert to_numeric_level(Severity.TRACE) == 0
        assert to_numeric_level(Severity.DEBUG) == 10
        assert to_numeric_level(Severity.INFO) == 20
        assert to_numeric_level(Severity.WARN) == 30
        assert to_numeric_level(Severity.ERROR) == 40
        assert to_numeric_level(Severity.FATAL) == 50
        assert to_numeric_level(Severity.NONE) == 60

    def test_to_numeric_level_from_string(self):
        """Should convert string to numeric level."""
        assert to_numeric_level("TRACE") == 0
        assert to_numeric_level("INFO") == 20
        assert to_numeric_level("ERROR") == 40

    def test_to_numeric_level_case_insensitive(self):
        """Should handle lowercase strings."""
        assert to_numeric_level("debug") == 10
        assert to_numeric_level("warn") == 30

    def test_to_numeric_level_invalid_string_defaults_to_20(self):
        """Invalid severity string should default to 20 (INFO)."""
        assert to_numeric_level("INVALID") == 20
        assert to_numeric_level("unknown") == 20


class TestFromPythonLevel:
    """Test from_python_level conversion function."""

    def test_from_python_level_exact_match(self):
        """Should convert Python logging level to Severity."""
        assert from_python_level(logging.DEBUG) == Severity.DEBUG
        assert from_python_level(logging.INFO) == Severity.INFO
        assert from_python_level(logging.WARNING) == Severity.WARN
        assert from_python_level(logging.ERROR) == Severity.ERROR
        assert from_python_level(logging.CRITICAL) == Severity.FATAL

    def test_from_python_level_ranges(self):
        """Should map level ranges to appropriate Severity."""
        # 0-9 -> DEBUG
        assert from_python_level(5) == Severity.DEBUG
        # 10-19 -> DEBUG
        assert from_python_level(15) == Severity.DEBUG
        # 20-29 -> INFO
        assert from_python_level(25) == Severity.INFO
        # 30-39 -> WARN
        assert from_python_level(35) == Severity.WARN
        # 40-49 -> ERROR
        assert from_python_level(45) == Severity.ERROR
        # 50+ -> FATAL
        assert from_python_level(55) == Severity.FATAL
        assert from_python_level(100) == Severity.FATAL


class TestFromNumericLevel:
    """Test from_numeric_level conversion function."""

    def test_from_numeric_level_exact_match(self):
        """Should convert exact numeric levels to Severity."""
        assert from_numeric_level(0) == Severity.TRACE
        assert from_numeric_level(10) == Severity.DEBUG
        assert from_numeric_level(20) == Severity.INFO
        assert from_numeric_level(30) == Severity.WARN
        assert from_numeric_level(40) == Severity.ERROR
        assert from_numeric_level(50) == Severity.FATAL
        assert from_numeric_level(60) == Severity.NONE

    def test_from_numeric_level_ranges(self):
        """Should map numeric ranges to appropriate Severity."""
        # 0-9 -> TRACE
        assert from_numeric_level(5) == Severity.TRACE
        # 10-19 -> DEBUG
        assert from_numeric_level(15) == Severity.DEBUG
        # 20-29 -> INFO
        assert from_numeric_level(25) == Severity.INFO
        # 30-39 -> WARN
        assert from_numeric_level(35) == Severity.WARN
        # 40-49 -> ERROR
        assert from_numeric_level(45) == Severity.ERROR
        # 50-59 -> FATAL
        assert from_numeric_level(55) == Severity.FATAL
        # 60+ -> NONE
        assert from_numeric_level(65) == Severity.NONE
        assert from_numeric_level(100) == Severity.NONE


class TestSeverityRoundtrip:
    """Test roundtrip conversions between formats."""

    def test_roundtrip_via_python_level(self):
        """Severity -> Python level -> Severity should roundtrip."""
        for severity in [Severity.DEBUG, Severity.INFO, Severity.WARN, Severity.ERROR]:
            python_level = to_python_level(severity)
            result = from_python_level(python_level)
            assert result == severity

    def test_roundtrip_via_numeric_level(self):
        """Severity -> Numeric level -> Severity should roundtrip."""
        for severity in [
            Severity.TRACE,
            Severity.DEBUG,
            Severity.INFO,
            Severity.WARN,
            Severity.ERROR,
            Severity.FATAL,
            Severity.NONE,
        ]:
            numeric_level = to_numeric_level(severity)
            result = from_numeric_level(numeric_level)
            assert result == severity

    def test_roundtrip_via_string(self):
        """Severity -> String -> Numeric level should work."""
        severity = Severity.INFO
        string_value = severity.value
        numeric = to_numeric_level(string_value)
        assert numeric == 20
