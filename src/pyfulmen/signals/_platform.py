"""Platform detection and Windows fallback support.

Provides platform introspection capabilities including the supports_signal() API
required by Crucible v0.2.6. Handles Windows fallback behaviors with structured
logging and HTTP endpoint guidance.
"""

from __future__ import annotations

import signal
import sys
from typing import Any

from pyfulmen.signals._catalog import get_signal_metadata, list_all_signals


def _get_platform_name() -> str:
    """Get normalized platform name for signal support checks.
    
    Returns:
        Normalized platform name: 'windows', 'linux', 'darwin', or 'freebsd'.
    """
    platform = sys.platform.lower()
    
    if platform.startswith("win"):
        return "windows"
    elif platform.startswith("linux"):
        return "linux"
    elif platform.startswith("darwin"):
        return "darwin"
    elif platform.startswith("freebsd"):
        return "freebsd"
    else:
        # Default to generic Unix for other platforms
        return "unix"


def supports_signal(sig: signal.Signals) -> bool:
    """Check if a signal is natively supported on the current platform.
    
    This implements the Crucible v0.2.6 supports_signal() API contract.
    
    Args:
        sig: Signal to check (from signal.Signals enum).
        
    Returns:
        True if signal is natively supported, False if it uses Windows fallback.
        
    Examples:
        >>> import signal
        >>> from pyfulmen.signals import supports_signal
        >>> supports_signal(signal.SIGTERM)
        True
        >>> supports_signal(signal.SIGHUP)  # On Windows
        False
    """
    platform = _get_platform_name()
    
    # Windows has limited signal support
    if platform == "windows":
        # Only SIGTERM, SIGINT, and SIGQUIT are supported on Windows
        supported_windows_signals = {
            signal.SIGTERM,  # Maps to CTRL_CLOSE_EVENT
            signal.SIGINT,   # Maps to CTRL_C_EVENT
            signal.SIGQUIT,  # Maps to CTRL_BREAK_EVENT
        }
        return sig in supported_windows_signals
    
    # Unix platforms support all standard signals
    # Note: Some signal numbers vary by platform (e.g., SIGUSR1/SIGUSR2 on macOS/FreeBSD)
    unix_signals = {
        signal.SIGTERM,
        signal.SIGINT,
        signal.SIGHUP,
        signal.SIGQUIT,
        signal.SIGPIPE,
        signal.SIGALRM,
        signal.SIGUSR1,
        signal.SIGUSR2,
    }
    return sig in unix_signals


def get_signal_fallback_behavior(signal_name: str) -> dict[str, str] | None:
    """Get Windows fallback behavior for unsupported signals.
    
    Args:
        signal_name: Name of the signal (e.g., "SIGHUP", "SIGPIPE").
        
    Returns:
        Fallback behavior dict or None if signal is supported.
    """
    # Check if signal is supported on current platform
    try:
        sig_obj = getattr(signal, signal_name)
        if supports_signal(sig_obj):
            return None
    except AttributeError:
        # Signal doesn't exist in this Python build
        return None
    
    # Get fallback behavior from catalog
    metadata = get_signal_metadata(signal_name)
    if not metadata:
        return None
    
    return metadata.get("windows_fallback")


def get_windows_event_mapping(signal_name: str) -> int | None:
    """Get Windows console event for supported signals.
    
    Args:
        signal_name: Name of the signal (e.g., "SIGTERM", "SIGINT").
        
    Returns:
        Windows event number or None if no mapping exists.
    """
    metadata = get_signal_metadata(signal_name)
    if not metadata:
        return None
    
    windows_event = metadata.get("windows_event")
    if windows_event is None:
        return None
    
    # Map event names to numbers (from Windows API)
    event_mapping = {
        "CTRL_C_EVENT": 0,
        "CTRL_BREAK_EVENT": 1,
        "CTRL_CLOSE_EVENT": 2,
        "CTRL_LOGOFF_EVENT": 5,
        "CTRL_SHUTDOWN_EVENT": 6,
    }
    
    return event_mapping.get(windows_event)


def get_platform_signal_number(signal_name: str) -> int | None:
    """Get the actual signal number for the current platform.
    
    Args:
        signal_name: Name of the signal (e.g., "SIGUSR1", "SIGUSR2").
        
    Returns:
        Signal number for current platform or None if not available.
    """
    try:
        sig_obj = getattr(signal, signal_name)
        return sig_obj.value
    except AttributeError:
        # Signal doesn't exist in this Python build
        return None


def list_supported_signals() -> list[str]:
    """Get list of signals supported on current platform.
    
    Returns:
        List of signal names that are natively supported.
    """
    supported = []
    for signal_name in list_all_signals():
        try:
            sig_obj = getattr(signal, signal_name)
            if supports_signal(sig_obj):
                supported.append(signal_name)
        except AttributeError:
            # Signal doesn't exist in this Python build
            continue
    
    return supported


def list_unsupported_signals() -> list[str]:
    """Get list of signals that require Windows fallbacks.
    
    Returns:
        List of signal names that use Windows fallback behaviors.
    """
    unsupported = []
    for signal_name in list_all_signals():
        try:
            sig_obj = getattr(signal, signal_name)
            if not supports_signal(sig_obj):
                unsupported.append(signal_name)
        except AttributeError:
            # Signal doesn't exist in this Python build
            continue
    
    return unsupported


def get_platform_info() -> dict[str, Any]:
    """Get comprehensive platform information for debugging.
    
    Returns:
        Dictionary with platform details and signal support matrix.
    """
    platform = _get_platform_name()
    
    return {
        "platform": platform,
        "python_platform": sys.platform,
        "supported_signals": list_supported_signals(),
        "unsupported_signals": list_unsupported_signals(),
        "total_signals": len(list_all_signals()),
    }