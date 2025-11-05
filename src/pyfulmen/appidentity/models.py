"""
Dataclass models for application identity.

This module defines the AppIdentity dataclass and related models
following the Crucible app identity standard.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AppIdentity:
    """
    Canonical application identity following Crucible standard.

    This class represents application metadata including binary names,
    vendor information, environment variables, and telemetry namespaces.
    """

    # Required fields (app object)
    binary_name: str
    vendor: str
    env_prefix: str
    config_name: str
    description: str

    # Optional fields (metadata object)
    project_url: str | None = None
    support_email: str | None = None
    license: str | None = None
    repository_category: str | None = None
    telemetry_namespace: str | None = None
    registry_id: UUID | None = None

    # Python-specific metadata
    python_distribution: str | None = None
    python_package: str | None = None
    console_scripts: list[dict] | None = None

    # Internal fields (not exposed in repr)
    _raw_metadata: dict[str, Any] = field(repr=False, init=False)
    _provenance: dict[str, str] = field(repr=False, init=False)

    def __post_init__(self) -> None:
        """Validate fields and set internal data."""
        # Validate env_prefix pattern to match schema: ^[A-Z][A-Z0-9_]*_$
        env_prefix_pattern = re.compile(r"^[A-Z][A-Z0-9_]*_$")
        if not env_prefix_pattern.match(self.env_prefix):
            raise ValueError(
                f"Environment prefix '{self.env_prefix}' must start with uppercase letter, "
                f"contain only uppercase letters, digits, and underscores, and end with '_' "
                f"(e.g., 'APP_', 'MY_APP_1_')"
            )

        # Set internal fields (object.__setattr__ needed for frozen dataclass)
        object.__setattr__(self, "_raw_metadata", {})
        object.__setattr__(self, "_provenance", {})

    def to_json(self) -> str:
        """Serialize identity to JSON string."""
        data = asdict(self)

        # Handle UUID serialization
        if self.registry_id:
            data["registry_id"] = str(self.registry_id)

        # Remove internal fields
        data.pop("_raw_metadata", None)
        data.pop("_provenance", None)

        return json.dumps(data, indent=2, sort_keys=True)

    @property
    def app_name(self) -> str:
        """Get the application name (same as binary_name)."""
        return self.binary_name

    @property
    def env_vars(self) -> dict[str, str]:
        """Get common environment variable names."""
        return {
            "config": f"{self.env_prefix}CONFIG",
            "log_level": f"{self.env_prefix}LOG_LEVEL",
            "debug": f"{self.env_prefix}DEBUG",
        }

    @property
    def provenance(self) -> dict[str, str]:
        """Get provenance metadata (read-only access to internal _provenance)."""
        return self._provenance.copy()

    @property
    def raw_metadata(self) -> dict[str, Any]:
        """Get raw metadata from identity file (read-only access to internal _raw_metadata)."""
        return self._raw_metadata.copy()
