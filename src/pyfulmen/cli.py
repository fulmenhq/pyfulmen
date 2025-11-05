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

    # Signals subcommand
    signals_parser = subparsers.add_parser(
        "signals",
        help="Signal handling information",
        description="Show signal handling information and platform support",
    )
    signals_subparsers = signals_parser.add_subparsers(dest="signals_command", required=True, help="Signals commands")

    # Signals info command
    info_parser = signals_subparsers.add_parser("info", help="Show signals module information")
    info_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text)")

    # Signals list command
    list_parser = signals_subparsers.add_parser("list", help="List available signals and platform support")
    list_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text)")
    list_parser.add_argument(
        "--platform",
        choices=["all", "current"],
        default="current",
        help="Show support for all platforms or current platform (default: current)",
    )

    # Signals windows-fallback command
    windows_parser = signals_subparsers.add_parser("windows-fallback", help="Show Windows fallback documentation")
    windows_parser.add_argument(
        "--format", choices=["text", "json", "markdown"], default="text", help="Output format (default: text)"
    )

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
            from .version import get_version_info

            version_info = get_version_info()
            print(f"PyFulmen Schema Version: {version_info}")
            return 0
        except Exception as e:
            print(f"❌ Error getting schema version: {e}", file=sys.stderr)
            return 1
    else:
        print("Use --version to show schema information")
        return 0


def cmd_signals_info(args: Any) -> int:
    """Handle signals info command."""
    try:
        from .signals import get_module_info

        info = get_module_info()

        if args.format == "json":
            import json

            print(json.dumps(info, indent=2))
        else:
            print("PyFulmen Signals Module Information")
            print("=" * 40)
            print(f"PyFulmen Version: {info['pyfulmen_version']}")
            print(f"Catalog Version: {info['catalog_version']['version']}")
            print(f"Platform: {info['platform']}")
            print(f"Python Version: {info['python_version']}")
            print(f"Description: {info['catalog_version']['description']}")

        return 0
    except Exception as e:
        print(f"❌ Error getting signals info: {e}", file=sys.stderr)
        return 1


def cmd_signals_list(args: Any) -> int:
    """Handle signals list command."""
    try:
        import signal

        from .signals import get_module_info, get_signal_metadata, list_all_signals, supports_signal

        signal_names = list_all_signals()

        if args.format == "json":
            import json

            output = []

            for sig_name in signal_names:
                sig_info = get_signal_metadata(sig_name)
                if sig_info is None:
                    continue

                if args.platform == "all":
                    # Show support for all platforms
                    platforms = sig_info.get("platforms", {})
                    support_info = {
                        "signal": sig_name,
                        "description": sig_info.get("description", ""),
                        "platforms": {
                            "linux": platforms.get("linux", {}).get("supported", False),
                            "darwin": platforms.get("darwin", {}).get("supported", False),
                            "windows": platforms.get("windows", {}).get("supported", False),
                        },
                    }
                else:
                    # Show support for current platform only
                    current_platform = get_module_info()["platform"]
                    platform_info = platforms.get(current_platform, {"supported": False})
                    support_info = {
                        "signal": sig_name,
                        "description": sig_info.get("description", ""),
                        "supported": platform_info.get("supported", False),
                        "fallback": platform_info.get("fallback")
                        if not platform_info.get("supported", False)
                        else None,
                    }

                output.append(support_info)

            print(json.dumps(output, indent=2))
        else:
            print("Available Signals")
            print("=" * 20)

            if args.platform == "all":
                print("Signal         | Linux | macOS | Windows | Description")
                print("-" * 70)
                for sig_name in signal_names:
                    sig_info = get_signal_metadata(sig_name)
                    if sig_info is None:
                        continue
                    platforms = sig_info.get("platforms", {})

                    linux_support = platforms.get("linux", {}).get("supported", False)
                    darwin_support = platforms.get("darwin", {}).get("supported", False)
                    windows_support = platforms.get("windows", {}).get("supported", False)

                    linux_mark = "✅" if linux_support else "❌"
                    darwin_mark = "✅" if darwin_support else "❌"
                    windows_mark = "✅" if windows_support else "❌"

                    description = sig_info.get("description", "")[:40]
                    if len(description) == 40:
                        description += "..."

                    print(f"{sig_name:<15} | {linux_mark:<6} | {darwin_mark:<6} | {windows_mark:<7} | {description}")
            else:
                current_platform = get_module_info()["platform"]
                print(f"Signal Support on {current_platform.title()}")
                print("-" * 30)
                print("Signal         | Supported | Description")
                print("-" * 50)

                for sig_name in signal_names:
                    # Get signal object from name
                    sig_obj = getattr(signal, sig_name, None)
                    if sig_obj is None:
                        continue

                    sig_info = get_signal_metadata(sig_name)
                    if sig_info is None:
                        continue
                    platforms = sig_info.get("platforms", {})
                    platform_info = platforms.get(current_platform, {"supported": False})
                    supported = supports_signal(sig_obj)

                    support_mark = "✅" if supported else "❌"
                    description = sig_info.get("description", "")[:30]
                    if len(description) == 30:
                        description += "..."

                    print(f"{sig_name:<15} | {support_mark:<9} | {description}")

        return 0
    except Exception as e:
        print(f"❌ Error listing signals: {e}", file=sys.stderr)
        return 1


def cmd_signals_windows_fallback(args: Any) -> int:
    """Handle signals windows-fallback command."""
    try:
        from .signals import build_windows_fallback_docs

        docs = build_windows_fallback_docs()

        if args.format == "json":
            import json

            # For JSON format, return the markdown as a string
            print(json.dumps({"documentation": docs}, indent=2))
        elif args.format == "markdown":
            print(docs)
        else:
            # Default format - just print the markdown
            print(docs)

        return 0
    except Exception as e:
        print(f"❌ Error generating Windows fallback docs: {e}", file=sys.stderr)
        return 1


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
    elif args.command == "signals":
        if args.signals_command == "info":
            return cmd_signals_info(args)
        elif args.signals_command == "list":
            return cmd_signals_list(args)
        elif args.signals_command == "windows-fallback":
            return cmd_signals_windows_fallback(args)
        else:
            parser.error(f"Unknown signals command: {args.signals_command}")
            return 1
    else:
        parser.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
