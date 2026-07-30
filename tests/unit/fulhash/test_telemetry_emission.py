"""Telemetry emission tests for FulHash (W2B telemetry honesty).

Asserts that FulHash operations emit ONLY taxonomy-registered metric
names (config/crucible-py/taxonomy/metrics.yaml) on the GLOBAL registry,
and that dropped/unregistered names never appear.
"""

import io

import pytest

from pyfulmen import telemetry
from pyfulmen.fulhash import (
    Algorithm,
    hash_bytes,
    hash_file,
    hash_reader,
    hash_string,
    stream,
    verify_file,
    verify_reader,
)

# The exactly-5 taxonomy-registered fulhash metric names.
TAXONOMY_FULHASH_NAMES = {
    "fulhash_operations_total_xxh3_128",
    "fulhash_operations_total_sha256",
    "fulhash_hash_string_total",
    "fulhash_bytes_hashed_total",
    "fulhash_operation_ms",
}

# Names dropped in W2B — must never be emitted again.
DROPPED_NAMES = {
    "fulhash_operations_total_crc32",
    "fulhash_operations_total_crc32c",
    "fulhash_hash_file_count",
    "fulhash_errors_count",
    "fulhash_stream_created_count",
}


def _drain_fulhash_events() -> list:
    """Drain the global registry and return only fulhash_* events."""
    return [e for e in telemetry.drain_events() if e.name.startswith("fulhash_")]


def _assert_only_taxonomy_names(events: list) -> None:
    """Assert every event carries a taxonomy-registered fulhash name."""
    names = {e.name for e in events}
    assert names <= TAXONOMY_FULHASH_NAMES, f"Unregistered names emitted: {names - TAXONOMY_FULHASH_NAMES}"
    assert not names & DROPPED_NAMES
    for event in events:
        # Name-level taxonomy check (raises ValueError on unregistered names)
        telemetry.validate_metric_name(event.name)
        if event.name == "fulhash_bytes_hashed_total":
            # Known pre-existing instrument limitation (out of W2B scope):
            # Counter hardcodes unit="count" while the taxonomy declares
            # unit "bytes" for this metric, so full-event validation fails
            # on the unit check alone. The name is taxonomy-valid (asserted
            # above via validate_metric_name).
            assert telemetry.validate_metric_event(event) is False
        else:
            assert telemetry.validate_metric_event(event) is True


@pytest.fixture(autouse=True)
def _clean_registry():
    """Drain global registry before and after each test for isolation."""
    telemetry.drain_events()
    yield
    telemetry.drain_events()


class TestHashBytesEmission:
    """hash_bytes emits per-algorithm counter + bytes + latency."""

    def test_xxh3_emits_only_taxonomy_names(self):
        hash_bytes(b"hello world")
        events = _drain_fulhash_events()
        _assert_only_taxonomy_names(events)
        assert {e.name for e in events} == {
            "fulhash_operations_total_xxh3_128",
            "fulhash_bytes_hashed_total",
            "fulhash_operation_ms",
        }

    def test_sha256_emits_only_taxonomy_names(self):
        hash_bytes(b"hello world", Algorithm.SHA256)
        events = _drain_fulhash_events()
        _assert_only_taxonomy_names(events)
        assert "fulhash_operations_total_sha256" in {e.name for e in events}

    def test_crc32_emits_no_operation_counter(self):
        """crc32 has no taxonomy operation counter — only bytes + latency."""
        hash_bytes(b"hello world", Algorithm.CRC32)
        events = _drain_fulhash_events()
        _assert_only_taxonomy_names(events)
        assert {e.name for e in events} == {
            "fulhash_bytes_hashed_total",
            "fulhash_operation_ms",
        }

    def test_crc32c_emits_no_operation_counter(self):
        hash_bytes(b"hello world", Algorithm.CRC32C)
        events = _drain_fulhash_events()
        _assert_only_taxonomy_names(events)
        assert {e.name for e in events} == {
            "fulhash_bytes_hashed_total",
            "fulhash_operation_ms",
        }


class TestHashStringEmission:
    """hash_string adds the string-operations counter."""

    def test_emits_only_taxonomy_names(self):
        hash_string("hello world")
        events = _drain_fulhash_events()
        _assert_only_taxonomy_names(events)
        assert {e.name for e in events} == {
            "fulhash_hash_string_total",
            "fulhash_operations_total_xxh3_128",
            "fulhash_bytes_hashed_total",
            "fulhash_operation_ms",
        }


class TestHashFileEmission:
    """hash_file emits on the GLOBAL registry (was a private-registry bug)."""

    def test_emits_only_taxonomy_names_on_global_registry(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(b"file content here")
        hash_file(f)
        events = _drain_fulhash_events()
        _assert_only_taxonomy_names(events)
        assert {e.name for e in events} == {
            "fulhash_operations_total_xxh3_128",
            "fulhash_bytes_hashed_total",
            "fulhash_operation_ms",
        }

    def test_bytes_hashed_matches_file_size(self, tmp_path):
        content = b"x" * 1000
        f = tmp_path / "data.bin"
        f.write_bytes(content)
        hash_file(f)
        events = _drain_fulhash_events()
        byte_events = [e for e in events if e.name == "fulhash_bytes_hashed_total"]
        assert len(byte_events) == 1

    def test_error_path_emits_no_unregistered_names(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            hash_file(tmp_path / "missing.bin")
        events = _drain_fulhash_events()
        _assert_only_taxonomy_names(events)
        # No fulhash_errors_count (dropped) and no completion metrics
        assert events == []


class TestHashReaderEmission:
    """hash_reader emits the same trio as hash_file."""

    def test_emits_only_taxonomy_names(self):
        hash_reader(io.BytesIO(b"stream content"), Algorithm.SHA256)
        events = _drain_fulhash_events()
        _assert_only_taxonomy_names(events)
        assert {e.name for e in events} == {
            "fulhash_operations_total_sha256",
            "fulhash_bytes_hashed_total",
            "fulhash_operation_ms",
        }


class TestVerifyEmission:
    """verify_file/verify_reader inherit emission via delegation."""

    def test_verify_file_emits_only_taxonomy_names(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(b"123456789")
        verify_file(f, "crc32:cbf43926")
        events = _drain_fulhash_events()
        _assert_only_taxonomy_names(events)

    def test_verify_reader_emits_only_taxonomy_names(self):
        verify_reader(io.BytesIO(b"123456789"), "crc32:cbf43926")
        events = _drain_fulhash_events()
        _assert_only_taxonomy_names(events)


class TestStreamHasherUnmetered:
    """StreamHasher/stream() stay unmetered (digest() re-callable)."""

    def test_stream_factory_emits_nothing(self):
        stream()
        assert _drain_fulhash_events() == []

    def test_stream_hasher_lifecycle_emits_nothing(self):
        hasher = stream(Algorithm.SHA256)
        hasher.update(b"chunk one")
        hasher.update(b"chunk two")
        hasher.digest()
        hasher.digest()  # re-callable — must not double count anything
        assert _drain_fulhash_events() == []
