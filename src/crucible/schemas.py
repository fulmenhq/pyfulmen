import json
from pathlib import Path
from typing import Any

import yaml

_PACKAGE_ROOT = Path(__file__).parent
_SCHEMAS_DIR = _PACKAGE_ROOT.parent.parent / "schemas"


def get_schema(category: str, version: str, name: str) -> dict[str, Any]:
    if not name.endswith(".json") and not name.endswith(".yaml"):
        schema_path = _SCHEMAS_DIR / category / version / f"{name}.schema.json"
        if not schema_path.exists():
            schema_path = _SCHEMAS_DIR / category / version / f"{name}.schema.yaml"
    else:
        schema_path = _SCHEMAS_DIR / category / version / name

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    if schema_path.suffix == ".json":
        with open(schema_path) as f:
            return json.load(f)
    else:
        with open(schema_path) as f:
            return yaml.safe_load(f)


def list_schemas(category: str, version: str) -> list[str]:
    schema_dir = _SCHEMAS_DIR / category / version
    if not schema_dir.exists():
        return []

    schemas = []
    for path in schema_dir.iterdir():
        if path.is_file() and (".schema." in path.name or path.suffix in [".json", ".yaml"]):
            schemas.append(path.name)

    return sorted(schemas)
