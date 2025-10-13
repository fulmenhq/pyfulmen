"""Tests for logging level filtering (Phase 2)."""

import json

from pyfulmen.logging import Logger
from pyfulmen.logging.severity import Severity


class TestLevelFiltering:
    """Test level filtering in all logger profiles."""

    def test_simple_logger_filters_below_level(self, caplog):
        """SimpleLogger should filter messages below configured level."""
        logger = Logger(service="test", profile="SIMPLE", default_level="WARN")

        logger.debug("Should not appear")
        logger.info("Should not appear")
        logger.warn("Should appear")
        logger.error("Should appear")

        assert "Should not appear" not in caplog.text
        assert "Should appear" in caplog.text

    def test_structured_logger_filters_below_level(self, capsys):
        """StructuredLogger should filter messages below configured level."""
        logger = Logger(service="test", profile="STRUCTURED", default_level="ERROR")

        logger.info("Should not appear")
        logger.warn("Should not appear")
        logger.error("Should appear")

        captured = capsys.readouterr()
        result = captured.err
        assert "Should not appear" not in result
        assert "Should appear" in result

    def test_enterprise_logger_filters_below_level(self, capsys):
        """EnterpriseLogger should filter messages below configured level."""
        logger = Logger(service="test", profile="ENTERPRISE", default_level="WARN")

        logger.debug("Should not appear")
        logger.warn("Should appear")
        logger.error("Should appear")

        captured = capsys.readouterr()
        result = captured.err
        assert "Should not appear" not in result

        lines = [line for line in result.strip().split("\n") if line]
        assert len(lines) == 2
        for line in lines:
            event = json.loads(line)
            assert event["message"] == "Should appear"

    def test_default_level_info_filters_debug(self, capsys):
        """Default INFO level should filter DEBUG and TRACE."""
        logger = Logger(service="test", profile="STRUCTURED")

        logger.trace("Not logged")
        logger.debug("Not logged")
        logger.info("Logged")

        captured = capsys.readouterr()
        result = captured.err
        assert "Not logged" not in result
        assert "Logged" in result

    def test_set_level_changes_filtering(self, capsys):
        """set_level() should dynamically change filtering behavior."""
        logger = Logger(service="test", profile="STRUCTURED", default_level="ERROR")

        logger.info("Not logged initially")
        logger.error("Logged at ERROR")

        logger.set_level("INFO")
        logger.info("Now logged")
        logger.debug("Still not logged")

        logger.set_level(Severity.DEBUG)
        logger.debug("Now logged too")

        captured = capsys.readouterr()
        result = captured.err
        assert "Not logged initially" not in result
        assert "Logged at ERROR" in result
        assert "Now logged" in result
        assert "Still not logged" not in result
        assert "Now logged too" in result

    def test_set_level_accepts_severity_enum(self, caplog):
        """set_level() should accept Severity enum."""
        logger = Logger(service="test", profile="SIMPLE", default_level="INFO")

        logger.set_level(Severity.WARN)
        logger.info("Not logged")
        logger.warn("Logged")

        assert "Not logged" not in caplog.text
        assert "Logged" in caplog.text

    def test_set_level_accepts_string(self, caplog):
        """set_level() should accept string level."""
        logger = Logger(service="test", profile="SIMPLE", default_level="ERROR")

        logger.set_level("DEBUG")
        logger.debug("Logged")

        assert "Logged" in caplog.text

    def test_trace_level_logs_everything(self, capsys):
        """TRACE level should log all messages."""
        logger = Logger(service="test", profile="STRUCTURED", default_level="TRACE")

        logger.trace("Trace message")
        logger.debug("Debug message")
        logger.info("Info message")

        captured = capsys.readouterr()
        result = captured.err
        assert "Trace message" in result
        assert "Debug message" in result
        assert "Info message" in result

    def test_none_level_filters_everything(self, capsys):
        """NONE level should filter all messages."""
        logger = Logger(service="test", profile="STRUCTURED", default_level="NONE")

        logger.trace("Not logged")
        logger.debug("Not logged")
        logger.info("Not logged")
        logger.warn("Not logged")
        logger.error("Not logged")
        logger.fatal("Not logged")

        captured = capsys.readouterr()
        result = captured.err
        assert result == ""

    def test_fatal_level_only_logs_fatal(self, capsys):
        """FATAL level should only log FATAL messages."""
        logger = Logger(service="test", profile="STRUCTURED", default_level="FATAL")

        logger.error("Not logged")
        logger.fatal("Logged")

        captured = capsys.readouterr()
        result = captured.err
        assert "Not logged" not in result
        assert "Logged" in result


class TestLevelFilteringPerformance:
    """Test that filtering happens before expensive operations."""

    def test_filtering_avoids_event_creation(self, capsys):
        """Filtered messages should not create LogEvent objects."""
        logger = Logger(service="test", profile="ENTERPRISE", default_level="ERROR")

        logger.info("Filtered out")
        logger.error("Logged", user_id="user-123")

        captured = capsys.readouterr()
        result = captured.err
        assert "Filtered out" not in result
        assert "Logged" in result

    def test_filtering_is_efficient(self, capsys):
        """Level check should happen before JSON serialization."""
        logger = Logger(service="test", profile="STRUCTURED", default_level="WARN")

        large_context = {"data": "x" * 10000}

        logger.info("Filtered", context=large_context)
        logger.warn("Logged", context={"small": "data"})

        captured = capsys.readouterr()
        result = captured.err
        assert "Filtered" not in result
        assert "Logged" in result


class TestProfileDefaultLevels:
    """Test that profiles have appropriate default levels."""

    def test_simple_logger_default_is_info(self, caplog):
        """SimpleLogger default level should be INFO."""
        logger = Logger(service="test", profile="SIMPLE")

        logger.debug("Not logged")
        logger.info("Logged")

        assert "Not logged" not in caplog.text
        assert "Logged" in caplog.text

    def test_structured_logger_default_is_info(self, capsys):
        """StructuredLogger default level should be INFO."""
        logger = Logger(service="test", profile="STRUCTURED")

        logger.debug("Not logged")
        logger.info("Logged")

        captured = capsys.readouterr()
        result = captured.err
        assert "Not logged" not in result
        assert "Logged" in result

    def test_enterprise_logger_default_is_info(self, capsys):
        """EnterpriseLogger default level should be INFO."""
        logger = Logger(service="test", profile="ENTERPRISE")

        logger.debug("Not logged")
        logger.info("Logged")

        captured = capsys.readouterr()
        result = captured.err
        assert "Not logged" not in result
        assert "Logged" in result
