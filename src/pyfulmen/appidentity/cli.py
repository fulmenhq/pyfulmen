"""
CLI commands for PyFulmen AppIdentity module.

Provides commands for showing and validating application identity configuration.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..foundry import ExitCode
from . import get_identity, load_from_path
from .errors import AppIdentityError, AppIdentityNotFoundError, AppIdentityValidationError


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for appidentity CLI."""
    parser = argparse.ArgumentParser(description="PyFulmen AppIdentity CLI - Show and validate application identity")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Show command
    show_parser = subparsers.add_parser("show", help="Show current application identity")
    show_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text)")
    show_parser.add_argument("--path", type=Path, help="Explicit identity file path (overrides discovery)")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate identity file")
    validate_parser.add_argument("path", type=Path, help="Path to identity file to validate")

    return parser


def format_identity_text(identity) -> str:
    """Format identity as readable text."""
    lines = [
        f"Application Identity: {identity.binary_name}",
        f"Vendor: {identity.vendor}",
        f"Environment Prefix: {identity.env_prefix}",
        f"Config Directory: {identity.config_name}",
        f"Description: {identity.description}",
    ]

    if identity.project_url:
        lines.append(f"Project URL: {identity.project_url}")

    if identity.support_email:
        lines.append(f"Support Email: {identity.support_email}")

    if identity.license:
        lines.append(f"License: {identity.license}")

    if identity.repository_category:
        lines.append(f"Repository Category: {identity.repository_category}")

    if identity.telemetry_namespace:
        lines.append(f"Telemetry Namespace: {identity.telemetry_namespace}")

    if identity.python_distribution:
        lines.append(f"Python Distribution: {identity.python_distribution}")

    if identity.python_package:
        lines.append(f"Python Package: {identity.python_package}")

    if identity.console_scripts:
        lines.append("Console Scripts:")
        for script in identity.console_scripts:
            if isinstance(script, dict) and "name" in script:
                lines.append(f"  - {script['name']}")

    # Add provenance info
    if hasattr(identity, "_provenance") and identity._provenance:
        lines.append("")
        lines.append("Provenance:")
        for key, value in identity._provenance.items():
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)


def cmd_show(args) -> int:
    """Handle the show command."""
    try:
        identity = load_from_path(args.path) if args.path else get_identity()

        if args.format == "json":
            print(identity.to_json())
        else:
            print(format_identity_text(identity))

        return ExitCode.EXIT_SUCCESS.value

    except AppIdentityNotFoundError as e:
        print(f"❌ Application identity not found: {e}", file=sys.stderr)
        print("   Create a .fulmen/app.yaml file or use --path to specify location", file=sys.stderr)
        return ExitCode.EXIT_FILE_NOT_FOUND.value

    except AppIdentityValidationError as e:
        print(f"❌ Application identity validation failed: {e}", file=sys.stderr)
        return ExitCode.EXIT_DATA_INVALID.value

    except AppIdentityError as e:
        print(f"❌ Application identity error: {e}", file=sys.stderr)
        return ExitCode.EXIT_FAILURE.value

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return ExitCode.EXIT_FAILURE.value


def cmd_validate(args) -> int:
    """Handle the validate command."""
    try:
        identity = load_from_path(args.path)
        print(f"✅ Valid application identity: {identity.binary_name}")
        print(f"   Vendor: {identity.vendor}")
        print(f"   Environment Prefix: {identity.env_prefix}")
        return ExitCode.EXIT_SUCCESS.value

    except AppIdentityNotFoundError as e:
        print(f"❌ Application identity not found: {e}", file=sys.stderr)
        return ExitCode.EXIT_FILE_NOT_FOUND.value

    except AppIdentityValidationError as e:
        print(f"❌ Application identity validation failed: {e}", file=sys.stderr)
        if hasattr(e, "validation_errors") and e.validation_errors:
            print("   Validation errors:")
            for error in e.validation_errors:
                print(f"     - {error}")
        return ExitCode.EXIT_DATA_INVALID.value

    except AppIdentityError as e:
        print(f"❌ Application identity error: {e}", file=sys.stderr)
        return ExitCode.EXIT_FAILURE.value

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return ExitCode.EXIT_FAILURE.value


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "show":
        return cmd_show(args)
    elif args.command == "validate":
        return cmd_validate(args)
    else:
        parser.error("Unknown command")
        return ExitCode.EXIT_FAILURE.value


__all__ = ["main", "build_parser"]
