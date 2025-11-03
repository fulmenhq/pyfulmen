"""Throttling and backpressure control for log events.

Provides rate limiting and burst handling to prevent log volume overload.
Supports multiple drop policies for handling excess events.

Example:
    >>> from pyfulmen.logging.throttling import ThrottleController
    >>>
    >>> # Create throttle controller with 10 events/second, burst of 20
    >>> controller = ThrottleController(
    ...     max_rate=10,
    ...     burst_size=20,
    ...     window_size=1.0,
    ...     drop_policy="drop-oldest"
    ... )
    >>>
    >>> # Check if event should be emitted
    >>> if controller.should_emit(event):
    ...     emit_event(event)
    ...     controller.record_emission()
"""

import time
from collections import deque
from threading import Lock
from typing import Any

from .middleware import Middleware


class ThrottleController:
    """Rate limiting controller with burst support and drop policies.

    Uses a sliding window algorithm to track event rates and enforce
    throttling limits. Supports burst allowances and configurable
    drop policies when limits are exceeded.

    Attributes:
        max_rate: Maximum events per window_size (0 = unlimited)
        burst_size: Maximum burst capacity (0 = no burst)
        window_size: Time window in seconds for rate calculation
        drop_policy: Policy for handling excess ("drop-oldest", "drop-newest", "block")
    """

    def __init__(
        self,
        max_rate: int = 0,
        burst_size: int = 0,
        window_size: float = 1.0,
        drop_policy: str = "drop-oldest",
    ):
        """Initialize throttle controller.

        Args:
            max_rate: Maximum events per window_size (0 = unlimited)
            burst_size: Maximum burst capacity (0 = no burst, use max_rate)
            window_size: Time window in seconds (default: 1.0)
            drop_policy: Drop policy ("drop-oldest", "drop-newest", "block")

        Example:
            >>> # 100 events/second with burst of 150
            >>> controller = ThrottleController(
            ...     max_rate=100,
            ...     burst_size=150,
            ...     window_size=1.0
            ... )
        """
        self.max_rate = max_rate
        self.burst_size = burst_size if burst_size > 0 else max_rate
        self.window_size = window_size
        self.drop_policy = drop_policy

        # Event tracking
        self._events: deque[float] = deque()
        self._lock = Lock()
        self._dropped_count = 0

        # Validate configuration
        if max_rate < 0:
            raise ValueError("max_rate must be non-negative")
        if burst_size < 0:
            raise ValueError("burst_size must be non-negative")
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if drop_policy not in ("drop-oldest", "drop-newest", "block"):
            raise ValueError(f"Invalid drop_policy '{drop_policy}'. Must be 'drop-oldest', 'drop-newest', or 'block'")

    def should_emit(self, event: dict[str, Any] | None = None) -> bool:
        """Check if event should be emitted based on throttling rules.

        Uses sliding window rate limiting with burst support. Automatically
        cleans up old events outside the current window.

        Args:
            event: Event to check (currently unused, reserved for future)

        Returns:
            True if event should be emitted, False if dropped

        Example:
            >>> controller = ThrottleController(max_rate=10, window_size=1.0)
            >>> if controller.should_emit(event):
            ...     # Event passes throttle check
            ...     emit_event(event)
            ...     controller.record_emission()
        """
        # Unlimited rate (0 = no throttling)
        if self.max_rate == 0:
            return True

        with self._lock:
            current_time = time.time()

            # Remove events outside current window
            self._cleanup_old_events(current_time)

            # Check if we're within burst limit (absolute cap)
            if len(self._events) >= self.burst_size:
                # Over burst limit - apply drop policy
                if self.drop_policy == "drop-oldest":
                    # Allow new event, drop oldest
                    if self._events:
                        self._events.popleft()
                    self._dropped_count += 1
                    return True
                elif self.drop_policy == "drop-newest":
                    # Drop this new event
                    self._dropped_count += 1
                    return False
                else:  # block
                    # Block until window allows emission
                    # For now, drop - blocking would require sleep/retry
                    self._dropped_count += 1
                    return False

            # Under burst limit - allow event
            return True

    def record_emission(self) -> None:
        """Record that an event was emitted.

        Must be called after successfully emitting an event that passed
        should_emit() check. Updates internal state for rate limiting.

        Example:
            >>> if controller.should_emit(event):
            ...     emit_event(event)
            ...     controller.record_emission()  # Record successful emission
        """
        with self._lock:
            current_time = time.time()
            self._events.append(current_time)

            # Maintain burst size limit
            while len(self._events) > self.burst_size:
                self._events.popleft()

    def get_dropped_count(self) -> int:
        """Get number of events dropped since controller creation.

        Returns:
            Number of dropped events

        Example:
            >>> controller = ThrottleController(max_rate=10)
            >>> # ... emit events ...
            >>> dropped = controller.get_dropped_count()
            >>> print(f"Dropped {dropped} events due to throttling")
        """
        with self._lock:
            return self._dropped_count

    def reset_dropped_count(self) -> int:
        """Reset dropped event counter and return previous value.

        Returns:
            Number of dropped events before reset

        Example:
            >>> dropped = controller.reset_dropped_count()
            >>> print(f"Reset counter, had {dropped} dropped events")
        """
        with self._lock:
            count = self._dropped_count
            self._dropped_count = 0
            return count

    def get_current_rate(self) -> float:
        """Calculate current event rate (events per second).

        Returns:
            Current rate in events/second

        Example:
            >>> rate = controller.get_current_rate()
            >>> print(f"Current rate: {rate:.2f} events/second")
        """
        with self._lock:
            current_time = time.time()
            self._cleanup_old_events(current_time)

            if not self._events:
                return 0.0

            # Calculate rate over current window
            return len(self._events) / self.window_size

    def _cleanup_old_events(self, current_time: float) -> None:
        """Remove events outside current time window.

        Args:
            current_time: Current timestamp for window calculation

        Note:
            Must be called with _lock held.
        """
        window_start = current_time - self.window_size

        # Remove events before window start
        while self._events and self._events[0] < window_start:
            self._events.popleft()


class ThrottlingMiddleware(Middleware):
    """Middleware that applies throttling to log events.

    Integrates with middleware pipeline to drop events based on rate limits.
    Supports burst capacity and multiple drop policies.

    Example:
        >>> from pyfulmen.logging import Logger, LoggingProfile
        >>> from pyfulmen.logging.throttling import ThrottlingMiddleware
        >>>
        >>> # Create throttling middleware
        >>> throttle = ThrottlingMiddleware(max_rate=100, burst_size=150)
        >>>
        >>> # Use in logger
        >>> logger = Logger(
        ...     service="myapp",
        ...     profile=LoggingProfile.ENTERPRISE,
        ...     middleware=[throttle]
        ... )
    """

    def __init__(
        self,
        max_rate: int = 0,
        burst_size: int = 0,
        window_size: float = 1.0,
        drop_policy: str = "drop-oldest",
        config: dict[str, Any] | None = None,
        order: int = 50,
    ):
        """Initialize throttling middleware.

        Args:
            max_rate: Maximum events per window_size (0 = unlimited)
            burst_size: Maximum burst capacity (0 = use max_rate)
            window_size: Time window in seconds
            drop_policy: Drop policy for excess events
            config: Optional configuration dictionary (for registry instantiation)
            order: Middleware execution order (default: 50)
        """
        # Extract values from config if provided (schema uses camelCase)
        if config:
            max_rate = config.get("maxRate", max_rate)
            burst_size = config.get("burstSize", burst_size)
            window_size = config.get("windowSize", window_size)
            drop_policy = config.get("dropPolicy", drop_policy)
            # Handle bucketId -> bucket_id conversion
            if "bucketId" in config:
                config["bucket_id"] = config["bucketId"]

        # Initialize base Middleware with combined config
        throttle_config = config or {}
        throttle_config.update(
            {
                "max_rate": max_rate,
                "burst_size": burst_size,
                "window_size": window_size,
                "drop_policy": drop_policy,
            }
        )
        super().__init__(config=throttle_config, order=order)

        # Create throttle controller
        self.controller = ThrottleController(
            max_rate=max_rate,
            burst_size=burst_size,
            window_size=window_size,
            drop_policy=drop_policy,
        )

    def process(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Process event through throttle controller.

        Args:
            event: Log event to process

        Returns:
            Event if allowed, None if dropped

        Note:
            When event is dropped, throttle_bucket field is set for
            observability before returning None.
        """
        if self.controller.should_emit(event):
            self.controller.record_emission()
            return event
        else:
            # Event dropped - set throttle_bucket before dropping
            # NOTE: We still drop it (return None) but record the bucket
            # This is for observability - the event won't be emitted but
            # if it were, it would have this bucket identifier
            bucket_id = self.config.get("bucket_id", "default")
            event["throttle_bucket"] = f"throttle:{bucket_id}:{self.controller.max_rate}"

            # Still return None to drop the event
            # The throttle_bucket is set for debugging/observability only
            return None

    def get_dropped_count(self) -> int:
        """Get number of events dropped by this middleware.

        Returns:
            Number of dropped events
        """
        return self.controller.get_dropped_count()


__all__ = [
    "ThrottleController",
    "ThrottlingMiddleware",
]
