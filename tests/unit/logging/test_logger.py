"""Tests for pyfulmen.logging.logger module."""

import logging

from pyfulmen.logging import logger
from pyfulmen.logging.severity import Severity


def test_configure_logging_default():
    """Test basic logging configuration."""
    log = logger.configure_logging(app_name="test_app")

    assert isinstance(log, logging.Logger)
    assert log.name == "test_app"
    assert log.level == logging.INFO  # Default level


def test_configure_logging_with_level():
    """Test logging configuration with custom level."""
    log = logger.configure_logging(app_name="test_debug", level=Severity.DEBUG)

    assert log.level == logging.DEBUG


def test_configure_logging_with_level_string():
    """Test logging configuration with level as string."""
    log = logger.configure_logging(app_name="test_warn", level="warn")

    assert log.level == logging.WARNING


def test_configure_logging_with_config():
    """Test logging configuration with custom config."""
    config = {"level": "error", "format": "%(levelname)s - %(message)s"}

    log = logger.configure_logging(app_name="test_config", config=config)

    assert log.level == logging.ERROR


def test_configure_logging_adds_handler():
    """Test that configure_logging adds a handler."""
    log = logger.configure_logging(app_name="test_handler")

    # Should have at least one handler
    assert len(log.handlers) > 0


def test_get_logger():
    """Test getting a logger instance."""
    log = logger.get_logger("test_module")

    assert isinstance(log, logging.Logger)
    assert log.name == "test_module"


def test_get_logger_with_level():
    """Test getting logger with custom level."""
    log = logger.get_logger("test_custom_level", level=Severity.ERROR)

    assert log.level == logging.ERROR


def test_logging_actual_output(caplog):
    """Test that logging actually produces output."""
    with caplog.at_level(logging.INFO):
        log = logger.configure_logging(app_name="test_output")
        log.info("Test message")

    assert "Test message" in caplog.text
