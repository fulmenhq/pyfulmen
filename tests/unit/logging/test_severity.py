"""Tests for pyfulmen.logging.severity module."""

import logging

from pyfulmen.logging.severity import Severity, from_python_level, to_python_level


def test_severity_enum():
    """Test Severity enum values."""
    assert Severity.DEBUG == "debug"
    assert Severity.INFO == "info"
    assert Severity.WARN == "warn"
    assert Severity.ERROR == "error"
    assert Severity.CRITICAL == "critical"


def test_to_python_level_from_enum():
    """Test converting Severity enum to Python level."""
    assert to_python_level(Severity.DEBUG) == logging.DEBUG
    assert to_python_level(Severity.INFO) == logging.INFO
    assert to_python_level(Severity.WARN) == logging.WARNING
    assert to_python_level(Severity.ERROR) == logging.ERROR
    assert to_python_level(Severity.CRITICAL) == logging.CRITICAL


def test_to_python_level_from_string():
    """Test converting string severity to Python level."""
    assert to_python_level("debug") == logging.DEBUG
    assert to_python_level("info") == logging.INFO
    assert to_python_level("warn") == logging.WARNING
    assert to_python_level("error") == logging.ERROR
    assert to_python_level("critical") == logging.CRITICAL


def test_to_python_level_case_insensitive():
    """Test severity conversion is case-insensitive."""
    assert to_python_level("DEBUG") == logging.DEBUG
    assert to_python_level("Info") == logging.INFO
    assert to_python_level("WARN") == logging.WARNING


def test_to_python_level_unknown():
    """Test unknown severity defaults to INFO."""
    assert to_python_level("unknown") == logging.INFO
    assert to_python_level("") == logging.INFO


def test_from_python_level():
    """Test converting Python level to Severity."""
    assert from_python_level(logging.DEBUG) == Severity.DEBUG
    assert from_python_level(logging.INFO) == Severity.INFO
    assert from_python_level(logging.WARNING) == Severity.WARN
    assert from_python_level(logging.ERROR) == Severity.ERROR
    assert from_python_level(logging.CRITICAL) == Severity.CRITICAL


def test_from_python_level_boundaries():
    """Test level conversion at boundaries."""
    # Just below thresholds
    assert from_python_level(5) == Severity.DEBUG  # < DEBUG (10)
    assert from_python_level(15) == Severity.DEBUG  # < INFO (20)
    assert from_python_level(25) == Severity.INFO  # < WARNING (30)
    assert from_python_level(35) == Severity.WARN  # < ERROR (40)
    assert from_python_level(45) == Severity.ERROR  # < CRITICAL (50)
    assert from_python_level(60) == Severity.CRITICAL  # >= CRITICAL
