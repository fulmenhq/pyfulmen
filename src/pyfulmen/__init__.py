"""PyFulmen - Python Fulmen libraries for enterprise-scale development.

This package provides templates, processes, and tools for enterprise-scale
development in Python, following the Fulmen ecosystem standards.

Example:
    >>> import pyfulmen
    >>> pyfulmen.__version__  # e.g., '0.2.0'
"""

from importlib.metadata import version as _get_version

__version__ = _get_version("pyfulmen")

# Export public API
__all__ = [
    "__version__",
    "appidentity",
    "ascii",
    "config",
    "crucible",
    "docscribe",
    "error_handling",
    "foundry",
    "fulhash",
    "fulpack",
    "logging",
    "pathfinder",
    "schema",
    "signals",
    "similarity",
    "telemetry",
    "version",
]

# Submodules
from . import (
    appidentity,
    ascii,
    config,
    crucible,
    docscribe,
    error_handling,
    foundry,
    fulhash,
    fulpack,
    logging,
    pathfinder,
    schema,
    signals,
    similarity,
    telemetry,
    version,
)
