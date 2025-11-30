from pyfulmen import crucible


class TestConsumerAssets:
    """Verify that Crucible assets are accessible to downstream consumers.

    This test suite replicates the usage patterns documented for library users,
    ensuring that the 'crucible' module and its bridge API function correctly.
    """

    def test_import_crucible_module(self):
        """Verify 'from pyfulmen import crucible' works and exposes expected API."""
        assert hasattr(crucible, "list_categories")
        assert hasattr(crucible, "find_schema")
        assert hasattr(crucible, "find_config")
        assert hasattr(crucible, "get_doc")
        assert hasattr(crucible, "get_crucible_version")

    def test_list_categories(self):
        """Verify listing asset categories."""
        categories = crucible.list_categories()
        assert isinstance(categories, list)
        assert "schemas" in categories
        assert "docs" in categories
        assert "config" in categories

    def test_find_schema_access(self):
        """Verify accessing a specific schema and its metadata."""
        # Using a known stable schema path
        schema_id = "observability/logging/v1.0.0/logger-config"

        # This should not raise
        schema, metadata = crucible.find_schema(schema_id)

        # Verify schema content (it should be a dict for JSON schemas)
        assert isinstance(schema, dict)

        # Verify metadata
        assert metadata.id == schema_id
        assert metadata.category == "schemas"
        assert metadata.format == "json"  # Assuming standard format
        assert metadata.size is not None
        assert metadata.path.exists()

    def test_find_config_access(self):
        """Verify accessing configuration defaults."""
        config_id = "terminal/v1.0.0/terminal-overrides-defaults"

        config_data, metadata = crucible.find_config(config_id)

        assert isinstance(config_data, dict)
        assert metadata.id == config_id
        assert metadata.category == "config"

    def test_get_documentation_access(self):
        """Verify accessing documentation."""
        doc_id = "standards/observability/logging.md"

        content, metadata = crucible.get_doc(doc_id)

        assert isinstance(content, str)
        assert len(content) > 0
        assert metadata.id == doc_id
        assert metadata.category == "docs"
        assert metadata.format == "md"

    def test_crucible_version_access(self):
        """Verify accessing the Crucible version."""
        version_info = crucible.get_crucible_version()

        assert version_info.version is not None
        assert isinstance(version_info.version, str)
        # Ensure it looks like a version (e.g., has dots or is a date)
        assert "." in version_info.version or "-" in version_info.version

    def test_example_snippet_correctness(self):
        """Verify the corrected version of the user's snippet runs."""
        # 1. List available asset categories
        cats = crucible.list_categories()
        assert "schemas" in cats

        # 2. Find a specific schema
        schema, metadata = crucible.find_schema("observability/logging/v1.0.0/logger-config")
        # metadata.version does not exist, check id instead or parse it if needed
        assert "v1.0.0" in metadata.id

        # 3. Get configuration defaults
        config, meta = crucible.find_config("terminal/v1.0.0/terminal-overrides-defaults")
        assert config is not None
