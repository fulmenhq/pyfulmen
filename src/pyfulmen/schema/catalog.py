"""Schema catalog and metadata utilities for PyFulmen."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from ..crucible import _paths as crucible_paths
from ..crucible import schemas as crucible_schemas


@dataclass(slots=True)
class SchemaInfo:
    """Metadata describing a Crucible schema."""

    id: str
    category: str
    version: str
    name: str
    path: Path
    description: str | None = None


def _strip_schema_suffix(filename: str) -> str:
    for suffix in (".schema.json", ".schema.yaml", ".json", ".yaml", ".yml"):
        if filename.endswith(suffix):
            return filename[: -len(suffix)]
    return filename


def _iter_schema_files() -> Iterator[Path]:
    root = crucible_paths.get_schemas_dir()
    if not root.exists():
        return iter(())

    suffixes = (".schema.json", ".schema.yaml", ".json", ".yaml", ".yml")

    def generator() -> Iterator[Path]:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(str(path).endswith(suffix) for suffix in suffixes):
                yield path

    return generator()


def _schema_info_from_path(path: Path) -> SchemaInfo:
    root = crucible_paths.get_schemas_dir()
    relative = path.relative_to(root)
    parts = relative.parts
    if len(parts) < 3:
        raise ValueError(f"Invalid schema layout: {path}")
    category_parts = parts[:-2]
    version = parts[-2]
    name = _strip_schema_suffix(parts[-1])
    category = "/".join(category_parts)
    schema_id = f"{category}/{version}/{name}" if category else f"{version}/{name}"
    description = None
    try:
        schema_data = crucible_schemas.load_schema(category, version, name)
        description = schema_data.get("description") if isinstance(schema_data, dict) else None
    except Exception:  # noqa: BLE001
        description = None
    return SchemaInfo(
        id=schema_id,
        category=category,
        version=version,
        name=name,
        path=path,
        description=description,
    )


def list_schemas(prefix: str | None = None) -> list[SchemaInfo]:
    """List schemas available in the catalog, optionally filtered by prefix."""
    infos = []
    for path in _iter_schema_files():
        try:
            info = _schema_info_from_path(path)
        except ValueError:
            continue
        if prefix and not info.id.startswith(prefix):
            continue
        infos.append(info)
    return sorted(infos, key=lambda info: info.id)


def get_schema(schema_id: str) -> SchemaInfo:
    """Return SchemaInfo for given schema identifier."""
    category, version, name = parse_schema_id(schema_id)
    path = crucible_schemas.get_schema_path(category, version, name)
    schema_data = crucible_schemas.load_schema(category, version, name)
    description = schema_data.get("description") if isinstance(schema_data, dict) else None
    return SchemaInfo(
        id=schema_id,
        category=category,
        version=version,
        name=name,
        path=path,
        description=description,
    )


def parse_schema_id(schema_id: str) -> tuple[str, str, str]:
    parts = schema_id.split("/")
    if len(parts) < 3:
        raise ValueError(f"Invalid schema identifier: {schema_id}")
    category = "/".join(parts[:-2])
    version = parts[-2]
    name = parts[-1]
    return category, version, name


__all__ = [
    "SchemaInfo",
    "list_schemas",
    "get_schema",
    "parse_schema_id",
]
