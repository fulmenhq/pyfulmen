"""Tests for schema catalog utilities."""

from pyfulmen.schema import catalog


def test_list_schemas_returns_entries():
    schemas = catalog.list_schemas()
    assert schemas
    assert any(info.id.startswith("observability/") for info in schemas)


def test_get_schema_round_trip():
    info = catalog.get_schema("observability/logging/v1.0.0/logger-config")
    assert info.name == "logger-config"
    assert info.category == "observability/logging"
    assert info.version == "v1.0.0"


def test_parse_schema_id():
    category, version, name = catalog.parse_schema_id("observability/logging/v1.0.0/logger-config")
    assert category == "observability/logging"
    assert version == "v1.0.0"
    assert name == "logger-config"
