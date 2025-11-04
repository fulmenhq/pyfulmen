"""
File discovery and loading for app identity.

This module implements the discovery precedence and loading logic
following the Crucible app identity standard.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from ._validator import validate_app_identity
from .errors import AppIdentityLoadError, AppIdentityNotFoundError
from .models import AppIdentity


def _discover_identity_path() -> Path:
    """
    Discover identity file path following precedence rules.

    Precedence:
    1. Environment variable FULMEN_APP_IDENTITY_PATH
    2. Ancestor search from Path.cwd() for .fulmen/app.yaml
    3. Raise AppIdentityNotFoundError with searched paths

    Returns:
        Path to the identity file

    Raises:
        AppIdentityNotFoundError: If no identity file found
    """
    searched_paths = []

    # 1. Environment variable override (highest precedence)
    env_path = os.environ.get("FULMEN_APP_IDENTITY_PATH")
    if env_path:
        env_path_obj = Path(env_path).resolve()
        searched_paths.append(env_path_obj)
        if env_path_obj.is_file():
            return env_path_obj
        else:
            # Environment variable is set but file doesn't exist - fail immediately
            raise AppIdentityNotFoundError(searched_paths)

    # 2. Ancestor search from current working directory
    cwd = Path.cwd()
    search_dir = cwd

    while True:
        candidate_path = search_dir / ".fulmen" / "app.yaml"
        searched_paths.append(candidate_path)

        if candidate_path.is_file():
            return candidate_path

        # Move to parent directory, stop at filesystem root
        parent_dir = search_dir.parent
        if parent_dir == search_dir:  # We've reached the root
            break
        search_dir = parent_dir

    # 3. No file found - raise with searched paths
    raise AppIdentityNotFoundError(searched_paths)


def _load_identity_from_path(path: Path) -> dict[str, Any]:
    """
    Load and parse identity file from path.

    Args:
        path: Path to the identity file

    Returns:
        Parsed identity data as dictionary

    Raises:
        AppIdentityLoadError: If file cannot be loaded or parsed
    """
    try:
        # Validate file size (security: limit to 10KB)
        file_size = path.stat().st_size
        if file_size > 10 * 1024:  # 10KB limit
            raise AppIdentityLoadError(path, ValueError(f"File too large: {file_size} bytes (max 10KB)"))

        # Load YAML with safe loader
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            raise AppIdentityLoadError(path, ValueError("File is empty or contains only whitespace"))

        if not isinstance(data, dict):
            raise AppIdentityLoadError(path, ValueError(f"Expected dictionary, got {type(data).__name__}"))

        return data

    except (OSError, yaml.YAMLError) as e:
        raise AppIdentityLoadError(path, e) from e


def _create_app_identity_from_data(data: dict[str, Any], source_path: Path) -> AppIdentity:
    """
    Create AppIdentity instance from validated data.

    Args:
        data: Validated identity data
        source_path: Path where the data was loaded from

    Returns:
        AppIdentity instance

    Raises:
        AppIdentityLoadError: If data structure is invalid
    """

    try:
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
                "source_path": str(source_path),
                "loaded_at": datetime.now(UTC).isoformat(),  # UTC timestamp when loaded
            },
        )

        return identity

    except (KeyError, TypeError, ValueError) as e:
        raise AppIdentityLoadError(source_path, ValueError(f"Invalid data structure: {e}")) from e


def load_from_path(path: Path) -> AppIdentity:
    """
    Load identity from explicit path (highest precedence).

    Args:
        path: Explicit path to identity file

    Returns:
        AppIdentity instance

    Raises:
        AppIdentityLoadError: If file cannot be loaded
        AppIdentityValidationError: If file fails validation
    """
    path = path.resolve()

    if not path.is_file():
        raise AppIdentityLoadError(path, FileNotFoundError(f"Identity file not found: {path}"))

    # Load raw data
    raw_data = _load_identity_from_path(path)

    # Validate against schema and apply defaults
    validated_data = validate_app_identity(raw_data, path)

    # Create AppIdentity instance
    return _create_app_identity_from_data(validated_data, path)


def load() -> AppIdentity:
    """
    Load identity using discovery algorithm.

    Returns:
        AppIdentity instance

    Raises:
        AppIdentityNotFoundError: If no identity file found
        AppIdentityLoadError: If file cannot be loaded
        AppIdentityValidationError: If file fails validation
    """
    # Discover file path
    identity_path = _discover_identity_path()

    # Load and return
    return load_from_path(identity_path)
