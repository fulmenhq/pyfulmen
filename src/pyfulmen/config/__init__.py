"""Config utilities for PyFulmen.

This package provides platform-aware configuration path resolution and
configuration loading utilities following the XDG Base Directory Specification.

Example:
    >>> from pyfulmen import config
    >>> config.paths.get_fulmen_config_dir()
    PosixPath('/Users/you/.config/fulmen')
    >>> loader = config.loader.ConfigLoader()
    >>> cfg = loader.load('terminal/v1.0.0/terminal-overrides-defaults')
"""

from . import loader, merger, paths

__all__ = [
    "paths",
    "loader",
    "merger",
]
