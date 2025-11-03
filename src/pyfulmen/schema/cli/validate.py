"""Validation command for schema CLI."""

from __future__ import annotations

import json
from pathlib import Path

import click

from ..validator import format_diagnostics, validate_data, validate_file


@click.command("validate")
@click.argument("schema_id")
@click.option("--file", "file_path", type=click.Path(path_type=Path), help="Path to JSON/YAML payload")
@click.option("--data", "inline_data", help="Inline JSON string to validate")
@click.option("--format", "format_", type=click.Choice(["text", "json"]), default="text")
@click.option(
    "--use-goneat/--no-goneat",
    default=False,
    help="Invoke goneat when available (default: disabled)",
)
def validate_payload(
    schema_id: str,
    file_path: Path | None,
    inline_data: str | None,
    format_: str,
    use_goneat: bool,
) -> None:
    """Validate data against a schema."""
    if bool(file_path) == bool(inline_data):
        raise click.UsageError("Provide exactly one of --file or --data")

    if inline_data is not None:
        try:
            payload = json.loads(inline_data)
        except json.JSONDecodeError as exc:
            raise click.BadParameter(f"Invalid JSON payload: {exc}") from exc
        result = validate_data(schema_id, payload, use_goneat=use_goneat)
    else:
        result = validate_file(schema_id, file_path, use_goneat=use_goneat)

    click.echo(format_diagnostics(result.diagnostics, style=format_))
    if not result.is_valid:
        raise SystemExit(1)


__all__ = ["validate_payload"]
