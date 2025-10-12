"""Crucible shim package for PyFulmen.

This package provides idiomatic Python access to synced Crucible assets
including schemas, documentation, and configuration defaults.

Users don't need to sync Crucible separately - PyFulmen includes synced assets.

Example:
    >>> from pyfulmen import crucible
    >>> crucible.schemas.list_available_schemas()
    ['ascii', 'config', 'observability', ...]
    >>> crucible.docs.read_doc('guides/bootstrap-goneat.md')
    '# Goneat Bootstrap Guide\\n\\n...'
    >>> info = crucible.get_crucible_info()
    >>> info['schemas_dir']
    '/path/to/pyfulmen/schemas/crucible-py'

Note: Crucible version tracking will be added in goneat v0.3.x.
"""

from . import config, docs, schemas
from ._version import get_crucible_info, get_crucible_metadata_path

__all__ = [
    # Version info
    "get_crucible_metadata_path",
    "get_crucible_info",
    # Submodules
    "schemas",
    "docs",
    "config",
]
