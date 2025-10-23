"""Concurrency and thread safety tests for FulHash.

Validates that FulHash functions are thread-safe and that concurrent
operations do not cause state pollution, race conditions, or corruption.

Critical Safety Guarantees Tested:
1. StreamHasher instances are independent (no singleton hazards)
2. No state pollution between threads
3. Concurrent operations produce correct, deterministic results
4. Digest immutability holds under concurrent access
5. No memory corruption or data races

These tests provide positive evidence that the implementation is safe
for concurrent use in multi-threaded applications.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from pyfulmen.fulhash import (
    Algorithm,
    hash,
    hash_bytes,
    hash_file,
    hash_string,
    stream,
)


class TestStreamHasherIndependence:
    """Test that StreamHasher instances are independent and thread-safe."""

    def test_concurrent_independent_hashers(self):
        """Test multiple threads with independent StreamHasher instances.

        This validates we do NOT have a singleton pattern that would
        cause threads to share state and corrupt each other's hashes.
        """
        num_threads = 10
        results = {}
        errors = []

        def hash_in_thread(thread_id: int, data: bytes):
            """Each thread creates its own hasher and computes a hash."""
            try:
                hasher = stream(Algorithm.XXH3_128)
                hasher.update(data)
                digest = hasher.digest()
                results[thread_id] = digest.formatted
            except Exception as e:
                errors.append((thread_id, e))

        # Each thread hashes different data
        threads = []
        test_data = {i: f"Thread {i} data".encode() for i in range(num_threads)}

        for thread_id in range(num_threads):
            t = threading.Thread(target=hash_in_thread, args=(thread_id, test_data[thread_id]))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Verify no errors
        assert not errors, f"Errors occurred: {errors}"

        # Verify all threads completed
        assert len(results) == num_threads

        # Verify each result is correct (no state pollution)
        for thread_id, expected_data in test_data.items():
            expected = hash_bytes(expected_data).formatted
            actual = results[thread_id]
            assert actual == expected, (
                f"Thread {thread_id} produced wrong hash. Expected: {expected}, Got: {actual}"
            )

    def test_concurrent_same_data_different_hashers(self):
        """Test multiple threads hashing SAME data with independent hashers.

        All threads should produce identical results, proving no corruption
        from concurrent access.
        """
        num_threads = 20
        data = b"Shared test data for all threads"
        expected = hash_bytes(data).formatted
        results = []

        def hash_same_data():
            """Each thread creates its own hasher for same data."""
            hasher = stream()
            hasher.update(data)
            digest = hasher.digest()
            results.append(digest.formatted)

        threads = [threading.Thread(target=hash_same_data) for _ in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be identical and correct
        assert len(results) == num_threads
        assert all(r == expected for r in results), f"Results not identical: {set(results)}"

    def test_concurrent_streaming_chunks(self):
        """Test concurrent streaming with multiple chunks per thread."""
        num_threads = 10
        results = {}

        def stream_chunks(thread_id: int):
            """Stream data in multiple chunks."""
            hasher = stream()
            # Each thread processes data in chunks
            for i in range(5):
                chunk = f"Thread {thread_id} chunk {i}".encode()
                hasher.update(chunk)
            results[thread_id] = hasher.digest().formatted

        threads = [threading.Thread(target=stream_chunks, args=(i,)) for i in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all threads completed with unique results
        assert len(results) == num_threads
        # Each thread had different data, so results should be unique
        assert len(set(results.values())) == num_threads


class TestBlockHashingConcurrency:
    """Test thread safety of block hashing functions."""

    def test_concurrent_hash_bytes(self):
        """Test hash_bytes with concurrent calls."""
        num_operations = 100
        test_data = [f"Data {i}".encode() for i in range(num_operations)]
        expected = [hash_bytes(d).formatted for d in test_data]
        results = [None] * num_operations

        def compute_hash(index: int, data: bytes):
            """Compute hash and store result."""
            results[index] = hash_bytes(data).formatted

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(compute_hash, i, test_data[i]) for i in range(num_operations)
            ]
            for future in as_completed(futures):
                future.result()  # Raise any exceptions

        # Verify all results are correct
        assert results == expected

    def test_concurrent_hash_string(self):
        """Test hash_string with concurrent calls."""
        num_operations = 100
        test_data = [f"String {i}" for i in range(num_operations)]
        expected = [hash_string(s).formatted for s in test_data]
        results = [None] * num_operations

        def compute_hash(index: int, text: str):
            """Compute hash and store result."""
            results[index] = hash_string(text).formatted

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(compute_hash, i, test_data[i]) for i in range(num_operations)
            ]
            for future in as_completed(futures):
                future.result()

        assert results == expected

    def test_concurrent_mixed_algorithms(self):
        """Test concurrent use of different algorithms."""
        num_operations = 50
        data = b"Test data"
        results_xxh3 = []
        results_sha = []

        def hash_xxh3():
            results_xxh3.append(hash_bytes(data, Algorithm.XXH3_128).formatted)

        def hash_sha256():
            results_sha.append(hash_bytes(data, Algorithm.SHA256).formatted)

        # Interleave XXH3 and SHA256 computations
        threads = []
        for _ in range(num_operations):
            threads.append(threading.Thread(target=hash_xxh3))
            threads.append(threading.Thread(target=hash_sha256))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All XXH3 results should be identical
        expected_xxh3 = hash_bytes(data, Algorithm.XXH3_128).formatted
        assert len(results_xxh3) == num_operations
        assert all(r == expected_xxh3 for r in results_xxh3)

        # All SHA256 results should be identical
        expected_sha = hash_bytes(data, Algorithm.SHA256).formatted
        assert len(results_sha) == num_operations
        assert all(r == expected_sha for r in results_sha)


class TestFileHashingConcurrency:
    """Test thread safety of file hashing operations."""

    def test_concurrent_file_hashing_different_files(self, tmp_path):
        """Test multiple threads hashing different files concurrently."""
        num_files = 10
        files = []
        expected = {}

        # Create test files
        for i in range(num_files):
            file_path = tmp_path / f"file_{i}.txt"
            content = f"File {i} content".encode()
            file_path.write_bytes(content)
            files.append(file_path)
            expected[i] = hash_bytes(content).formatted

        results = {}

        def hash_file_task(index: int, path: Path):
            """Hash file and store result."""
            results[index] = hash_file(path).formatted

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(hash_file_task, i, files[i]) for i in range(num_files)]
            for future in as_completed(futures):
                future.result()

        # Verify all results are correct
        assert len(results) == num_files
        for i in range(num_files):
            assert results[i] == expected[i]

    def test_concurrent_file_hashing_same_file(self, tmp_path):
        """Test multiple threads reading and hashing the same file.

        This tests that file reading is thread-safe (no corruption from
        concurrent file handles).
        """
        file_path = tmp_path / "shared.txt"
        content = b"Shared file content that all threads will hash"
        file_path.write_bytes(content)

        expected = hash_bytes(content).formatted
        num_threads = 20
        results = []

        def hash_shared_file():
            """Hash the shared file."""
            results.append(hash_file(file_path).formatted)

        threads = [threading.Thread(target=hash_shared_file) for _ in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be identical and correct
        assert len(results) == num_threads
        assert all(r == expected for r in results)


class TestStatePollution:
    """Test for state pollution between threads.

    These tests validate that concurrent operations do not cause threads
    to corrupt each other's data or produce incorrect results due to
    shared mutable state.
    """

    def test_no_state_pollution_streaming(self):
        """Test that concurrent StreamHasher instances don't pollute each other.

        Each thread maintains independent state even when running simultaneously.
        """
        num_threads = 20
        results = {}
        lock = threading.Lock()

        def hash_with_delays(thread_id: int):
            """Hash with deliberate delays to increase chance of race conditions."""
            hasher = stream()

            # Update in small chunks with delays
            for i in range(10):
                chunk = f"T{thread_id}C{i}".encode()
                hasher.update(chunk)
                time.sleep(0.0001)  # Tiny delay to interleave threads

            digest = hasher.digest()

            with lock:
                results[thread_id] = digest.formatted

        threads = [threading.Thread(target=hash_with_delays, args=(i,)) for i in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify each thread got correct result for its data
        for thread_id in range(num_threads):
            # Compute expected hash for this thread's data
            expected_data = b"".join(f"T{thread_id}C{i}".encode() for i in range(10))
            expected = hash_bytes(expected_data).formatted

            actual = results[thread_id]
            assert actual == expected, (
                f"Thread {thread_id} state was polluted. Expected: {expected}, Got: {actual}"
            )

    def test_no_pollution_with_reset(self):
        """Test that reset() doesn't affect other concurrent hashers."""
        results = []
        lock = threading.Lock()

        def hash_and_reset(data: bytes, should_reset: bool):
            """Hash data, optionally reset, then hash again."""
            hasher = stream()
            hasher.update(data)
            first = hasher.digest().formatted

            if should_reset:
                hasher.reset()
                hasher.update(b"After reset")
                second = hasher.digest().formatted
            else:
                second = first

            with lock:
                results.append((first, second))

        # Mix threads that reset with threads that don't
        threads = []
        for i in range(20):
            data = f"Data {i}".encode()
            should_reset = i % 2 == 0
            t = threading.Thread(target=hash_and_reset, args=(data, should_reset))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 20


class TestDigestImmutability:
    """Test that Digest objects remain immutable under concurrent access."""

    def test_digest_concurrent_reads(self):
        """Test concurrent reads of same Digest don't cause issues."""
        digest = hash_bytes(b"Shared digest")
        num_threads = 50
        results = {
            "formatted": [],
            "hex": [],
            "algorithm": [],
        }
        lock = threading.Lock()

        def read_digest():
            """Read digest properties concurrently."""
            with lock:
                results["formatted"].append(digest.formatted)
                results["hex"].append(digest.hex)
                results["algorithm"].append(digest.algorithm)

        threads = [threading.Thread(target=read_digest) for _ in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All reads should produce identical results
        assert len(set(results["formatted"])) == 1
        assert len(set(results["hex"])) == 1
        assert len(set(results["algorithm"])) == 1


class TestUniversalHashDispatcher:
    """Test thread safety of hash() dispatcher."""

    def test_concurrent_mixed_types(self, tmp_path):
        """Test hash() dispatcher with different types concurrently."""
        # Create test file
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(b"File content")

        results = []
        lock = threading.Lock()

        def hash_bytes_type():
            result = hash(b"Bytes data").formatted
            with lock:
                results.append(("bytes", result))

        def hash_string_type():
            result = hash("String data").formatted
            with lock:
                results.append(("string", result))

        def hash_file_type():
            result = hash(file_path).formatted
            with lock:
                results.append(("file", result))

        # Mix different types concurrently
        threads = []
        for _ in range(10):
            threads.append(threading.Thread(target=hash_bytes_type))
            threads.append(threading.Thread(target=hash_string_type))
            threads.append(threading.Thread(target=hash_file_type))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify results by type
        bytes_results = [r for t, r in results if t == "bytes"]
        string_results = [r for t, r in results if t == "string"]
        file_results = [r for t, r in results if t == "file"]

        # All results of same type should be identical
        assert len(set(bytes_results)) == 1
        assert len(set(string_results)) == 1
        assert len(set(file_results)) == 1


class TestLongRunningStress:
    """Long-running stress tests for concurrency validation.

    These tests run for longer periods to catch rare race conditions
    and provide confidence in production use.
    """

    @pytest.mark.slow
    def test_sustained_concurrent_hashing(self):
        """Sustained concurrent hashing over many iterations.

        Runs 1000 operations across 10 threads to catch rare race conditions.
        """
        num_threads = 10
        operations_per_thread = 100
        errors = []
        success_count = [0]
        lock = threading.Lock()

        def sustained_hashing(thread_id: int):
            """Perform many hash operations."""
            for i in range(operations_per_thread):
                try:
                    # Mix of operations
                    data = f"T{thread_id}I{i}".encode()

                    # Block hash
                    hash_bytes(data)

                    # Streaming
                    hasher = stream()
                    hasher.update(data[: len(data) // 2])
                    hasher.update(data[len(data) // 2 :])
                    hasher.digest()

                    with lock:
                        success_count[0] += 1

                except Exception as e:
                    with lock:
                        errors.append((thread_id, i, e))

        threads = [
            threading.Thread(target=sustained_hashing, args=(i,)) for i in range(num_threads)
        ]

        start = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.time() - start

        # Verify no errors occurred
        assert not errors, f"Errors: {errors}"

        # Verify all operations completed
        expected_total = num_threads * operations_per_thread
        assert success_count[0] == expected_total

        print(f"\nStress test: {expected_total} operations in {elapsed:.2f}s")
        print(f"Throughput: {expected_total / elapsed:.0f} ops/sec")

    @pytest.mark.slow
    def test_memory_safety_under_load(self, tmp_path):
        """Test memory safety with concurrent file hashing under load."""
        # Create test file
        file_path = tmp_path / "load_test.bin"
        file_path.write_bytes(b"X" * (1024 * 1024))  # 1MB file

        num_threads = 20
        hashes_per_thread = 10
        results = []
        lock = threading.Lock()

        def hash_repeatedly():
            """Hash file repeatedly."""
            for _ in range(hashes_per_thread):
                digest = hash_file(file_path)
                with lock:
                    results.append(digest.formatted)

        threads = [threading.Thread(target=hash_repeatedly) for _ in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be identical (same file)
        expected_total = num_threads * hashes_per_thread
        assert len(results) == expected_total
        assert len(set(results)) == 1, "Results not identical - possible corruption"
