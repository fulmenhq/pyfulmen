"""Lightweight CLI for schema catalog exploration and validation.

This utility is intended for demonstration and manual validation during
development. For production workflows prefer the PyFulmen APIs or the
goneat command-line tooling.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from . import catalog, validator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PyFulmen schema helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available schemas")
    list_parser.add_argument("--prefix", help="Filter schema IDs by prefix")

    info_parser = subparsers.add_parser("info", help="Show schema metadata")
    info_parser.add_argument("schema_id")

    validate_parser = subparsers.add_parser("validate", help="Validate data against a schema")
    validate_parser.add_argument("schema_id")
    validate_group = validate_parser.add_mutually_exclusive_group(required=True)
    validate_group.add_argument("--file", type=Path, help="Path to JSON/YAML payload")
    validate_group.add_argument("--data", help="Inline JSON string")
    validate_parser.add_argument("--format", choices=["text", "json"], default="text")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        for info in catalog.list_schemas(args.prefix):
            print(info.id)
        return 0

    if args.command == "info":
        info = catalog.get_schema(args.schema_id)
        payload = {
            "id": info.id,
            "category": info.category,
            "version": info.version,
            "name": info.name,
            "path": str(info.path),
            "description": info.description,
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "validate":
        if args.data is not None:
            try:
                data = json.loads(args.data)
            except json.JSONDecodeError as exc:
                parser.error(f"Invalid JSON payload: {exc}")
            result = validator.validate_data(args.schema_id, data)
        else:
            result = validator.validate_file(args.schema_id, args.file)

        print(validator.format_diagnostics(result.diagnostics, style=args.format))
        return 0 if result.is_valid else 1

    parser.error("Unknown command")
    return 1


__all__ = ["main", "build_parser"]
