"""Crucible shim package for PyFulmen.

This package provides idiomatic Python access to synced Crucible assets
including schemas, documentation, and configuration defaults.

Users don't need to sync Crucible separately - PyFulmen includes synced assets.

Example:
    >>> from pyfulmen import crucible
    >>> crucible.schemas.list_available_schemas()
    ['ascii', 'config', 'observability', ...]

    >>> # Legacy API (returns raw content with frontmatter)
    >>> crucible.docs.read_doc('guides/bootstrap-goneat.md')
    '# Goneat Bootstrap Guide\\n\\n...'

    >>> # Enhanced API (v0.1.4+) - returns clean content
    >>> content = crucible.get_documentation('standards/observability/logging.md')
    >>> metadata = crucible.get_documentation_metadata('standards/observability/logging.md')

    >>> info = crucible.get_crucible_info()
    >>> info['schemas_dir']
    '/path/to/pyfulmen/schemas/crucible-py'

Note: Crucible version tracking will be added in goneat v0.3.x.
"""

from . import config, docs, schemas
from ._version import get_crucible_info, get_crucible_metadata_path
from .docs import (
    get_documentation,
    get_documentation_metadata,
    get_documentation_with_metadata,
)
from .errors import AssetNotFoundError, CrucibleVersionError, ParseError

__all__ = [
    # Version info
    "get_crucible_metadata_path",
    "get_crucible_info",
    # Enhanced documentation APIs (v0.1.4+)
    "get_documentation",
    "get_documentation_metadata",
    "get_documentation_with_metadata",
    # Error classes
    "AssetNotFoundError",
    "ParseError",
    "CrucibleVersionError",
    # Submodules (legacy compatibility)
    "schemas",
    "docs",
    "config",
]
