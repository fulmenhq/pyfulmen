from pathlib import Path
from typing import Any

import yaml

_PACKAGE_ROOT = Path(__file__).parent
_CONFIG_DIR = _PACKAGE_ROOT.parent.parent / "config" / "terminal"


def load_terminal_catalog() -> dict[str, Any]:
    catalog_files = list(_CONFIG_DIR.rglob("*.yaml"))
    if not catalog_files:
        return {}

    catalog = {}
    for catalog_file in catalog_files:
        with open(catalog_file) as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict) and "terminals" in data:
                for key, terminal_data in data["terminals"].items():
                    name = terminal_data.get("name", key)
                    catalog[name] = terminal_data
                    catalog[name]["name"] = name

    return catalog


def get_terminal_config(name: str) -> dict[str, Any]:
    catalog = load_terminal_catalog()
    if name not in catalog:
        raise ValueError(f"Terminal config not found: {name}")
    return catalog[name]
