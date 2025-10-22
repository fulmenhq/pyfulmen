"""Tests for pyfulmen.crucible._version module."""

from pathlib import Path

from pyfulmen.crucible import get_crucible_info, get_crucible_metadata_path
from pyfulmen.crucible._version import get_crucible_version
from pyfulmen.crucible.models import CrucibleVersion


def test_get_crucible_metadata_path():
    """Test getting Crucible metadata directory path."""
    metadata_path = get_crucible_metadata_path()

    assert isinstance(metadata_path, Path)
    assert metadata_path.name == "metadata"
    assert metadata_path.parent.name == ".crucible"
    assert metadata_path.exists()


def test_get_crucible_info():
    """Test getting Crucible info dictionary."""
    info = get_crucible_info()

    assert "schemas_dir" in info
    assert "docs_dir" in info
    assert "config_dir" in info
    assert "metadata_dir" in info

    # All paths should contain 'crucible'
    assert "crucible" in info["schemas_dir"]
    assert "crucible" in info["docs_dir"]
    assert "crucible" in info["config_dir"]
    assert "crucible" in info["metadata_dir"]

    # metadata_dir should point to actual metadata location
    assert info["metadata_dir"].endswith(".crucible/metadata")


class TestGetCrucibleVersion:
    """Tests for get_crucible_version function."""

    def test_version_from_real_metadata(self):
        """Test parsing version from actual sync-keys.yaml."""
        version = get_crucible_version()

        assert isinstance(version, CrucibleVersion)
        assert version.version == "2025.10.0"
        assert version.commit == "unknown"
        assert version.synced_at is None

    def test_version_with_missing_commit_defaults_to_unknown(self):
        """Missing commit field should default to 'unknown'."""
        version = get_crucible_version()

        assert version.commit == "unknown"

    def test_version_with_missing_synced_at_defaults_to_none(self):
        """Missing syncedAt field should default to None."""
        version = get_crucible_version()

        assert version.synced_at is None

    def test_version_metadata_structure(self):
        """Verify version metadata has correct structure."""
        version = get_crucible_version()

        assert hasattr(version, "version")
        assert hasattr(version, "commit")
        assert hasattr(version, "synced_at")
        assert isinstance(version.version, str)
        assert isinstance(version.commit, str) or version.commit is None
        assert isinstance(version.synced_at, str) or version.synced_at is None
