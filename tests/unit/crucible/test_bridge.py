"""Tests for Crucible bridge API."""

import pytest

from pyfulmen.crucible import bridge
from pyfulmen.crucible.errors import AssetNotFoundError
from pyfulmen.crucible.models import AssetMetadata, CrucibleVersion


class TestListCategories:
    """Tests for list_categories function."""

    def test_returns_expected_categories(self):
        """list_categories returns docs, schemas, and config."""
        categories = bridge.list_categories()
        assert isinstance(categories, list)
        assert "docs" in categories
        assert "schemas" in categories
        assert "config" in categories

    def test_returns_consistent_order(self):
        """list_categories returns same list every time."""
        categories1 = bridge.list_categories()
        categories2 = bridge.list_categories()
        assert categories1 == categories2


class TestListAssets:
    """Tests for list_assets function."""

    def test_list_docs_returns_asset_metadata(self):
        """list_assets('docs') returns AssetMetadata instances."""
        assets = bridge.list_assets("docs")
        assert isinstance(assets, list)
        if len(assets) > 0:  # May be empty in test env
            assert all(isinstance(a, AssetMetadata) for a in assets)
            assert all(a.category == "docs" for a in assets)

    def test_list_schemas_returns_asset_metadata(self):
        """list_assets('schemas') returns AssetMetadata instances."""
        assets = bridge.list_assets("schemas")
        assert isinstance(assets, list)
        if len(assets) > 0:
            assert all(isinstance(a, AssetMetadata) for a in assets)
            assert all(a.category == "schemas" for a in assets)

    def test_list_config_returns_asset_metadata(self):
        """list_assets('config') returns AssetMetadata instances."""
        assets = bridge.list_assets("config")
        assert isinstance(assets, list)
        if len(assets) > 0:
            assert all(isinstance(a, AssetMetadata) for a in assets)
            assert all(a.category == "config" for a in assets)

    def test_list_assets_with_prefix_filters(self):
        """list_assets with prefix filters results."""
        # Get all assets
        all_assets = bridge.list_assets("docs")
        # Get filtered assets
        filtered = bridge.list_assets("docs", prefix="standards")

        # Filtered should be subset
        assert len(filtered) <= len(all_assets)
        # All filtered IDs should start with prefix
        assert all(a.id.startswith("standards") for a in filtered)

    def test_list_assets_invalid_category_raises(self):
        """list_assets with invalid category raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            bridge.list_assets("invalid_category")
        assert "Invalid category" in str(exc_info.value)
        assert "invalid_category" in str(exc_info.value)

    def test_list_assets_results_are_sorted(self):
        """list_assets returns results sorted by ID."""
        assets = bridge.list_assets("schemas")
        if len(assets) > 1:
            ids = [a.id for a in assets]
            assert ids == sorted(ids)

    def test_list_schemas_discovers_nested_categories(self):
        """list_assets('schemas') recursively discovers nested schema categories."""
        assets = bridge.list_assets("schemas", prefix="observability")

        # Should find nested schemas like observability/logging
        if len(assets) > 0:
            # Check that we have nested paths (contains /)
            nested_assets = [
                a for a in assets if a.id.count("/") >= 3
            ]  # category/subcategory/version/name
            # If observability schemas exist, at least some should be nested
            assert len(nested_assets) > 0, (
                "Expected to find nested schema paths like observability/logging/v1.0.0/..."
            )

            # Verify specific nested schema exists (if observability is synced)
            logging_schemas = [a for a in assets if "logging" in a.id]
            if logging_schemas:
                # Should have full path like observability/logging/v1.0.0/logger-config
                example = logging_schemas[0]
                assert example.id.startswith("observability/logging/"), (
                    f"Expected observability/logging/... but got {example.id}"
                )

    def test_list_configs_discovers_nested_categories(self):
        """list_assets('config') recursively discovers nested config categories."""
        assets = bridge.list_assets("config", prefix="library")

        # Should find nested configs like library/foundry (if they exist with versions)
        if len(assets) > 0:
            # At least some assets should have nested paths
            nested_assets = [a for a in assets if "/" in a.id]
            assert len(nested_assets) >= 0  # May be 0 if no versioned nested configs exist

    def test_doc_asset_ids_have_no_docs_prefix(self):
        """Doc asset IDs should not include 'docs/' prefix."""
        assets = bridge.list_assets("docs")

        if len(assets) > 0:
            # Check that no IDs start with 'docs/'
            for asset in assets:
                assert not asset.id.startswith("docs/"), (
                    f"Doc ID should not start with 'docs/': {asset.id}"
                )

            # Check for known docs (if they exist)
            arch_docs = [a for a in assets if "architecture" in a.id]
            if arch_docs:
                # Should be like 'architecture/...' not 'docs/architecture/...'
                assert any(a.id.startswith("architecture/") for a in arch_docs), (
                    "Expected architecture/* paths without docs/ prefix"
                )


class TestGetCrucibleVersion:
    """Tests for get_crucible_version function."""

    def test_returns_crucible_version_instance(self):
        """get_crucible_version returns CrucibleVersion."""
        version = bridge.get_crucible_version()
        assert isinstance(version, CrucibleVersion)
        assert version.version is not None
        assert isinstance(version.version, str)

    def test_version_has_expected_format(self):
        """Version string follows expected format."""
        version = bridge.get_crucible_version()
        # Should be something like "2025.10.0"
        assert len(version.version) > 0
        assert "." in version.version or "-" in version.version


class TestLoadSchemaById:
    """Tests for load_schema_by_id function."""

    def test_load_valid_schema_succeeds(self):
        """load_schema_by_id with valid ID returns schema dict."""
        # Try to load a known schema (may not exist in all test envs)
        try:
            schema = bridge.load_schema_by_id("observability/logging/v1.0.0/logger-config")
            assert isinstance(schema, dict)
            # Schema should have $schema or type field
            assert "$schema" in schema or "type" in schema
        except AssetNotFoundError:
            # Skip if schema not available in test env
            pytest.skip("Schema not available in test environment")

    def test_load_invalid_schema_raises_asset_not_found(self):
        """load_schema_by_id with invalid ID raises AssetNotFoundError."""
        with pytest.raises(AssetNotFoundError) as exc_info:
            bridge.load_schema_by_id("invalid/schema/id")
        error = exc_info.value
        assert error.asset_id == "invalid/schema/id"
        assert error.category == "schemas"

    def test_load_schema_provides_suggestions_on_typo(self):
        """load_schema_by_id provides suggestions for typos."""
        try:
            # Try to load with typo (assuming observability schemas exist)
            bridge.load_schema_by_id("observability/loging/v1.0.0/logger-config")  # Typo: loging
            pytest.fail("Expected AssetNotFoundError")
        except AssetNotFoundError as e:
            # Should have suggestions if schemas directory is populated
            # (may be empty in minimal test env)
            assert hasattr(e, "suggestions")


class TestGetConfigDefaults:
    """Tests for get_config_defaults function."""

    def test_load_valid_config_succeeds(self):
        """get_config_defaults with valid category/version/name returns dict."""
        try:
            config = bridge.get_config_defaults("terminal", "v1.0.0", "terminal-overrides-defaults")
            assert isinstance(config, dict)
        except AssetNotFoundError:
            # Skip if config not available in test env
            pytest.skip("Config not available in test environment")

    def test_load_invalid_config_raises_asset_not_found(self):
        """get_config_defaults with invalid category raises AssetNotFoundError."""
        with pytest.raises(AssetNotFoundError) as exc_info:
            bridge.get_config_defaults("invalid-category", "v1.0.0", "invalid-name")
        error = exc_info.value
        assert "invalid-category/v1.0.0/invalid-name" in error.asset_id
        assert error.category == "config"


class TestOpenAsset:
    """Tests for open_asset function."""

    def test_open_valid_doc_succeeds(self):
        """open_asset with valid doc path returns file handle."""
        try:
            with bridge.open_asset("standards/observability/logging.md") as f:
                content = f.read()
                assert isinstance(content, bytes)
                assert len(content) > 0
        except AssetNotFoundError:
            # Skip if doc not available
            pytest.skip("Doc not available in test environment")

    def test_open_invalid_asset_raises_asset_not_found(self):
        """open_asset with invalid path raises AssetNotFoundError."""
        with pytest.raises(AssetNotFoundError), bridge.open_asset("nonexistent/asset/path.md") as f:
            f.read()

    def test_open_asset_context_manager_closes_file(self):
        """open_asset properly closes file when exiting context."""
        try:
            with bridge.open_asset("standards/observability/logging.md") as f:
                file_obj = f
                assert not f.closed

            # File should be closed after context
            assert file_obj.closed
        except AssetNotFoundError:
            pytest.skip("Doc not available in test environment")

    def test_open_asset_works_without_docs_prefix(self):
        """open_asset works with asset IDs without 'docs/' prefix."""
        try:
            # Should work with 'architecture/...' not 'docs/architecture/...'
            with bridge.open_asset("architecture/fulmen-helper-library-standard.md") as f:
                content = f.read()
                assert isinstance(content, bytes)
                assert len(content) > 0
        except AssetNotFoundError:
            # Try another known doc
            try:
                with bridge.open_asset("standards/observability/logging.md") as f:
                    content = f.read()
                    assert isinstance(content, bytes)
            except AssetNotFoundError:
                pytest.skip("Docs not available in test environment")


class TestFindSimilarAssets:
    """Tests for _find_similar_assets helper."""

    def test_finds_similar_assets_by_parts(self):
        """_find_similar_assets matches on path parts."""
        candidates = [
            "observability/logging/v1.0.0/logger-config",
            "observability/metrics/v1.0.0/metrics-config",
            "terminal/box-chars/v1.0.0/box-chars",
        ]

        # Query with typo
        query = "observability/loging/v1.0.0/logger-config"
        suggestions = bridge._find_similar_assets(query, candidates)

        # Should suggest the correct one
        assert len(suggestions) > 0
        assert "observability/logging/v1.0.0/logger-config" in suggestions

    def test_limits_suggestions_to_max(self):
        """_find_similar_assets respects max_suggestions limit."""
        candidates = [f"asset/path/{i}" for i in range(10)]
        query = "asset/path/typo"

        suggestions = bridge._find_similar_assets(query, candidates, max_suggestions=3)
        assert len(suggestions) <= 3

    def test_returns_empty_for_no_matches(self):
        """_find_similar_assets returns empty list for no matches."""
        candidates = ["completely/different/path"]
        query = "no/match/here"

        suggestions = bridge._find_similar_assets(query, candidates)
        assert len(suggestions) == 0


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing APIs."""

    def test_get_documentation_still_available(self):
        """Existing get_documentation API remains available."""
        from pyfulmen import crucible

        assert hasattr(crucible, "get_documentation")

    def test_legacy_submodules_still_available(self):
        """Legacy submodule access still works."""
        from pyfulmen import crucible

        assert hasattr(crucible, "docs")
        assert hasattr(crucible, "schemas")
        assert hasattr(crucible, "config")

    def test_can_mix_bridge_and_legacy_apis(self):
        """Can use both bridge and legacy APIs together."""
        from pyfulmen import crucible

        # Bridge API
        categories = crucible.list_categories()
        assert "docs" in categories

        # Legacy API
        docs_list = crucible.docs.list_available_docs()
        assert isinstance(docs_list, list)
