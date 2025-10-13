"""Tests for logging middleware pipeline and redaction."""

import pytest

from pyfulmen.logging.middleware import (
    Middleware,
    MiddlewarePipeline,
    MiddlewareRegistry,
    RedactPIIMiddleware,
    RedactSecretsMiddleware,
)


class TestMiddlewareBase:
    """Tests for Middleware base interface."""

    def test_middleware_abstract(self):
        """Middleware cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Middleware()

    def test_custom_middleware(self):
        """Custom middleware can be created."""

        class AddFieldMiddleware(Middleware):
            def process(self, event):
                event["custom_field"] = "custom_value"
                return event

        middleware = AddFieldMiddleware()
        event = {"message": "test"}
        result = middleware.process(event)

        assert result["custom_field"] == "custom_value"
        assert result["message"] == "test"

    def test_middleware_can_drop_events(self):
        """Middleware can return None to drop events."""

        class DropMiddleware(Middleware):
            def process(self, event):
                if event["message"] == "drop":
                    return None
                return event

        middleware = DropMiddleware()
        assert middleware.process({"message": "keep"}) is not None
        assert middleware.process({"message": "drop"}) is None

    def test_middleware_order(self):
        """Middleware order can be configured."""

        class FirstMiddleware(Middleware):
            def __init__(self):
                super().__init__(order=10)

            def process(self, event):
                return event

        class SecondMiddleware(Middleware):
            def __init__(self):
                super().__init__(order=20)

            def process(self, event):
                return event

        first = FirstMiddleware()
        second = SecondMiddleware()

        assert first.order == 10
        assert second.order == 20


class TestMiddlewarePipeline:
    """Tests for MiddlewarePipeline."""

    def test_empty_pipeline(self):
        """Empty pipeline passes events through."""
        pipeline = MiddlewarePipeline([])
        event = {"message": "test"}
        result = pipeline.process(event)
        assert result == event

    def test_single_middleware(self):
        """Pipeline with single middleware."""

        class AddFieldMiddleware(Middleware):
            def process(self, event):
                event["added"] = True
                return event

        pipeline = MiddlewarePipeline([AddFieldMiddleware()])
        event = {"message": "test"}
        result = pipeline.process(event)

        assert result["message"] == "test"
        assert result["added"] is True

    def test_multiple_middleware_order(self):
        """Multiple middleware execute in order."""

        class FirstMiddleware(Middleware):
            def __init__(self):
                super().__init__(order=10)

            def process(self, event):
                event["sequence"] = ["first"]
                return event

        class SecondMiddleware(Middleware):
            def __init__(self):
                super().__init__(order=20)

            def process(self, event):
                event["sequence"].append("second")
                return event

        pipeline = MiddlewarePipeline([SecondMiddleware(), FirstMiddleware()])
        event = {"message": "test"}
        result = pipeline.process(event)

        assert result["sequence"] == ["first", "second"]

    def test_pipeline_drops_on_none(self):
        """Pipeline stops processing when middleware returns None."""

        class DropMiddleware(Middleware):
            def __init__(self):
                super().__init__(order=10)

            def process(self, event):
                return None

        class NeverRunMiddleware(Middleware):
            def __init__(self):
                super().__init__(order=20)

            def process(self, event):
                event["should_not_run"] = True
                return event

        pipeline = MiddlewarePipeline([DropMiddleware(), NeverRunMiddleware()])
        event = {"message": "test"}
        result = pipeline.process(event)

        assert result is None

    def test_none_middleware_list(self):
        """Pipeline handles None middleware list."""
        pipeline = MiddlewarePipeline(None)
        event = {"message": "test"}
        result = pipeline.process(event)
        assert result == event


class TestRedactSecretsMiddleware:
    """Tests for RedactSecretsMiddleware."""

    def test_redact_api_keys(self):
        """Redact Stripe-style API keys."""
        middleware = RedactSecretsMiddleware()
        event = {"message": "API key: sk_live_abc123def456ghi789", "context": {}}
        result = middleware.process(event)

        assert "sk_live_abc123def456ghi789" not in result["message"]
        assert "[REDACTED]" in result["message"]
        assert "secrets" in result["redaction_flags"]

    def test_redact_api_key_patterns(self):
        """Redact various API key patterns."""
        middleware = RedactSecretsMiddleware()

        test_cases = [
            ("sk_test_abc123def456ghi789", True),
            ("api_key=abc123def456ghi789jkl012", True),
            ("apikey: abc123def456ghi789jkl012", True),
        ]

        for secret, should_redact in test_cases:
            event = {"message": f"Secret: {secret}", "context": {}}
            result = middleware.process(event)
            if should_redact:
                assert secret not in result["message"]
                assert "secrets" in result["redaction_flags"]

    def test_redact_bearer_tokens(self):
        """Redact Bearer tokens."""
        middleware = RedactSecretsMiddleware()
        event = {"message": "Authorization: Bearer abc123.def456.ghi789", "context": {}}
        result = middleware.process(event)

        assert "abc123.def456.ghi789" not in result["message"]
        assert "[REDACTED]" in result["message"]
        assert "secrets" in result["redaction_flags"]

    def test_redact_passwords(self):
        """Redact password patterns."""
        middleware = RedactSecretsMiddleware()

        test_cases = [
            "password=secret123",
            "pwd: secret456",
            'pass="secret789"',
        ]

        for password_string in test_cases:
            event = {"message": f"Config: {password_string}", "context": {}}
            result = middleware.process(event)
            assert "secret" not in result["message"]
            assert "[REDACTED]" in result["message"]
            assert "secrets" in result["redaction_flags"]

    def test_redact_jwt_tokens(self):
        """Redact JWT tokens."""
        middleware = RedactSecretsMiddleware()
        jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
            "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        )
        event = {"message": f"Token: {jwt}", "context": {}}
        result = middleware.process(event)

        assert jwt not in result["message"]
        assert "[REDACTED_JWT]" in result["message"]
        assert "secrets" in result["redaction_flags"]

    def test_redact_authorization_headers(self):
        """Redact Authorization headers."""
        middleware = RedactSecretsMiddleware()
        event = {
            "message": "Request sent",
            "context": {"Authorization": "Bearer token123"},
        }
        result = middleware.process(event)

        assert "token123" not in str(result["context"])
        assert "[REDACTED]" in result["context"]["Authorization"]
        assert "secrets" in result["redaction_flags"]

    def test_no_redaction_when_no_secrets(self):
        """No redaction flags when no secrets found."""
        middleware = RedactSecretsMiddleware()
        event = {"message": "Normal log message", "context": {"key": "value"}}
        result = middleware.process(event)

        assert result["message"] == "Normal log message"
        assert "redaction_flags" not in result or "secrets" not in result["redaction_flags"]

    def test_redact_nested_context(self):
        """Redact secrets in nested context."""
        middleware = RedactSecretsMiddleware()
        event = {
            "message": "Processing",
            "context": {
                "config": {
                    "api_key": "sk_live_abc123def456ghi789",
                    "normal": "value",
                }
            },
        }
        result = middleware.process(event)

        assert "sk_live_abc123def456ghi789" not in str(result["context"])
        assert "[REDACTED]" in result["context"]["config"]["api_key"]
        assert result["context"]["config"]["normal"] == "value"
        assert "secrets" in result["redaction_flags"]

    def test_custom_patterns(self):
        """Custom redaction patterns."""
        custom_patterns = [(r"SECRET-\d+", "[CUSTOM_REDACTED]")]
        middleware = RedactSecretsMiddleware(custom_patterns=custom_patterns)
        event = {"message": "ID: SECRET-12345", "context": {}}
        result = middleware.process(event)

        assert "SECRET-12345" not in result["message"]
        assert "[CUSTOM_REDACTED]" in result["message"]
        assert "secrets" in result["redaction_flags"]

    def test_case_insensitive_patterns(self):
        """Patterns are case-insensitive."""
        middleware = RedactSecretsMiddleware()
        event = {"message": "PASSWORD=MySecret123", "context": {}}
        result = middleware.process(event)

        assert "MySecret123" not in result["message"]
        assert "[REDACTED]" in result["message"]


class TestRedactPIIMiddleware:
    """Tests for RedactPIIMiddleware."""

    def test_redact_email_addresses(self):
        """Redact email addresses."""
        middleware = RedactPIIMiddleware()
        event = {"message": "Contact: user@example.com for help", "context": {}}
        result = middleware.process(event)

        assert "user@example.com" not in result["message"]
        assert "[REDACTED_EMAIL]" in result["message"]
        assert "pii" in result["redaction_flags"]

    def test_redact_multiple_emails(self):
        """Redact multiple email addresses."""
        middleware = RedactPIIMiddleware()
        event = {
            "message": "From: alice@test.com to bob@example.org",
            "context": {},
        }
        result = middleware.process(event)

        assert "alice@test.com" not in result["message"]
        assert "bob@example.org" not in result["message"]
        assert result["message"].count("[REDACTED_EMAIL]") == 2
        assert "pii" in result["redaction_flags"]

    def test_redact_phone_numbers(self):
        """Redact US phone number formats."""
        middleware = RedactPIIMiddleware()

        test_cases = [
            "555-1234",
            "(555) 555-1234",
            "555.555.1234",
            "5555551234",
            "+1-555-555-1234",
        ]

        for phone in test_cases:
            event = {"message": f"Call: {phone}", "context": {}}
            result = middleware.process(event)
            assert "[REDACTED_PHONE]" in result["message"]
            assert "pii" in result["redaction_flags"]

    def test_redact_ssn_with_dashes(self):
        """Redact SSN with dashes."""
        middleware = RedactPIIMiddleware()
        event = {"message": "SSN: 123-45-6789", "context": {}}
        result = middleware.process(event)

        assert "123-45-6789" not in result["message"]
        assert "[REDACTED_SSN]" in result["message"]
        assert "pii" in result["redaction_flags"]

    def test_redact_ssn_without_dashes(self):
        """Redact SSN without dashes."""
        middleware = RedactPIIMiddleware()
        event = {"message": "SSN: 123456789", "context": {}}
        result = middleware.process(event)

        assert "123456789" not in result["message"]
        assert "[REDACTED_SSN]" in result["message"]
        assert "pii" in result["redaction_flags"]

    def test_redact_pii_in_context(self):
        """Redact PII in context."""
        middleware = RedactPIIMiddleware()
        event = {
            "message": "User registration",
            "context": {"email": "user@example.com", "phone": "555-1234"},
        }
        result = middleware.process(event)

        assert "user@example.com" not in result["context"]["email"]
        assert "[REDACTED_EMAIL]" in result["context"]["email"]
        assert "[REDACTED_PHONE]" in result["context"]["phone"]
        assert "pii" in result["redaction_flags"]

    def test_no_redaction_when_no_pii(self):
        """No redaction flags when no PII found."""
        middleware = RedactPIIMiddleware()
        event = {"message": "Normal log message", "context": {"key": "value"}}
        result = middleware.process(event)

        assert result["message"] == "Normal log message"
        assert "redaction_flags" not in result or "pii" not in result["redaction_flags"]

    def test_redact_nested_pii(self):
        """Redact PII in nested context."""
        middleware = RedactPIIMiddleware()
        event = {
            "message": "User data",
            "context": {
                "user": {
                    "email": "alice@example.com",
                    "name": "Alice",
                }
            },
        }
        result = middleware.process(event)

        assert "alice@example.com" not in str(result["context"])
        assert "[REDACTED_EMAIL]" in result["context"]["user"]["email"]
        assert result["context"]["user"]["name"] == "Alice"
        assert "pii" in result["redaction_flags"]

    def test_custom_pii_patterns(self):
        """Custom PII patterns."""
        custom_patterns = [(r"\bCUSTOMER-\d{6}\b", "[REDACTED_CUSTOMER_ID]")]
        middleware = RedactPIIMiddleware(custom_patterns=custom_patterns)
        event = {"message": "Customer: CUSTOMER-123456", "context": {}}
        result = middleware.process(event)

        assert "CUSTOMER-123456" not in result["message"]
        assert "[REDACTED_CUSTOMER_ID]" in result["message"]
        assert "pii" in result["redaction_flags"]


class TestMiddlewareRegistry:
    """Tests for MiddlewareRegistry."""

    def test_register_middleware(self):
        """Register custom middleware."""

        class CustomMiddleware(Middleware):
            def process(self, event):
                return event

        MiddlewareRegistry.register("custom", CustomMiddleware)
        assert "custom" in MiddlewareRegistry.list_registered()

    def test_create_registered_middleware(self):
        """Create middleware from registry."""
        middleware = MiddlewareRegistry.create("redact-secrets")
        assert isinstance(middleware, RedactSecretsMiddleware)

    def test_create_with_config(self):
        """Create middleware with config."""
        config = {"order": 50}
        middleware = MiddlewareRegistry.create("redact-secrets", config=config)
        assert middleware.order == 50

    def test_create_unregistered_raises(self):
        """Creating unregistered middleware raises KeyError."""
        with pytest.raises(KeyError, match="not registered"):
            MiddlewareRegistry.create("nonexistent")

    def test_list_registered_middleware(self):
        """List registered middleware."""
        registered = MiddlewareRegistry.list_registered()
        assert "redact-secrets" in registered
        assert "redact-pii" in registered

    def test_builtin_middleware_registered(self):
        """Built-in middleware are pre-registered."""
        assert "redact-secrets" in MiddlewareRegistry.list_registered()
        assert "redact-pii" in MiddlewareRegistry.list_registered()


class TestCombinedMiddleware:
    """Tests for combined middleware scenarios."""

    def test_secrets_and_pii_redaction(self):
        """Both secrets and PII are redacted."""
        pipeline = MiddlewarePipeline([RedactSecretsMiddleware(), RedactPIIMiddleware()])

        event = {
            "message": "User user@example.com has API key sk_live_abc123def456ghi789",
            "context": {},
        }
        result = pipeline.process(event)

        assert "user@example.com" not in result["message"]
        assert "sk_live_abc123def456ghi789" not in result["message"]
        assert "[REDACTED_EMAIL]" in result["message"]
        assert "[REDACTED]" in result["message"]
        assert "secrets" in result["redaction_flags"]
        assert "pii" in result["redaction_flags"]

    def test_multiple_redaction_flags(self):
        """Multiple redaction flags are accumulated."""
        secrets = RedactSecretsMiddleware(order=10)
        pii = RedactPIIMiddleware(order=20)
        pipeline = MiddlewarePipeline([secrets, pii])

        event = {
            "message": "user@example.com password=secret123",
            "context": {},
        }
        result = pipeline.process(event)

        assert "secrets" in result["redaction_flags"]
        assert "pii" in result["redaction_flags"]
        assert len(result["redaction_flags"]) == 2

    def test_redaction_preserves_other_fields(self):
        """Redaction preserves non-sensitive fields."""
        pipeline = MiddlewarePipeline([RedactSecretsMiddleware(), RedactPIIMiddleware()])

        event = {
            "message": "Login attempt from user@example.com",
            "context": {"request_id": "req-123", "status": "success"},
            "severity": "INFO",
        }
        result = pipeline.process(event)

        assert result["context"]["request_id"] == "req-123"
        assert result["context"]["status"] == "success"
        assert result["severity"] == "INFO"
        assert "[REDACTED_EMAIL]" in result["message"]
