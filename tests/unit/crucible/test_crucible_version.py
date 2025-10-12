"""Tests for pyfulmen.crucible._version module."""

from pathlib import Path

from pyfulmen.crucible import get_crucible_info, get_crucible_metadata_path


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
