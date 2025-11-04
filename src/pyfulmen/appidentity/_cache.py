"""
Process-level caching for AppIdentity instances.

This module provides thread-safe caching with test override capabilities.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import ClassVar

from .models import AppIdentity


class IdentityCache:
    """Thread-safe cache for AppIdentity instances."""

    _instance: ClassVar[IdentityCache | None] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self):
        """Initialize cache storage."""
        # Only initialize if this is the first time
        if not hasattr(self, "_initialized"):
            self._cache: dict[str, AppIdentity] = {}
            self._cache_lock: threading.RLock = threading.RLock()
            self._test_override: threading.local = threading.local()
            self._initialized = True

    def __new__(cls) -> IdentityCache:
        """Singleton pattern with thread safety."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def get(self, key: str) -> AppIdentity | None:
        """Get cached identity or test override."""
        # Check for test override first
        override = self._get_test_override()
        if override is not None:
            return override

        # Check cache
        with self._cache_lock:
            return self._cache.get(key)

    def set(self, key: str, identity: AppIdentity) -> None:
        """Cache identity if no test override is active."""
        # Don't cache if test override is active
        if self._get_test_override() is not None:
            return

        with self._cache_lock:
            self._cache[key] = identity

    def clear(self) -> None:
        """Clear all cached identities."""
        with self._cache_lock:
            self._cache.clear()

    def reload(self) -> None:
        """Clear cache and test overrides."""
        self.clear()
        self._clear_test_override()

    def _get_test_override(self) -> AppIdentity | None:
        """Get test override for current thread."""
        return getattr(self._test_override, "override", None)

    def _set_test_override(self, identity: AppIdentity) -> None:
        """Set test override for current thread."""
        self._test_override.override = identity

    def _clear_test_override(self) -> None:
        """Clear test override for current thread."""
        if hasattr(self._test_override, "override"):
            delattr(self._test_override, "override")


@contextmanager
def override_identity_for_testing(identity: AppIdentity):
    """
    Context manager for test identity override.

    This provides thread-local test isolation without polluting the cache.

    Args:
        identity: The AppIdentity to use for the test context

    Example:
        with test_identity_override(test_identity):
            # All get_identity() calls return test_identity
            result = get_identity()
    """
    cache = IdentityCache()
    old_override = cache._get_test_override()
    had_override = old_override is not None

    try:
        cache._set_test_override(identity)
        yield
    finally:
        # Restore previous override state
        if had_override:
            cache._set_test_override(old_override)
        else:
            cache._clear_test_override()
