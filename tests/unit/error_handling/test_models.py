"""
Tests for error_handling.models

Covers PathfinderError and FulmenError data models.
"""

from datetime import UTC, datetime

import pytest

from pyfulmen.error_handling.models import FulmenError, PathfinderError, _map_severity_level


class TestPathfinderError:
    """Tests for PathfinderError base model."""

    def test_minimal_error_creation(self):
        """Test creating error with required fields only."""
        err = PathfinderError(code="TEST_ERROR", message="Test message")

        assert err.code == "TEST_ERROR"
        assert err.message == "Test message"
        assert err.details is None
        assert err.path is None
        assert err.timestamp is not None  # Auto-generated

    def test_timestamp_auto_generated(self):
        """Test timestamp is auto-generated if not provided."""
        before = datetime.now(UTC)
        err = PathfinderError(code="TEST", message="Test")
        after = datetime.now(UTC)

        assert before <= err.timestamp <= after

    def test_timestamp_preserved_when_provided(self):
        """Test explicit timestamp is preserved."""
        ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        err = PathfinderError(code="TEST", message="Test", timestamp=ts)

        assert err.timestamp == ts

    def test_all_fields_populated(self):
        """Test error with all optional fields."""
        ts = datetime.now(UTC)
        err = PathfinderError(
            code="CONFIG_INVALID",
            message="Config load failed",
            details={"file": "config.yaml", "line": 10},
            path="/app/config.yaml",
            timestamp=ts,
        )

        assert err.code == "CONFIG_INVALID"
        assert err.message == "Config load failed"
        assert err.details == {"file": "config.yaml", "line": 10}
        assert err.path == "/app/config.yaml"
        assert err.timestamp == ts

    def test_model_serialization(self):
        """Test serialization to dict."""
        err = PathfinderError(code="TEST", message="Test message")
        data = err.model_dump()

        assert data["code"] == "TEST"
        assert data["message"] == "Test message"
        assert "timestamp" in data


class TestFulmenError:
    """Tests for FulmenError extended model."""

    def test_minimal_creation(self):
        """Test creating FulmenError with required fields only."""
        ts = datetime.now(UTC)
        err = FulmenError(code="TEST", message="Test", timestamp=ts)

        assert err.code == "TEST"
        assert err.message == "Test"
        assert err.timestamp == ts
        assert err.severity is None
        assert err.correlation_id is None

    def test_severity_level_auto_mapped(self):
        """Test severity_level is auto-mapped from severity."""
        ts = datetime.now(UTC)
        err = FulmenError(code="TEST", message="Test", timestamp=ts, severity="high")

        assert err.severity == "high"
        assert err.severity_level == 3

    def test_explicit_severity_level_preserved(self):
        """Test explicit severity_level is not overwritten."""
        ts = datetime.now(UTC)
        err = FulmenError(
            code="TEST", message="Test", timestamp=ts, severity="high", severity_level=99
        )

        assert err.severity_level == 99  # Explicit value preserved

    def test_all_telemetry_fields(self):
        """Test FulmenError with all telemetry fields."""
        ts = datetime.now(UTC)
        err = FulmenError(
            code="PATH_TRAVERSAL",
            message="Invalid path",
            timestamp=ts,
            severity="critical",
            severity_level=4,
            correlation_id="req-abc123",
            trace_id="trace-xyz",
            exit_code=1,
            context={"path": "/etc/passwd", "user": "attacker"},
            original={"type": "ValueError", "message": "Invalid input"},
        )

        assert err.severity == "critical"
        assert err.severity_level == 4
        assert err.correlation_id == "req-abc123"
        assert err.trace_id == "trace-xyz"
        assert err.exit_code == 1
        assert err.context == {"path": "/etc/passwd", "user": "attacker"}
        assert err.original == {"type": "ValueError", "message": "Invalid input"}

    def test_original_as_string(self):
        """Test original field accepts string."""
        ts = datetime.now(UTC)
        err = FulmenError(
            code="TEST", message="Test", timestamp=ts, original="Traceback string here"
        )

        assert err.original == "Traceback string here"


class TestSeverityMapping:
    """Tests for severity level mapping."""

    def test_info_maps_to_zero(self):
        """Test 'info' severity maps to level 0."""
        assert _map_severity_level("info") == 0

    def test_low_maps_to_one(self):
        """Test 'low' severity maps to level 1."""
        assert _map_severity_level("low") == 1

    def test_medium_maps_to_two(self):
        """Test 'medium' severity maps to level 2."""
        assert _map_severity_level("medium") == 2

    def test_high_maps_to_three(self):
        """Test 'high' severity maps to level 3."""
        assert _map_severity_level("high") == 3

    def test_critical_maps_to_four(self):
        """Test 'critical' severity maps to level 4."""
        assert _map_severity_level("critical") == 4

    def test_case_insensitive_mapping(self):
        """Test severity mapping is case-insensitive."""
        assert _map_severity_level("HIGH") == 3
        assert _map_severity_level("CriTiCaL") == 4

    def test_invalid_severity_raises_error(self):
        """Test invalid severity name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid severity 'unknown'"):
            _map_severity_level("unknown")

    def test_empty_severity_raises_error(self):
        """Test empty severity raises ValueError."""
        with pytest.raises(ValueError):
            _map_severity_level("")
