"""Tests for pyfulmen.config.loader module."""

import tempfile
from pathlib import Path

from pyfulmen.config.loader import ConfigLoader, ConfigLoadResult


def test_config_loader_init():
    """Test ConfigLoader initialization."""
    loader = ConfigLoader()
    assert loader.app == "fulmen"
    assert isinstance(loader.user_config_dir, Path)
    assert "fulmen" in str(loader.user_config_dir)


def test_config_loader_custom_app():
    """Test ConfigLoader with custom app name."""
    loader = ConfigLoader(app="myapp", vendor="acme")
    assert loader.app == "myapp"
    assert loader.vendor == "acme"
    assert "acme" in str(loader.user_config_dir)


def test_load_crucible_defaults():
    """Test loading Crucible defaults (Layer 1)."""
    loader = ConfigLoader()

    # Load known config from Crucible
    result = loader.load_with_metadata("terminal/v1.0.0/terminal-overrides-defaults")
    assert isinstance(result, ConfigLoadResult)
    config = result.data

    assert isinstance(config, dict)
    # Should have terminal-related config
    assert len(config) > 0


def test_load_with_user_config():
    """Test loading with application-provided config (Layer 3)."""
    loader = ConfigLoader()

    user_config = {"custom": {"setting": "value"}}

    config = loader.load("terminal/v1.0.0/terminal-overrides-defaults", app_config=user_config)

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

        loader = ConfigLoader(app="testapp")
        loader.user_config_dir = user_config_dir

        # Layer 1: Crucible defaults
        # Layer 2: User overrides (user_layer: value: 2)
        # Layer 3: App config
        app_config = {"app_layer": {"value": 3}}

        result = loader.load_with_metadata(
            "terminal/v1.0.0/terminal-overrides-defaults", app_config=app_config
        )
        config = result.data

        # Should have all layers
        assert "user_layer" in config  # Layer 2
        assert "app_layer" in config  # Layer 3
        assert len(result.sources) == 3
        assert result.sources[0].layer == "defaults"
        assert result.sources[1].layer == "user"
        assert result.sources[2].layer == "application"


def test_user_override_with_yml(tmp_path):
    """Loader should pick up .yml overrides."""
    user_config_dir = tmp_path / "fulmen"
    override = user_config_dir / "terminal" / "v1.0.0" / "terminal-overrides-defaults.yml"
    override.parent.mkdir(parents=True)
    override.write_text("""test:\n  value: 1\n""")

    loader = ConfigLoader()
    loader.user_config_dir = user_config_dir

    result = loader.load_with_metadata("terminal/v1.0.0/terminal-overrides-defaults")
    assert result.data.get("test", {}).get("value") == 1
    assert result.sources[1].applied is True


def test_load_with_metadata_no_layers(tmp_path):
    """Metadata should reflect missing layers."""
    loader = ConfigLoader(app="app", vendor="acme")
    loader.user_config_dir = tmp_path / "empty"

    result = loader.load_with_metadata("nonexistent/config")
    assert result.data == {}
    assert len(result.sources) == 3
    assert not any(source.applied for source in result.sources)


class TestTelemetry:
    """Test telemetry instrumentation.

    Note: Current implementation creates independent MetricRegistry instances per call,
    so telemetry emission cannot be directly tested without module-level singleton helpers
    (per ADR-0008). These tests verify the code path executes without errors.

    Full telemetry testing will be added when module-level helpers are implemented.
    """

    def test_load_with_telemetry_enabled(self):
        """Verify load_with_metadata executes with telemetry without errors."""
        loader = ConfigLoader()
        result = loader.load_with_metadata("terminal/v1.0.0/terminal-overrides-defaults")

        # Verify operation succeeded
        assert isinstance(result.data, dict)
        assert len(result.sources) == 3

        # Telemetry is emitted to an internal registry instance.
        # Full assertion testing requires module-level singleton helpers per ADR-0008.

    def test_load_errors_counter_on_invalid_yaml(self, tmp_path):
        """Verify config_load_errors counter is emitted on YAML parse failure."""
        user_config_dir = tmp_path / "fulmen"
        override = user_config_dir / "test" / "config.yaml"
        override.parent.mkdir(parents=True)
        # Write invalid YAML (unclosed bracket)
        override.write_text("key: [invalid yaml")

        loader = ConfigLoader()
        loader.user_config_dir = user_config_dir

        # Should handle YAML error gracefully and continue
        result = loader.load_with_metadata("test/config")

        # Operation succeeds but without user layer applied
        assert isinstance(result.data, dict)
        # Counter is emitted but to independent registry instance.
        # Full metric assertion requires module-level helpers per ADR-0008.
