"""Schema export utilities for PyFulmen."""

from pathlib import Path

from . import catalog
from ._provenance import _add_provenance, _format_yaml_provenance_header


def export_schema(
    schema_id: str,
    out_path: Path | str,
    *,
    include_provenance: bool = True,
    validate: bool = True,
    overwrite: bool = False
) -> Path:
    """Export a Crucible schema to a local file with optional provenance.
    
    Args:
        schema_id: Schema identifier (category/version/name format)
        out_path: Output file path (JSON or YAML based on extension)
        include_provenance: Add Crucible source metadata (default: True)
        validate: Validate schema before writing (default: True)
        overwrite: Allow overwriting existing files (default: False)
        
    Returns:
        Absolute path to exported file
        
    Raises:
        FileNotFoundError: Schema not found in catalog
        FileExistsError: Output file exists and overwrite=False
        ValueError: Invalid schema_id format
        SchemaValidationError: Validation failure when validate=True
        IOError: File write error
        
    Example:
        >>> from pyfulmen.schema import export_schema
        >>> path = export_schema(
        ...     "observability/logging/v1.0.0/logger-config",
        ...     "schemas/logger-config.json"
        ... )
        >>> path.exists()
        True
    """
    import json

    from ..crucible import schemas as crucible_schemas
    from .validator import SchemaValidationError

    try:
        import yaml
    except ImportError:
        yaml = None
    
    out_path = Path(out_path)
    
    # Parse schema_id and verify schema exists
    try:
        category, version, name = catalog.parse_schema_id(schema_id)
    except ValueError as e:
        raise ValueError(f"Invalid schema_id format: {schema_id}") from e
    
    # Check if file exists
    if out_path.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {out_path}\n"
            "Use overwrite=True to replace existing file."
        )
    
    # Load schema
    try:
        schema_data = crucible_schemas.load_schema(category, version, name)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Schema not found: {schema_id}\n"
            "Run 'make sync-crucible' to sync Crucible assets."
        ) from e
    
    # Add provenance (if requested)
    if include_provenance:
        schema_data_with_provenance = _add_provenance(schema_data, schema_id, out_path)
    else:
        schema_data_with_provenance = schema_data
    
    # Validate (if requested)
    if validate:
        # Validate the original schema (without provenance) against meta-schema
        from jsonschema import Draft202012Validator

        try:
            Draft202012Validator.check_schema(schema_data)
        except Exception as exc:  # jsonschema.SchemaError
            raise SchemaValidationError(
                f"Schema validation failed for {schema_id}",
                errors=[str(exc)],
            ) from exc
    
    # Write to file
    out_path.parent.mkdir(parents=True, exist_ok=True)

    suffix_lower = out_path.suffix.lower()
    if suffix_lower in [".json", ".schema.json", ".jsonc"]:
        with open(out_path, "w") as f:
            json.dump(schema_data_with_provenance, f, indent=2, sort_keys=True)
            f.write("\n")  # Ensure newline EOF
    elif suffix_lower in [".yaml", ".yml", ".schema.yaml"]:
        if yaml is None:
            raise RuntimeError(
                "PyYAML is required for YAML export but not installed. "
                "Install with: uv add PyYAML"
            )
        # Handle YAML provenance as comment header
        if include_provenance and "_provenance" in schema_data_with_provenance:
            provenance = schema_data_with_provenance.pop("_provenance")
            with open(out_path, "w") as f:
                f.write(_format_yaml_provenance_header(provenance))
                yaml.safe_dump(  # type: ignore
                    schema_data_with_provenance,
                    f,
                    default_flow_style=False,
                    sort_keys=True
                )
        else:
            with open(out_path, "w") as f:
                yaml.safe_dump(  # type: ignore
                    schema_data_with_provenance,
                    f,
                    default_flow_style=False,
                    sort_keys=True
                )
    else:
        # Default to JSON for unknown extensions (treat as JSON-like)
        # For unknown extensions, ensure provenance is added as $comment if not already present
        if include_provenance and "_provenance" in schema_data_with_provenance:
            # Convert _provenance to $comment for JSON-like formats
            prov_data = schema_data_with_provenance.pop("_provenance")
            if "$comment" not in schema_data_with_provenance:
                schema_data_with_provenance["$comment"] = {"x-crucible-source": prov_data}
            # If $comment exists, we skip adding provenance to avoid schema validation issues

        with open(out_path, "w") as f:
            json.dump(schema_data_with_provenance, f, indent=2, sort_keys=True)
            f.write("\n")  # Ensure newline EOF
    
    return out_path.absolute()


__all__ = [
    "export_schema",
]