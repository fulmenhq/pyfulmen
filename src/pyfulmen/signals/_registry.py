"""Signal handler registry and management.

Provides thread-safe handler registration, priority-based execution,
and Ctrl+C double-tap logic with monotonic timing.
"""

from __future__ import annotations

import contextlib
import signal as stdlib_signal
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any, NamedTuple

from pyfulmen.logging import Logger
from pyfulmen.signals._asyncio import (
    AsyncioIntegration,
    create_async_safe_handler,
    register_with_asyncio_if_available,
)
from pyfulmen.signals._catalog import get_signal_metadata
from pyfulmen.signals._reload import get_config_reloader
from pyfulmen.telemetry import MetricRegistry


class HandlerInfo(NamedTuple):
    """Information about a registered signal handler."""
    handler: Callable[[], Any]
    priority: int
    name: str | None


class DoubleTapState:
    """State for Ctrl+C double-tap logic."""
    
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._first_tap_time: float | None = None
        self._graceful_shutdown_started = False
        self._force_exit_suppressed = False
    
    def record_first_tap(self) -> bool:
        """Record first Ctrl+C tap and return whether to start graceful shutdown.
        
        Returns:
            True if this is the first tap and graceful shutdown should start.
        """
        with self._lock:
            if self._first_tap_time is None:
                self._first_tap_time = time.monotonic()
                self._graceful_shutdown_started = True
                return True
            return False
    
    def should_force_exit(self, window_seconds: float = 2.0) -> bool:
        """Check if second tap should force exit.
        
        Args:
            window_seconds: Time window for double-tap detection.
            
        Returns:
            True if second tap is within window and should force exit.
        """
        with self._lock:
            if self._first_tap_time is None:
                return False
            
            elapsed = time.monotonic() - self._first_tap_time
            return elapsed <= window_seconds
    
    def reset(self) -> None:
        """Reset double-tap state after graceful shutdown completion."""
        with self._lock:
            self._first_tap_time = None
            self._graceful_shutdown_started = False
    
    def suppress_force_exit(self, suppress: bool = True) -> None:
        """Suppress or unsuppress force exit behavior (for testing)."""
        with self._lock:
            self._force_exit_suppressed = suppress
    
    def is_force_exit_suppressed(self) -> bool:
        """Check if force exit is currently suppressed."""
        with self._lock:
            return self._force_exit_suppressed


class SignalRegistry:
    """Thread-safe registry for signal handlers with priority ordering."""
    
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handlers: dict[stdlib_signal.Signals, list[HandlerInfo]] = defaultdict(list)
        self._double_tap = DoubleTapState()
        self._original_handlers: dict[stdlib_signal.Signals, Callable | int | None] = {}
        self._asyncio = AsyncioIntegration()
        self._logger = Logger(service="pyfulmen.signals")
        self._telemetry = MetricRegistry()
    
    def register(
        self,
        sig: stdlib_signal.Signals,
        handler: Callable[[], Any],
        *,
        priority: int = 0,
        name: str | None = None,
    ) -> None:
        """Register a handler for a signal.
        
        Args:
            sig: Signal to register for.
            handler: Handler function to call.
            priority: Priority for ordering (higher = called first).
            name: Optional name for debugging.
        """
        with self._lock:
            handler_info = HandlerInfo(handler=handler, priority=priority, name=name)
            self._handlers[sig].append(handler_info)
            
            # Sort by priority (highest first)
            self._handlers[sig].sort(key=lambda h: h.priority, reverse=True)
            
            # Register with OS if this is the first handler
            if len(self._handlers[sig]) == 1:
                self._register_with_os(sig)
    
    def unregister(self, sig: stdlib_signal.Signals, handler: Callable[[], Any]) -> bool:
        """Unregister a specific handler.
        
        Args:
            sig: Signal to unregister from.
            handler: Handler function to remove.
            
        Returns:
            True if handler was found and removed.
        """
        with self._lock:
            handlers = self._handlers[sig]
            for i, handler_info in enumerate(handlers):
                if handler_info.handler is handler:
                    del handlers[i]
                    
                    # Unregister from OS if no more handlers
                    if not handlers:
                        self._unregister_from_os(sig)
                    
                    return True
            return False
    
    def get_handlers(self, sig: stdlib_signal.Signals) -> list[HandlerInfo]:
        """Get all handlers for a signal, sorted by priority.
        
        Args:
            sig: Signal to get handlers for.
            
        Returns:
            List of handler info sorted by priority.
        """
        with self._lock:
            return list(self._handlers[sig])
    
    def clear_all(self) -> None:
        """Clear all registered handlers and restore original signal handling."""
        with self._lock:
            # Restore all original handlers
            for sig, original_handler in self._original_handlers.items():
                if original_handler is not None:  # Skip Windows fallback signals
                    with contextlib.suppress(ValueError, OSError):
                        # Signal might not be supported on this platform
                        stdlib_signal.signal(sig, original_handler)
            
            # Clear registry
            self._handlers.clear()
            self._original_handlers.clear()
            self._double_tap.reset()
    
    def _register_with_os(self, sig: stdlib_signal.Signals) -> None:
        """Register signal with OS, storing original handler.
        
        Tries asyncio registration first, falls back to signal.signal.
        For Windows fallback signals, logs warning and continues registration
        without OS-level signal handling.
        """
        # Try asyncio registration first if available
        # Create a wrapper that calls our dispatcher with the expected signal args
        def asyncio_wrapper() -> None:
            # Simulate signal call with dummy values
            self._make_signal_dispatcher(sig)(sig.value, None)
        
        asyncio_registered = register_with_asyncio_if_available(sig, asyncio_wrapper)
        if asyncio_registered:
            # Asyncio registration succeeded, no original handler to store
            self._original_handlers[sig] = None
            return
        
        # Fall back to standard signal registration
        try:
            original_handler = stdlib_signal.signal(sig, self._make_signal_dispatcher(sig))
            self._original_handlers[sig] = original_handler
        except (ValueError, OSError) as e:
            # Signal not supported on this platform - implement Windows fallback
            metadata = get_signal_metadata(sig.name)
            if metadata and metadata.get("windows_fallback"):
                fallback = metadata["windows_fallback"]
                
                # Log structured warning for Windows fallback
                self._logger.warn(
                    fallback["log_message"],
                    context={
                        "signal": sig.name,
                        "platform": "windows",
                        "fallback_behavior": fallback["fallback_behavior"],
                        "operation_hint": fallback["operation_hint"],
                        "event_type": "signal_fallback"
                    }
                )
                
                # Emit telemetry event with tags
                from datetime import UTC, datetime

                from pyfulmen.telemetry.models import MetricEvent
                
                telemetry_tags = fallback.get("telemetry_tags", {
                    "signal": sig.name,
                    "platform": "windows",
                    "fallback_behavior": fallback["fallback_behavior"]
                })
                
                self._telemetry._record(
                    MetricEvent(
                        timestamp=datetime.now(UTC),
                        name="fulmen.signal.unsupported",
                        value=1.0,
                        unit="count",
                        tags=telemetry_tags
                    )
                )
                
                # Store None to indicate no OS handler registered
                self._original_handlers[sig] = None
            else:
                # For truly unsupported signals, still raise error
                raise RuntimeError(f"Signal {sig.name} not supported on this platform: {e}") from e
    
    def _unregister_from_os(self, sig: stdlib_signal.Signals) -> None:
        """Unregister signal from OS, restoring original handler."""
        try:
            original_handler = self._original_handlers.get(sig, stdlib_signal.SIG_DFL)
            stdlib_signal.signal(sig, original_handler)
            del self._original_handlers[sig]
        except (ValueError, OSError):
            # Signal might not be supported on this platform
            pass
    
    def _make_signal_dispatcher(self, sig: stdlib_signal.Signals) -> Callable[[int, Any], None]:
        """Create a dispatcher function for a signal."""
        def dispatcher(signum: int, frame: Any) -> None:
            """Dispatch signal to registered handlers."""
            try:
                # Handle Ctrl+C double-tap logic
                if sig == stdlib_signal.SIGINT:
                    self._handle_sigint_double_tap(sig)
                    return
                
                # Handle all other signals normally
                self._dispatch_handlers(sig)
                
            except Exception as e:
                # Log error but don't let it crash signal handling
                print(f"Error in signal handler for {sig.name}: {e}")
        
        return dispatcher
    
    def _handle_sigint_double_tap(self, sig: stdlib_signal.Signals) -> None:
        """Handle Ctrl+C double-tap logic."""
        metadata = get_signal_metadata("SIGINT")
        if not metadata:
            # Fallback to immediate exit if no metadata
            self._dispatch_handlers(sig)
            return
        
        window_seconds = metadata.get("double_tap_window_seconds", 2.0)
        message = metadata.get("double_tap_message", "Press Ctrl+C again to force quit")
        exit_code = metadata.get("double_tap_exit_code", 130)
        
        if self._double_tap.record_first_tap():
            # First tap - start graceful shutdown and show hint
            print(f"\n{message}")
            self._dispatch_handlers(sig)
        elif self._double_tap.should_force_exit(window_seconds):
            # Second tap within window - force exit
            if not self._double_tap.is_force_exit_suppressed():
                print("\nForce quitting...")
                import os
                os._exit(exit_code)
        else:
            # Second tap outside window - treat as new first tap
            self._double_tap.reset()
            self._double_tap.record_first_tap()
            print(f"\n{message}")
            self._dispatch_handlers(sig)
    
    def _dispatch_handlers(self, sig: stdlib_signal.Signals) -> None:
        """Dispatch signal to all registered handlers, handling both sync and async."""
        handlers = self.get_handlers(sig)
        
        for handler_info in handlers:
            try:
                # Create async-safe handler that handles both sync and async
                safe_handler = create_async_safe_handler(handler_info.handler)
                safe_handler()
            except Exception as e:
                # Continue with other handlers even if one fails
                handler_name = handler_info.name or "unnamed"
                print(f"Handler '{handler_name}' failed for {sig.name}: {e}")
    
    def get_double_tap_state(self) -> DoubleTapState:
        """Get the double-tap state object (for testing)."""
        return self._double_tap


# Global registry instance
_registry = SignalRegistry()


def handle(
    signal_name: str | stdlib_signal.Signals,
    handler: Callable[[], Any],
    *,
    priority: int = 0,
    name: str | None = None,
) -> None:
    """Register a handler for a signal.
    
    Args:
        signal_name: Signal name (e.g., "SIGTERM") or signal.Signals object.
        handler: Handler function to call when signal is received.
        priority: Priority for ordering (higher = called first).
        name: Optional name for debugging.
        
    Raises:
        ValueError: If signal is not supported on current platform.
        RuntimeError: If signal registration fails.
        
    Examples:
        >>> import signal
        >>> from pyfulmen.signals import handle
        >>> 
        >>> def cleanup():
        ...     print("Cleaning up...")
        >>> 
        >>> handle("SIGTERM", cleanup, priority=10)
        >>> handle(signal.SIGINT, cleanup, name="cleanup-handler")
    """
    # Convert string signal name to Signals object
    if isinstance(signal_name, str):
        try:
            sig = getattr(stdlib_signal, signal_name)
        except AttributeError as e:
            raise ValueError(f"Unknown signal name: {signal_name}") from e
    else:
        sig = signal_name
    
    # Register with global registry (platform check done there)
    _registry.register(sig, handler, priority=priority, name=name)


def on_shutdown(handler: Callable[[], Any], *, priority: int = 0) -> None:
    """Register a handler for graceful shutdown signals.
    
    Registers the handler for SIGTERM and SIGINT (first tap).
    
    Args:
        handler: Handler function to call during graceful shutdown.
        priority: Priority for ordering (higher = called first).
        
    Examples:
        >>> from pyfulmen.signals import on_shutdown
        >>> 
        >>> def cleanup():
        ...     print("Shutting down gracefully...")
        >>> 
        >>> on_shutdown(cleanup, priority=10)
    """
    handle("SIGTERM", handler, priority=priority, name=f"shutdown-{priority}")
    handle("SIGINT", handler, priority=priority, name=f"shutdown-{priority}")


def on_reload(handler: Callable[[], Any]) -> None:
    """Register a handler for config reload signal.
    
    Registers the handler for SIGHUP (Unix only). Integrates with
    the config reloader to provide full restart-based reload workflow.
    
    Args:
        handler: Handler function to call for config reload.
        
    Examples:
        >>> from pyfulmen.signals import on_reload
        >>> 
        >>> def reload_config():
        ...     print("Reloading configuration...")
        >>> 
        >>> on_reload(reload_config)
    """
    # Register handler with SIGHUP
    handle("SIGHUP", handler, name="reload")
    
    # Also register with config reloader for shutdown callbacks
    config_reloader = get_config_reloader()
    config_reloader.register_shutdown_callback(handler)


def on_force_quit(handler: Callable[[], Any]) -> None:
    """Register a handler for immediate quit signal.
    
    Registers the handler for SIGQUIT.
    
    Args:
        handler: Handler function to call for immediate quit.
        
    Examples:
        >>> from pyfulmen.signals import on_force_quit
        >>> 
        >>> def emergency_cleanup():
        ...     print("Emergency cleanup...")
        >>> 
        >>> on_force_quit(emergency_cleanup)
    """
    handle("SIGQUIT", handler, name="force-quit")


def get_registry() -> SignalRegistry:
    """Get the global signal registry (for testing and advanced usage).
    
    Returns:
        The global SignalRegistry instance.
    """
    return _registry


def clear_all_handlers() -> None:
    """Clear all registered handlers and restore original signal handling.
    
    This is primarily useful for testing and cleanup.
    """
    _registry.clear_all()