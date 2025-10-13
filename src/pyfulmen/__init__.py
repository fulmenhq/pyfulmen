"""PyFulmen - Python Fulmen libraries for enterprise-scale development.

This package provides templates, processes, and tools for enterprise-scale
development in Python, following the Fulmen ecosystem standards.

Example:
    >>> import pyfulmen
    >>> print(pyfulmen.__version__)
    0.1.1
"""

__version__ = "0.1.1"

# Export public API
__all__ = [
    "__version__",
    "version",
    "crucible",
    "config",
    "schema",
    "logging",
]

# Submodules
from . import config, crucible, logging, schema, version
