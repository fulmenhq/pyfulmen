"""
Terminal detection and configuration for pyfulmen.ascii.

Handles terminal type detection, width override loading, and three-layer
configuration (defaults, user overrides, BYOC).
"""

import os
from pathlib import Path
from typing import Optional

import yaml

from pyfulmen.config.paths import get_fulmen_config_dir
from pyfulmen.crucible.config import load_config_defaults

from .models import TerminalConfig, TerminalOverrides

# Module-level state for terminal configuration
_terminal_catalog: Optional[TerminalOverrides] = None
_current_terminal_config: Optional[TerminalConfig] = None


def _load_terminal_catalog() -> None:
    """
    Load terminal configuration catalog (three-layer config pattern).

    Layer 1: Crucible defaults from synced SSOT
    Layer 2: User overrides from ~/.config/fulmen/terminal-overrides.yaml
    Layer 3: Application overrides via set_terminal_overrides()
    """
    global _terminal_catalog

    # Layer 1: Load Crucible defaults from synced asset
    try:
        data = load_config_defaults("terminal", "v1.0.0", "terminal-overrides-defaults")
        _terminal_catalog = TerminalOverrides(**data)
    except (FileNotFoundError, ValueError):
        # Fallback to empty catalog if Crucible asset not synced
        # This allows module to work even without `make sync-crucible`
        _terminal_catalog = TerminalOverrides(
            version="v1.0.0",
            last_updated="",
            notes="Fallback: Crucible assets not synced (run 'make sync-crucible')",
            terminals={},
        )

    # Layer 2: Merge user overrides
    fulmen_config_dir = get_fulmen_config_dir()
    user_config_path = Path(fulmen_config_dir) / "terminal-overrides.yaml"

    if user_config_path.exists():
        try:
            with open(user_config_path, "r") as f:
                user_data = yaml.safe_load(f)
            user_overrides = TerminalOverrides(**user_data)
            _merge_terminal_configs(_terminal_catalog, user_overrides)
        except Exception:
            # Silently continue with defaults if user config is invalid
            pass


def _merge_terminal_configs(base: TerminalOverrides, override: TerminalOverrides) -> None:
    """
    Merge terminal configurations (Layer 2 into Layer 1).

    Args:
        base: Base configuration (modified in-place)
        override: Override configuration to merge in
    """
    if not override.terminals:
        return

    for term_id, user_config in override.terminals.items():
        if term_id not in base.terminals:
            # New terminal, add it
            base.terminals[term_id] = user_config
            continue

        # Merge into existing terminal config
        base_config = base.terminals[term_id]

        # Merge overrides dict
        if user_config.overrides:
            if not base_config.overrides:
                base_config.overrides = {}
            base_config.overrides.update(user_config.overrides)

        # Override name and notes if provided
        if user_config.name:
            base_config.name = user_config.name
        if user_config.notes:
            base_config.notes = user_config.notes


def _detect_current_terminal() -> None:
    """
    Detect the current terminal and set _current_terminal_config.

    Uses TERM_PROGRAM or TERM environment variables.
    """
    global _current_terminal_config

    if _terminal_catalog is None:
        return

    # Try TERM_PROGRAM first (most specific)
    term_program = os.environ.get("TERM_PROGRAM", "")

    if term_program and term_program in _terminal_catalog.terminals:
        _current_terminal_config = _terminal_catalog.terminals[term_program]
        return

    # Fallback: check TERM for ghostty
    term = os.environ.get("TERM", "")
    if "ghostty" in term and "ghostty" in _terminal_catalog.terminals:
        _current_terminal_config = _terminal_catalog.terminals["ghostty"]
        return

    # No match found
    _current_terminal_config = None


# Initialize on module load
_load_terminal_catalog()
_detect_current_terminal()


def get_terminal_config() -> Optional[TerminalConfig]:
    """
    Get the current terminal configuration.

    Returns:
        TerminalConfig for the detected terminal, or None if unknown

    Example:
        >>> config = get_terminal_config()
        >>> if config:
        ...     print(f"Terminal: {config.name}")
        ...     print(f"Overrides: {config.overrides}")
    """
    return _current_terminal_config


def get_all_terminal_configs() -> dict[str, TerminalConfig]:
    """
    Get all available terminal configurations.

    Returns:
        Dictionary mapping terminal IDs to TerminalConfig objects

    Example:
        >>> configs = get_all_terminal_configs()
        >>> for term_id, config in configs.items():
        ...     print(f"{term_id}: {config.name}")
    """
    if _terminal_catalog is None:
        return {}
    return _terminal_catalog.terminals


def set_terminal_overrides(overrides: TerminalOverrides) -> None:
    """
    Set terminal overrides (Layer 3: BYOC - Bring Your Own Config).

    This allows applications to provide their own terminal configurations,
    completely replacing the defaults and user overrides.

    Args:
        overrides: Complete TerminalOverrides configuration

    Example:
        >>> from pyfulmen.ascii import set_terminal_overrides, TerminalOverrides, TerminalConfig
        >>> my_config = TerminalOverrides(
        ...     version="1.0.0",
        ...     terminals={
        ...         "myterm": TerminalConfig(
        ...             name="My Terminal",
        ...             overrides={"🔧": 2}
        ...         )
        ...     }
        ... )
        >>> set_terminal_overrides(my_config)
    """
    global _terminal_catalog
    _terminal_catalog = overrides
    _detect_current_terminal()


def set_terminal_config(terminal_name: str, config: TerminalConfig) -> None:
    """
    Set configuration for a specific terminal (Layer 3: BYOC).

    Convenience function when you only need to override one terminal.

    Args:
        terminal_name: Terminal identifier (e.g., "iTerm.app")
        config: TerminalConfig for this terminal

    Example:
        >>> from pyfulmen.ascii import set_terminal_config, TerminalConfig
        >>> config = TerminalConfig(
        ...     name="My Custom Terminal",
        ...     overrides={"🔧": 3}
        ... )
        >>> set_terminal_config("myterm", config)
    """
    global _terminal_catalog

    if _terminal_catalog is None:
        _terminal_catalog = TerminalOverrides(version="1.0.0", terminals={})

    _terminal_catalog.terminals[terminal_name] = config
    _detect_current_terminal()


def reload_terminal_overrides() -> None:
    """
    Reload terminal configuration from defaults and user overrides.

    Useful to reset after using set_terminal_overrides() or set_terminal_config().

    Example:
        >>> from pyfulmen.ascii import reload_terminal_overrides
        >>> reload_terminal_overrides()  # Reset to defaults + user config
    """
    _load_terminal_catalog()
    _detect_current_terminal()
