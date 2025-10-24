#!/usr/bin/env python3
"""
Profile Pathfinder checksum overhead to identify bottlenecks.

Breaks down overhead into components:
- File I/O (open, read, close)
- Hashing (FulHash)
- Metadata construction
- Model validation
"""

import tempfile
import time
from pathlib import Path

from pyfulmen.fulhash import Algorithm, hash_file
from pyfulmen.pathfinder.models import PathMetadata


def profile_components(file_path: Path, runs: int = 100):
    """Profile individual components of checksum calculation."""

    print("=" * 70)
    print("Component-Level Profiling")
    print("=" * 70)
    print(f"File: {file_path}")
    print(f"Size: {file_path.stat().st_size} bytes")
    print(f"Runs: {runs}")
    print()

    # 1. Baseline: Just stat the file
    times_stat = []
    for _ in range(runs):
        start = time.perf_counter()
        stat_result = file_path.stat()
        _ = stat_result.st_size
        elapsed = time.perf_counter() - start
        times_stat.append(elapsed)

    avg_stat = sum(times_stat) / len(times_stat) * 1000
    print(f"1. File stat only:              {avg_stat:.4f} ms")

    # 2. Just hash_file (includes I/O + hashing)
    times_hash = []
    for _ in range(runs):
        start = time.perf_counter()
        hash_file(file_path, Algorithm.XXH3_128)
        elapsed = time.perf_counter() - start
        times_hash.append(elapsed)

    avg_hash = sum(times_hash) / len(times_hash) * 1000
    print(f"2. hash_file (I/O + hashing):   {avg_hash:.4f} ms")

    # 3. Just read file (I/O only)
    times_read = []
    for _ in range(runs):
        start = time.perf_counter()
        with open(file_path, "rb") as f:
            _ = f.read()
        elapsed = time.perf_counter() - start
        times_read.append(elapsed)

    avg_read = sum(times_read) / len(times_read) * 1000
    print(f"3. File read only (I/O):        {avg_read:.4f} ms")

    # 4. Construct PathMetadata (with checksum fields)
    from datetime import UTC, datetime

    stat_result = file_path.stat()
    modified = datetime.fromtimestamp(stat_result.st_mtime, tz=UTC).isoformat()
    permissions = oct(stat_result.st_mode & 0o777)

    times_metadata = []
    for _ in range(runs):
        start = time.perf_counter()
        PathMetadata(
            size=stat_result.st_size,
            modified=modified,
            permissions=permissions,
            checksum="xxh3-128:abc123",
            checksumAlgorithm="xxh3-128",
            checksumError=None,
        )
        elapsed = time.perf_counter() - start
        times_metadata.append(elapsed)

    avg_metadata = sum(times_metadata) / len(times_metadata) * 1000
    print(f"4. PathMetadata construction:   {avg_metadata:.4f} ms")

    # Analysis
    print("\n" + "=" * 70)
    print("Breakdown Analysis")
    print("=" * 70)

    pure_hash_time = avg_hash - avg_read
    print(
        f"Pure hashing overhead:          {pure_hash_time:.4f} ms ({pure_hash_time / avg_hash * 100:.1f}% of hash_file)"
    )
    print(
        f"I/O overhead:                   {avg_read:.4f} ms ({avg_read / avg_hash * 100:.1f}% of hash_file)"
    )
    print(f"Model overhead:                 {avg_metadata:.4f} ms")

    total_overhead = avg_stat + avg_hash + avg_metadata
    print(f"\nTotal per-file overhead:        {total_overhead:.4f} ms")
    print(f"  - File stat:                  {avg_stat / total_overhead * 100:.1f}%")
    print(f"  - Hash calculation:           {avg_hash / total_overhead * 100:.1f}%")
    print(f"  - Metadata construction:      {avg_metadata / total_overhead * 100:.1f}%")

    return {
        "stat": avg_stat,
        "hash": avg_hash,
        "read": avg_read,
        "metadata": avg_metadata,
        "pure_hash": pure_hash_time,
    }


def compare_file_sizes():
    """Compare overhead across different file sizes."""
    print("\n" + "=" * 70)
    print("File Size Comparison")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        sizes = [
            (100, "100 bytes"),
            (1024, "1 KB"),
            (10240, "10 KB"),
            (102400, "100 KB"),
        ]

        results = []
        for size, label in sizes:
            test_file = Path(tmpdir) / f"test_{size}.bin"
            test_file.write_bytes(b"x" * size)

            print(f"\n{label}:")
            print("-" * 70)
            profile = profile_components(test_file, runs=50)
            results.append((label, size, profile))

        # Summary table
        print("\n" + "=" * 70)
        print("Summary: Overhead vs File Size")
        print("=" * 70)
        print(
            f"{'Size':<15} {'Total(ms)':<12} {'I/O(ms)':<12} {'Hash(ms)':<12} {'Model(ms)'}"
        )
        print("-" * 70)

        for label, size, profile in results:
            total = profile["stat"] + profile["hash"] + profile["metadata"]
            print(
                f"{label:<15} {total:>8.4f}     {profile['read']:>8.4f}     {profile['pure_hash']:>8.4f}     {profile['metadata']:>8.4f}"
            )


if __name__ == "__main__":
    compare_file_sizes()
