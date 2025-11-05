"""Tests for signal catalog loading and metadata management."""

import pytest
from pathlib import Path

from pyfulmen.signals._catalog import (
    get_signals_version,
    get_signal_metadata,
    list_all_signals,
    get_signal_by_id,
    _load_catalog,
    _get_catalog_path,
    _get_schema_path,
)


class TestCatalogLoading:
    """Test catalog loading and validation."""

    def test_load_catalog_success(self):
        """Test successful catalog loading."""
        catalog = _load_catalog()
        
        assert catalog is not None
        assert "signals" in catalog
        assert "behaviors" in catalog
        assert "os_mappings" in catalog
        assert "platform_support" in catalog

    def test_catalog_has_eight_signals(self):
        """Test catalog contains exactly 8 standard signals."""
        catalog = _load_catalog()
        signals = catalog["signals"]
        
        assert len(signals) == 8
        signal_ids = [s["id"] for s in signals]
        expected_ids = ["term", "int", "hup", "quit", "pipe", "alrm", "usr1", "usr2"]
        assert signal_ids == expected_ids

    def test_get_signals_version(self):
        """Test version information retrieval."""
        version = get_signals_version()
        
        assert isinstance(version, dict)
        assert "version" in version
        assert "description" in version
        assert "schema" in version
        assert version["version"] == "v1.0.0"

    def test_list_all_signals(self):
        """Test listing all signal names."""
        signals = list_all_signals()
        
        assert isinstance(signals, list)
        assert len(signals) == 8
        expected_signals = [
            "SIGTERM", "SIGINT", "SIGHUP", "SIGQUIT",
            "SIGPIPE", "SIGALRM", "SIGUSR1", "SIGUSR2"
        ]
        assert signals == expected_signals

    def test_catalog_path_exists(self):
        """Test catalog path points to existing file."""
        catalog_path = _get_catalog_path()
        assert catalog_path.exists()
        assert catalog_path.is_file()
        assert catalog_path.name == "signals.yaml"

    def test_schema_path_exists(self):
        """Test schema path points to existing file."""
        schema_path = _get_schema_path()
        assert schema_path.exists()
        assert schema_path.is_file()
        assert schema_path.name == "signals.schema.json"


class TestSignalMetadata:
    """Test signal metadata lookup functions."""

    def test_get_signal_metadata_by_name(self):
        """Test getting metadata by signal name."""
        metadata = get_signal_metadata("SIGTERM")
        
        assert metadata is not None
        assert metadata["name"] == "SIGTERM"
        assert metadata["id"] == "term"
        assert metadata["description"] == "Graceful termination signal"
        assert "default_behavior" in metadata
        assert "exit_code" in metadata

    def test_get_signal_metadata_unknown(self):
        """Test getting metadata for unknown signal."""
        metadata = get_signal_metadata("SIGUNKNOWN")
        assert metadata is None

    def test_get_signal_by_id(self):
        """Test getting metadata by signal ID."""
        metadata = get_signal_by_id("term")
        
        assert metadata is not None
        assert metadata["id"] == "term"
        assert metadata["name"] == "SIGTERM"

    def test_get_signal_by_unknown_id(self):
        """Test getting metadata by unknown ID."""
        metadata = get_signal_by_id("unknown")
        assert metadata is None

    def test_sigint_double_tap_metadata(self):
        """Test SIGINT has double-tap configuration."""
        metadata = get_signal_metadata("SIGINT")
        
        assert metadata is not None
        assert metadata["default_behavior"] == "graceful_shutdown_with_double_tap"
        assert "double_tap_window_seconds" in metadata
        assert "double_tap_message" in metadata
        assert metadata["double_tap_window_seconds"] == 2

    def test_sighup_reload_metadata(self):
        """Test SIGHUP has reload configuration."""
        metadata = get_signal_metadata("SIGHUP")
        
        assert metadata is not None
        assert metadata["default_behavior"] == "reload_via_restart"
        assert "validation_required" in metadata
        assert metadata["validation_required"] is True
        assert "windows_fallback" in metadata

    def test_windows_fallback_metadata(self):
        """Test Windows fallback metadata structure."""
        sighup_metadata = get_signal_metadata("SIGHUP")
        fallback = sighup_metadata["windows_fallback"]
        
        assert fallback["fallback_behavior"] == "http_admin_endpoint"
        assert "log_level" in fallback
        assert "log_message" in fallback
        assert "log_template" in fallback
        assert "operation_hint" in fallback
        assert "telemetry_event" in fallback
        assert "telemetry_tags" in fallback

    def test_all_signals_have_required_fields(self):
        """Test all signals have required metadata fields."""
        signals = list_all_signals()
        required_fields = ["id", "name", "description", "default_behavior"]
        
        for signal_name in signals:
            metadata = get_signal_metadata(signal_name)
            assert metadata is not None, f"Missing metadata for {signal_name}"
            
            for field in required_fields:
                assert field in metadata, f"Signal {signal_name} missing field {field}"


class TestCatalogValidation:
    """Test catalog validation logic."""

    def test_catalog_structure_validation(self):
        """Test catalog passes structural validation."""
        # This is implicitly tested by successful loading in _load_catalog()
        catalog = _load_catalog()
        
        # Verify required top-level sections
        required_sections = ["signals", "behaviors", "os_mappings", "platform_support"]
        for section in required_sections:
            assert section in catalog, f"Missing section: {section}"

    def test_signal_structure_validation(self):
        """Test individual signal structure validation."""
        catalog = _load_catalog()
        signals = catalog["signals"]
        
        for signal in signals:
            # Each signal should have required fields
            required_fields = ["id", "name", "description", "default_behavior"]
            for field in required_fields:
                assert field in signal, f"Signal missing {field}: {signal}"
            
            # Name should be a valid signal name
            assert signal["name"].startswith("SIG"), f"Invalid signal name: {signal['name']}"