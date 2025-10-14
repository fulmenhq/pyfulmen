"""Logging profile definitions and validation.

Provides progressive logging profiles (SIMPLE, STRUCTURED, ENTERPRISE, CUSTOM)
with profile-specific requirements and validation.

Example:
    >>> from pyfulmen.logging.profiles import LoggingProfile, get_profile_requirements
    >>> profile = LoggingProfile.ENTERPRISE
    >>> requirements = get_profile_requirements(profile)
    >>> print(requirements['required_sinks'])
    ['console', 'file']
"""

from enum import Enum
from typing import Any


class LoggingProfile(str, Enum):
    """Progressive logging profiles from Crucible standards.

    Profiles provide zero-complexity defaults with enterprise power-ups:
    - SIMPLE: Basic console logging for development
    - STRUCTURED: Structured JSON output with sinks
    - ENTERPRISE: Full middleware, policy, and compliance features
    - CUSTOM: User-defined configuration
    """

    SIMPLE = "SIMPLE"
    STRUCTURED = "STRUCTURED"
    ENTERPRISE = "ENTERPRISE"
    CUSTOM = "CUSTOM"


def get_profile_requirements(profile: LoggingProfile) -> dict[str, Any]:
    """Get required configuration for a logging profile.

    Args:
        profile: The logging profile to check

    Returns:
        Dictionary of profile requirements

    Example:
        >>> reqs = get_profile_requirements(LoggingProfile.ENTERPRISE)
        >>> reqs['required_middleware']
        ['correlation']
    """
    requirements = {
        LoggingProfile.SIMPLE: {
            "required_sinks": ["console"],
            "allowed_formats": ["text", "console"],
            "max_middleware": 0,
            "throttling_allowed": False,
            "policy_enforcement": False,
        },
        LoggingProfile.STRUCTURED: {
            "required_sinks": [],  # User-configured
            "allowed_formats": ["json", "text"],
            "max_middleware": 2,
            "throttling_allowed": True,
            "policy_enforcement": False,
        },
        LoggingProfile.ENTERPRISE: {
            "required_sinks": [],  # User-configured, but validated by policy
            "allowed_formats": ["json"],
            "min_middleware": 1,  # At least correlation
            "throttling_allowed": True,
            "policy_enforcement": True,
        },
        LoggingProfile.CUSTOM: {
            "required_sinks": [],
            "allowed_formats": ["json", "text", "console"],
            "max_middleware": None,  # Unlimited
            "throttling_allowed": True,
            "policy_enforcement": False,  # User-controlled
        },
    }

    return requirements.get(profile, {})


def validate_profile_requirements(
    profile: LoggingProfile,
    sinks: list | None = None,
    middleware: list | None = None,
    format: str = "json",
    throttling_enabled: bool = False,
    policy_enabled: bool = False,
) -> list[str]:
    """Validate configuration against profile requirements.

    Args:
        profile: The logging profile
        sinks: List of configured sinks
        middleware: List of configured middleware
        format: Log format (json, text, console)
        throttling_enabled: Whether throttling is enabled
        policy_enabled: Whether policy enforcement is enabled

    Returns:
        List of validation error messages (empty if valid)
    """
    reqs = get_profile_requirements(profile)
    errors = []

    # Check required sinks
    if reqs.get("required_sinks"):
        configured_sinks = [s.get("type") if isinstance(s, dict) else s for s in (sinks or [])]
        for required in reqs["required_sinks"]:
            if required not in configured_sinks:
                errors.append(f"Profile {profile} requires sink type '{required}'")

    # Check format
    if format not in reqs.get("allowed_formats", []):
        errors.append(f"Profile {profile} does not allow format '{format}'")

    # Check middleware count
    middleware_count = len(middleware or [])
    if (
        "max_middleware" in reqs
        and reqs["max_middleware"] is not None
        and middleware_count > reqs["max_middleware"]
    ):
        max_allowed = reqs["max_middleware"]
        errors.append(
            f"Profile {profile} allows max {max_allowed} middleware, got {middleware_count}"
        )
    if (
        "min_middleware" in reqs
        and reqs["min_middleware"] is not None
        and middleware_count < reqs["min_middleware"]
    ):
        min_required = reqs["min_middleware"]
        errors.append(
            f"Profile {profile} requires min {min_required} middleware, got {middleware_count}"
        )

    # Check throttling
    if not reqs.get("throttling_allowed", False) and throttling_enabled:
        errors.append(f"Profile {profile} does not allow throttling")

    # Check policy enforcement
    if profile == LoggingProfile.ENTERPRISE and not policy_enabled:
        errors.append("ENTERPRISE profile requires policy enforcement")
    if (
        profile != LoggingProfile.ENTERPRISE
        and policy_enabled
        and not reqs.get("policy_enforcement", False)
    ):
        errors.append(f"Profile {profile} does not support policy enforcement")

    return errors


__all__ = [
    "LoggingProfile",
    "get_profile_requirements",
    "validate_profile_requirements",
]
