"""Asyncio integration for signal handling.

Provides automatic event loop detection and registration of signal handlers
with asyncio event loops when available, with thread-safe fallbacks.
"""

from __future__ import annotations

import asyncio
import signal as stdlib_signal
import threading
from collections.abc import Callable
from typing import Any


class AsyncioIntegration:
    """Manages asyncio integration for signal handlers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_checked = False

    def get_running_loop(self) -> asyncio.AbstractEventLoop | None:
        """Get the current running event loop.

        Returns:
            The running event loop or None if no loop is running.
        """
        with self._lock:
            if not self._loop_checked:
                try:
                    self._loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running loop
                    self._loop = None
                self._loop_checked = True

            return self._loop

    def register_async_handler(
        self,
        sig: stdlib_signal.Signals,
        handler: Callable[[], Any],
    ) -> bool:
        """Register a handler with the running event loop.

        Args:
            sig: Signal to register for.
            handler: Handler function (can be sync or async).

        Returns:
            True if registered with event loop, False if no loop available.
        """
        loop = self.get_running_loop()
        if loop is None:
            return False

        # Wrap handler to handle both sync and async functions
        async def async_wrapper() -> None:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                print(f"Error in async signal handler for {sig.name}: {e}")

        # Register with event loop
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(async_wrapper()))
            return True
        except (NotImplementedError, RuntimeError):
            # Event loop doesn't support signal handling
            return False

    def is_async_available(self) -> bool:
        """Check if asyncio signal handling is available.

        Returns:
            True if running loop supports signal handling.
        """
        loop = self.get_running_loop()
        return loop is not None

    def reset(self) -> None:
        """Reset loop detection (for testing)."""
        with self._lock:
            self._loop = None
            self._loop_checked = False


# Global asyncio integration instance
_asyncio_integration = AsyncioIntegration()


def register_with_asyncio_if_available(
    sig: stdlib_signal.Signals,
    handler: Callable[[], Any],
) -> bool:
    """Register a handler with asyncio if available, otherwise return False.

    Args:
        sig: Signal to register for.
        handler: Handler function to register.

    Returns:
        True if registered with asyncio, False if fallback needed.
    """
    return _asyncio_integration.register_async_handler(sig, handler)


def is_asyncio_available() -> bool:
    """Check if asyncio signal handling is available.

    Returns:
        True if running event loop supports signal handling.
    """
    return _asyncio_integration.is_async_available()


def get_running_loop() -> asyncio.AbstractEventLoop | None:
    """Get the current running event loop.

    Returns:
        The running event loop or None if no loop is running.
    """
    return _asyncio_integration.get_running_loop()


def reset_asyncio_detection() -> None:
    """Reset asyncio loop detection (for testing).

    This allows testing of asyncio detection in different contexts.
    """
    _asyncio_integration.reset()


class AsyncSignalHandler:
    """Base class for async signal handlers.

    Provides a convenient way to create async signal handlers
    that work both with and without asyncio.
    """

    def __init__(self, handler: Callable[[], Any]) -> None:
        self._handler = handler
        self._is_async = asyncio.iscoroutinefunction(handler)

    def __call__(self) -> Any:
        """Call handler appropriately based on context."""
        if self._is_async:
            loop = get_running_loop()
            if loop is not None:
                # Run async handler in event loop
                task = asyncio.create_task(self._handler())
                return task
            else:
                # No event loop - run sync version
                return asyncio.run(self._handler())
        else:
            # Sync handler - call directly
            return self._handler()

    def is_async(self) -> bool:
        """Check if this is an async handler."""
        return self._is_async


def wrap_async_handler(handler: Callable[[], Any]) -> AsyncSignalHandler:
    """Wrap a handler for async/sync compatibility.

    Args:
        handler: Handler function to wrap.

    Returns:
        Wrapped handler that works in both async and sync contexts.
    """
    return AsyncSignalHandler(handler)


def create_async_safe_handler(
    handler: Callable[[], Any],
    fallback: Callable[[], Any] | None = None,
) -> Callable[[], Any]:
    """Create a handler that works safely in both async and sync contexts.

    Args:
        handler: Primary handler (can be sync or async).
        fallback: Optional fallback handler for sync contexts.

    Returns:
        Handler that adapts to current context.
    """

    def safe_handler() -> Any:
        try:
            if is_asyncio_available():
                # Try asyncio registration first
                return handler()
            else:
                # No asyncio - use fallback or direct call
                if fallback:
                    return fallback()
                elif asyncio.iscoroutinefunction(handler):
                    # Async handler without loop - run in new event loop
                    return asyncio.run(handler())
                else:
                    # Sync handler - call directly
                    return handler()
        except Exception as e:
            print(f"Error in async-safe signal handler: {e}")

    return safe_handler
