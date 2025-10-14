"""Unit tests for logging profiles module."""

from pyfulmen.logging.profiles import (
    LoggingProfile,
    get_profile_requirements,
    validate_profile_requirements,
)


class TestLoggingProfile:
    """Test LoggingProfile enum."""

    def test_profile_values(self):
        """Test all profile values are defined."""
        assert LoggingProfile.SIMPLE == "SIMPLE"
        assert LoggingProfile.STRUCTURED == "STRUCTURED"
        assert LoggingProfile.ENTERPRISE == "ENTERPRISE"
        assert LoggingProfile.CUSTOM == "CUSTOM"

    def test_profile_enum_properties(self):
        """Test profile enum properties."""
        assert LoggingProfile.SIMPLE.value == "SIMPLE"
        assert LoggingProfile.ENTERPRISE.value == "ENTERPRISE"


class TestGetProfileRequirements:
    """Test get_profile_requirements function."""

    def test_simple_profile_requirements(self):
        """Test SIMPLE profile requirements."""
        reqs = get_profile_requirements(LoggingProfile.SIMPLE)
        assert reqs["required_sinks"] == ["console"]
        assert "text" in reqs["allowed_formats"]
        assert reqs["max_middleware"] == 0
        assert not reqs["throttling_allowed"]
        assert not reqs["policy_enforcement"]

    def test_structured_profile_requirements(self):
        """Test STRUCTURED profile requirements."""
        reqs = get_profile_requirements(LoggingProfile.STRUCTURED)
        assert reqs["required_sinks"] == []
        assert "json" in reqs["allowed_formats"]
        assert reqs["max_middleware"] == 2
        assert reqs["throttling_allowed"]
        assert not reqs["policy_enforcement"]

    def test_enterprise_profile_requirements(self):
        """Test ENTERPRISE profile requirements."""
        reqs = get_profile_requirements(LoggingProfile.ENTERPRISE)
        assert reqs["required_sinks"] == []
        assert reqs["allowed_formats"] == ["json"]
        assert reqs["min_middleware"] == 1
        assert reqs["throttling_allowed"]
        assert reqs["policy_enforcement"]

    def test_custom_profile_requirements(self):
        """Test CUSTOM profile requirements."""
        reqs = get_profile_requirements(LoggingProfile.CUSTOM)
        assert reqs["required_sinks"] == []
        assert "json" in reqs["allowed_formats"]
        assert reqs["max_middleware"] is None  # Unlimited
        assert reqs["throttling_allowed"]
        assert not reqs["policy_enforcement"]


class TestValidateProfileRequirements:
    """Test validate_profile_requirements function."""

    def test_valid_simple_config(self):
        """Test valid SIMPLE profile configuration."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.SIMPLE,
            sinks=[{"type": "console"}],
            format="text",
            throttling_enabled=False,
            policy_enabled=False,
        )
        assert errors == []

    def test_invalid_simple_missing_console(self):
        """Test SIMPLE profile without required console sink."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.SIMPLE,
            sinks=[{"type": "file"}],
            format="text",
        )
        assert "requires sink type 'console'" in errors[0]

    def test_invalid_simple_with_middleware(self):
        """Test SIMPLE profile with middleware (not allowed)."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.SIMPLE,
            sinks=[{"type": "console"}],
            middleware=[{"name": "correlation"}],
            format="text",
        )
        assert "allows max 0 middleware" in errors[0]

    def test_valid_structured_config(self):
        """Test valid STRUCTURED profile configuration."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.STRUCTURED,
            sinks=[{"type": "console"}],
            middleware=[{"name": "correlation"}],
            format="json",
            throttling_enabled=True,
        )
        assert errors == []

    def test_invalid_structured_format(self):
        """Test STRUCTURED profile with invalid format."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.STRUCTURED,
            sinks=[{"type": "console"}],
            format="console",  # Not allowed for STRUCTURED
        )
        assert "does not allow format 'console'" in errors[0]

    def test_valid_enterprise_config(self):
        """Test valid ENTERPRISE profile configuration."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.ENTERPRISE,
            sinks=[{"type": "console"}],
            middleware=[{"name": "correlation"}],
            format="json",
            policy_enabled=True,
        )
        assert errors == []

    def test_invalid_enterprise_no_middleware(self):
        """Test ENTERPRISE profile without required middleware."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.ENTERPRISE,
            sinks=[{"type": "console"}],
            format="json",
            policy_enabled=True,
        )
        assert "requires min 1 middleware" in errors[0]

    def test_invalid_enterprise_no_policy(self):
        """Test ENTERPRISE profile without policy enforcement."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.ENTERPRISE,
            sinks=[{"type": "console"}],
            middleware=[{"name": "correlation"}],
            format="json",
            policy_enabled=False,
        )
        assert "requires policy enforcement" in errors[0]

    def test_valid_custom_config(self):
        """Test valid CUSTOM profile configuration."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.CUSTOM,
            sinks=[{"type": "console"}],
            middleware=[{"name": "correlation"}, {"name": "redaction"}],
            format="text",
            throttling_enabled=True,
        )
        assert errors == []

    def test_invalid_throttling_for_simple(self):
        """Test throttling not allowed for SIMPLE profile."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.SIMPLE,
            sinks=[{"type": "console"}],
            format="text",
            throttling_enabled=True,
        )
        assert "does not allow throttling" in errors[0]

    def test_invalid_policy_for_structured(self):
        """Test policy enforcement not supported for STRUCTURED profile."""
        errors = validate_profile_requirements(
            profile=LoggingProfile.STRUCTURED,
            sinks=[{"type": "console"}],
            format="json",
            policy_enabled=True,
        )
        assert "does not support policy enforcement" in errors[0]
