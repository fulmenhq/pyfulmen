"""Lightweight CLI for schema catalog exploration and validation.

This utility is intended for demonstration and manual validation during
development. For production workflows prefer the PyFulmen APIs or the
goneat command-line tooling.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from ..foundry import ExitCode
from . import catalog, validator
from .export import export_schema
from .validator import SchemaValidationError


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

    # NEW: export parser
    export_parser = subparsers.add_parser("export", help="Export schema to local file")
    export_parser.add_argument("schema_id", help="Schema identifier (category/version/name)")
    export_parser.add_argument("--out", "-o", required=True, type=Path, help="Output file path")
    export_parser.add_argument("--no-provenance", action="store_true", help="Omit provenance metadata")
    export_parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    export_parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing files")
    export_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

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

    if args.command == "export":
        try:
            result_path = export_schema(
                schema_id=args.schema_id,
                out_path=args.out,
                include_provenance=not args.no_provenance,
                validate=not args.no_validate,
                overwrite=args.force,
            )

            if args.verbose:
                print(f"✅ Exported schema: {args.schema_id}")
                print(f"   Output: {result_path}")
                print(f"   Provenance: {'included' if not args.no_provenance else 'omitted'}")
                print(f"   Validation: {'passed' if not args.no_validate else 'skipped'}")
            else:
                print(result_path)

            return ExitCode.EXIT_SUCCESS.value

        except FileNotFoundError as e:
            print(f"❌ Schema not found: {e}", file=sys.stderr)
            return ExitCode.EXIT_FILE_NOT_FOUND.value

        except FileExistsError as e:
            print(f"❌ File exists: {e}", file=sys.stderr)
            print("   Use --force to overwrite", file=sys.stderr)
            return ExitCode.EXIT_FILE_WRITE_ERROR.value

        except SchemaValidationError as e:
            print(f"❌ Validation failed: {e}", file=sys.stderr)
            return ExitCode.EXIT_DATA_INVALID.value

        except OSError as e:
            print(f"❌ Write error: {e}", file=sys.stderr)
            return ExitCode.EXIT_FILE_WRITE_ERROR.value

        except Exception as e:
            print(f"❌ Unexpected error: {e}", file=sys.stderr)
            return ExitCode.EXIT_FAILURE.value

    parser.error("Unknown command")
    return ExitCode.EXIT_FAILURE.value


__all__ = ["main", "build_parser"]
