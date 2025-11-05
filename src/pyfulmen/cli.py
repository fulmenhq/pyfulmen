"""Top-level CLI for PyFulmen.

This module provides the main CLI entry point for PyFulmen, dispatching
to subcommands for various modules like appidentity, schema, etc.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the main argument parser for PyFulmen CLI."""
    parser = argparse.ArgumentParser(
        description="PyFulmen - Python Fulmen libraries for enterprise-scale development", prog="pyfulmen"
    )
    parser.add_argument("--version", action="version", version=f"pyfulmen {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # AppIdentity subcommand
    appidentity_parser = subparsers.add_parser(
        "appidentity", help="Application identity management", description="Manage application identity configuration"
    )
    appidentity_subparsers = appidentity_parser.add_subparsers(
        dest="appidentity_command", required=True, help="AppIdentity commands"
    )

    # AppIdentity show command
    show_parser = appidentity_subparsers.add_parser("show", help="Show current application identity")
    show_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text)")
    show_parser.add_argument("--path", type=str, help="Explicit identity file path (overrides discovery)")

    # AppIdentity validate command
    validate_parser = appidentity_subparsers.add_parser("validate", help="Validate identity file")
    validate_parser.add_argument("path", type=str, help="Path to identity file to validate")

    # Schema subcommand (placeholder for future expansion)
    schema_parser = subparsers.add_parser("schema", help="Schema management", description="Manage and validate schemas")
    schema_parser.add_argument("--version", action="store_true", help="Show schema version information")

    return parser


def cmd_appidentity_show(args: Any) -> int:
    """Handle appidentity show command."""
    try:
        from pathlib import Path

        from .appidentity.cli import cmd_show as appidentity_show

        # Convert args to match expected format
        class Args:
            def __init__(self):
                self.path = Path(args.path) if args.path else None
                self.format = args.format

        return appidentity_show(Args())
    except Exception as e:
        print(f"❌ Error in appidentity show: {e}", file=sys.stderr)
        return 1


def cmd_appidentity_validate(args: Any) -> int:
    """Handle appidentity validate command."""
    try:
        from pathlib import Path

        from .appidentity.cli import cmd_validate as appidentity_validate

        # Convert args to match expected format
        class Args:
            def __init__(self):
                self.path = Path(args.path)

        return appidentity_validate(Args())
    except Exception as e:
        print(f"❌ Error in appidentity validate: {e}", file=sys.stderr)
        return 1


def cmd_schema(args: Any) -> int:
    """Handle schema command."""
    if args.version:
        try:
            from .crucible import get_version

            version_info = get_version()
            print(f"PyFulmen Schema Version: {version_info}")
            return 0
        except Exception as e:
            print(f"❌ Error getting schema version: {e}", file=sys.stderr)
            return 1
    else:
        print("Use --version to show schema information")
        return 0


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "appidentity":
        if args.appidentity_command == "show":
            return cmd_appidentity_show(args)
        elif args.appidentity_command == "validate":
            return cmd_appidentity_validate(args)
        else:
            parser.error(f"Unknown appidentity command: {args.appidentity_command}")
            return 1
    elif args.command == "schema":
        return cmd_schema(args)
    else:
        parser.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
