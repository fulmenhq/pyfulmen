"""PyFulmen - Python Fulmen libraries for enterprise-scale development.

This package provides templates, processes, and tools for enterprise-scale
development in Python, following the Fulmen ecosystem standards.

Example:
    >>> import pyfulmen
    >>> print(pyfulmen.__version__)
    0.1.2
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
]

# Submodules
from . import ascii, config, crucible, foundry, logging, pathfinder, schema, version
