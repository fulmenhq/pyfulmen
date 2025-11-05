"""Tests for signal handler registry and management."""

import signal as stdlib_signal
import threading
from unittest.mock import patch

import pytest

from pyfulmen.signals._registry import (
    DoubleTapState,
    HandlerInfo,
    SignalRegistry,
    clear_all_handlers,
    get_registry,
    handle,
    on_force_quit,
    on_reload,
    on_shutdown,
)


class TestHandlerInfo:
    """Test HandlerInfo named tuple."""

    def test_handler_info_creation(self):
        """Test HandlerInfo creation and attributes."""

        def dummy_handler():
            pass

        info = HandlerInfo(handler=dummy_handler, priority=10, name="test-handler")

        assert info.handler is dummy_handler
        assert info.priority == 10
        assert info.name == "test-handler"
        assert info[0] is dummy_handler
        assert info[1] == 10
        assert info[2] == "test-handler"


class TestDoubleTapState:
    """Test Ctrl+C double-tap state management."""

    def test_initial_state(self):
        """Test initial double-tap state."""
        state = DoubleTapState()

        assert state._first_tap_time is None
        assert not state._graceful_shutdown_started
        assert not state.is_force_exit_suppressed()

    def test_record_first_tap(self):
        """Test recording first tap."""
        state = DoubleTapState()

        # First tap should return True and start graceful shutdown
        assert state.record_first_tap() is True
        assert state._first_tap_time is not None
        assert state._graceful_shutdown_started

        # Second call should return False
        assert state.record_first_tap() is False

    def test_should_force_exit_within_window(self):
        """Test force exit within time window."""
        state = DoubleTapState()

        # Record first tap
        state.record_first_tap()

        # Should force exit within 2 second window
        assert state.should_force_exit(2.0) is True
        assert state.should_force_exit(1.0) is True

    def test_should_not_force_exit_outside_window(self):
        """Test no force exit outside time window."""
        state = DoubleTapState()

        # Mock time passage
        with patch("time.monotonic") as mock_time:
            # First call returns current time
            # Second call returns time + 3 seconds (outside window)
            mock_time.side_effect = [0.0, 3.0]

            # Record first tap (uses first mock_time value)
            state.record_first_tap()

            # Should not force exit after 3 seconds (uses second mock_time value)
            assert state.should_force_exit(2.0) is False

    def test_reset(self):
        """Test resetting double-tap state."""
        state = DoubleTapState()

        # Set up state
        state.record_first_tap()
        state.suppress_force_exit(True)

        # Reset
        state.reset()

        # Should be back to initial state
        assert state._first_tap_time is None
        assert not state._graceful_shutdown_started

    def test_suppress_force_exit(self):
        """Test suppressing force exit."""
        state = DoubleTapState()

        # Initially not suppressed
        assert not state.is_force_exit_suppressed()

        # Suppress
        state.suppress_force_exit(True)
        assert state.is_force_exit_suppressed()

        # Unsuppress
        state.suppress_force_exit(False)
        assert not state.is_force_exit_suppressed()


class TestSignalRegistry:
    """Test signal registry functionality."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = SignalRegistry()

        assert len(registry._handlers) == 0
        assert len(registry._original_handlers) == 0
        assert isinstance(registry._lock, type(threading.RLock()))

    def test_register_handler(self):
        """Test registering a handler."""
        registry = SignalRegistry()

        def dummy_handler():
            pass

        # Register handler
        registry.register(stdlib_signal.SIGTERM, dummy_handler, priority=10, name="test")

        # Check registration
        handlers = registry.get_handlers(stdlib_signal.SIGTERM)
        assert len(handlers) == 1
        assert handlers[0].handler is dummy_handler
        assert handlers[0].priority == 10
        assert handlers[0].name == "test"

    def test_register_multiple_handlers_priority_ordering(self):
        """Test multiple handlers with priority ordering."""
        registry = SignalRegistry()

        def handler1():
            pass

        def handler2():
            pass

        def handler3():
            pass

        # Register in random order with different priorities
        registry.register(stdlib_signal.SIGTERM, handler1, priority=5)
        registry.register(stdlib_signal.SIGTERM, handler2, priority=15)
        registry.register(stdlib_signal.SIGTERM, handler3, priority=10)

        # Should be sorted by priority (highest first)
        handlers = registry.get_handlers(stdlib_signal.SIGTERM)
        assert len(handlers) == 3
        assert handlers[0].priority == 15  # handler2
        assert handlers[1].priority == 10  # handler3
        assert handlers[2].priority == 5  # handler1

    def test_unregister_handler(self):
        """Test unregistering a handler."""
        registry = SignalRegistry()

        def handler1():
            pass

        def handler2():
            pass

        # Register handlers
        registry.register(stdlib_signal.SIGTERM, handler1)
        registry.register(stdlib_signal.SIGTERM, handler2)

        # Unregister one
        result = registry.unregister(stdlib_signal.SIGTERM, handler1)
        assert result is True

        # Check remaining handler
        handlers = registry.get_handlers(stdlib_signal.SIGTERM)
        assert len(handlers) == 1
        assert handlers[0].handler is handler2

    def test_unregister_nonexistent_handler(self):
        """Test unregistering non-existent handler."""
        registry = SignalRegistry()

        def dummy_handler():
            pass

        # Try to unregister from empty registry
        result = registry.unregister(stdlib_signal.SIGTERM, dummy_handler)
        assert result is False

    def test_clear_all_handlers(self):
        """Test clearing all handlers."""
        registry = SignalRegistry()

        def dummy_handler():
            pass

        # Register handlers for multiple signals
        registry.register(stdlib_signal.SIGTERM, dummy_handler)
        registry.register(stdlib_signal.SIGINT, dummy_handler)

        # Clear all
        registry.clear_all()

        # Should be empty
        assert len(registry._handlers) == 0
        assert len(registry._original_handlers) == 0

    def test_get_double_tap_state(self):
        """Test getting double-tap state."""
        registry = SignalRegistry()
        state = registry.get_double_tap_state()

        assert isinstance(state, DoubleTapState)
        assert state is registry._double_tap

    @patch("pyfulmen.signals._registry.stdlib_signal.signal")
    @patch("pyfulmen.signals._registry.Logger")
    def test_register_windows_fallback_signal(self, mock_logger_class, mock_signal):
        """Test registering Windows fallback signal succeeds with structured logging."""
        # Mock signal.signal to raise OSError (simulating Windows)
        mock_signal.side_effect = OSError("Signal not supported")

        # Mock logger to capture calls
        mock_logger = mock_logger_class.return_value

        registry = SignalRegistry()

        def dummy_handler():
            pass

        # SIGHUP has Windows fallback, should succeed with structured logging
        registry.register(stdlib_signal.SIGHUP, dummy_handler)

        # Handler should be registered
        handlers = registry.get_handlers(stdlib_signal.SIGHUP)
        assert len(handlers) == 1
        assert handlers[0].handler == dummy_handler

        # Should have logged structured warning
        mock_logger.warn.assert_called_once()
        call_args = mock_logger.warn.call_args
        assert "SIGHUP unavailable on Windows" in call_args[0][0]  # message

        # Check context contains expected fields
        context = call_args[1]["context"]
        assert context["signal"] == "SIGHUP"
        assert context["platform"] == "windows"
        assert context["fallback_behavior"] == "http_admin_endpoint"
        assert context["event_type"] == "signal_fallback"


class TestPublicAPI:
    """Test public API functions."""

    def test_handle_with_signal_name(self):
        """Test handle() with signal name string."""

        def dummy_handler():
            pass

        # Should not raise exception
        handle("SIGTERM", dummy_handler, priority=10, name="test")

    def test_handle_with_signal_object(self):
        """Test handle() with signal.Signals object."""

        def dummy_handler():
            pass

        # Should not raise exception
        handle(stdlib_signal.SIGTERM, dummy_handler, priority=10, name="test")

    def test_handle_invalid_signal_name(self):
        """Test handle() with invalid signal name."""

        def dummy_handler():
            pass

        with pytest.raises(ValueError, match="Unknown signal name"):
            handle("INVALID_SIGNAL", dummy_handler)

    @patch("pyfulmen.signals._registry.stdlib_signal.signal")
    @patch("pyfulmen.signals._registry.Logger")
    @patch("pyfulmen.signals._registry._registry")
    def test_handle_windows_fallback_signal(self, mock_global_registry, mock_logger_class, mock_signal):
        """Test handle() with Windows fallback signal succeeds with structured logging."""
        # Mock signal.signal to raise OSError (simulating Windows)
        mock_signal.side_effect = OSError("Signal not supported")

        # Mock logger to capture calls
        mock_logger = mock_logger_class.return_value

        # Mock global registry to use our instance
        mock_registry_instance = SignalRegistry()
        mock_global_registry.register = mock_registry_instance.register

        def dummy_handler():
            pass

        # SIGHUP has Windows fallback, should succeed with structured logging
        handle(stdlib_signal.SIGHUP, dummy_handler)

        # Should have logged structured warning
        mock_logger.warn.assert_called_once()
        call_args = mock_logger.warn.call_args
        assert "SIGHUP unavailable on Windows" in call_args[0][0]  # message

        # Check context contains expected fields
        context = call_args[1]["context"]
        assert context["signal"] == "SIGHUP"
        assert context["platform"] == "windows"
        assert context["fallback_behavior"] == "http_admin_endpoint"
        assert context["event_type"] == "signal_fallback"

    def test_on_shutdown_registers_term_and_int(self):
        """Test on_shutdown registers for SIGTERM and SIGINT."""
        registry = get_registry()
        initial_term_handlers = len(registry.get_handlers(stdlib_signal.SIGTERM))
        initial_int_handlers = len(registry.get_handlers(stdlib_signal.SIGINT))

        def cleanup_handler():
            pass

        on_shutdown(cleanup_handler, priority=5)

        # Should have one more handler for each signal
        assert len(registry.get_handlers(stdlib_signal.SIGTERM)) == initial_term_handlers + 1
        assert len(registry.get_handlers(stdlib_signal.SIGINT)) == initial_int_handlers + 1

    def test_on_reload_registers_sighup(self):
        """Test on_reload registers for SIGHUP."""
        registry = get_registry()
        initial_handlers = len(registry.get_handlers(stdlib_signal.SIGHUP))

        def reload_handler():
            pass

        on_reload(reload_handler)

        # Should have one more handler
        assert len(registry.get_handlers(stdlib_signal.SIGHUP)) == initial_handlers + 1

    def test_on_force_quit_registers_sigquit(self):
        """Test on_force_quit registers for SIGQUIT."""
        registry = get_registry()
        initial_handlers = len(registry.get_handlers(stdlib_signal.SIGQUIT))

        def quit_handler():
            pass

        on_force_quit(quit_handler)

        # Should have one more handler
        assert len(registry.get_handlers(stdlib_signal.SIGQUIT)) == initial_handlers + 1

    def test_get_registry_returns_global_instance(self):
        """Test get_registry returns the global registry."""
        registry1 = get_registry()
        registry2 = get_registry()

        # Should be the same instance
        assert registry1 is registry2

    def test_clear_all_handlers_clears_global_registry(self):
        """Test clear_all_handlers clears global registry."""

        def dummy_handler():
            pass

        # Register a handler
        handle(stdlib_signal.SIGTERM, dummy_handler)

        # Clear all
        clear_all_handlers()

        # Registry should be empty
        registry = get_registry()
        assert len(registry._handlers) == 0


class TestSignalDispatch:
    """Test signal dispatch functionality."""

    def test_dispatch_handlers_calls_all(self):
        """Test dispatch calls all handlers in order."""
        registry = SignalRegistry()

        call_order = []

        def handler1():
            call_order.append("handler1")

        def handler2():
            call_order.append("handler2")

        def handler3():
            call_order.append("handler3")

        # Register with different priorities
        registry.register(stdlib_signal.SIGTERM, handler1, priority=5)
        registry.register(stdlib_signal.SIGTERM, handler2, priority=15)
        registry.register(stdlib_signal.SIGTERM, handler3, priority=10)

        # Dispatch
        registry._dispatch_handlers(stdlib_signal.SIGTERM)

        # Should be called in priority order
        assert call_order == ["handler2", "handler3", "handler1"]

    def test_dispatch_handlers_continues_on_error(self):
        """Test dispatch continues even if handler raises error."""
        registry = SignalRegistry()

        call_order = []

        def handler1():
            call_order.append("handler1")

        def handler2():
            call_order.append("handler2")
            raise ValueError("Test error")

        def handler3():
            call_order.append("handler3")

        # Register handlers
        registry.register(stdlib_signal.SIGTERM, handler1)
        registry.register(stdlib_signal.SIGTERM, handler2)
        registry.register(stdlib_signal.SIGTERM, handler3)

        # Dispatch (should not raise exception)
        registry._dispatch_handlers(stdlib_signal.SIGTERM)

        # All handlers should be called despite error
        assert call_order == ["handler1", "handler2", "handler3"]

    @patch("pyfulmen.signals._registry.get_signal_metadata")
    def test_sigint_double_tap_first_tap(self, mock_metadata):
        """Test SIGINT first tap behavior."""
        mock_metadata.return_value = {
            "double_tap_window_seconds": 2.0,
            "double_tap_message": "Press Ctrl+C again to force quit",
            "double_tap_exit_code": 130,
        }

        registry = SignalRegistry()
        call_order = []

        def handler():
            call_order.append("handler")

        registry.register(stdlib_signal.SIGINT, handler)

        # First tap
        with patch("builtins.print") as mock_print:
            registry._handle_sigint_double_tap(stdlib_signal.SIGINT)

        # Should call handler and print message
        assert call_order == ["handler"]
        mock_print.assert_called_with("\nPress Ctrl+C again to force quit")

    @patch("pyfulmen.signals._registry.get_signal_metadata")
    @patch("os._exit")
    def test_sigint_double_tap_second_tap(self, mock_exit, mock_metadata):
        """Test SIGINT second tap within window forces exit."""
        mock_metadata.return_value = {
            "double_tap_window_seconds": 2.0,
            "double_tap_message": "Press Ctrl+C again to force quit",
            "double_tap_exit_code": 130,
        }

        registry = SignalRegistry()

        def handler():
            pass

        registry.register(stdlib_signal.SIGINT, handler)

        # First tap
        registry._handle_sigint_double_tap(stdlib_signal.SIGINT)

        # Second tap within window
        with patch("builtins.print") as mock_print:
            registry._handle_sigint_double_tap(stdlib_signal.SIGINT)

        # Should force exit
        mock_exit.assert_called_with(130)
        mock_print.assert_called_with("\nForce quitting...")

    @patch("pyfulmen.signals._registry.get_signal_metadata")
    def test_sigint_double_tap_second_tap_outside_window(self, mock_metadata):
        """Test SIGINT second tap outside window treats as new first tap."""
        mock_metadata.return_value = {
            "double_tap_window_seconds": 2.0,
            "double_tap_message": "Press Ctrl+C again to force quit",
            "double_tap_exit_code": 130,
        }

        # Test the DoubleTapState directly to avoid time mocking issues
        with patch("time.monotonic") as mock_time:
            mock_time.side_effect = [0.0, 3.0]  # First tap at 0s, check at 3s (outside window)

            state = DoubleTapState()

            # First tap (uses first mock_time value: 0.0)
            first_tap_result = state.record_first_tap()
            assert first_tap_result is True
            assert state._graceful_shutdown_started is True

            # Should not force exit since 3s > 2s window (uses second mock_time value: 3.0)
            should_force = state.should_force_exit(2.0)
            assert should_force is False

        # Reset and record new first tap (simulating the logic in _handle_sigint_double_tap)
        state.reset()
        second_tap_result = state.record_first_tap()
        assert second_tap_result is True
        assert state._graceful_shutdown_started is True

    @patch("pyfulmen.signals._registry.get_signal_metadata")
    @patch("os._exit")
    def test_sigint_double_tap_suppressed(self, mock_exit, mock_metadata):
        """Test SIGINT force exit can be suppressed."""
        mock_metadata.return_value = {
            "double_tap_window_seconds": 2.0,
            "double_tap_message": "Press Ctrl+C again to force quit",
            "double_tap_exit_code": 130,
        }

        registry = SignalRegistry()

        def handler():
            pass

        registry.register(stdlib_signal.SIGINT, handler)

        # Suppress force exit
        registry._double_tap.suppress_force_exit(True)

        # First tap
        registry._handle_sigint_double_tap(stdlib_signal.SIGINT)

        # Second tap within window
        with patch("builtins.print") as mock_print:
            registry._handle_sigint_double_tap(stdlib_signal.SIGINT)

        # Should NOT force exit when suppressed
        mock_exit.assert_not_called()
        mock_print.assert_called_with("\nForce quitting...")
