"""Tests for correlation context management (Phase 3)."""

import json
import threading

from pyfulmen.logging import Logger, LoggingProfile
from pyfulmen.logging.context import (
    clear_context,
    correlation_context,
    extract_correlation_id_from_headers,
    get_context,
    get_correlation_id,
    set_context_value,
    set_correlation_id,
)


class TestCorrelationID:
    """Test correlation ID management."""

    def test_get_correlation_id_initially_none(self):
        """get_correlation_id() should return None initially."""
        clear_context()
        set_correlation_id(None)
        assert get_correlation_id() is None

    def test_set_and_get_correlation_id(self):
        """set_correlation_id() should store value retrievable by get_correlation_id()."""
        test_id = "test-correlation-123"
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id

        # Cleanup
        set_correlation_id(None)

    def test_set_correlation_id_none_clears(self):
        """set_correlation_id(None) should clear the correlation ID."""
        set_correlation_id("test-id")
        assert get_correlation_id() == "test-id"

        set_correlation_id(None)
        assert get_correlation_id() is None

    def test_correlation_id_thread_local(self):
        """Correlation IDs should be thread-local."""
        main_id = "main-thread-id"
        set_correlation_id(main_id)

        thread_results = []

        def thread_func():
            # Should not see main thread's ID
            assert get_correlation_id() is None

            # Set thread-specific ID
            thread_id = "thread-specific-id"
            set_correlation_id(thread_id)
            assert get_correlation_id() == thread_id
            thread_results.append(get_correlation_id())

        thread = threading.Thread(target=thread_func)
        thread.start()
        thread.join()

        # Main thread should still have its ID
        assert get_correlation_id() == main_id
        assert thread_results[0] == "thread-specific-id"

        # Cleanup
        set_correlation_id(None)


class TestContext:
    """Test general logging context management."""

    def test_get_context_initially_empty(self):
        """get_context() should return empty dict initially."""
        clear_context()
        assert get_context() == {}

    def test_set_and_get_context_value(self):
        """set_context_value() should store values in context."""
        clear_context()
        set_context_value("user_id", "user-123")
        set_context_value("tenant_id", "tenant-456")

        ctx = get_context()
        assert ctx["user_id"] == "user-123"
        assert ctx["tenant_id"] == "tenant-456"

        # Cleanup
        clear_context()

    def test_clear_context(self):
        """clear_context() should remove all context values."""
        set_context_value("key1", "value1")
        set_context_value("key2", "value2")
        assert len(get_context()) == 2

        clear_context()
        assert get_context() == {}

    def test_context_thread_local(self):
        """Context should be thread-local."""
        set_context_value("main_key", "main_value")

        thread_results = []

        def thread_func():
            # Should not see main thread's context
            assert get_context() == {}

            # Set thread-specific context
            set_context_value("thread_key", "thread_value")
            thread_results.append(get_context().copy())

        thread = threading.Thread(target=thread_func)
        thread.start()
        thread.join()

        # Main thread should still have its context
        assert get_context()["main_key"] == "main_value"
        assert "thread_key" not in get_context()

        assert thread_results[0]["thread_key"] == "thread_value"
        assert "main_key" not in thread_results[0]

        # Cleanup
        clear_context()


class TestCorrelationContext:
    """Test correlation_context context manager."""

    def test_correlation_context_generates_id(self):
        """correlation_context should generate ID if none provided."""
        with correlation_context() as corr_id:
            assert corr_id is not None
            assert len(corr_id) > 0
            assert get_correlation_id() == corr_id

        # Should be cleared after context
        assert get_correlation_id() is None

    def test_correlation_context_with_explicit_id(self):
        """correlation_context should use provided correlation_id."""
        test_id = "explicit-correlation-789"

        with correlation_context(correlation_id=test_id) as corr_id:
            assert corr_id == test_id
            assert get_correlation_id() == test_id

        assert get_correlation_id() is None

    def test_correlation_context_with_additional_values(self):
        """correlation_context should set additional context values."""
        with correlation_context(user_id="user-123", tenant_id="tenant-456") as corr_id:
            assert get_correlation_id() == corr_id
            ctx = get_context()
            assert ctx["user_id"] == "user-123"
            assert ctx["tenant_id"] == "tenant-456"

        assert get_correlation_id() is None
        assert get_context() == {}

    def test_correlation_context_nested(self):
        """Nested correlation_context should preserve parent on exit."""
        parent_id = "parent-id"
        child_id = "child-id"

        with correlation_context(correlation_id=parent_id):
            assert get_correlation_id() == parent_id

            with correlation_context(correlation_id=child_id):
                assert get_correlation_id() == child_id

            # Should restore parent
            assert get_correlation_id() == parent_id

        # Should clear completely
        assert get_correlation_id() is None

    def test_correlation_context_preserves_existing_context(self):
        """correlation_context should preserve existing context on exit."""
        set_correlation_id("original-id")
        set_context_value("original_key", "original_value")

        with correlation_context(correlation_id="temp-id", temp_key="temp_value"):
            assert get_correlation_id() == "temp-id"
            assert get_context()["temp_key"] == "temp_value"

        # Should restore original
        assert get_correlation_id() == "original-id"
        assert get_context()["original_key"] == "original_value"
        assert "temp_key" not in get_context()

        # Cleanup
        set_correlation_id(None)
        clear_context()


class TestLoggerCorrelationIntegration:
    """Test logger integration with correlation context."""

    def test_structured_logger_uses_context_correlation_id(self, capsys):
        """StructuredLogger should use correlation_id from context."""
        logger = Logger(service="test", profile=LoggingProfile.STRUCTURED)

        with correlation_context(correlation_id="ctx-correlation-123"):
            logger.info("Test message")

        captured = capsys.readouterr()
        log_line = json.loads(captured.out.strip())

        assert log_line["correlation_id"] == "ctx-correlation-123"
        assert log_line["message"] == "Test message"

    def test_enterprise_logger_uses_context_correlation_id(self, capsys):
        """EnterpriseLogger should use correlation_id from context."""
        logger = Logger(service="test", profile=LoggingProfile.ENTERPRISE)

        with correlation_context(correlation_id="ent-correlation-456"):
            logger.info("Enterprise log")

        captured = capsys.readouterr()
        log_line = json.loads(captured.out.strip())

        assert log_line["correlation_id"] == "ent-correlation-456"
        assert log_line["message"] == "Enterprise log"

    def test_explicit_correlation_id_overrides_context(self, capsys):
        """Explicit correlation_id should override context."""
        logger = Logger(service="test", profile=LoggingProfile.STRUCTURED)

        with correlation_context(correlation_id="context-id"):
            logger.info("Message", correlation_id="explicit-id")

        captured = capsys.readouterr()
        log_line = json.loads(captured.out.strip())

        # Explicit should win
        assert log_line["correlation_id"] == "explicit-id"

    def test_logger_with_context_values(self, capsys):
        """Logger should include context values in logs."""
        logger = Logger(service="test", profile=LoggingProfile.STRUCTURED)

        with correlation_context(user_id="user-789", tenant_id="tenant-123"):
            logger.info("Processing request")

        captured = capsys.readouterr()
        log_line = json.loads(captured.out.strip())

        assert "context" in log_line
        assert log_line["context"]["user_id"] == "user-789"
        assert log_line["context"]["tenant_id"] == "tenant-123"

    def test_explicit_context_merges_with_thread_context(self, capsys):
        """Explicit context should merge with thread-local context."""
        logger = Logger(service="test", profile=LoggingProfile.STRUCTURED)

        with correlation_context(user_id="user-111"):
            logger.info("Message", context={"request_id": "req-222"})

        captured = capsys.readouterr()
        log_line = json.loads(captured.out.strip())

        # Should have both
        assert log_line["context"]["user_id"] == "user-111"
        assert log_line["context"]["request_id"] == "req-222"

    def test_explicit_context_takes_precedence(self, capsys):
        """Explicit context values should override thread-local context."""
        logger = Logger(service="test", profile=LoggingProfile.STRUCTURED)

        with correlation_context(key="context-value"):
            logger.info("Message", context={"key": "explicit-value"})

        captured = capsys.readouterr()
        log_line = json.loads(captured.out.strip())

        # Explicit should win
        assert log_line["context"]["key"] == "explicit-value"

    def test_multiple_logs_same_correlation_id(self, capsys):
        """Multiple logs in same context should share correlation_id."""
        logger = Logger(service="test", profile=LoggingProfile.STRUCTURED)

        with correlation_context() as corr_id:
            logger.info("First message")
            logger.warn("Second message")
            logger.error("Third message")

        captured = capsys.readouterr()
        lines = [json.loads(line) for line in captured.out.strip().split("\n")]

        assert len(lines) == 3
        # All should have same correlation_id
        assert lines[0]["correlation_id"] == corr_id
        assert lines[1]["correlation_id"] == corr_id
        assert lines[2]["correlation_id"] == corr_id


class TestHeaderExtraction:
    """Test X-Correlation-ID header extraction."""

    def test_extract_from_x_correlation_id(self):
        """Should extract from X-Correlation-ID header."""
        headers = {"X-Correlation-ID": "header-corr-123"}
        corr_id = extract_correlation_id_from_headers(headers)
        assert corr_id == "header-corr-123"

    def test_extract_case_insensitive(self):
        """Header extraction should be case-insensitive."""
        headers = {"x-correlation-id": "lowercase-123"}
        corr_id = extract_correlation_id_from_headers(headers)
        assert corr_id == "lowercase-123"

        headers = {"X-CORRELATION-ID": "uppercase-456"}
        corr_id = extract_correlation_id_from_headers(headers)
        assert corr_id == "uppercase-456"

    def test_extract_from_x_request_id(self):
        """Should extract from X-Request-ID as fallback."""
        headers = {"X-Request-ID": "request-789"}
        corr_id = extract_correlation_id_from_headers(headers)
        assert corr_id == "request-789"

    def test_extract_priority_order(self):
        """X-Correlation-ID should take precedence over X-Request-ID."""
        headers = {
            "X-Correlation-ID": "correlation-first",
            "X-Request-ID": "request-second",
        }
        corr_id = extract_correlation_id_from_headers(headers)
        assert corr_id == "correlation-first"

    def test_extract_custom_headers(self):
        """Should support custom header names."""
        headers = {"Custom-Trace-ID": "custom-trace-999"}
        corr_id = extract_correlation_id_from_headers(headers, header_names=["Custom-Trace-ID"])
        assert corr_id == "custom-trace-999"

    def test_extract_no_headers_returns_none(self):
        """Should return None if no correlation headers found."""
        headers = {"Content-Type": "application/json"}
        corr_id = extract_correlation_id_from_headers(headers)
        assert corr_id is None

    def test_extract_empty_headers(self):
        """Should handle empty headers dict."""
        corr_id = extract_correlation_id_from_headers({})
        assert corr_id is None
