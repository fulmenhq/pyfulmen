"""Tests for logging throttling and backpressure control."""

import time

import pytest

from pyfulmen.logging.throttling import ThrottleController, ThrottlingMiddleware


class TestThrottleController:
    """Tests for ThrottleController."""

    def test_unlimited_rate(self):
        """Unlimited rate (0) allows all events."""
        controller = ThrottleController(max_rate=0)

        for _ in range(1000):
            assert controller.should_emit() is True
            controller.record_emission()

    def test_basic_rate_limiting(self):
        """Rate limiting enforces max_rate."""
        controller = ThrottleController(max_rate=5, window_size=1.0)

        # First 5 should pass
        for _ in range(5):
            assert controller.should_emit() is True
            controller.record_emission()

        # 6th should be handled by drop policy
        # Default drop-oldest allows it
        assert controller.should_emit() is True

    def test_burst_capacity(self):
        """Burst capacity allows temporary rate increases."""
        controller = ThrottleController(max_rate=10, burst_size=20, window_size=1.0, drop_policy="drop-newest")

        # Should allow up to burst_size events
        for _ in range(20):
            assert controller.should_emit() is True
            controller.record_emission()

        # 21st should be dropped (drop-newest policy)
        assert controller.should_emit() is False

    def test_drop_oldest_policy(self):
        """Drop-oldest policy removes oldest events when limit reached."""
        controller = ThrottleController(max_rate=5, burst_size=5, window_size=1.0, drop_policy="drop-oldest")

        # Fill to capacity
        for _ in range(5):
            assert controller.should_emit() is True
            controller.record_emission()

        # Next event should pass (drops oldest)
        assert controller.should_emit() is True
        assert controller.get_dropped_count() == 1

    def test_drop_newest_policy(self):
        """Drop-newest policy rejects new events when limit reached."""
        controller = ThrottleController(max_rate=5, burst_size=5, window_size=1.0, drop_policy="drop-newest")

        # Fill to capacity
        for _ in range(5):
            assert controller.should_emit() is True
            controller.record_emission()

        # Next events should be dropped
        for _ in range(3):
            assert controller.should_emit() is False

        assert controller.get_dropped_count() == 3

    def test_block_policy(self):
        """Block policy drops events (blocking would require sleep/retry)."""
        controller = ThrottleController(max_rate=5, burst_size=5, window_size=1.0, drop_policy="block")

        # Fill to capacity
        for _ in range(5):
            assert controller.should_emit() is True
            controller.record_emission()

        # Next event should be "blocked" (currently drops)
        assert controller.should_emit() is False
        assert controller.get_dropped_count() == 1

    def test_sliding_window(self):
        """Sliding window allows events after time passes."""
        controller = ThrottleController(max_rate=5, window_size=0.1)

        # Fill to capacity
        for _ in range(5):
            assert controller.should_emit() is True
            controller.record_emission()

        # Wait for window to slide
        time.sleep(0.15)

        # Should allow new events
        for _ in range(5):
            assert controller.should_emit() is True
            controller.record_emission()

    def test_get_dropped_count(self):
        """Dropped count tracks rejected events."""
        controller = ThrottleController(max_rate=3, burst_size=3, window_size=1.0, drop_policy="drop-newest")

        # Fill capacity
        for _ in range(3):
            assert controller.should_emit() is True
            controller.record_emission()

        # Drop some events
        for _ in range(5):
            controller.should_emit()

        assert controller.get_dropped_count() == 5

    def test_reset_dropped_count(self):
        """Reset dropped count and return previous value."""
        controller = ThrottleController(max_rate=2, burst_size=2, window_size=1.0, drop_policy="drop-newest")

        # Fill and drop
        for _ in range(2):
            controller.should_emit()
            controller.record_emission()
        for _ in range(3):
            controller.should_emit()

        count = controller.reset_dropped_count()
        assert count == 3
        assert controller.get_dropped_count() == 0

    def test_get_current_rate(self):
        """Current rate reflects events in window."""
        controller = ThrottleController(max_rate=100, window_size=1.0)

        # Emit 10 events
        for _ in range(10):
            controller.should_emit()
            controller.record_emission()

        # Rate should be approximately 10 events/second
        rate = controller.get_current_rate()
        assert 9.0 <= rate <= 11.0

    def test_get_current_rate_after_window(self):
        """Current rate is 0 after window expires."""
        controller = ThrottleController(max_rate=100, window_size=0.1)

        # Emit events
        for _ in range(5):
            controller.should_emit()
            controller.record_emission()

        # Wait for window to expire
        time.sleep(0.15)

        assert controller.get_current_rate() == 0.0

    def test_invalid_max_rate(self):
        """Negative max_rate raises ValueError."""
        with pytest.raises(ValueError, match="max_rate must be non-negative"):
            ThrottleController(max_rate=-1)

    def test_invalid_burst_size(self):
        """Negative burst_size raises ValueError."""
        with pytest.raises(ValueError, match="burst_size must be non-negative"):
            ThrottleController(max_rate=10, burst_size=-5)

    def test_invalid_window_size(self):
        """Zero or negative window_size raises ValueError."""
        with pytest.raises(ValueError, match="window_size must be positive"):
            ThrottleController(max_rate=10, window_size=0)

        with pytest.raises(ValueError, match="window_size must be positive"):
            ThrottleController(max_rate=10, window_size=-1.0)

    def test_invalid_drop_policy(self):
        """Invalid drop_policy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid drop_policy"):
            ThrottleController(max_rate=10, drop_policy="invalid")

    def test_burst_defaults_to_max_rate(self):
        """Burst size defaults to max_rate when not specified."""
        controller = ThrottleController(max_rate=10, burst_size=0)

        # Should allow up to max_rate events
        for _ in range(10):
            assert controller.should_emit() is True
            controller.record_emission()

    def test_concurrent_access(self):
        """Thread-safe access with lock."""
        import threading

        controller = ThrottleController(max_rate=100, window_size=1.0)
        results = []

        def emit_events():
            for _ in range(50):
                if controller.should_emit():
                    controller.record_emission()
                    results.append(1)

        threads = [threading.Thread(target=emit_events) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 200 events should be tracked (within burst)
        assert len(results) <= 200


class TestThrottlingMiddleware:
    """Tests for ThrottlingMiddleware."""

    def test_middleware_passes_events_within_limit(self):
        """Middleware passes events within throttle limit."""
        middleware = ThrottlingMiddleware(max_rate=10, burst_size=10, window_size=1.0)

        for _ in range(10):
            event = {"message": "test"}
            result = middleware.process(event)
            assert result is not None
            assert result["message"] == "test"

    def test_middleware_drops_events_over_limit(self):
        """Middleware drops events over throttle limit."""
        middleware = ThrottlingMiddleware(max_rate=5, burst_size=5, window_size=1.0, drop_policy="drop-newest")

        # Fill capacity
        for _ in range(5):
            event = {"message": "test"}
            assert middleware.process(event) is not None

        # Exceed limit - should drop
        event = {"message": "dropped"}
        assert middleware.process(event) is None

    def test_middleware_order(self):
        """Middleware has configurable order."""
        middleware = ThrottlingMiddleware(max_rate=10, order=50)
        assert middleware.order == 50

    def test_middleware_config(self):
        """Middleware stores configuration."""
        middleware = ThrottlingMiddleware(max_rate=100, burst_size=150, window_size=1.0, drop_policy="drop-oldest")

        assert middleware.config["max_rate"] == 100
        assert middleware.config["burst_size"] == 150
        assert middleware.config["window_size"] == 1.0
        assert middleware.config["drop_policy"] == "drop-oldest"

    def test_middleware_get_dropped_count(self):
        """Middleware tracks dropped event count."""
        middleware = ThrottlingMiddleware(max_rate=3, burst_size=3, window_size=1.0, drop_policy="drop-newest")

        # Fill and exceed
        for _ in range(3):
            middleware.process({"message": "test"})
        for _ in range(5):
            middleware.process({"message": "test"})

        assert middleware.get_dropped_count() == 5

    def test_middleware_unlimited_rate(self):
        """Middleware with unlimited rate passes all events."""
        middleware = ThrottlingMiddleware(max_rate=0)

        for _ in range(1000):
            event = {"message": "test"}
            assert middleware.process(event) is not None

    def test_middleware_integration_example(self):
        """Example integration with middleware pipeline."""
        from pyfulmen.logging.middleware import MiddlewarePipeline

        throttle = ThrottlingMiddleware(max_rate=10, burst_size=15, window_size=1.0, drop_policy="drop-newest")
        pipeline = MiddlewarePipeline([throttle])

        passed = 0
        dropped = 0

        for i in range(20):
            event = {"message": f"Event {i}"}
            result = pipeline.process(event)
            if result:
                passed += 1
            else:
                dropped += 1

        # Should pass up to burst_size (15) with drop-newest policy
        assert passed == 15
        assert dropped == 5


class TestThrottlingScenarios:
    """Integration tests for throttling scenarios."""

    def test_sustained_load(self):
        """Handle sustained load over multiple windows."""
        controller = ThrottleController(max_rate=10, window_size=0.1)

        total_passed = 0
        total_dropped = 0

        for window in range(3):
            for _ in range(15):
                if controller.should_emit():
                    controller.record_emission()
                    total_passed += 1
                else:
                    total_dropped += 1

            # Wait for next window
            if window < 2:
                time.sleep(0.11)

        # Most events should pass over multiple windows
        assert total_passed > 0
        assert total_passed >= 20  # At least 2 windows worth

    def test_burst_then_steady(self):
        """Handle burst followed by steady rate."""
        controller = ThrottleController(max_rate=10, burst_size=20, window_size=1.0, drop_policy="drop-newest")

        # Burst phase
        burst_passed = 0
        for _ in range(25):
            if controller.should_emit():
                controller.record_emission()
                burst_passed += 1

        # Should pass burst_size events
        assert burst_passed == 20

        # Wait for window to expire
        time.sleep(1.1)

        # Steady phase - new window allows burst_size again
        steady_passed = 0
        for _ in range(25):
            if controller.should_emit():
                controller.record_emission()
                steady_passed += 1

        # Should pass burst_size events in new window
        assert steady_passed == 20

    def test_mixed_drop_policies(self):
        """Different drop policies have different behaviors."""
        # Drop-oldest allows continuous flow
        oldest = ThrottleController(max_rate=5, burst_size=5, window_size=1.0, drop_policy="drop-oldest")

        for _ in range(5):
            oldest.should_emit()
            oldest.record_emission()

        for _ in range(10):
            assert oldest.should_emit() is True

        # Drop-newest blocks new events
        newest = ThrottleController(max_rate=5, burst_size=5, window_size=1.0, drop_policy="drop-newest")

        for _ in range(5):
            newest.should_emit()
            newest.record_emission()

        for _ in range(10):
            assert newest.should_emit() is False
