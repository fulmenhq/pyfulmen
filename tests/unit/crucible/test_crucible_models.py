"""Tests for Crucible data models."""

from pathlib import Path

import pytest

from pyfulmen.crucible.models import AssetMetadata, CrucibleVersion


class TestAssetMetadata:
    """Tests for AssetMetadata dataclass."""

    def test_basic_asset_metadata(self):
        """Create AssetMetadata with required fields only."""
        asset = AssetMetadata(
            id="observability/logging/v1.0.0/logger-config",
            category="schemas",
            path=Path("/path/to/schema.json"),
        )
        assert asset.id == "observability/logging/v1.0.0/logger-config"
        assert asset.category == "schemas"
        assert asset.path == Path("/path/to/schema.json")
        assert asset.description is None
        assert asset.format is None
        assert asset.size is None
        assert asset.modified is None
        assert asset.checksum is None

    def test_asset_metadata_with_all_fields(self):
        """Create AssetMetadata with all fields populated."""
        asset = AssetMetadata(
            id="standards/observability/logging.md",
            category="docs",
            path=Path("/path/to/doc.md"),
            description="Logging observability standard",
            format="md",
            size=2048,
            modified="2025-10-20T15:30:00Z",
            checksum="abc123def456",
        )
        assert asset.id == "standards/observability/logging.md"
        assert asset.category == "docs"
        assert asset.path == Path("/path/to/doc.md")
        assert asset.description == "Logging observability standard"
        assert asset.format == "md"
        assert asset.size == 2048
        assert asset.modified == "2025-10-20T15:30:00Z"
        assert asset.checksum == "abc123def456"

    def test_asset_metadata_is_frozen(self):
        """AssetMetadata instances are immutable."""
        asset = AssetMetadata(
            id="test/asset",
            category="schemas",
            path=Path("/path"),
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            asset.id = "modified"

    def test_asset_metadata_equality(self):
        """AssetMetadata instances with same values are equal."""
        asset1 = AssetMetadata(
            id="test/asset",
            category="schemas",
            path=Path("/path"),
        )
        asset2 = AssetMetadata(
            id="test/asset",
            category="schemas",
            path=Path("/path"),
        )
        assert asset1 == asset2

    def test_asset_metadata_hash(self):
        """AssetMetadata instances are hashable (frozen)."""
        asset = AssetMetadata(
            id="test/asset",
            category="schemas",
            path=Path("/path"),
        )
        # Should not raise
        hash(asset)
        # Can use in set
        assets_set = {asset}
        assert asset in assets_set

    def test_asset_metadata_with_new_fields(self):
        """AssetMetadata supports new format, size, modified fields."""
        asset = AssetMetadata(
            id="observability/logging/v1.0.0/logger-config",
            category="schemas",
            path=Path("/path/to/schema.json"),
            format="json",
            size=1024,
            modified="2025-10-20T18:42:11Z",
        )
        assert asset.format == "json"
        assert asset.size == 1024
        assert asset.modified == "2025-10-20T18:42:11Z"

    def test_asset_metadata_partial_new_fields(self):
        """AssetMetadata allows partial population of new fields."""
        asset = AssetMetadata(
            id="test/asset",
            category="schemas",
            path=Path("/path"),
            format="yaml",
        )
        assert asset.format == "yaml"
        assert asset.size is None
        assert asset.modified is None

    def test_asset_metadata_ordering_with_new_fields(self):
        """AssetMetadata ordering remains stable with new fields."""
        assets = [
            AssetMetadata(
                id="z/asset",
                category="schemas",
                path=Path("/z"),
                format="json",
                size=100,
            ),
            AssetMetadata(
                id="a/asset",
                category="schemas",
                path=Path("/a"),
                format="yaml",
                size=200,
            ),
        ]
        sorted_assets = sorted(assets, key=lambda a: a.id)
        assert sorted_assets[0].id == "a/asset"
        assert sorted_assets[1].id == "z/asset"


class TestCrucibleVersion:
    """Tests for CrucibleVersion dataclass."""

    def test_basic_crucible_version(self):
        """Create CrucibleVersion with version only."""
        version = CrucibleVersion(version="2025.10.0")
        assert version.version == "2025.10.0"
        assert version.commit is None
        assert version.synced_at is None

    def test_crucible_version_with_all_fields(self):
        """Create CrucibleVersion with all fields populated."""
        version = CrucibleVersion(
            version="2025.10.0",
            commit="abc123def456",
            synced_at="2025-10-20T18:42:11Z",
        )
        assert version.version == "2025.10.0"
        assert version.commit == "abc123def456"
        assert version.synced_at == "2025-10-20T18:42:11Z"

    def test_crucible_version_is_frozen(self):
        """CrucibleVersion instances are immutable."""
        version = CrucibleVersion(version="2025.10.0")
        with pytest.raises(Exception):  # FrozenInstanceError
            version.version = "2025.11.0"

    def test_crucible_version_equality(self):
        """CrucibleVersion instances with same values are equal."""
        version1 = CrucibleVersion(
            version="2025.10.0",
            commit="abc123",
            synced_at="2025-10-20T18:42:11Z",
        )
        version2 = CrucibleVersion(
            version="2025.10.0",
            commit="abc123",
            synced_at="2025-10-20T18:42:11Z",
        )
        assert version1 == version2

    def test_crucible_version_hash(self):
        """CrucibleVersion instances are hashable (frozen)."""
        version = CrucibleVersion(version="2025.10.0")
        # Should not raise
        hash(version)
        # Can use in set
        versions_set = {version}
        assert version in versions_set

    def test_crucible_version_string_representation(self):
        """CrucibleVersion has readable string representation."""
        version = CrucibleVersion(
            version="2025.10.0",
            commit="abc123",
            synced_at="2025-10-20T18:42:11Z",
        )
        assert "2025.10.0" in str(version)

    def test_crucible_version_with_unknown_commit(self):
        """CrucibleVersion handles 'unknown' commit gracefully."""
        version = CrucibleVersion(
            version="2025.10.0",
            commit="unknown",
            synced_at=None,
        )
        assert version.commit == "unknown"
        assert version.synced_at is None

    def test_crucible_version_field_order(self):
        """CrucibleVersion field order matches spec: version, commit, synced_at."""
        version = CrucibleVersion(
            version="2025.10.0",
            commit="abc123",
            synced_at="2025-10-20T18:42:11Z",
        )
        assert version.version == "2025.10.0"
        assert version.commit == "abc123"
        assert version.synced_at == "2025-10-20T18:42:11Z"
