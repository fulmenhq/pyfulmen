"""
Tests for AppIdentity caching system.
"""

import threading

from pyfulmen.appidentity._cache import IdentityCache, override_identity_for_testing
from pyfulmen.appidentity.models import AppIdentity


class TestIdentityCache:
    """Test the IdentityCache singleton and caching behavior."""

    def test_singleton_pattern(self):
        """Test that IdentityCache follows singleton pattern."""
        cache1 = IdentityCache()
        cache2 = IdentityCache()

        assert cache1 is cache2

    def test_thread_safety(self):
        """Test that singleton creation is thread-safe."""
        caches = []

        def create_cache():
            caches.append(IdentityCache())

        threads = [threading.Thread(target=create_cache) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All should be the same instance
        first_cache = caches[0]
        for cache in caches:
            assert cache is first_cache

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = IdentityCache()
        cache.clear()  # Start fresh

        identity = AppIdentity(
            binary_name="test-app",
            vendor="test-vendor",
            env_prefix="TEST_",
            config_name="test-config",
            description="Test application",
        )

        # Test cache miss
        assert cache.get("test-key") is None

        # Test cache set and hit
        cache.set("test-key", identity)
        assert cache.get("test-key") is identity

    def test_cache_clear(self):
        """Test cache clearing functionality."""
        cache = IdentityCache()
        cache.clear()  # Start fresh

        identity = AppIdentity(
            binary_name="test-app",
            vendor="test-vendor",
            env_prefix="TEST_",
            config_name="test-config",
            description="Test application",
        )

        cache.set("test-key", identity)
        assert cache.get("test-key") is identity

        cache.clear()
        assert cache.get("test-key") is None

    def test_cache_reload(self):
        """Test cache reload functionality."""
        cache = IdentityCache()
        cache.clear()  # Start fresh

        identity = AppIdentity(
            binary_name="test-app",
            vendor="test-vendor",
            env_prefix="TEST_",
            config_name="test-config",
            description="Test application",
        )

        cache.set("test-key", identity)
        assert cache.get("test-key") is identity

        cache.reload()
        assert cache.get("test-key") is None


class TestIdentityOverride:
    """Test the test identity override functionality."""

    def test_override_context_manager(self):
        """Test test identity override context manager."""
        cache = IdentityCache()
        cache.clear()  # Start fresh

        normal_identity = AppIdentity(
            binary_name="normal-app",
            vendor="normal-vendor",
            env_prefix="NORMAL_",
            config_name="normal-config",
            description="Normal application",
        )

        override_identity = AppIdentity(
            binary_name="override-app",
            vendor="override-vendor",
            env_prefix="OVERRIDE_",
            config_name="override-config",
            description="Override application",
        )

        # Set normal cache
        cache.set("test-key", normal_identity)
        assert cache.get("test-key") is normal_identity

        # Test override
        with override_identity_for_testing(override_identity):
            assert cache.get("test-key") is override_identity

        # Test restoration
        assert cache.get("test-key") is normal_identity

    def test_override_without_cache(self):
        """Test override context manager without pre-existing cache."""
        cache = IdentityCache()
        cache.clear()  # Start fresh

        override_identity = AppIdentity(
            binary_name="override-app",
            vendor="override-vendor",
            env_prefix="OVERRIDE_",
            config_name="override-config",
            description="Override application",
        )

        # Test override without cache
        with override_identity_for_testing(override_identity):
            assert cache.get("any-key") is override_identity

        # Test no override after context
        assert cache.get("any-key") is None

    def test_thread_isolation(self):
        """Test that overrides are isolated between threads."""
        cache = IdentityCache()
        cache.clear()  # Start fresh

        main_identity = AppIdentity(
            binary_name="main-app",
            vendor="main-vendor",
            env_prefix="MAIN_",
            config_name="main-config",
            description="Main application",
        )

        thread_identity = AppIdentity(
            binary_name="thread-app",
            vendor="thread-vendor",
            env_prefix="THREAD_",
            config_name="thread-config",
            description="Thread application",
        )

        results = {}

        def thread_func():
            with override_identity_for_testing(thread_identity):
                results["thread"] = cache.get("test-key")

        # Main thread with override
        with override_identity_for_testing(main_identity):
            results["main"] = cache.get("test-key")

            # Start thread
            thread = threading.Thread(target=thread_func)
            thread.start()
            thread.join()

        # Check results
        assert results["main"] is main_identity
        assert results["thread"] is thread_identity

    def test_no_caching_with_override(self):
        """Test that cache doesn't store values when override is active."""
        cache = IdentityCache()
        cache.clear()  # Start fresh

        override_identity = AppIdentity(
            binary_name="override-app",
            vendor="override-vendor",
            env_prefix="OVERRIDE_",
            config_name="override-config",
            description="Override application",
        )

        with override_identity_for_testing(override_identity):
            # Try to cache while override is active
            cache.set("test-key", override_identity)

        # Should not be cached after override ends
        assert cache.get("test-key") is None

    def test_nested_overrides(self):
        """Test nested override context managers."""
        cache = IdentityCache()
        cache.clear()  # Start fresh

        outer_identity = AppIdentity(
            binary_name="outer-app",
            vendor="outer-vendor",
            env_prefix="OUTER_",
            config_name="outer-config",
            description="Outer application",
        )

        inner_identity = AppIdentity(
            binary_name="inner-app",
            vendor="inner-vendor",
            env_prefix="INNER_",
            config_name="inner-config",
            description="Inner application",
        )

        with override_identity_for_testing(outer_identity):
            assert cache.get("test-key") is outer_identity

            with override_identity_for_testing(inner_identity):
                assert cache.get("test-key") is inner_identity

            # Should restore to outer
            assert cache.get("test-key") is outer_identity

        # Should restore to None
        assert cache.get("test-key") is None


def override_identity_for_testing_direct():
    """Test the override_identity_for_testing function directly."""
    override_identity = AppIdentity(
        binary_name="test-override",
        vendor="test-vendor",
        env_prefix="TEST_",
        config_name="test-config",
        description="Test override application",
    )

    cache = IdentityCache()
    cache.clear()

    # Test override context
    with override_identity_for_testing(override_identity):
        assert cache.get("any-key") is override_identity

    # Test no override after context
    assert cache.get("any-key") is None
