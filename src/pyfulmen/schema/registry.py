"""Offline ``$ref`` resolution registry for synced Crucible schemas.

Crucible schemas historically used relative ``$ref`` URLs, but newer syncs
(crucible >= v0.4.15) absolutize refs to URLs such as
``https://schemas.fulmenhq.dev/crucible/...``. Plain ``jsonschema`` validation
would either fail to resolve those or, with a legacy resolver, attempt a
network fetch. This module builds a :class:`referencing.Registry` so every
ref resolves from the local ``schemas/crucible-py/`` tree and validation
never touches the network.

Mapping rule (URI -> disk path)
-------------------------------

Every ``*.json`` / ``*.yaml`` / ``*.yml`` document under the synced schemas
directory (``schemas/crucible-py/``) is loaded once and registered under up
to two URIs:

1. **Declared ``$id`` (primary).** If the document declares an absolute
   ``$id``, it is registered under that exact URI. This handles refs that
   were absolutized against the target's canonical identity, regardless of
   host (``schemas.fulmenhq.dev``, ``schemas.goneat.dev``,
   ``schemas.3leaps.net``, ...) and regardless of whether the ``$id`` shape
   matches the on-disk layout (several v0.4.x ``$id``s use a flat
   ``<category>/<name>-vX.Y.Z.json`` shape while the file lives at
   ``<category>/vX.Y.Z/<name>.schema.json``).

2. **Derived catalog URI (secondary).** Every document is also registered
   under ``https://schemas.fulmenhq.dev/crucible/<path relative to the
   schemas dir, POSIX-style>``. Example::

       schemas/crucible-py/design/tui/v1.0.0/theme.schema.json
       -> https://schemas.fulmenhq.dev/crucible/design/tui/v1.0.0/theme.schema.json

   This mirrors the upstream absolutization convention (base URL + tree
   path), so refs that were originally *relative to the tree layout* still
   resolve after being absolutized, even when the target's declared ``$id``
   uses a different (legacy/flat) shape. On collision, the declared ``$id``
   registration wins.

Unknown URIs are never fetched: the registry has no ``retrieve`` hook, so an
unregistered absolute ref surfaces as ``referencing.exceptions.Unresolvable``,
which the validation layer converts into :class:`OfflineSchemaResolutionError`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from ..crucible import _paths

#: Base URL used for the derived (layout-based) URI of every synced schema.
DERIVED_URI_BASE = "https://schemas.fulmenhq.dev/crucible/"

_SCHEMA_SUFFIXES = (".json", ".yaml", ".yml")


class OfflineSchemaResolutionError(Exception):
    """A ``$ref`` points at a URI that is not in the offline schema registry.

    Raised instead of attempting any network fetch. Fix by syncing the
    referenced schema into ``schemas/crucible-py/`` (``make sync-crucible``)
    or correcting the ``$ref``.
    """


def derived_uri_for_path(path: Path, schemas_dir: Path) -> str:
    """Return the derived catalog URI for a schema file (see module docstring)."""
    return DERIVED_URI_BASE + path.relative_to(schemas_dir).as_posix()


def _load_document(path: Path) -> dict | None:
    """Parse a schema document, returning None for unparseable/non-object files."""
    try:
        text = path.read_text(encoding="utf-8")
        contents = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (OSError, json.JSONDecodeError, yaml.YAMLError, UnicodeDecodeError):
        return None
    return contents if isinstance(contents, dict) else None


def build_registry(schemas_dir: Path) -> Registry:
    """Build an offline Registry from every schema document under schemas_dir."""
    derived: list[tuple[str, Resource]] = []
    by_id: list[tuple[str, Resource]] = []

    if schemas_dir.exists():
        for path in sorted(schemas_dir.rglob("*")):
            if not path.is_file() or path.suffix not in _SCHEMA_SUFFIXES:
                continue
            contents = _load_document(path)
            if contents is None:
                continue
            resource = Resource.from_contents(contents, default_specification=DRAFT202012)
            derived.append((derived_uri_for_path(path, schemas_dir), resource))
            schema_id = contents.get("$id")
            if isinstance(schema_id, str) and schema_id:
                by_id.append((schema_id, resource))

    # Later entries win on duplicate URIs, so declared $ids take precedence
    # over derived catalog URIs.
    return Registry().with_resources(derived + by_id)


@lru_cache(maxsize=1)
def crucible_registry() -> Registry:
    """Cached offline registry for the synced Crucible schemas tree.

    Call ``crucible_registry.cache_clear()`` after re-syncing schemas (or in
    tests that redirect the schemas directory).
    """
    return build_registry(_paths.get_schemas_dir())


__all__ = [
    "DERIVED_URI_BASE",
    "OfflineSchemaResolutionError",
    "build_registry",
    "crucible_registry",
    "derived_uri_for_path",
]
