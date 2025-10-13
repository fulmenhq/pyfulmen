"""Middleware pipeline for log event processing.

Provides base middleware interface, built-in processors for redaction,
and a registry system for middleware management.

Example:
    >>> from pyfulmen.logging.middleware import RedactSecretsMiddleware, MiddlewarePipeline
    >>>
    >>> # Create middleware pipeline
    >>> pipeline = MiddlewarePipeline([
    ...     RedactSecretsMiddleware(),
    ...     RedactPIIMiddleware()
    ... ])
    >>>
    >>> # Process log event
    >>> event = {"message": "API key: sk_live_abc123", "context": {}}
    >>> processed = pipeline.process(event)
    >>> # Message is redacted: "API key: [REDACTED]"
"""

import re
from abc import ABC, abstractmethod
from typing import Any


class Middleware(ABC):
    """Base middleware interface for log event processing.

    Middleware processors can modify, enrich, or filter log events as they
    flow through the logging pipeline. Return None to drop an event.

    Attributes:
        order: Processing order (lower values run first, default: 100)
        config: Optional configuration dictionary
    """

    def __init__(self, config: dict[str, Any] | None = None, order: int = 100):
        """Initialize middleware.

        Args:
            config: Optional configuration dictionary
            order: Processing order (lower runs first, default: 100)
        """
        self.config = config or {}
        self.order = order

    @abstractmethod
    def process(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Process log event.

        Args:
            event: Log event dictionary to process

        Returns:
            Modified event dictionary or None to drop the event

        Note:
            Implementers should avoid modifying the input event directly.
            Create a shallow copy if modifications are needed.
        """


class MiddlewarePipeline:
    """Pipeline for executing middleware in order.

    Middleware are executed in order of their `order` attribute (ascending).
    If any middleware returns None, the event is dropped and no further
    processing occurs.

    Example:
        >>> pipeline = MiddlewarePipeline([
        ...     RedactSecretsMiddleware(order=10),
        ...     RedactPIIMiddleware(order=20)
        ... ])
        >>> event = {"message": "secret", "context": {}}
        >>> result = pipeline.process(event)
    """

    def __init__(self, middleware: list[Middleware] | None = None):
        """Initialize pipeline with middleware.

        Args:
            middleware: List of middleware processors (empty list if None)
        """
        self.middleware = sorted(middleware or [], key=lambda m: m.order)

    def process(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Process event through middleware pipeline.

        Args:
            event: Log event dictionary to process

        Returns:
            Processed event or None if dropped by middleware
        """
        current_event: dict[str, Any] | None = event
        for m in self.middleware:
            current_event = m.process(current_event)
            if current_event is None:
                return None
        return current_event


class RedactSecretsMiddleware(Middleware):
    """Redact secrets from log messages and context.

    Detects and redacts common secret patterns including API keys, tokens,
    passwords, and authentication credentials. Adds 'secrets' to redactionFlags
    when redaction occurs.

    Default patterns:
    - API keys: sk_live_, sk_test_, api_key_, apikey_
    - Bearer tokens: Bearer [token]
    - Passwords: password=..., pwd=..., pass=...
    - Authorization headers: Authorization: ...
    - JWT tokens: eyJ[...]

    Example:
        >>> middleware = RedactSecretsMiddleware()
        >>> event = {"message": "API key: sk_live_abc123", "context": {}}
        >>> result = middleware.process(event)
        >>> result["message"]
        'API key: [REDACTED]'
        >>> result["redaction_flags"]
        ['secrets']
    """

    DEFAULT_PATTERNS = [
        (r"sk_(live|test)_[a-zA-Z0-9]{10,}", "[REDACTED]"),
        (r"api[_-]?key[_:\s=]+['\"]?([a-zA-Z0-9_\-]{10,})", "api_key=[REDACTED]"),
        (r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*", "Bearer [REDACTED]"),
        (r"(password|pwd|pass)[_:\s=]+['\"]?[^\s'\"]{6,}", r"\1=[REDACTED]"),
        (r"Authorization[:\s]+[^\s]+\s+[^\s]+", "Authorization: [REDACTED]"),
        (r"eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+", "[REDACTED_JWT]"),
    ]

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        order: int = 10,
        custom_patterns: list[tuple[str, str]] | None = None,
    ):
        """Initialize secrets redaction middleware.

        Args:
            config: Optional configuration dictionary
            order: Processing order (default: 10, early in pipeline)
            custom_patterns: Additional (pattern, replacement) tuples
        """
        super().__init__(config, order)
        patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            patterns.extend(custom_patterns)
        self.patterns = [(re.compile(p, re.IGNORECASE), r) for p, r in patterns]

    def process(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Redact secrets from event.

        Args:
            event: Log event dictionary

        Returns:
            Event with secrets redacted
        """
        redacted = False

        if "message" in event:
            original_message = event["message"]
            redacted_message = self._redact_string(original_message)
            if redacted_message != original_message:
                event["message"] = redacted_message
                redacted = True

        if "context" in event and isinstance(event["context"], dict):
            original_context = event["context"]
            redacted_context = self._redact_dict(original_context)
            if redacted_context != original_context:
                event["context"] = redacted_context
                redacted = True

        if redacted:
            flags = event.get("redaction_flags", [])
            if "secrets" not in flags:
                flags = flags + ["secrets"]
                event["redaction_flags"] = flags

        return event

    def _redact_string(self, value: str) -> str:
        """Redact secrets from string value.

        Args:
            value: String to redact

        Returns:
            Redacted string
        """
        result = value
        for pattern, replacement in self.patterns:
            result = pattern.sub(replacement, result)
        return result

    def _redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact secrets from dictionary.

        Args:
            data: Dictionary to redact

        Returns:
            Dictionary with redacted values
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._redact_string(value)
            elif isinstance(value, dict):
                result[key] = self._redact_dict(value)
            elif isinstance(value, list):
                result[key] = [self._redact_string(v) if isinstance(v, str) else v for v in value]
            else:
                result[key] = value
        return result


class RedactPIIMiddleware(Middleware):
    """Redact personally identifiable information (PII) from log events.

    Detects and redacts PII patterns including email addresses, phone numbers,
    and US Social Security Numbers. Adds 'pii' to redactionFlags when redaction
    occurs.

    Default patterns:
    - Email addresses: user@example.com
    - Phone numbers: US formats (555-1234, (555) 555-1234, etc.)
    - SSN: 123-45-6789, 123456789

    Example:
        >>> middleware = RedactPIIMiddleware()
        >>> event = {"message": "Contact: user@example.com", "context": {}}
        >>> result = middleware.process(event)
        >>> result["message"]
        'Contact: [REDACTED_EMAIL]'
        >>> result["redaction_flags"]
        ['pii']
    """

    DEFAULT_PATTERNS = [
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]"),
        (
            r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "[REDACTED_PHONE]",
        ),
        (r"\b\d{3}-\d{4}\b", "[REDACTED_PHONE]"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]"),
        (r"\b\d{9}\b", "[REDACTED_SSN]"),
    ]

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        order: int = 20,
        custom_patterns: list[tuple[str, str]] | None = None,
    ):
        """Initialize PII redaction middleware.

        Args:
            config: Optional configuration dictionary
            order: Processing order (default: 20)
            custom_patterns: Additional (pattern, replacement) tuples
        """
        super().__init__(config, order)
        patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            patterns.extend(custom_patterns)
        self.patterns = [(re.compile(p), r) for p, r in patterns]

    def process(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Redact PII from event.

        Args:
            event: Log event dictionary

        Returns:
            Event with PII redacted
        """
        redacted = False

        if "message" in event:
            original_message = event["message"]
            redacted_message = self._redact_string(original_message)
            if redacted_message != original_message:
                event["message"] = redacted_message
                redacted = True

        if "context" in event and isinstance(event["context"], dict):
            original_context = event["context"]
            redacted_context = self._redact_dict(original_context)
            if redacted_context != original_context:
                event["context"] = redacted_context
                redacted = True

        if redacted:
            flags = event.get("redaction_flags", [])
            if "pii" not in flags:
                flags = flags + ["pii"]
                event["redaction_flags"] = flags

        return event

    def _redact_string(self, value: str) -> str:
        """Redact PII from string value.

        Args:
            value: String to redact

        Returns:
            Redacted string
        """
        result = value
        for pattern, replacement in self.patterns:
            result = pattern.sub(replacement, result)
        return result

    def _redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact PII from dictionary.

        Args:
            data: Dictionary to redact

        Returns:
            Dictionary with redacted values
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._redact_string(value)
            elif isinstance(value, dict):
                result[key] = self._redact_dict(value)
            elif isinstance(value, list):
                result[key] = [self._redact_string(v) if isinstance(v, str) else v for v in value]
            else:
                result[key] = value
        return result


class MiddlewareRegistry:
    """Registry for middleware types with factory creation.

    Provides centralized registration and creation of middleware instances
    from configuration. Useful for loading middleware from config files.

    Example:
        >>> MiddlewareRegistry.register("redact-secrets", RedactSecretsMiddleware)
        >>> middleware = MiddlewareRegistry.create("redact-secrets", {"order": 10})
    """

    _registry: dict[str, type[Middleware]] = {}

    @classmethod
    def register(cls, name: str, middleware_class: type[Middleware]) -> None:
        """Register middleware type.

        Args:
            name: Middleware name for config references
            middleware_class: Middleware class to register
        """
        cls._registry[name] = middleware_class

    @classmethod
    def create(cls, name: str, config: dict[str, Any] | None = None) -> Middleware:
        """Create middleware instance from config.

        Args:
            name: Registered middleware name
            config: Optional configuration dictionary

        Returns:
            Middleware instance

        Raises:
            KeyError: If middleware name not registered
        """
        if name not in cls._registry:
            raise KeyError(f"Middleware '{name}' not registered")

        middleware_class = cls._registry[name]

        # Extract order from config if provided
        if config and "order" in config:
            return middleware_class(config=config, order=config["order"])
        return middleware_class(config=config)

    @classmethod
    def list_registered(cls) -> list[str]:
        """List registered middleware names.

        Returns:
            List of registered middleware names
        """
        return list(cls._registry.keys())


MiddlewareRegistry.register("redact-secrets", RedactSecretsMiddleware)
MiddlewareRegistry.register("redact-pii", RedactPIIMiddleware)


__all__ = [
    "Middleware",
    "MiddlewarePipeline",
    "RedactSecretsMiddleware",
    "RedactPIIMiddleware",
    "MiddlewareRegistry",
]
