"""
Embedded identity registration and retrieval for distributed packages.

This module provides the mechanism for Python packages to register their
app identity at import time, enabling standalone binaries/wheels to know
their identity without requiring .fulmen/app.yaml on disk.

The embedded identity serves as a fallback when filesystem discovery fails,
following the discovery precedence:
1. Explicit path parameter
2. FULMEN_APP_IDENTITY_PATH environment variable
3. Filesystem discovery (CWD ancestor search)
4. Embedded identity fallback (this module)
5. Raise AppIdentityNotFoundError

Usage for downstream packages (e.g., percheron):

    # src/percheron/__init__.py
    from importlib.resources import files
    from pyfulmen.appidentity import register_embedded_identity_yaml

    try:
        _data = files("percheron").joinpath("_assets/app.yaml").read_bytes()
        register_embedded_identity_yaml(_data)
    except Exception:
        pass  # Graceful degradation if package data missing
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from ._validator import validate_app_identity
from .errors import EmbeddedIdentityAlreadyRegisteredError
from .models import AppIdentity

# Module-level state for embedded identity (thread-safe via lock)
_embedded_lock = threading.Lock()
_embedded_identity: AppIdentity | None = None
_embedded_registered: bool = False


def register_embedded_identity_yaml(data: bytes) -> None:
    """
    Register YAML bytes as fallback identity when runtime discovery fails.

    This function should be called at package import time (in __init__.py)
    before any get_identity() calls. It validates the YAML on registration
    and stores the parsed identity for later use as a fallback.

    Semantics:
    - First registration wins (subsequent calls raise EmbeddedIdentityAlreadyRegisteredError)
    - Validates YAML against schema on registration (fail-fast)
    - Stored as immutable process-level fallback

    Args:
        data: Raw bytes of app.yaml content (typically from importlib.resources)

    Raises:
        EmbeddedIdentityAlreadyRegisteredError: If already registered
        AppIdentityValidationError: If YAML is invalid
        yaml.YAMLError: If YAML parsing fails
        ValueError: If data is empty or not a valid dictionary

    Example:
        >>> from importlib.resources import files
        >>> from pyfulmen.appidentity import register_embedded_identity_yaml
        >>> data = files("mypackage").joinpath("_assets/app.yaml").read_bytes()
        >>> register_embedded_identity_yaml(data)
    """
    global _embedded_identity, _embedded_registered

    with _embedded_lock:
        if _embedded_registered:
            raise EmbeddedIdentityAlreadyRegisteredError()

        # Parse YAML
        raw_data = yaml.safe_load(data)

        if raw_data is None:
            raise ValueError("Embedded identity data is empty or contains only whitespace")

        if not isinstance(raw_data, dict):
            raise ValueError(f"Expected dictionary, got {type(raw_data).__name__}")

        # Validate against schema (use synthetic path for error messages)
        synthetic_path = Path("<embedded>")
        validated_data = validate_app_identity(raw_data, synthetic_path)

        # Create AppIdentity instance
        identity = _create_embedded_identity(validated_data)

        # Store and mark as registered
        _embedded_identity = identity
        _embedded_registered = True


def _create_embedded_identity(data: dict[str, Any]) -> AppIdentity:
    """
    Create AppIdentity instance from validated embedded data.

    Args:
        data: Validated identity data

    Returns:
        AppIdentity instance with embedded provenance
    """
    # Extract app and metadata sections
    app_data = data["app"]
    metadata_data = data.get("metadata", {})
    python_metadata = metadata_data.get("python") or {}

    # Apply telemetry default: fallback to binary_name if not specified
    telemetry_namespace = metadata_data.get("telemetry_namespace")
    if telemetry_namespace is None:
        telemetry_namespace = app_data["binary_name"]

    # Create AppIdentity instance
    identity = AppIdentity(
        binary_name=app_data["binary_name"],
        vendor=app_data["vendor"],
        env_prefix=app_data["env_prefix"],
        config_name=app_data["config_name"],
        description=app_data["description"],
        project_url=metadata_data.get("project_url"),
        support_email=metadata_data.get("support_email"),
        license=metadata_data.get("license"),
        repository_category=metadata_data.get("repository_category"),
        telemetry_namespace=telemetry_namespace,
        registry_id=metadata_data.get("registry_id"),
        python_distribution=python_metadata.get("distribution_name"),
        python_package=python_metadata.get("package_name"),
        console_scripts=python_metadata.get("console_scripts"),
    )

    # Populate internal fields (need object.__setattr__ for frozen dataclass)
    object.__setattr__(identity, "_raw_metadata", data)
    object.__setattr__(
        identity,
        "_provenance",
        {
            "source_path": "<embedded>",
            "source_type": "embedded",
            "loaded_at": datetime.now(UTC).isoformat(),
        },
    )

    return identity


def get_embedded_identity() -> AppIdentity | None:
    """
    Return the registered embedded identity, or None if not registered.

    This function is used by the discovery logic as a fallback when
    filesystem discovery fails.

    Returns:
        The registered AppIdentity if available, None otherwise

    Example:
        >>> from pyfulmen.appidentity import get_embedded_identity
        >>> identity = get_embedded_identity()
        >>> if identity is not None:
        ...     print(f"Embedded identity: {identity.binary_name}")
    """
    with _embedded_lock:
        return _embedded_identity


def clear_embedded_identity() -> None:
    """
    Clear registered embedded identity. Primarily for testing.

    This function resets the embedded identity state, allowing
    re-registration. Should only be used in test fixtures.

    Example:
        >>> from pyfulmen.appidentity import clear_embedded_identity
        >>> clear_embedded_identity()  # Reset for next test
    """
    global _embedded_identity, _embedded_registered

    with _embedded_lock:
        _embedded_identity = None
        _embedded_registered = False


def is_embedded_identity_registered() -> bool:
    """
    Check if an embedded identity has been registered.

    Returns:
        True if embedded identity is registered, False otherwise
    """
    with _embedded_lock:
        return _embedded_registered
