"""Tests for config reload workflow."""

from unittest.mock import MagicMock, patch

import pytest

from pyfulmen.signals._reload import (
    ConfigReloader,
    get_config_reloader,
    register_shutdown_callback,
    reload_config,
)


class TestConfigReloader:
    """Test config reloader functionality."""

    def test_initialization(self):
        """Test config reloader initialization."""
        reloader = ConfigReloader()

        assert reloader._shutdown_callbacks == []
        assert reloader._logger is not None

    def test_register_shutdown_callback(self):
        """Test registering shutdown callbacks."""
        reloader = ConfigReloader()

        callback1 = MagicMock()
        callback2 = MagicMock()

        reloader.register_shutdown_callback(callback1)
        reloader.register_shutdown_callback(callback2)

        assert len(reloader._shutdown_callbacks) == 2
        assert reloader._shutdown_callbacks[0] == callback1
        assert reloader._shutdown_callbacks[1] == callback2

    @patch("pyfulmen.signals._reload.reload_identity")
    @patch("pyfulmen.signals._reload.get_identity")
    @patch("pyfulmen.signals._reload.create_loader_with_identity")
    def test_validate_new_config_success(self, mock_loader, mock_identity, mock_reload):
        """Test successful config validation."""
        # Setup mocks
        mock_identity.return_value = MagicMock(config_name="testapp", vendor="testvendor")
        mock_loader.return_value.load.return_value = {"test": "config"}

        reloader = ConfigReloader()

        # Should not raise exception
        reloader._validate_new_config()

        # Verify calls were made
        mock_reload.assert_called_once()
        mock_identity.assert_called_once()
        mock_loader.assert_called_once()

    @patch("pyfulmen.signals._reload.reload_identity")
    def test_validate_new_config_failure(self, mock_reload):
        """Test config validation failure."""
        # Setup mock to raise exception
        mock_reload.side_effect = Exception("Identity reload failed")

        reloader = ConfigReloader()

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Config validation failed"):
            reloader._validate_new_config()

    def test_execute_shutdown_callbacks(self):
        """Test execution of shutdown callbacks."""
        reloader = ConfigReloader()

        # Setup callbacks
        callback1 = MagicMock()
        callback2 = MagicMock(side_effect=Exception("Callback failed"))
        callback3 = MagicMock()

        reloader.register_shutdown_callback(callback1)
        reloader.register_shutdown_callback(callback2)
        reloader.register_shutdown_callback(callback3)

        # Execute callbacks
        reloader._execute_shutdown_callbacks()

        # All callbacks should be called
        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()

    @patch("pyfulmen.signals._reload.subprocess.Popen")
    @patch("pyfulmen.signals._reload.sys.exit")
    def test_restart_process_success(self, mock_exit, mock_popen):
        """Test successful process restart."""
        # Setup mocks
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        mock_exit.side_effect = SystemExit(0)

        reloader = ConfigReloader()

        # Should not return (calls sys.exit)
        with pytest.raises(SystemExit):
            reloader._restart_process()

        # Verify subprocess was called
        mock_popen.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch("pyfulmen.signals._reload.subprocess.Popen")
    def test_restart_process_failure(self, mock_popen):
        """Test process restart failure."""
        # Setup mock to raise exception
        mock_popen.side_effect = Exception("Subprocess failed")

        reloader = ConfigReloader()

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Process restart failed"):
            reloader._restart_process()


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_get_config_reloader(self):
        """Test getting global config reloader."""
        reloader1 = get_config_reloader()
        reloader2 = get_config_reloader()

        # Should return same instance
        assert reloader1 is reloader2

    @patch("pyfulmen.signals._reload._config_reloader")
    def test_register_shutdown_callback_global(self, mock_reloader):
        """Test global shutdown callback registration."""
        callback = MagicMock()

        register_shutdown_callback(callback)

        mock_reloader.register_shutdown_callback.assert_called_once_with(callback)

    @patch("pyfulmen.signals._reload._config_reloader")
    def test_reload_config_global(self, mock_reloader):
        """Test global config reload function."""
        reload_config()

        mock_reloader.reload_config.assert_called_once()
