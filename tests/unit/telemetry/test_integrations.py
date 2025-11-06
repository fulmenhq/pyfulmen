"""Test telemetry integrations across PyFulmen modules."""

import time

from pyfulmen.error_handling._wrap import wrap
from pyfulmen.error_handling.models import PathfinderError
from pyfulmen.foundry.mime_detection import detect_mime_type
from pyfulmen.fulhash._hash import hash_bytes, hash_string
from pyfulmen.telemetry import clear_metrics, get_events


class TestFoundryTelemetry:
    """Test foundry module telemetry integration."""

    def setup_method(self):
        """Clear metrics before each test."""
        clear_metrics()

    def test_mime_detection_telemetry_json(self):
        """Test JSON detection emits telemetry."""
        data = b'{"key": "value"}'

        result = detect_mime_type(data)

        events = get_events()
        assert result is not None
        assert result.id == "json"

        # Should have detection counter and duration histogram
        metric_names = [event.name for event in events]
        assert "foundry_mime_detections_total_json" in metric_names
        assert "foundry_mime_detection_ms_json" in metric_names

    def test_mime_detection_telemetry_xml(self):
        """Test XML detection emits telemetry."""
        data = b'<?xml version="1.0"?><root></root>'

        result = detect_mime_type(data)

        events = get_events()
        assert result is not None
        assert result.id == "xml"

        metric_names = [event.name for event in events]
        assert "foundry_mime_detections_total_xml" in metric_names
        assert "foundry_mime_detection_ms_xml" in metric_names

    def test_mime_detection_telemetry_unknown(self):
        """Test unknown data emits telemetry."""
        data = b"\x00\x01\x02\xff\xfe"

        result = detect_mime_type(data)

        events = get_events()
        assert result is None

        metric_names = [event.name for event in events]
        assert "foundry_mime_detections_total_unknown" in metric_names
        assert "foundry_mime_detection_ms_unknown" in metric_names


class TestErrorHandlingTelemetry:
    """Test error handling module telemetry integration."""

    def setup_method(self):
        """Clear metrics before each test."""
        clear_metrics()

    def test_wrap_telemetry(self):
        """Test error wrap emits telemetry."""
        base_error = PathfinderError(code="TEST_ERROR", message="Test error")

        result = wrap(base_error, severity="high")

        events = get_events()
        assert result.code == "TEST_ERROR"
        assert result.severity == "high"

        # Should have wrap counter and duration histogram
        metric_names = [event.name for event in events]
        assert "error_handling_wraps_total" in metric_names
        assert "error_handling_wrap_ms" in metric_names


class TestFulhashTelemetry:
    """Test fulhash module telemetry integration."""

    def setup_method(self):
        """Clear metrics before each test."""
        clear_metrics()

    def test_hash_bytes_telemetry_xxh3(self):
        """Test hash_bytes with XXH3 emits telemetry."""
        data = b"Hello, World!"

        result = hash_bytes(data)

        events = get_events()
        assert result.algorithm.value == "xxh3-128"

        # Should have operation counter, bytes counter, and duration histogram
        metric_names = [event.name for event in events]
        assert "fulhash_operations_total_xxh3_128" in metric_names
        assert "fulhash_bytes_hashed_total" in metric_names
        assert "fulhash_operation_ms" in metric_names

    def test_hash_bytes_telemetry_sha256(self):
        """Test hash_bytes with SHA256 emits telemetry."""
        data = b"Hello, World!"

        from pyfulmen.fulhash.models import Algorithm

        result = hash_bytes(data, Algorithm.SHA256)

        events = get_events()
        assert result.algorithm.value == "sha256"

        metric_names = [event.name for event in events]
        assert "fulhash_operations_total_sha256" in metric_names
        assert "fulhash_bytes_hashed_total" in metric_names
        assert "fulhash_operation_ms" in metric_names

    def test_hash_string_telemetry(self):
        """Test hash_string emits telemetry."""
        text = "Hello, World!"

        result = hash_string(text)

        events = get_events()
        assert result.algorithm.value == "xxh3-128"

        # Should have string counter from hash_string and operation metrics from hash_bytes
        metric_names = [event.name for event in events]
        assert "fulhash_hash_string_total" in metric_names
        assert "fulhash_operations_total_xxh3_128" in metric_names
        assert "fulhash_bytes_hashed_total" in metric_names
        assert "fulhash_operation_ms" in metric_names

    def test_bytes_counter_value(self):
        """Test bytes counter records correct data size."""
        data = b"Hello, World!"  # 13 bytes

        hash_bytes(data)

        events = get_events()

        # Find bytes counter event
        bytes_events = [e for e in events if e.name == "fulhash_bytes_hashed_total"]
        assert len(bytes_events) == 1
        assert bytes_events[0].value == 13.0


class TestTelemetryPerformance:
    """Test telemetry doesn't significantly impact performance."""

    def setup_method(self):
        """Clear metrics before each test."""
        clear_metrics()

    def test_telemetry_overhead_minimal(self):
        """Test telemetry overhead is minimal."""
        data = b'{"key": "value"}'

        # Simple performance test - just verify telemetry doesn't crash
        start_time = time.perf_counter()
        for _ in range(100):
            detect_mime_type(data)
        with_telemetry_time = time.perf_counter() - start_time

        # Should complete without errors and in reasonable time
        assert with_telemetry_time < 1.0, f"Telemetry too slow: {with_telemetry_time:.3f}s"

        # Verify metrics were collected
        events = get_events()
        assert len(events) > 0, "No telemetry events collected"
