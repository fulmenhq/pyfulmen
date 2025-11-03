"""Schema helper CLI (experimental)."""

from __future__ import annotations

import click

from . import export, info, listing, validate


@click.group(help="Explore PyFulmen schema catalog and validate payloads.")
def cli() -> None:
    """Root command group."""


cli.add_command(listing.list_schemas)
cli.add_command(info.show_schema)
cli.add_command(validate.validate_payload)
cli.add_command(export.export_schema_cmd)


__all__ = ["cli"]
