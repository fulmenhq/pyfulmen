"""Crucible shim package for PyFulmen.

This package provides idiomatic Python access to synced Crucible assets
including schemas, documentation, and configuration defaults. Tools and
applications should use the bridge API for unified asset access.

Users don't need to sync Crucible separately - PyFulmen includes synced assets.

Bridge API Examples (v0.1.4+):
    >>> from pyfulmen import crucible

    >>> # Discover available assets
    >>> categories = crucible.list_categories()
    >>> schemas = crucible.list_assets('schemas', prefix='observability')

    >>> # Load content with enhanced error handling
    >>> schema = crucible.load_schema_by_id('observability/logging/v1.0.0/logger-config')
    >>> doc = crucible.get_documentation('standards/observability/logging.md')

    >>> # Stream large assets
    >>> with crucible.open_asset('architecture/fulmen-helper-library-standard.md') as f:
    ...     content = f.read()

    >>> # Version metadata
    >>> version = crucible.get_crucible_version()
    >>> print(f"Crucible v{version.version}")

Legacy Submodule Access (backward compatibility):
    >>> crucible.schemas.list_available_schemas()
    ['ascii', 'config', 'observability', ...]
    >>> crucible.docs.read_doc('guides/bootstrap-goneat.md')
    '# Goneat Bootstrap Guide\\n\\n...'
"""

# Legacy submodule access (backward compatibility)
from . import config, docs, schemas
from ._version import get_crucible_info, get_crucible_metadata_path

# Bridge API (v0.1.4+, v0.1.5+ new helpers)
from .bridge import (
    find_config,
    find_schema,
    get_config_defaults,
    get_crucible_version,
    get_doc,
    list_assets,
    list_categories,
    load_schema_by_id,
    open_asset,
)

# Enhanced documentation APIs (v0.1.4+)
from .docs import (
    get_documentation,
    get_documentation_metadata,
    get_documentation_with_metadata,
)

# Error classes
from .errors import AssetNotFoundError, CrucibleVersionError, ParseError

# Data models
from .models import AssetMetadata, CrucibleVersion

__all__ = [
    # Bridge API (v0.1.5+) - Recommended for new code
    "list_categories",
    "list_assets",
    "get_crucible_version",
    "find_schema",
    "find_config",
    "get_doc",
    # Legacy bridge functions (deprecated in v0.1.5, removal in v0.2.0)
    "load_schema_by_id",
    "get_config_defaults",
    "open_asset",
    # Enhanced documentation APIs (v0.1.4+)
    "get_documentation",
    "get_documentation_metadata",
    "get_documentation_with_metadata",
    # Data models
    "AssetMetadata",
    "CrucibleVersion",
    # Error classes
    "AssetNotFoundError",
    "ParseError",
    "CrucibleVersionError",
    # Legacy APIs (backward compatibility)
    "get_crucible_metadata_path",
    "get_crucible_info",
    # Submodules (legacy compatibility)
    "schemas",
    "docs",
    "config",
]
