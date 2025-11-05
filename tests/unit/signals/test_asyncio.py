"""Tests for asyncio integration."""

import asyncio
import signal as stdlib_signal
from unittest.mock import MagicMock, patch

import pytest

from pyfulmen.signals._asyncio import (
    AsyncioIntegration,
    AsyncSignalHandler,
    create_async_safe_handler,
    get_running_loop,
    is_asyncio_available,
    register_with_asyncio_if_available,
    reset_asyncio_detection,
    wrap_async_handler,
)


class TestAsyncioIntegration:
    """Test asyncio integration class."""

    def test_initialization(self):
        """Test AsyncioIntegration initialization."""
        integration = AsyncioIntegration()

        assert integration._loop is None
        assert not integration._loop_checked
        assert integration._lock is not None

    @patch("asyncio.get_running_loop")
    def test_get_running_loop_with_loop(self, mock_get_loop):
        """Test getting running loop when loop exists."""
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        integration = AsyncioIntegration()
        loop = integration.get_running_loop()

        assert loop is mock_loop
        assert integration._loop is mock_loop
        assert integration._loop_checked
        mock_get_loop.assert_called_once()

    @patch("asyncio.get_running_loop")
    def test_get_running_loop_no_loop(self, mock_get_loop):
        """Test getting running loop when no loop exists."""
        mock_get_loop.side_effect = RuntimeError("no running event loop")

        integration = AsyncioIntegration()
        loop = integration.get_running_loop()

        assert loop is None
        assert integration._loop is None
        assert integration._loop_checked

    @patch("asyncio.get_running_loop")
    def test_get_running_loop_cached(self, mock_get_loop):
        """Test that running loop is cached after first call."""
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        integration = AsyncioIntegration()

        # First call
        loop1 = integration.get_running_loop()
        # Second call
        loop2 = integration.get_running_loop()

        assert loop1 is mock_loop
        assert loop2 is mock_loop
        # Should only call get_running_loop once
        mock_get_loop.assert_called_once()

    @patch("asyncio.get_running_loop")
    def test_register_async_handler_with_loop(self, mock_get_loop):
        """Test registering async handler when loop is available."""
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        integration = AsyncioIntegration()

        async def async_handler():
            await asyncio.sleep(0.1)

        result = integration.register_async_handler(stdlib_signal.SIGTERM, async_handler)

        assert result is True
        mock_loop.add_signal_handler.assert_called_once()

        # Check the wrapper was created correctly
        call_args = mock_loop.add_signal_handler.call_args
        assert call_args[0][0] == stdlib_signal.SIGTERM
        assert callable(call_args[0][1])

    @patch("asyncio.get_running_loop")
    def test_register_sync_handler_with_loop(self, mock_get_loop):
        """Test registering sync handler when loop is available."""
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        integration = AsyncioIntegration()

        def sync_handler():
            pass

        result = integration.register_async_handler(stdlib_signal.SIGTERM, sync_handler)

        assert result is True
        mock_loop.add_signal_handler.assert_called_once()

    @patch("asyncio.get_running_loop")
    def test_register_async_handler_no_loop(self, mock_get_loop):
        """Test registering handler when no loop is available."""
        mock_get_loop.side_effect = RuntimeError("no running event loop")

        integration = AsyncioIntegration()

        def handler():
            pass

        result = integration.register_async_handler(stdlib_signal.SIGTERM, handler)

        assert result is False
        mock_get_loop.assert_called_once()

    @patch("asyncio.get_running_loop")
    def test_register_async_handler_loop_error(self, mock_get_loop):
        """Test registering handler when loop doesn't support signals."""
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        mock_loop.add_signal_handler.side_effect = NotImplementedError("not supported")

        integration = AsyncioIntegration()

        def handler():
            pass

        result = integration.register_async_handler(stdlib_signal.SIGTERM, handler)

        assert result is False

    @patch("asyncio.get_running_loop")
    def test_is_async_available_true(self, mock_get_loop):
        """Test is_async_available returns True when loop exists."""
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        integration = AsyncioIntegration()

        assert integration.is_async_available() is True

    @patch("asyncio.get_running_loop")
    def test_is_async_available_false(self, mock_get_loop):
        """Test is_async_available returns False when no loop."""
        mock_get_loop.side_effect = RuntimeError("no running event loop")

        integration = AsyncioIntegration()

        assert integration.is_async_available() is False

    def test_reset(self):
        """Test resetting integration state."""
        integration = AsyncioIntegration()

        # Set some state
        integration._loop = MagicMock()
        integration._loop_checked = True

        # Reset
        integration.reset()

        assert integration._loop is None
        assert not integration._loop_checked


class TestAsyncSignalHandler:
    """Test AsyncSignalHandler class."""

    def test_async_handler_creation(self):
        """Test creating async handler."""

        async def async_handler():
            await asyncio.sleep(0.1)

        wrapper = AsyncSignalHandler(async_handler)

        assert wrapper._handler is async_handler
        assert wrapper.is_async() is True

    def test_sync_handler_creation(self):
        """Test creating sync handler."""

        def sync_handler():
            pass

        wrapper = AsyncSignalHandler(sync_handler)

        assert wrapper._handler is sync_handler
        assert wrapper.is_async() is False

    @pytest.mark.asyncio
    async def test_call_async_handler_with_loop(self):
        """Test calling async handler with running loop."""

        # Reset asyncio detection to ensure fresh state
        reset_asyncio_detection()

        # This test requires an actual running loop
        async def async_handler():
            await asyncio.sleep(0.001)
            return "async_result"

        wrapper = AsyncSignalHandler(async_handler)

        # Test with actual event loop (pytest-asyncio provides this)
        result = wrapper()
        # Should create a task or future
        assert asyncio.isfuture(result)
        # Wait for the task to complete
        if asyncio.isfuture(result):
            final_result = await result
        else:
            final_result = result

        # The result should be completed
        assert final_result == "async_result"

    @patch("pyfulmen.signals._asyncio.get_running_loop")
    @patch("asyncio.run")
    def test_call_async_handler_no_loop(self, mock_run, mock_get_loop):
        """Test calling async handler without running loop."""
        mock_get_loop.return_value = None
        mock_run.return_value = "async_result"

        async def async_handler():
            await asyncio.sleep(0.1)
            return "async_result"

        wrapper = AsyncSignalHandler(async_handler)
        result = wrapper()

        # Should run in new event loop
        mock_run.assert_called_once()
        assert result == "async_result"

    @patch("pyfulmen.signals._asyncio.get_running_loop")
    def test_call_sync_handler_with_loop(self, mock_get_loop):
        """Test calling sync handler with running loop."""
        mock_get_loop.return_value = MagicMock()

        def sync_handler():
            return "sync_result"

        wrapper = AsyncSignalHandler(sync_handler)
        result = wrapper()

        # Should call directly
        assert result == "sync_result"

    @patch("pyfulmen.signals._asyncio.get_running_loop")
    def test_call_sync_handler_no_loop(self, mock_get_loop):
        """Test calling sync handler without running loop."""
        mock_get_loop.return_value = None

        def sync_handler():
            return "sync_result"

        wrapper = AsyncSignalHandler(sync_handler)
        result = wrapper()

        # Should call directly
        assert result == "sync_result"


class TestGlobalFunctions:
    """Test global asyncio integration functions."""

    @patch("pyfulmen.signals._asyncio._asyncio_integration")
    def test_register_with_asyncio_if_available_success(self, mock_integration):
        """Test successful registration with asyncio."""
        mock_integration.register_async_handler.return_value = True

        def handler():
            pass

        result = register_with_asyncio_if_available(stdlib_signal.SIGTERM, handler)

        assert result is True
        mock_integration.register_async_handler.assert_called_once_with(stdlib_signal.SIGTERM, handler)

    @patch("pyfulmen.signals._asyncio._asyncio_integration")
    def test_register_with_asyncio_if_available_failure(self, mock_integration):
        """Test failed registration with asyncio."""
        mock_integration.register_async_handler.return_value = False

        def handler():
            pass

        result = register_with_asyncio_if_available(stdlib_signal.SIGTERM, handler)

        assert result is False

    @patch("pyfulmen.signals._asyncio._asyncio_integration")
    def test_is_asyncio_available_true(self, mock_integration):
        """Test is_asyncio_available returns True."""
        mock_integration.is_async_available.return_value = True

        result = is_asyncio_available()

        assert result is True
        mock_integration.is_async_available.assert_called_once()

    @patch("pyfulmen.signals._asyncio._asyncio_integration")
    def test_is_asyncio_available_false(self, mock_integration):
        """Test is_asyncio_available returns False."""
        mock_integration.is_async_available.return_value = False

        result = is_asyncio_available()

        assert result is False
        mock_integration.is_async_available.assert_called_once()

    @patch("pyfulmen.signals._asyncio._asyncio_integration")
    def test_get_running_loop_with_loop(self, mock_integration):
        """Test get_running_loop returns loop."""
        mock_loop = MagicMock()
        mock_integration.get_running_loop.return_value = mock_loop

        result = get_running_loop()

        assert result is mock_loop
        mock_integration.get_running_loop.assert_called_once()

    @patch("pyfulmen.signals._asyncio._asyncio_integration")
    def test_get_running_loop_no_loop(self, mock_integration):
        """Test get_running_loop returns None."""
        mock_integration.get_running_loop.return_value = None

        result = get_running_loop()

        assert result is None
        mock_integration.get_running_loop.assert_called_once()

    @patch("pyfulmen.signals._asyncio._asyncio_integration")
    def test_reset_asyncio_detection(self, mock_integration):
        """Test reset_asyncio_detection."""
        reset_asyncio_detection()

        mock_integration.reset.assert_called_once()


class TestWrapAsyncHandler:
    """Test async handler wrapping."""

    def test_wrap_async_handler(self):
        """Test wrapping async handler."""

        async def async_handler():
            await asyncio.sleep(0.1)
            return "async_result"

        wrapper = wrap_async_handler(async_handler)

        assert isinstance(wrapper, AsyncSignalHandler)
        assert wrapper._handler is async_handler
        assert wrapper.is_async() is True

    def test_wrap_sync_handler(self):
        """Test wrapping sync handler."""

        def sync_handler():
            return "sync_result"

        wrapper = wrap_async_handler(sync_handler)

        assert isinstance(wrapper, AsyncSignalHandler)
        assert wrapper._handler is sync_handler
        assert wrapper.is_async() is False


class TestCreateAsyncSafeHandler:
    """Test creating async-safe handlers."""

    @patch("pyfulmen.signals._asyncio.is_asyncio_available")
    @patch("pyfulmen.signals._asyncio.asyncio.iscoroutinefunction")
    def test_create_async_safe_handler_with_asyncio_and_async_handler(self, mock_iscoro, mock_is_async):
        """Test async-safe handler with asyncio available and async handler."""
        mock_is_async.return_value = True
        mock_iscoro.return_value = True

        async def async_handler():
            await asyncio.sleep(0.1)
            return "async_result"

        safe_handler = create_async_safe_handler(async_handler)
        result = safe_handler()

        # Should call async handler directly (returns coroutine)
        mock_is_async.assert_called_once()
        # Result should be a coroutine when asyncio is available
        assert asyncio.iscoroutine(result)

    @patch("pyfulmen.signals._asyncio.is_asyncio_available")
    @patch("pyfulmen.signals._asyncio.asyncio.iscoroutinefunction")
    def test_create_async_safe_handler_with_asyncio_and_sync_handler(self, mock_iscoro, mock_is_async):
        """Test async-safe handler with asyncio available and sync handler."""
        mock_is_async.return_value = True
        mock_iscoro.return_value = False

        def sync_handler():
            return "sync_result"

        safe_handler = create_async_safe_handler(sync_handler)
        result = safe_handler()

        # Should call sync handler directly
        mock_is_async.assert_called_once()
        assert result == "sync_result"

    @patch("pyfulmen.signals._asyncio.is_asyncio_available")
    @patch("pyfulmen.signals._asyncio.asyncio.iscoroutinefunction")
    @patch("asyncio.run")
    def test_create_async_safe_handler_no_asyncio_async_handler(self, mock_run, mock_iscoro, mock_is_async):
        """Test async-safe handler without asyncio and async handler."""
        mock_is_async.return_value = False
        mock_iscoro.return_value = True
        mock_run.return_value = "async_result"

        async def async_handler():
            await asyncio.sleep(0.1)
            return "async_result"

        safe_handler = create_async_safe_handler(async_handler)
        result = safe_handler()

        # Should run async handler in new event loop
        mock_is_async.assert_called_once()
        mock_run.assert_called_once()
        assert result == "async_result"

    @patch("pyfulmen.signals._asyncio.is_asyncio_available")
    @patch("pyfulmen.signals._asyncio.asyncio.iscoroutinefunction")
    def test_create_async_safe_handler_no_asyncio_sync_handler(self, mock_iscoro, mock_is_async):
        """Test async-safe handler without asyncio and sync handler."""
        mock_is_async.return_value = False
        mock_iscoro.return_value = False

        def sync_handler():
            return "sync_result"

        safe_handler = create_async_safe_handler(sync_handler)
        result = safe_handler()

        # Should call sync handler directly
        mock_is_async.assert_called_once()
        assert result == "sync_result"

    @patch("pyfulmen.signals._asyncio.is_asyncio_available")
    def test_create_async_safe_handler_with_fallback(self, mock_is_async):
        """Test async-safe handler with fallback."""
        mock_is_async.return_value = False

        def primary_handler():
            return "primary"

        def fallback_handler():
            return "fallback"

        safe_handler = create_async_safe_handler(primary_handler, fallback=fallback_handler)
        result = safe_handler()

        # Should use fallback when no asyncio
        mock_is_async.assert_called_once()
        assert result == "fallback"

    @patch("pyfulmen.signals._asyncio.is_asyncio_available")
    def test_create_async_safe_handler_error_handling(self, mock_is_async):
        """Test async-safe handler error handling."""
        mock_is_async.return_value = True

        def failing_handler():
            raise ValueError("Test error")

        safe_handler = create_async_safe_handler(failing_handler)

        # Should not raise exception
        with patch("builtins.print") as mock_print:
            result = safe_handler()

        mock_print.assert_called()
        assert "Error in async-safe signal handler" in str(mock_print.call_args)
