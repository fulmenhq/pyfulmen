"""Tests for pyfulmen.crucible.schemas module."""

import pytest

from pyfulmen.crucible import schemas


def test_list_available_schemas():
    """Test listing schema categories."""
    categories = schemas.list_available_schemas()

    assert isinstance(categories, list)
    assert len(categories) > 0
    # Should include common categories from Crucible
    assert "observability" in categories or "config" in categories


def test_list_schema_versions():
    """Test listing schema versions for a category."""
    # Test with observability/logging
    versions = schemas.list_schema_versions("observability/logging")

    assert isinstance(versions, list)
    if len(versions) > 0:
        # Versions should follow vX.Y.Z format
        assert versions[0].startswith("v")


def test_get_schema_path():
    """Test getting path to a schema file."""
    # Test with known schema from sync
    path = schemas.get_schema_path("observability/logging", "v1.0.0", "logger-config")

    assert path.exists()
    assert path.suffix in [".json", ".yaml"]
    assert "logger-config" in path.name


def test_get_schema_path_not_found():
    """Test getting path to non-existent schema."""
    with pytest.raises(FileNotFoundError):
        schemas.get_schema_path("invalid", "v1.0.0", "nonexistent")


def test_load_schema():
    """Test loading a JSON schema."""
    schema = schemas.load_schema("observability/logging", "v1.0.0", "logger-config")

    assert isinstance(schema, dict)
    # JSON schemas should have $schema property
    assert "$schema" in schema or "type" in schema
