"""
PyFulmen Signal Handling Module

Provides cross-platform signal handling with Windows fallbacks, graceful shutdown,
config reload workflows, and comprehensive testing utilities.

This module implements the Crucible v0.2.6 signal handling standard for the Fulmen ecosystem.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from typing import Any

from pyfulmen.signals._asyncio import (
    create_async_safe_handler,
    get_running_loop,
    is_asyncio_available,
    register_with_asyncio_if_available,
    reset_asyncio_detection,
    wrap_async_handler,
)

# Import internal components
from pyfulmen.signals._catalog import (
    _load_catalog,
    get_signal_metadata,
    get_signals_version,
)
from pyfulmen.signals._http import (
    SignalEndpointHelper,
    build_signal_request,
    build_windows_fallback_docs,
    get_http_helper,
)
from pyfulmen.signals._platform import supports_signal
from pyfulmen.signals._registry import (
    clear_all_handlers,
    get_registry,
    handle,
    on_force_quit,
    on_reload,
    on_shutdown,
)
from pyfulmen.signals._reload import (
    get_config_reloader,
    register_shutdown_callback,
    reload_config,
)

# Public API surface
__all__ = [
    # Version and metadata
    "get_signals_version",
    "get_signal_metadata", 
    "supports_signal",
    
    # Handler registration
    "handle",
    "on_shutdown",
    "on_reload", 
    "on_force_quit",
    
    # Config reload workflow
    "get_config_reloader",
    "register_shutdown_callback",
    "reload_config",
    
    # HTTP endpoint helpers
    "SignalEndpointHelper",
    "build_signal_request",
    "build_windows_fallback_docs",
    "get_http_helper",
    
    # Asyncio integration
    "is_asyncio_available",
    "get_running_loop",
    "register_with_asyncio_if_available",
    "wrap_async_handler",
    "create_async_safe_handler",
    
    # Testing and utilities
    "clear_all_handlers",
    "get_registry",
    "reset_asyncio_detection",
]

# Load catalog at import time for performance
try:
    _catalog = _load_catalog()
except Exception as e:
    raise ImportError(f"Failed to load signal catalog: {e}") from e

# Module version (matches PyFulmen version)
__version__ = "0.1.10"

def get_module_info() -> Mapping[str, Any]:
    """Get comprehensive module information for debugging and diagnostics.
    
    Returns:
        Dictionary with module version, catalog provenance, and platform info.
    """
    return {
        "pyfulmen_version": __version__,
        "catalog_version": get_signals_version(),
        "python_version": sys.version,
        "platform": sys.platform,
    }