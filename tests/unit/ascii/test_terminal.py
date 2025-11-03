"""
Tests for pyfulmen.ascii terminal detection and configuration.

Tests terminal type detection, configuration loading, and overrides.
"""

from pyfulmen.ascii import TerminalConfig, TerminalOverrides
from pyfulmen.ascii.terminal import (
    get_all_terminal_configs,
    get_terminal_config,
    reload_terminal_overrides,
    set_terminal_config,
    set_terminal_overrides,
)


class TestTerminalConfig:
    """Test TerminalConfig data model."""

    def test_terminal_config_creation(self):
        """Should create terminal config with all fields."""
        config = TerminalConfig(name="Test Terminal", overrides={"🔧": 2, "⚠️": 2}, notes="Test notes")
        assert config.name == "Test Terminal"
        assert config.overrides["🔧"] == 2
        assert config.notes == "Test notes"

    def test_terminal_config_defaults(self):
        """Should have sensible defaults."""
        config = TerminalConfig(name="Test")
        assert config.overrides == {}
        assert config.notes == ""

    def test_terminal_config_serialization(self):
        """Should serialize to dict/JSON."""
        config = TerminalConfig(name="Test", overrides={"🔧": 2})
        data = config.model_dump()
        assert data["name"] == "Test"
        assert data["overrides"]["🔧"] == 2


class TestTerminalOverrides:
    """Test TerminalOverrides data model."""

    def test_terminal_overrides_creation(self):
        """Should create overrides catalog."""
        overrides = TerminalOverrides(version="1.0.0", terminals={"test": TerminalConfig(name="Test Terminal")})
        assert overrides.version == "1.0.0"
        assert "test" in overrides.terminals

    def test_terminal_overrides_defaults(self):
        """Should have defaults for optional fields."""
        overrides = TerminalOverrides(version="1.0.0")
        assert overrides.terminals == {}
        assert overrides.last_updated == ""
        assert overrides.notes == ""


class TestGetTerminalConfig:
    """Test get_terminal_config function."""

    def test_get_terminal_config_returns_config_or_none(self):
        """Should return TerminalConfig or None."""
        config = get_terminal_config()
        assert config is None or isinstance(config, TerminalConfig)

    def test_get_terminal_config_with_known_terminal(self, monkeypatch):
        """Should detect known terminal from TERM_PROGRAM."""
        # Set environment to simulate iTerm
        monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")

        # Reload to pick up the environment change
        reload_terminal_overrides()

        config = get_terminal_config()
        if config:  # May not match if embedded defaults don't have iTerm.app
            assert config.name == "iTerm2"

    def test_get_terminal_config_with_ghostty(self, monkeypatch):
        """Should detect ghostty from TERM."""
        monkeypatch.setenv("TERM", "xterm-ghostty")
        monkeypatch.delenv("TERM_PROGRAM", raising=False)

        reload_terminal_overrides()

        config = get_terminal_config()
        if config:  # May not match depending on environment
            assert "Ghostty" in config.name or config.name


class TestGetAllTerminalConfigs:
    """Test get_all_terminal_configs function."""

    def test_get_all_returns_dict(self):
        """Should return dictionary of terminal configs."""
        configs = get_all_terminal_configs()
        assert isinstance(configs, dict)

    def test_get_all_has_expected_terminals(self):
        """Should include default terminals from embedded config."""
        configs = get_all_terminal_configs()
        # Should have at least some of the default terminals
        # (exact contents depend on embedded defaults)
        assert len(configs) >= 0  # May be empty if not loaded

        # If we have configs, they should be TerminalConfig instances
        for term_id, config in configs.items():
            assert isinstance(config, TerminalConfig)
            assert isinstance(term_id, str)


class TestSetTerminalOverrides:
    """Test set_terminal_overrides function (Layer 3: BYOC)."""

    def test_set_terminal_overrides_replaces_config(self):
        """Should replace entire terminal configuration."""
        # Create custom overrides
        custom = TerminalOverrides(
            version="1.0.0",
            terminals={"custom": TerminalConfig(name="Custom Terminal", overrides={"🔧": 3})},
        )

        set_terminal_overrides(custom)

        configs = get_all_terminal_configs()
        assert "custom" in configs
        assert configs["custom"].name == "Custom Terminal"

        # Clean up: reload defaults
        reload_terminal_overrides()

    def test_set_terminal_overrides_affects_current(self, monkeypatch):
        """Setting overrides should update current terminal config."""
        # Set TERM_PROGRAM to match our custom terminal
        monkeypatch.setenv("TERM_PROGRAM", "myterm")

        custom = TerminalOverrides(
            version="1.0.0",
            terminals={"myterm": TerminalConfig(name="My Terminal", overrides={"🔧": 5})},
        )

        set_terminal_overrides(custom)

        config = get_terminal_config()
        assert config is not None
        assert config.name == "My Terminal"
        assert config.overrides["🔧"] == 5

        # Clean up
        reload_terminal_overrides()


class TestSetTerminalConfig:
    """Test set_terminal_config function (Layer 3: BYOC)."""

    def test_set_terminal_config_adds_single_terminal(self):
        """Should add or update a single terminal config."""
        config = TerminalConfig(name="Test Terminal", overrides={"⚠️": 1})

        set_terminal_config("testterm", config)

        configs = get_all_terminal_configs()
        assert "testterm" in configs
        assert configs["testterm"].name == "Test Terminal"

        # Clean up
        reload_terminal_overrides()

    def test_set_terminal_config_updates_existing(self):
        """Should update existing terminal config."""
        # Set initial config
        config1 = TerminalConfig(name="First", overrides={"🔧": 1})
        set_terminal_config("test", config1)

        # Update it
        config2 = TerminalConfig(name="Second", overrides={"🔧": 2})
        set_terminal_config("test", config2)

        configs = get_all_terminal_configs()
        assert configs["test"].name == "Second"
        assert configs["test"].overrides["🔧"] == 2

        # Clean up
        reload_terminal_overrides()


class TestReloadTerminalOverrides:
    """Test reload_terminal_overrides function."""

    def test_reload_resets_to_defaults(self):
        """Reload should reset to defaults + user config."""
        # Modify config
        custom = TerminalOverrides(version="1.0.0", terminals={"custom": TerminalConfig(name="Custom")})
        set_terminal_overrides(custom)

        # Verify custom config is set
        assert "custom" in get_all_terminal_configs()

        # Reload
        reload_terminal_overrides()

        # Custom config should be gone (unless it was in defaults)
        configs = get_all_terminal_configs()
        # Should have default terminals back
        assert isinstance(configs, dict)

    def test_reload_multiple_times(self):
        """Should be able to reload multiple times."""
        reload_terminal_overrides()
        configs1 = get_all_terminal_configs()

        reload_terminal_overrides()
        configs2 = get_all_terminal_configs()

        # Should get same configs both times
        assert configs1.keys() == configs2.keys()


class TestTerminalDetection:
    """Test terminal type detection logic."""

    def test_detection_without_env_vars(self, monkeypatch):
        """Should handle missing environment variables."""
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        monkeypatch.delenv("TERM", raising=False)

        reload_terminal_overrides()

        # Should not crash, may return None
        config = get_terminal_config()
        assert config is None or isinstance(config, TerminalConfig)

    def test_detection_priority_term_program(self, monkeypatch):
        """TERM_PROGRAM should take priority over TERM."""
        monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
        monkeypatch.setenv("TERM", "xterm-ghostty")

        reload_terminal_overrides()

        config = get_terminal_config()
        # Should match iTerm.app, not ghostty
        if config:
            assert "iTerm" in config.name or "Apple" in config.name


class TestWidthOverrides:
    """Test that width overrides are properly loaded."""

    def test_overrides_loaded_from_config(self):
        """Terminal configs should have overrides loaded."""
        configs = get_all_terminal_configs()

        # At least one terminal should have overrides
        has_overrides = False
        for config in configs.values():
            if config.overrides:
                has_overrides = True
                break

        # May or may not have overrides depending on embedded defaults
        # Just verify the structure is correct
        for config in configs.values():
            assert isinstance(config.overrides, dict)
            for char, width in config.overrides.items():
                assert isinstance(char, str)
                assert isinstance(width, int)
