"""Three-layer configuration loader.

Implements the Fulmen config loading pattern:
  Layer 1: Crucible defaults (embedded from sync)
  Layer 2: User overrides from ~/.config/fulmen/
  Layer 3: Application-provided config (BYOC)

Example:
    >>> from pyfulmen.config.loader import ConfigLoader
    >>> loader = ConfigLoader()
    >>> config = loader.load('terminal/v1.0.0/terminal-overrides-defaults')
"""

from typing import Any

import yaml

from .. import crucible
from . import paths
from .merger import merge_configs


class ConfigLoader:
    """Three-layer configuration loader.

    Loads configuration with the following precedence (later overrides earlier):
      1. Crucible defaults (Layer 1)
      2. User overrides from ~/.config/fulmen/ (Layer 2)
      3. Application-provided config (Layer 3 - BYOC)

    Example:
        >>> loader = ConfigLoader()
        >>> config = loader.load('terminal/v1.0.0/terminal-overrides-defaults')
        >>> # With user override:
        >>> config = loader.load(
        ...     'terminal/v1.0.0/terminal-overrides-defaults',
        ...     user_config={'ghostty': {'enabled': False}}
        ... )
    """

    def __init__(self, app_name: str = "fulmen"):
        """Initialize config loader.

        Args:
            app_name: Application name for user config directory
                     (default: 'fulmen' for shared Fulmen configs)
        """
        self.app_name = app_name
        self.user_config_dir = paths.get_app_config_dir(app_name)

    def load(
        self,
        crucible_path: str,
        user_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Load configuration with three-layer merge.

        Args:
            crucible_path: Path to Crucible config
                (e.g., 'terminal/v1.0.0/terminal-overrides-defaults')
            user_config: Optional application-provided config (Layer 3)

        Returns:
            Merged configuration dictionary

        Example:
            >>> loader = ConfigLoader()
            >>> config = loader.load('terminal/v1.0.0/terminal-overrides-defaults')
        """
        configs_to_merge = []

        # Layer 1: Crucible defaults
        crucible_defaults = self._load_crucible_defaults(crucible_path)
        if crucible_defaults:
            configs_to_merge.append(crucible_defaults)

        # Layer 2: User overrides
        user_overrides = self._load_user_overrides(crucible_path)
        if user_overrides:
            configs_to_merge.append(user_overrides)

        # Layer 3: Application config (BYOC)
        if user_config:
            configs_to_merge.append(user_config)

        # Merge all layers
        if not configs_to_merge:
            return {}

        return merge_configs(*configs_to_merge)

    def _load_crucible_defaults(self, crucible_path: str) -> dict[str, Any] | None:
        """Load Crucible config defaults (Layer 1).

        Args:
            crucible_path: Path to Crucible config
                (e.g., 'terminal/v1.0.0/terminal-overrides-defaults')

        Returns:
            Config dict or None if not found
        """
        try:
            # Parse category/version/name from path
            parts = crucible_path.split("/")
            if len(parts) == 3:
                category, version, name = parts
            elif len(parts) == 2:
                # Handle category/name format (assume latest version)
                category, name = parts
                versions = crucible.config.list_config_versions(category)
                version = versions[-1] if versions else "v1.0.0"
            else:
                # Single name - try to find it
                name = crucible_path
                # For now, return None - would need more sophisticated discovery
                return None

            return crucible.config.load_config_defaults(category, version, name)
        except FileNotFoundError:
            # Config not found in Crucible - return None
            return None

    def _load_user_overrides(self, crucible_path: str) -> dict[str, Any] | None:
        """Load user config overrides (Layer 2).

        Looks for user overrides in ~/.config/{app_name}/{crucible_path}.yaml

        Args:
            crucible_path: Path to config file (e.g., 'terminal/v1.0.0/terminal-overrides-defaults')

        Returns:
            Config dict or None if not found
        """
        # Construct user override path
        user_file = self.user_config_dir / f"{crucible_path}.yaml"

        if not user_file.exists():
            # Try without .yaml extension
            user_file = self.user_config_dir / crucible_path
            if not user_file.exists():
                return None

        try:
            with open(user_file) as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, OSError):
            # Failed to load user config - skip it
            return None


__all__ = [
    "ConfigLoader",
]
