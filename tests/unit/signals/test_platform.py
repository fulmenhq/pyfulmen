"""Tests for platform detection and Windows fallback support."""

import signal as stdlib_signal
from unittest.mock import patch

import pytest

from pyfulmen.signals._platform import (
    supports_signal,
    get_signal_fallback_behavior,
    get_windows_event_mapping,
    get_platform_signal_number,
    list_supported_signals,
    list_unsupported_signals,
    get_platform_info,
    _get_platform_name,
)


class TestPlatformDetection:
    """Test platform detection and normalization."""

    def test_get_platform_name_darwin(self):
        """Test macOS platform detection."""
        with patch("sys.platform", "darwin"):
            assert _get_platform_name() == "darwin"

    def test_get_platform_name_linux(self):
        """Test Linux platform detection."""
        with patch("sys.platform", "linux"):
            assert _get_platform_name() == "linux"

    def test_get_platform_name_windows(self):
        """Test Windows platform detection."""
        with patch("sys.platform", "win32"):
            assert _get_platform_name() == "windows"

    def test_get_platform_name_freebsd(self):
        """Test FreeBSD platform detection."""
        with patch("sys.platform", "freebsd12"):
            assert _get_platform_name() == "freebsd"

    def test_get_platform_name_fallback(self):
        """Test fallback for unknown Unix platforms."""
        with patch("sys.platform", "aix"):
            assert _get_platform_name() == "unix"


class TestSignalSupport:
    """Test signal support detection."""

    def test_unix_signal_support(self):
        """Test Unix platforms support all signals."""
        with patch("pyfulmen.signals._platform._get_platform_name", return_value="linux"):
            # All standard signals should be supported on Unix
            assert supports_signal(stdlib_signal.SIGTERM)
            assert supports_signal(stdlib_signal.SIGINT)
            assert supports_signal(stdlib_signal.SIGHUP)
            assert supports_signal(stdlib_signal.SIGQUIT)
            assert supports_signal(stdlib_signal.SIGPIPE)
            assert supports_signal(stdlib_signal.SIGALRM)
            assert supports_signal(stdlib_signal.SIGUSR1)
            assert supports_signal(stdlib_signal.SIGUSR2)

    def test_windows_signal_support(self):
        """Test Windows limited signal support."""
        with patch("pyfulmen.signals._platform._get_platform_name", return_value="windows"):
            # Only these signals are supported on Windows
            assert supports_signal(stdlib_signal.SIGTERM)  # CTRL_CLOSE_EVENT
            assert supports_signal(stdlib_signal.SIGINT)   # CTRL_C_EVENT
            assert supports_signal(stdlib_signal.SIGQUIT)  # CTRL_BREAK_EVENT
            
            # These are not supported on Windows
            assert not supports_signal(stdlib_signal.SIGHUP)
            assert not supports_signal(stdlib_signal.SIGPIPE)
            assert not supports_signal(stdlib_signal.SIGALRM)
            assert not supports_signal(stdlib_signal.SIGUSR1)
            assert not supports_signal(stdlib_signal.SIGUSR2)

    def test_supports_signal_with_signal_object(self):
        """Test supports_signal accepts signal.Signals objects."""
        sig = stdlib_signal.SIGTERM
        assert isinstance(sig, stdlib_signal.Signals)
        assert supports_signal(sig)


class TestWindowsFallbacks:
    """Test Windows fallback behavior detection."""

    def test_supported_signal_no_fallback(self):
        """Test supported signals return None for fallback behavior."""
        with patch("pyfulmen.signals._platform._get_platform_name", return_value="windows"):
            # SIGTERM is supported on Windows, so no fallback
            fallback = get_signal_fallback_behavior("SIGTERM")
            assert fallback is None

    def test_unsupported_signal_has_fallback(self):
        """Test unsupported signals return fallback behavior."""
        with patch("pyfulmen.signals._platform._get_platform_name", return_value="windows"):
            # SIGHUP is not supported on Windows
            fallback = get_signal_fallback_behavior("SIGHUP")
            assert fallback is not None
            assert fallback["fallback_behavior"] == "http_admin_endpoint"
            assert "log_level" in fallback
            assert "operation_hint" in fallback

    def test_unknown_signal_no_fallback(self):
        """Test unknown signals return None."""
        fallback = get_signal_fallback_behavior("SIGUNKNOWN")
        assert fallback is None

    def test_windows_event_mapping(self):
        """Test Windows event mapping for supported signals."""
        # SIGTERM maps to CTRL_CLOSE_EVENT (2)
        assert get_windows_event_mapping("SIGTERM") == 2
        
        # SIGINT maps to CTRL_C_EVENT (0)
        assert get_windows_event_mapping("SIGINT") == 0
        
        # SIGQUIT maps to CTRL_BREAK_EVENT (1)
        assert get_windows_event_mapping("SIGQUIT") == 1
        
        # SIGHUP has no Windows mapping
        assert get_windows_event_mapping("SIGHUP") is None

    def test_platform_signal_numbers(self):
        """Test getting platform-specific signal numbers."""
        # These should return valid numbers on current platform
        term_num = get_platform_signal_number("SIGTERM")
        assert isinstance(term_num, int)
        assert term_num > 0
        
        int_num = get_platform_signal_number("SIGINT")
        assert isinstance(int_num, int)
        assert int_num > 0


class TestSignalListing:
    """Test signal listing functions."""

    def test_list_supported_signals_unix(self):
        """Test listing supported signals on Unix."""
        with patch("pyfulmen.signals._platform._get_platform_name", return_value="linux"):
            supported = list_supported_signals()
            
            assert isinstance(supported, list)
            assert len(supported) == 8  # All signals supported on Unix
            assert "SIGTERM" in supported
            assert "SIGINT" in supported
            assert "SIGHUP" in supported

    def test_list_supported_signals_windows(self):
        """Test listing supported signals on Windows."""
        with patch("pyfulmen.signals._platform._get_platform_name", return_value="windows"):
            supported = list_supported_signals()
            
            assert isinstance(supported, list)
            assert len(supported) == 3  # Only 3 signals supported on Windows
            assert "SIGTERM" in supported
            assert "SIGINT" in supported
            assert "SIGQUIT" in supported
            assert "SIGHUP" not in supported

    def test_list_unsupported_signals_unix(self):
        """Test listing unsupported signals on Unix."""
        with patch("pyfulmen.signals._platform._get_platform_name", return_value="linux"):
            unsupported = list_unsupported_signals()
            
            assert isinstance(unsupported, list)
            assert len(unsupported) == 0  # All signals supported on Unix

    def test_list_unsupported_signals_windows(self):
        """Test listing unsupported signals on Windows."""
        with patch("pyfulmen.signals._platform._get_platform_name", return_value="windows"):
            unsupported = list_unsupported_signals()
            
            assert isinstance(unsupported, list)
            assert len(unsupported) == 5  # 5 signals not supported on Windows
            assert "SIGHUP" in unsupported
            assert "SIGPIPE" in unsupported
            assert "SIGALRM" in unsupported
            assert "SIGUSR1" in unsupported
            assert "SIGUSR2" in unsupported


class TestPlatformInfo:
    """Test platform information gathering."""

    def test_get_platform_info_structure(self):
        """Test platform info structure."""
        info = get_platform_info()
        
        assert isinstance(info, dict)
        assert "platform" in info
        assert "python_platform" in info
        assert "supported_signals" in info
        assert "unsupported_signals" in info
        assert "total_signals" in info

    def test_get_platform_info_values(self):
        """Test platform info values are reasonable."""
        info = get_platform_info()
        
        assert info["platform"] in ["windows", "linux", "darwin", "freebsd", "unix"]
        assert isinstance(info["python_platform"], str)
        assert isinstance(info["supported_signals"], list)
        assert isinstance(info["unsupported_signals"], list)
        assert info["total_signals"] == 8
        assert len(info["supported_signals"]) + len(info["unsupported_signals"]) == 8

    @patch("pyfulmen.signals._platform._get_platform_name", return_value="windows")
    def test_get_platform_info_windows(self, mock_platform):
        """Test platform info on Windows."""
        info = get_platform_info()
        
        assert info["platform"] == "windows"
        assert len(info["supported_signals"]) == 3
        assert len(info["unsupported_signals"]) == 5

    @patch("pyfulmen.signals._platform._get_platform_name", return_value="linux")
    def test_get_platform_info_linux(self, mock_platform):
        """Test platform info on Linux."""
        info = get_platform_info()
        
        assert info["platform"] == "linux"
        assert len(info["supported_signals"]) == 8
        assert len(info["unsupported_signals"]) == 0


class TestFallbackBehaviorDetails:
    """Test detailed Windows fallback behavior."""

    def test_sighup_fallback_details(self):
        """Test SIGHUP fallback behavior details."""
        fallback = get_signal_fallback_behavior("SIGHUP")
        
        if fallback:  # Only test if fallback exists (Windows)
            assert fallback["fallback_behavior"] == "http_admin_endpoint"
            assert fallback["log_level"] == "INFO"
            assert "SIGHUP unavailable on Windows" in fallback["log_message"]
            assert "POST /admin/signal with signal=HUP" in fallback["operation_hint"]
            assert fallback["telemetry_event"] == "fulmen.signal.unsupported"
            
            tags = fallback["telemetry_tags"]
            assert tags["signal"] == "SIGHUP"
            assert tags["platform"] == "windows"
            assert tags["fallback_behavior"] == "http_admin_endpoint"

    def test_sigpipe_fallback_details(self):
        """Test SIGPIPE fallback behavior details."""
        fallback = get_signal_fallback_behavior("SIGPIPE")
        
        if fallback:  # Only test if fallback exists (Windows)
            assert fallback["fallback_behavior"] == "exception_handling"
            assert fallback["log_level"] == "INFO"
            assert "BrokenPipeError" in fallback["operation_hint"]
            assert fallback["telemetry_event"] == "fulmen.signal.unsupported"

    def test_sigalrm_fallback_details(self):
        """Test SIGALRM fallback behavior details."""
        fallback = get_signal_fallback_behavior("SIGALRM")
        
        if fallback:  # Only test if fallback exists (Windows)
            assert fallback["fallback_behavior"] == "timer_api"
            assert fallback["log_level"] == "INFO"
            assert "threading.Timer" in fallback["operation_hint"]
            assert fallback["telemetry_event"] == "fulmen.signal.unsupported"