"""Provenance metadata utilities for schema exports."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _add_provenance(schema_data: dict[str, Any], schema_id: str, out_path: Path) -> dict[str, Any]:
    """Add provenance metadata to schema data.

    Args:
        schema_data: Original schema dictionary
        schema_id: Schema identifier
        out_path: Output path (determines format)

    Returns:
        Schema data with provenance metadata
    """
    from .. import version as pyfulmen_version
    from ..crucible import _version

    crucible_meta = _version.get_crucible_version()

    provenance = {
        "schema_id": schema_id,
        "crucible_version": crucible_meta.version,
        "pyfulmen_version": pyfulmen_version.read_version(),
        "revision": crucible_meta.commit[:8] if crucible_meta.commit and crucible_meta.commit != "unknown" else None,
        "exported_at": datetime.now(UTC).isoformat(),
    }

    suffix_lower = out_path.suffix.lower()
    if suffix_lower in [".json", ".schema.json", ".jsonc"]:
        # JSON: Add as $comment with x-crucible-source
        result = schema_data.copy()
        if "$comment" not in result:
            # Only add $comment if it doesn't exist to avoid schema validation issues
            result["$comment"] = {"x-crucible-source": provenance}
        else:
            # If $comment already exists, add provenance as a separate field
            result["_crucible_provenance"] = provenance
        return result
    else:
        # YAML and other formats: Add as frontmatter comment
        # For YAML, we'll need to handle this in the export function
        # by prepending a comment header before dumping
        result = schema_data.copy()
        result["_provenance"] = provenance  # Temp key, handled by export_schema
        return result


def _format_yaml_provenance_header(provenance: dict[str, Any]) -> str:
    """Format provenance as YAML comment header.

    Args:
        provenance: Provenance metadata dictionary

    Returns:
        Formatted YAML comment header
    """
    lines = [
        "# Crucible Schema Export Provenance",
        f"# Schema ID: {provenance['schema_id']}",
        f"# Crucible Version: {provenance['crucible_version']}",
        f"# PyFulmen Version: {provenance['pyfulmen_version']}",
    ]

    if provenance.get("revision"):
        lines.append(f"# Revision: {provenance['revision']}")

    lines.append(f"# Exported At: {provenance['exported_at']}")
    lines.append("")  # Blank line before schema content

    return "\n".join(lines)


__all__ = [
    "_add_provenance",
    "_format_yaml_provenance_header",
]
