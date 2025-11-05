"""Tests for the main signals module API."""

import signal as stdlib_signal
from unittest.mock import patch

import pytest

# Test the public API that should be available after import
import sys
sys.path.insert(0, 'src')

import pyfulmen.signals


class TestModuleImport:
    """Test module import and basic functionality."""

    def test_module_imports_successfully(self):
        """Test that the module imports without errors."""
        # This should not raise an exception
        assert pyfulmen.signals is not None

    def test_public_api_available(self):
        """Test that all public API functions are available."""
        # Check that expected functions are in the module
        assert hasattr(pyfulmen.signals, 'get_signals_version')
        assert hasattr(pyfulmen.signals, 'get_signal_metadata')
        assert hasattr(pyfulmen.signals, 'supports_signal')
        assert hasattr(pyfulmen.signals, 'get_module_info')

    def test_module_version(self):
        """Test module version is set correctly."""
        assert hasattr(pyfulmen.signals, '__version__')
        assert pyfulmen.signals.__version__ == "0.1.10"


class TestPublicAPI:
    """Test the public API functions."""

    def test_get_signals_version(self):
        """Test getting signals version information."""
        version = pyfulmen.signals.get_signals_version()
        
        assert isinstance(version, dict)
        assert "version" in version
        assert "description" in version
        assert "schema" in version
        assert version["version"] == "v1.0.0"

    def test_get_signal_metadata_existing(self):
        """Test getting metadata for existing signals."""
        metadata = pyfulmen.signals.get_signal_metadata("SIGTERM")
        
        assert metadata is not None
        assert metadata["name"] == "SIGTERM"
        assert metadata["id"] == "term"

    def test_get_signal_metadata_nonexistent(self):
        """Test getting metadata for nonexistent signals."""
        metadata = pyfulmen.signals.get_signal_metadata("SIGNONEXISTENT")
        assert metadata is None

    def test_supports_signal_interface(self):
        """Test supports_signal API matches Crucible v0.2.6 contract."""
        # Test with signal.Signals object (as required by spec)
        sig = stdlib_signal.SIGTERM
        assert isinstance(sig, stdlib_signal.Signals)
        
        result = pyfulmen.signals.supports_signal(sig)
        assert isinstance(result, bool)

    def test_supports_signal_sigterm(self):
        """Test supports_signal for SIGTERM."""
        result = pyfulmen.signals.supports_signal(stdlib_signal.SIGTERM)
        assert isinstance(result, bool)
        # SIGTERM should be supported on all platforms
        assert result is True

    def test_supports_signal_sigint(self):
        """Test supports_signal for SIGINT."""
        result = pyfulmen.signals.supports_signal(stdlib_signal.SIGINT)
        assert isinstance(result, bool)
        # SIGINT should be supported on all platforms
        assert result is True

    def test_get_module_info(self):
        """Test getting comprehensive module information."""
        info = pyfulmen.signals.get_module_info()
        
        assert isinstance(info, dict)
        assert "pyfulmen_version" in info
        assert "catalog_version" in info
        assert "python_version" in info
        assert "platform" in info
        
        assert info["pyfulmen_version"] == "0.1.10"
        assert isinstance(info["python_version"], str)
        assert isinstance(info["platform"], str)


class TestPlatformSpecificBehavior:
    """Test platform-specific behavior."""

    def test_supports_signal_on_current_platform(self):
        """Test signal support detection on current platform."""
        # Test a few signals that should have predictable behavior
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGTERM) is True
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGINT) is True

    @patch('pyfulmen.signals._platform._get_platform_name')
    def test_supports_signal_windows_behavior(self, mock_platform):
        """Test signal support detection on Windows."""
        mock_platform.return_value = "windows"
        
        # These should be supported on Windows
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGTERM) is True
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGINT) is True
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGQUIT) is True
        
        # These should NOT be supported on Windows
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGHUP) is False
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGPIPE) is False
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGALRM) is False
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGUSR1) is False
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGUSR2) is False

    @patch('pyfulmen.signals._platform._get_platform_name')
    def test_supports_signal_unix_behavior(self, mock_platform):
        """Test signal support detection on Unix."""
        mock_platform.return_value = "linux"
        
        # All standard signals should be supported on Unix
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGTERM) is True
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGINT) is True
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGHUP) is True
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGQUIT) is True
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGPIPE) is True
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGALRM) is True
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGUSR1) is True
        assert pyfulmen.signals.supports_signal(stdlib_signal.SIGUSR2) is True


class TestCatalogIntegration:
    """Test integration with catalog data."""

    def test_all_catalog_signals_accessible(self):
        """Test that all signals from catalog are accessible via API."""
        # Get all signal names from catalog
        from pyfulmen.signals._catalog import list_all_signals
        catalog_signals = list_all_signals()
        
        # Test that each can be looked up via public API
        for signal_name in catalog_signals:
            metadata = pyfulmen.signals.get_signal_metadata(signal_name)
            assert metadata is not None, f"Metadata not found for {signal_name}"
            assert metadata["name"] == signal_name

    def test_signal_metadata_consistency(self):
        """Test that signal metadata is consistent across APIs."""
        # Test SIGTERM specifically
        public_metadata = pyfulmen.signals.get_signal_metadata("SIGTERM")
        
        assert public_metadata is not None
        assert public_metadata["name"] == "SIGTERM"
        assert public_metadata["id"] == "term"
        assert "default_behavior" in public_metadata
        assert "description" in public_metadata


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_signal_name(self):
        """Test handling of invalid signal names."""
        metadata = pyfulmen.signals.get_signal_metadata("")
        assert metadata is None
        
        metadata = pyfulmen.signals.get_signal_metadata("INVALID")
        assert metadata is None
        
        metadata = pyfulmen.signals.get_signal_metadata("sigterm")  # Wrong case
        assert metadata is None

    def test_module_info_structure(self):
        """Test module info has expected structure."""
        info = pyfulmen.signals.get_module_info()
        
        # Should not raise any exceptions and have expected keys
        required_keys = ["pyfulmen_version", "catalog_version", "python_version", "platform"]
        for key in required_keys:
            assert key in info, f"Missing key in module info: {key}"
            assert info[key] is not None, f"None value for key: {key}"


class TestPerformanceRequirements:
    """Test performance-related requirements."""

    def test_import_performance(self):
        """Test that module import meets performance requirements."""
        import timeit
        
        # Test import time (should be < 5ms per requirements)
        import_time = timeit.timeit(
            "import sys; sys.path.insert(0, 'src'); import pyfulmen.signals",
            number=10
        )
        
        avg_time_per_import = import_time / 10
        assert avg_time_per_import < 0.005, f"Import too slow: {avg_time_per_import:.4f}s"

    def test_api_call_performance(self):
        """Test that API calls are reasonably fast."""
        import timeit
        
        # Test get_signals_version performance
        version_time = timeit.timeit(
            "get_signals_version()",
            number=1000,
            globals={"get_signals_version": pyfulmen.signals.get_signals_version}
        )
        
        avg_time_per_call = version_time / 1000
        assert avg_time_per_call < 0.001, f"API call too slow: {avg_time_per_call:.6f}s"