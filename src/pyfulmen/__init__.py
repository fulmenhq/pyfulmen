"""PyFulmen - Python Fulmen libraries for enterprise-scale development.

This package provides templates, processes, and tools for enterprise-scale
development in Python, following the Fulmen ecosystem standards.

Example:
    >>> import pyfulmen
    >>> pyfulmen.__version__  # e.g., '0.1.4'
"""

from importlib.metadata import version as _get_version

__version__ = _get_version("pyfulmen")

# Export public API
__all__ = [
    "__version__",
    "version",
    "crucible",
    "config",
    "schema",
    "logging",
    "foundry",
    "pathfinder",
    "ascii",
    "docscribe",
    "signals",
]

# Submodules
from . import ascii, config, crucible, docscribe, foundry, logging, pathfinder, schema, signals, version
