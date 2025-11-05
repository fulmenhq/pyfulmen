"""Integration utilities for AppIdentity and Config modules."""

from __future__ import annotations

import sys

from .loader import ConfigLoader


def create_loader_with_identity() -> ConfigLoader:
    """Create a ConfigLoader using AppIdentity data.

    Returns:
        ConfigLoader configured with AppIdentity app name and vendor

    Raises:
        Falls back to defaults if AppIdentity not available
    """
    try:
        # Import here to avoid circular dependencies
        from ..appidentity import get_identity

        identity = get_identity()
        return ConfigLoader(
            app=identity.config_name,
            vendor=identity.vendor,
        )
    except Exception as e:
        # Log debug message for visibility (use print as fallback since no logging guaranteed)
        print(f"DEBUG: AppIdentity lookup failed, using defaults: {e}", file=sys.stderr)
        # Fall back to defaults if AppIdentity not available
        return ConfigLoader()


__all__ = [
    "create_loader_with_identity",
]
