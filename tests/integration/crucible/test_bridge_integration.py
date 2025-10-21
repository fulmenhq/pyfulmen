"""Integration tests for Crucible bridge API against real synced assets.

These tests verify that the bridge API works correctly with real Crucible assets
that have been synced via 'make sync-crucible'. They test end-to-end functionality
including asset discovery, loading, and error handling.
"""

import pytest

from pyfulmen.crucible import (
    AssetNotFoundError,
    get_crucible_version,
    list_assets,
    list_categories,
    load_schema_by_id,
    open_asset,
)
from pyfulmen.crucible.errors import CrucibleVersionError


class TestBridgeIntegration:
    """Integration tests for bridge API against real synced assets."""

    def test_list_categories_returns_expected_categories(self):
        """list_categories returns expected categories."""
        categories = list_categories()
        assert isinstance(categories, list)
        assert "docs" in categories
        assert "schemas" in categories
        assert "config" in categories

    def test_list_schemas_returns_real_assets(self):
        """list_assets('schemas') returns real schema metadata."""
        assets = list_assets("schemas")
        assert len(assets) > 0, "Expected synced schemas to be available"
        assert all(asset.category == "schemas" for asset in assets)
        assert all(asset.path.exists() for asset in assets)

    def test_list_schemas_discovers_nested_categories(self):
        """list_assets discovers nested schema categories like observability/logging."""
        # Get observability schemas
        assets = list_assets("schemas", prefix="observability")

        if len(assets) == 0:
            pytest.skip("Observability schemas not synced")

        # Should find nested schemas
        logging_schemas = [a for a in assets if "logging" in a.id]
        assert len(logging_schemas) > 0, "Expected to find observability/logging schemas"

        # Verify IDs have correct format (category/subcategory/version/name)
        example = logging_schemas[0]
        assert example.id.startswith("observability/logging/"), (
            f"Expected observability/logging/... but got {example.id}"
        )
        assert "/v" in example.id, f"Expected version in ID: {example.id}"

    def test_load_real_observability_schema(self):
        """load_schema_by_id loads real observability/logging schema."""
        try:
            schema = load_schema_by_id("observability/logging/v1.0.0/logger-config")
        except AssetNotFoundError:
            pytest.skip("observability/logging/v1.0.0/logger-config not synced")

        # Verify schema structure
        assert isinstance(schema, dict)
        assert "$schema" in schema or "type" in schema
        if "type" in schema:
            assert schema["type"] == "object"

    def test_load_real_library_foundry_schema(self):
        """load_schema_by_id loads real nested library/foundry schema."""
        try:
            schema = load_schema_by_id("library/foundry/v1.0.0/mime-types")
        except AssetNotFoundError:
            pytest.skip("library/foundry/v1.0.0/mime-types not synced")

        # Verify schema structure
        assert isinstance(schema, dict)
        assert "$schema" in schema or "type" in schema

    def test_list_docs_returns_real_assets(self):
        """list_assets('docs') returns real documentation."""
        assets = list_assets("docs")
        assert len(assets) > 0, "Expected synced docs to be available"
        assert all(asset.category == "docs" for asset in assets)
        assert all(asset.path.exists() for asset in assets)

    def test_doc_asset_ids_have_no_docs_prefix(self):
        """Documentation asset IDs do not include 'docs/' prefix."""
        assets = list_assets("docs")

        # Check that no IDs start with 'docs/'
        docs_prefix_assets = [a for a in assets if a.id.startswith("docs/")]
        assert len(docs_prefix_assets) == 0, (
            f"Found {len(docs_prefix_assets)} assets with 'docs/' prefix"
        )

        # Check for known architecture docs
        arch_docs = [a for a in assets if "architecture" in a.id]
        if arch_docs:
            example = arch_docs[0]
            # Should start with 'architecture/' not 'docs/architecture/'
            assert example.id.startswith("architecture/"), (
                f"Expected architecture/... but got {example.id}"
            )

    def test_open_asset_with_architecture_doc(self):
        """open_asset works with architecture docs using correct ID (no docs/ prefix)."""
        try:
            with open_asset("architecture/fulmen-helper-library-standard.md") as f:
                content = f.read()
                assert isinstance(content, bytes)
                assert len(content) > 1000  # Should be substantial document
                # Verify it's markdown content
                text = content.decode("utf-8")
                assert "fulmen" in text.lower() or "library" in text.lower()
        except AssetNotFoundError:
            pytest.skip("architecture/fulmen-helper-library-standard.md not synced")

    def test_open_asset_with_standards_doc(self):
        """open_asset works with standards docs."""
        try:
            with open_asset("standards/observability/logging.md") as f:
                content = f.read()
                assert isinstance(content, bytes)
                assert len(content) > 0
        except AssetNotFoundError:
            pytest.skip("standards/observability/logging.md not synced")

    def test_asset_not_found_includes_suggestions(self):
        """AssetNotFoundError includes helpful suggestions for typos."""
        try:
            # Intentional typo: 'loging' instead of 'logging'
            load_schema_by_id("observability/loging/v1.0.0/logger-config")
            pytest.fail("Expected AssetNotFoundError")
        except AssetNotFoundError as e:
            # Should have suggestions if observability schemas exist
            assert hasattr(e, "suggestions")
            assert isinstance(e.suggestions, list)
            # May have suggestions if similar schemas exist
            if e.suggestions:
                assert any("logging" in s for s in e.suggestions)

    def test_get_crucible_version_returns_valid_version(self):
        """get_crucible_version returns valid version metadata."""
        try:
            version = get_crucible_version()
        except CrucibleVersionError:
            pytest.skip("Crucible version metadata not available")

        assert version.version is not None
        assert isinstance(version.version, str)
        assert len(version.version) > 0
        # Version should follow CalVer or SemVer format
        assert "." in version.version or "-" in version.version

    def test_list_assets_with_prefix_filter_works(self):
        """Prefix filtering works correctly across nested categories."""
        # Test with observability prefix
        obs_assets = list_assets("schemas", prefix="observability")

        if len(obs_assets) == 0:
            pytest.skip("No observability schemas synced")

        # All should start with observability
        assert all(a.id.startswith("observability/") for a in obs_assets)

        # Should not include other categories
        assert not any(a.id.startswith("ascii/") for a in obs_assets)
        assert not any(a.id.startswith("config/") for a in obs_assets)

    def test_list_assets_sorted_by_id(self):
        """list_assets returns results sorted by ID."""
        assets = list_assets("schemas")

        if len(assets) < 2:
            pytest.skip("Not enough schemas to test sorting")

        ids = [a.id for a in assets]
        assert ids == sorted(ids), "Asset IDs should be sorted"

    def test_nested_config_discovery(self):
        """Config discovery finds nested categories like library/v1.0.0."""
        assets = list_assets("config", prefix="library")

        # May not have any if library configs aren't versioned
        if len(assets) > 0:
            # Check that we found library configs
            assert all(a.id.startswith("library/") for a in assets)
            # At least one should be nested (contain / after library/)
            nested = [a for a in assets if a.id.count("/") >= 2]
            assert len(nested) > 0, "Expected nested config paths"

    def test_nested_prefix_filtering_library_foundry(self):
        """Prefix filtering works with nested paths like 'library/foundry'."""
        # Test nested schema prefix (versioned)
        schemas = list_assets("schemas", prefix="library/foundry")

        if len(schemas) == 0:
            pytest.skip("library/foundry schemas not synced")

        # All should start with library/foundry
        assert all(a.id.startswith("library/foundry/") for a in schemas)

        # Should find specific schemas
        schema_names = {s.id.split("/")[-1] for s in schemas}
        expected_schemas = {"country-codes", "http-status-groups", "mime-types", "patterns"}
        found = expected_schemas & schema_names
        assert len(found) > 0, f"Expected to find some of {expected_schemas}, got {schema_names}"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_schema_id_format_raises_helpful_error(self):
        """Invalid schema ID format raises AssetNotFoundError."""
        with pytest.raises(AssetNotFoundError) as exc_info:
            load_schema_by_id("invalid-format")

        error = exc_info.value
        assert "invalid-format" in error.asset_id

    def test_nonexistent_category_in_list_assets_raises(self):
        """list_assets with invalid category raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            list_assets("nonexistent")

        assert "Invalid category" in str(exc_info.value)

    def test_open_asset_with_invalid_id_raises_not_found(self):
        """open_asset with invalid ID raises AssetNotFoundError."""
        with pytest.raises(AssetNotFoundError), open_asset("completely/invalid/asset/path.md") as f:
            f.read()


class TestBackwardCompatibility:
    """Test that bridge API maintains backward compatibility."""

    def test_can_still_use_legacy_docs_api(self):
        """Legacy docs.list_available_docs() still works."""
        from pyfulmen.crucible import docs

        doc_list = docs.list_available_docs()
        assert isinstance(doc_list, list)

    def test_can_still_use_legacy_schemas_api(self):
        """Legacy schemas.list_available_schemas() still works."""
        from pyfulmen.crucible import schemas

        schema_list = schemas.list_available_schemas()
        assert isinstance(schema_list, list)

    def test_can_mix_bridge_and_legacy_apis(self):
        """Can use both bridge and legacy APIs in same code."""
        from pyfulmen import crucible

        # Bridge API
        categories = crucible.list_categories()
        assets = crucible.list_assets("docs")

        # Legacy API
        docs_list = crucible.docs.list_available_docs()

        # Both should work and return consistent results
        assert "docs" in categories
        assert isinstance(assets, list)
        assert isinstance(docs_list, list)
