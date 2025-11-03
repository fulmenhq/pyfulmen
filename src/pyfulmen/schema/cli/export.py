"""Export command for schema CLI."""

from __future__ import annotations

from pathlib import Path

import click

from ..export import export_schema
from ..validator import SchemaValidationError


@click.command("export")
@click.argument("schema_id")
@click.option("--out", "-o", "out_path", required=True, type=click.Path(path_type=Path), help="Output file path")
@click.option("--no-provenance", is_flag=True, help="Omit provenance metadata")
@click.option("--no-validate", is_flag=True, help="Skip validation")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def export_schema_cmd(
    schema_id: str,
    out_path: Path,
    no_provenance: bool,
    no_validate: bool,
    force: bool,
    verbose: bool,
) -> None:
    """Export schema to local file."""
    try:
        result_path = export_schema(
            schema_id=schema_id,
            out_path=out_path,
            include_provenance=not no_provenance,
            validate=not no_validate,
            overwrite=force
        )

        if verbose:
            click.echo(f"✅ Exported schema: {schema_id}")
            click.echo(f"   Output: {result_path}")
            click.echo(f"   Provenance: {'included' if not no_provenance else 'omitted'}")
            click.echo(f"   Validation: {'passed' if not no_validate else 'skipped'}")
        else:
            click.echo(result_path)

    except FileNotFoundError as e:
        raise click.ClickException(f"Schema not found: {e}") from e
    except FileExistsError as e:
        raise click.ClickException(f"File exists: {e}\nUse --force to overwrite") from e
    except SchemaValidationError as e:
        raise click.ClickException(f"Validation failed: {e}") from e
    except OSError as e:
        raise click.ClickException(f"Write error: {e}") from e


__all__ = ["export_schema_cmd"]