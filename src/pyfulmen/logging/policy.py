"""Policy enforcement for logging configuration.

Provides policy loading, validation, and enforcement for logging profiles.
Organizations can define policies to ensure appropriate logging patterns
across different application types and environments.

Example:
    >>> from pyfulmen.logging.policy import load_policy, validate_config_against_policy
    >>> from pyfulmen.logging import LoggingConfig, LoggingProfile
    >>>
    >>> # Load policy from file
    >>> policy = load_policy("config/logging-policy.yaml")
    >>>
    >>> # Validate configuration
    >>> config = LoggingConfig(profile=LoggingProfile.ENTERPRISE, service="myapp")
    >>> validate_config_against_policy(config, policy)
"""

from pathlib import Path

import yaml

from pyfulmen.config.paths import get_org_config_dir

from ._models import LoggingConfig, LoggingPolicy


def load_policy(policy_file: str | Path) -> LoggingPolicy:
    """Load logging policy from YAML file.

    Searches for policy file in standard locations if not found at
    specified path:
    1. Specified path (exact match)
    2. .fulmen/logging-policy.yaml (repository-local)
    3. /etc/fulmen/logging-policy.yaml (system-wide)
    4. $FULMEN_ORG_PATH/logging-policy.yaml (organization-level, default /opt/fulmen)

    Args:
        policy_file: Path to policy file (relative or absolute)

    Returns:
        LoggingPolicy instance loaded from file

    Raises:
        FileNotFoundError: If policy file cannot be found in any location
        ValueError: If policy file is invalid or cannot be parsed

    Example:
        >>> policy = load_policy("config/logging-policy.yaml")
        >>> policy.allowed_profiles
        ['STRUCTURED', 'ENTERPRISE']
    """
    # Convert to Path for easier handling
    path = Path(policy_file)

    # Search locations in order per updated logging standard
    search_paths = [
        path,  # Exact path specified
        Path(".fulmen") / "logging-policy.yaml",
        Path("/etc/fulmen") / "logging-policy.yaml",
        get_org_config_dir() / "logging-policy.yaml",
    ]

    # Find first existing policy file
    policy_path: Path | None = None
    for search_path in search_paths:
        if search_path.exists() and search_path.is_file():
            policy_path = search_path
            break

    if policy_path is None:
        raise FileNotFoundError(
            f"Policy file not found: {policy_file}. Searched: {', '.join(str(p) for p in search_paths)}"
        )

    # Load and parse YAML
    try:
        with open(policy_path, encoding="utf-8") as f:
            policy_data = yaml.safe_load(f)

        if not isinstance(policy_data, dict):
            raise ValueError(f"Policy file must contain a YAML dictionary: {policy_path}")

        # Create LoggingPolicy from data
        return LoggingPolicy(**policy_data)

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in policy file {policy_path}: {e}") from e
    except Exception as e:
        raise ValueError(f"Failed to load policy from {policy_path}: {e}") from e


def validate_config_against_policy(
    config: LoggingConfig,
    policy: LoggingPolicy,
    environment: str | None = None,
    app_type: str | None = None,
    strict_mode: bool = False,
) -> list[str]:
    """Validate logging configuration against policy constraints.

    Checks configuration for policy violations including:
    - Profile allowed by policy
    - Profile matches environment requirements
    - Profile meets app type requirements
    - Required features are enabled

    Args:
        config: Logging configuration to validate
        policy: Policy to validate against
        environment: Deployment environment (e.g., 'production', 'staging')
        app_type: Application type (e.g., 'workhorse', 'api', 'cli')
        strict_mode: If True, raise ValueError on any violations

    Returns:
        List of violation messages (empty if no violations)

    Raises:
        ValueError: If strict_mode=True and violations are found

    Example:
        >>> config = LoggingConfig(profile=LoggingProfile.SIMPLE, service="myapp")
        >>> policy = LoggingPolicy(allowed_profiles=["ENTERPRISE"])
        >>> violations = validate_config_against_policy(config, policy)
        >>> if violations:
        ...     print(f"Policy violations: {violations}")
    """
    violations: list[str] = []

    # Check if profile is allowed
    if config.profile not in policy.allowed_profiles:
        violations.append(f"Profile '{config.profile}' not in allowed profiles: {policy.allowed_profiles}")

    # Check environment rules
    if environment and environment in policy.environment_rules:
        allowed_for_env = policy.environment_rules[environment]
        if config.profile not in allowed_for_env:
            violations.append(
                f"Profile '{config.profile}' not allowed in environment '{environment}'. Allowed: {allowed_for_env}"
            )

    # Check app type requirements
    if app_type and app_type in policy.required_profiles:
        required_for_app = policy.required_profiles[app_type]
        if config.profile not in required_for_app:
            violations.append(
                f"Profile '{config.profile}' not required for app type '{app_type}'. Required: {required_for_app}"
            )

    # Check profile-specific requirements
    if config.profile in policy.profile_requirements:
        requirements = policy.profile_requirements[config.profile]
        required_features = requirements.get("requiredFeatures", [])

        # Validate required features are configured
        for feature in required_features:
            if feature == "correlation" and not _has_correlation(config):
                violations.append(
                    f"Profile '{config.profile}' requires 'correlation' feature but correlation_id is not configured"
                )
            elif feature == "middleware" and not config.middleware:
                violations.append(
                    f"Profile '{config.profile}' requires 'middleware' feature but no middleware configured"
                )
            elif feature == "throttling" and not config.throttling:
                violations.append(
                    f"Profile '{config.profile}' requires 'throttling' feature but no throttling configured"
                )

    # Handle strict mode
    if strict_mode and violations:
        violation_msg = "\n  - ".join(violations)
        raise ValueError(f"Policy validation failed in strict mode:\n  - {violation_msg}")

    return violations


def enforce_policy(
    config: LoggingConfig,
    policy: LoggingPolicy,
    environment: str | None = None,
    app_type: str | None = None,
) -> None:
    """Enforce policy constraints on logging configuration.

    Validates configuration and raises ValueError if violations are found.
    Uses strict_mode from policy's audit settings if available.

    Args:
        config: Logging configuration to validate
        policy: Policy to enforce
        environment: Deployment environment
        app_type: Application type

    Raises:
        ValueError: If configuration violates policy

    Example:
        >>> config = LoggingConfig(profile=LoggingProfile.ENTERPRISE, service="myapp")
        >>> policy = load_policy("config/logging-policy.yaml")
        >>> enforce_policy(config, policy, environment="production")
    """
    # Get strict mode from audit settings
    audit_settings = policy.audit_settings or {}
    strict_mode = audit_settings.get("enforceStrictMode", False)

    # Validate with strict mode
    violations = validate_config_against_policy(
        config,
        policy,
        environment=environment,
        app_type=app_type,
        strict_mode=strict_mode,
    )

    # Log violations if audit logging is enabled
    if audit_settings.get("logPolicyViolations", False) and violations:
        import sys

        for violation in violations:
            print(f"Policy violation: {violation}", file=sys.stderr)


def _has_correlation(config: LoggingConfig) -> bool:
    """Check if configuration has correlation support enabled.

    Args:
        config: Configuration to check

    Returns:
        True if correlation is configured, False otherwise

    Note:
        Correlation is considered enabled if middleware is configured
        or if ENTERPRISE profile is used (which auto-enables correlation).
    """
    # ENTERPRISE profile always has correlation support
    if config.profile == "ENTERPRISE":
        return True

    # Check if correlation middleware is configured
    if config.middleware:
        for mw in config.middleware:
            if isinstance(mw, dict):
                mw_type = mw.get("type", "")
                if "correlation" in mw_type.lower():
                    return True

    return False


__all__ = [
    "load_policy",
    "validate_config_against_policy",
    "enforce_policy",
]
