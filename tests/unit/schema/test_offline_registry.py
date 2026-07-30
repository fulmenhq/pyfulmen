"""Tests for offline $ref resolution (pyfulmen.schema.registry).

Proves that schema validation resolves absolute $refs from the local
schemas/crucible-py tree and never attempts a network fetch, ahead of the
crucible v0.4.15 sync that absolutizes $ref URLs.
"""

import json
import socket

import pytest

from pyfulmen.crucible import _paths
from pyfulmen.schema.registry import (
    DERIVED_URI_BASE,
    OfflineSchemaResolutionError,
    crucible_registry,
)
from pyfulmen.schema.validator import (
    SchemaValidationError,
    load_validator,
    validate_against_schema,
)

TARGET_ID = "https://schemas.fulmenhq.dev/crucible/testcat/target-v1.0.0.json"
UNKNOWN_URI = "https://schemas.fulmenhq.dev/crucible/testcat/does-not-exist-v9.9.9.json"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail loudly if anything in these tests attempts a network connection."""

    def _blocked(*args, **kwargs):
        raise AssertionError("Network access attempted during offline schema validation")

    monkeypatch.setattr(socket, "getaddrinfo", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)


@pytest.fixture
def temp_schema_tree(tmp_path, monkeypatch):
    """Redirect the crucible schemas dir to a controlled temporary tree."""
    cat = tmp_path / "testcat" / "v1.0.0"
    cat.mkdir(parents=True)

    # Target with a flat (legacy-shaped) $id that does NOT match its disk path.
    (cat / "target.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": TARGET_ID,
                "$defs": {"colorName": {"type": "string", "enum": ["red", "green", "blue"]}},
            }
        )
    )

    # Consumer referencing the target by its absolute $id (v0.4.15-style ref).
    (cat / "consumer.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://schemas.fulmenhq.dev/crucible/testcat/consumer-v1.0.0.json",
                "type": "object",
                "properties": {"color": {"$ref": f"{TARGET_ID}#/$defs/colorName"}},
                "required": ["color"],
            }
        )
    )

    # Schema with no $id at all -- only reachable via its derived catalog URI.
    (cat / "noid.schema.json").write_text(json.dumps({"$defs": {"port": {"type": "integer", "minimum": 1}}}))

    # Consumer using the derived (layout-based) URI of the no-$id schema.
    (cat / "derived-consumer.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"port": {"$ref": f"{DERIVED_URI_BASE}testcat/v1.0.0/noid.schema.json#/$defs/port"}},
            }
        )
    )

    # Consumer with a path-shaped $id and a v0.4.12-style relative ref.
    (cat / "rel-consumer.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": f"{DERIVED_URI_BASE}testcat/v1.0.0/rel-consumer.schema.json",
                "type": "object",
                "properties": {"port": {"$ref": "./noid.schema.json#/$defs/port"}},
            }
        )
    )

    # Consumer with an absolute ref that exists nowhere locally.
    (cat / "unknown-ref.schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"color": {"$ref": UNKNOWN_URI}},
            }
        )
    )

    monkeypatch.setattr(_paths, "get_schemas_dir", lambda: tmp_path)
    crucible_registry.cache_clear()
    yield tmp_path
    crucible_registry.cache_clear()


class TestRealCatalog:
    """(a) Existing validation against the synced catalog still works."""

    def test_valid_data_still_passes(self):
        validate_against_schema(
            {"profile": "SIMPLE", "service": "pyfulmen-tests"},
            "observability/logging",
            "v1.0.0",
            "logger-config",
        )

    def test_invalid_data_still_fails(self):
        with pytest.raises(SchemaValidationError):
            validate_against_schema(
                {"profile": "NOT-A-PROFILE"},
                "observability/logging",
                "v1.0.0",
                "logger-config",
            )

    def test_load_validator_carries_offline_registry(self):
        validator = load_validator("observability/logging", "v1.0.0", "logger-config")
        assert validator.is_valid({"profile": "SIMPLE", "service": "svc"})

    def test_registry_maps_declared_ids_and_derived_uris(self):
        registry = crucible_registry()
        # Declared (flat-shaped) $id of a real synced schema.
        contents = registry.contents(
            "https://schemas.fulmenhq.dev/crucible/assessment/severity-definitions-v1.0.0.json"
        )
        assert "severityName" in contents["$defs"]
        # Derived URI of the same file (layout-based mapping rule).
        derived = registry.contents(f"{DERIVED_URI_BASE}assessment/v1.0.0/severity-definitions.schema.json")
        assert derived == contents


class TestAbsoluteRefResolution:
    """(b) Absolute $refs to local schemas resolve entirely offline."""

    def test_absolute_ref_to_declared_id(self, temp_schema_tree):
        validate_against_schema({"color": "red"}, "testcat", "v1.0.0", "consumer")

        with pytest.raises(SchemaValidationError) as exc_info:
            validate_against_schema({"color": "purple"}, "testcat", "v1.0.0", "consumer")
        assert exc_info.value.errors

    def test_absolute_ref_to_derived_uri(self, temp_schema_tree):
        validate_against_schema({"port": 8080}, "testcat", "v1.0.0", "derived-consumer")

        with pytest.raises(SchemaValidationError):
            validate_against_schema({"port": 0}, "testcat", "v1.0.0", "derived-consumer")

    def test_relative_ref_via_path_shaped_id(self, temp_schema_tree):
        """v0.4.12-style relative refs resolve through the derived URI mapping."""
        validate_against_schema({"port": 443}, "testcat", "v1.0.0", "rel-consumer")

        with pytest.raises(SchemaValidationError):
            validate_against_schema({"port": -1}, "testcat", "v1.0.0", "rel-consumer")


class TestUnknownRef:
    """(c) Unknown absolute $refs raise the offline error -- no fetch."""

    def test_unknown_absolute_ref_raises_offline_error(self, temp_schema_tree):
        with pytest.raises(OfflineSchemaResolutionError) as exc_info:
            validate_against_schema({"color": "red"}, "testcat", "v1.0.0", "unknown-ref")

        message = str(exc_info.value)
        assert UNKNOWN_URI in message
        assert "network fetching is disabled" in message

    def test_offline_error_is_not_a_validation_error(self, temp_schema_tree):
        with pytest.raises(OfflineSchemaResolutionError):
            validate_against_schema({"color": "red"}, "testcat", "v1.0.0", "unknown-ref")
        assert not issubclass(OfflineSchemaResolutionError, SchemaValidationError)
