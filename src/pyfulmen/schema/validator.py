"""Schema validation utilities using jsonschema and optional goneat integration."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, ValidationError
from jsonschema import validate as jsonschema_validate

from .. import crucible
from ..telemetry import MetricRegistry
from . import catalog


@dataclass(slots=True)
class Diagnostic:
    pointer: str
    message: str
    keyword: str | None
    severity: str = "ERROR"
    source: str = "jsonschema"


@dataclass(slots=True)
class ValidationResult:
    schema: catalog.SchemaInfo
    is_valid: bool
    diagnostics: list[Diagnostic]
    source: str


class SchemaValidationError(Exception):
    """Schema validation failed."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


def load_validator(category: str, version: str, name: str) -> Draft7Validator:
    schema = crucible.schemas.load_schema(category, version, name)
    return Draft7Validator(schema)


def validate_against_schema(data: dict[str, Any], category: str, version: str, name: str) -> None:
    """
    Validate data against a schema, raising on validation failure.

    Telemetry:
        - Emits schema_validation_ms histogram (validation duration)
        - Emits schema_validation_errors counter (on validation failure)
    """
    start_time = time.perf_counter()
    registry = MetricRegistry()

    try:
        _validate_against_schema_impl(data, category, version, name, registry)
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        registry.histogram("schema_validation_ms").observe(duration_ms)


def _validate_against_schema_impl(
    data: dict[str, Any], category: str, version: str, name: str, registry: MetricRegistry
) -> None:
    """Internal implementation of validate_against_schema without telemetry."""
    schema = crucible.schemas.load_schema(category, version, name)

    try:
        jsonschema_validate(instance=data, schema=schema)
    except ValidationError as exc:
        registry.counter("schema_validation_errors").inc()
        validator = Draft7Validator(schema)
        errors = [err.message for err in validator.iter_errors(data)]

        raise SchemaValidationError(
            f"Schema validation failed for {category}/{version}/{name}",
            errors=errors,
        ) from exc


def is_valid(data: dict[str, Any], category: str, version: str, name: str) -> bool:
    try:
        validate_against_schema(data, category, version, name)
        return True
    except (SchemaValidationError, FileNotFoundError):
        return False


def validate_data(schema_id: str, data: Any, *, use_goneat: bool = True) -> ValidationResult:
    info = catalog.get_schema(schema_id)
    if use_goneat:
        result = _validate_with_goneat(info, data)
        if result is not None:
            return result

    schema = crucible.schemas.load_schema(info.category, info.version, info.name)
    validator = Draft7Validator(schema)
    diagnostics = _diagnostics_from_errors(validator.iter_errors(data))
    return ValidationResult(
        schema=info, is_valid=not diagnostics, diagnostics=diagnostics, source="jsonschema"
    )


def validate_file(schema_id: str, path: Path | str, *, use_goneat: bool = True) -> ValidationResult:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    if file_path.suffix in {".yaml", ".yml"}:
        import yaml

        data = yaml.safe_load(file_path.read_text())
    else:
        data = json.loads(file_path.read_text())

    return validate_data(schema_id, data, use_goneat=use_goneat)


def format_diagnostics(diagnostics: list[Diagnostic], *, style: str = "text") -> str:
    if not diagnostics:
        return "No diagnostics"

    if style == "json":
        return json.dumps([asdict(diag) for diag in diagnostics], indent=2)

    lines = []
    for diag in diagnostics:
        pointer = diag.pointer or "<root>"
        keyword = f" ({diag.keyword})" if diag.keyword else ""
        lines.append(f"- [{diag.severity}] {pointer}: {diag.message}{keyword} ({diag.source})")
    return "\n".join(lines)


# Internal helpers -----------------------------------------------------------


def _diagnostics_from_errors(errors: Iterable[ValidationError]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for err in errors:
        pointer = "/" + "/".join(str(part) for part in err.path) if err.path else ""
        diagnostics.append(
            Diagnostic(
                pointer=pointer,
                message=err.message,
                keyword=err.validator,
                severity="ERROR",
                source="jsonschema",
            )
        )
    return diagnostics


def _find_goneat_binary() -> str | None:
    return os.getenv("GONEAT_BIN") or shutil.which("goneat")


def _validate_with_goneat(info: catalog.SchemaInfo, data: Any) -> ValidationResult | None:
    goneat_bin = _find_goneat_binary()
    if not goneat_bin:
        return None

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(data, tmp)
        tmp_path = Path(tmp.name)

    cmd = [
        goneat_bin,
        "schema",
        "validate-data",
        "--schema",
        str(info.path),
        "--file",
        str(tmp_path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    finally:
        tmp_path.unlink(missing_ok=True)

    if proc.returncode == 0:
        return ValidationResult(schema=info, is_valid=True, diagnostics=[], source="goneat")

    diagnostics: list[Diagnostic] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        diagnostics.append(
            Diagnostic(
                pointer="", message=line.strip(), keyword=None, severity="ERROR", source="goneat"
            )
        )

    return ValidationResult(schema=info, is_valid=False, diagnostics=diagnostics, source="goneat")


__all__ = [
    "SchemaValidationError",
    "Diagnostic",
    "ValidationResult",
    "load_validator",
    "validate_against_schema",
    "validate_data",
    "validate_file",
    "format_diagnostics",
    "is_valid",
]
