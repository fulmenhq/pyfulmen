"""Tests for pyfulmen.config.loader module."""

import tempfile
from pathlib import Path

from pyfulmen.config.loader import ConfigLoader


def test_config_loader_init():
    """Test ConfigLoader initialization."""
    loader = ConfigLoader()
    assert loader.app_name == "fulmen"
    assert isinstance(loader.user_config_dir, Path)
    assert "fulmen" in str(loader.user_config_dir).lower()


def test_config_loader_custom_app():
    """Test ConfigLoader with custom app name."""
    loader = ConfigLoader(app_name="myapp")
    assert loader.app_name == "myapp"
    assert "myapp" in str(loader.user_config_dir).lower()


def test_load_crucible_defaults():
    """Test loading Crucible defaults (Layer 1)."""
    loader = ConfigLoader()

    # Load known config from Crucible
    config = loader.load("terminal/v1.0.0/terminal-overrides-defaults")

    assert isinstance(config, dict)
    # Should have terminal-related config
    assert len(config) > 0


def test_load_with_user_config():
    """Test loading with application-provided config (Layer 3)."""
    loader = ConfigLoader()

    user_config = {"custom": {"setting": "value"}}

    config = loader.load("terminal/v1.0.0/terminal-overrides-defaults", user_config=user_config)

    # Should include user config
    assert "custom" in config
    assert config["custom"]["setting"] == "value"


def test_load_nonexistent_config():
    """Test loading non-existent config returns empty."""
    loader = ConfigLoader()

    config = loader.load("nonexistent/v1.0.0/fake-config")

    # Should return empty dict when no layers exist
    assert config == {}


def test_load_with_user_override():
    """Test loading with user override file (Layer 2)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock user config directory
        user_config_dir = Path(tmpdir) / "fulmen"
        user_config_dir.mkdir()

        # Create user override file
        override_path = user_config_dir / "terminal/v1.0.0/terminal-overrides-defaults.yaml"
        override_path.parent.mkdir(parents=True)
        override_path.write_text("ghostty:\n  enabled: false\n")

        # Mock the user_config_dir
        loader = ConfigLoader()
        loader.user_config_dir = user_config_dir

        config = loader.load("terminal/v1.0.0/terminal-overrides-defaults")

        # Should include user override
        assert "ghostty" in config
        assert config["ghostty"]["enabled"] is False


def test_three_layer_merge():
    """Test that all three layers are merged correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        user_config_dir = Path(tmpdir) / "testapp"
        user_config_dir.mkdir()

        # Create user override
        override_path = user_config_dir / "terminal/v1.0.0/terminal-overrides-defaults.yaml"
        override_path.parent.mkdir(parents=True)
        override_path.write_text("user_layer:\n  value: 2\n")

        loader = ConfigLoader(app_name="testapp")
        loader.user_config_dir = user_config_dir

        # Layer 1: Crucible defaults
        # Layer 2: User overrides (user_layer: value: 2)
        # Layer 3: App config
        app_config = {"app_layer": {"value": 3}}

        config = loader.load("terminal/v1.0.0/terminal-overrides-defaults", user_config=app_config)

        # Should have all layers
        assert "user_layer" in config  # Layer 2
        assert "app_layer" in config  # Layer 3
        # Layer 1 (Crucible defaults) should also be present
        assert len(config) > 2  # More than just our two test layers
