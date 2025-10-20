"""Listing commands for schema CLI."""

from __future__ import annotations

import click

from .. import catalog


@click.command("list")
@click.option("--prefix", help="Filter schema IDs by prefix")
def list_schemas(prefix: str | None) -> None:
    """List available schemas."""
    infos = catalog.list_schemas(prefix)
    for info in infos:
        click.echo(info.id)


__all__ = ["list_schemas"]
