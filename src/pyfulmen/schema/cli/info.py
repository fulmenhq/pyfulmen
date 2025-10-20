"""Metadata command for schema CLI."""

from __future__ import annotations

import json

import click

from .. import catalog


@click.command("info")
@click.argument("schema_id")
def show_schema(schema_id: str) -> None:
    """Display metadata for a schema identifier."""
    info = catalog.get_schema(schema_id)
    payload = {
        "id": info.id,
        "category": info.category,
        "version": info.version,
        "name": info.name,
        "path": str(info.path),
        "description": info.description,
    }
    click.echo(json.dumps(payload, indent=2))


__all__ = ["show_schema"]
