#!/usr/bin/env python3
"""
Performance benchmark for Pathfinder checksum calculation.

Measures overhead of checksum calculation (both xxh3-128 and sha256)
compared to baseline file discovery without checksums.

Target: <10% overhead for xxh3-128, document sha256 overhead.
"""

import tempfile
import time
from pathlib import Path
from statistics import mean, stdev

from pyfulmen.pathfinder import Finder, FinderConfig, FindQuery


def create_test_tree(root: Path, file_count: int = 100, file_size: int = 1024):
    """Create a test directory tree with multiple files."""
    root.mkdir(exist_ok=True)

    # Create files at root level
    for i in range(file_count // 2):
        (root / f"file_{i:03d}.txt").write_text("x" * file_size)

    # Create subdirectories with files
    for i in range(5):
        subdir = root / f"subdir_{i}"
        subdir.mkdir(exist_ok=True)
        for j in range(file_count // 10):
            (subdir / f"nested_{j:03d}.py").write_text("x" * file_size)


def benchmark_configuration(config: FinderConfig, root: Path, runs: int = 5) -> dict:
    """Benchmark a specific Pathfinder configuration."""
    times = []

    for _ in range(runs):
        finder = Finder(config)
        query = FindQuery(root=str(root), include=["**/*.txt", "**/*.py"])

        start = time.perf_counter()
        results = finder.find_files(query)
        elapsed = time.perf_counter() - start

        times.append(elapsed)

    return {
        "mean": mean(times),
        "stdev": stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
        "runs": runs,
        "files_found": len(results),
    }


def format_benchmark_result(name: str, result: dict, baseline: dict = None) -> str:
    """Format benchmark results with optional baseline comparison."""
    output = [
        f"\n{name}:",
        f"  Files found: {result['files_found']}",
        f"  Mean time: {result['mean'] * 1000:.2f}ms",
        f"  Std dev: {result['stdev'] * 1000:.2f}ms",
        f"  Min/Max: {result['min'] * 1000:.2f}ms / {result['max'] * 1000:.2f}ms",
    ]

    if baseline:
        overhead = (result["mean"] - baseline["mean"]) / baseline["mean"] * 100
        output.append(f"  Overhead: {overhead:+.1f}% vs baseline")

    return "\n".join(output)


def main():
    """Run comprehensive performance benchmarks."""
    print("=" * 70)
    print("Pathfinder Checksum Performance Benchmark")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "benchmark_tree"

        # Test configurations
        configs = [
            ("Small files (100 files × 1KB)", 100, 1024),
            ("Medium files (100 files × 10KB)", 100, 10240),
            ("Many small files (500 files × 1KB)", 500, 1024),
        ]

        for config_name, file_count, file_size in configs:
            print(f"\n{config_name}")
            print("-" * 70)

            # Create test tree
            if root.exists():
                import shutil

                shutil.rmtree(root)
            create_test_tree(root, file_count, file_size)

            # Baseline (no checksums)
            print("\nRunning baseline (no checksums)...")
            baseline_config = FinderConfig(calculateChecksums=False)
            baseline = benchmark_configuration(baseline_config, root, runs=5)
            print(format_benchmark_result("Baseline (no checksums)", baseline))

            # XXH3-128
            print("\nRunning with xxh3-128 checksums...")
            xxh3_config = FinderConfig(
                calculateChecksums=True, checksumAlgorithm="xxh3-128"
            )
            xxh3_result = benchmark_configuration(xxh3_config, root, runs=5)
            print(format_benchmark_result("XXH3-128 checksums", xxh3_result, baseline))

            # SHA256
            print("\nRunning with sha256 checksums...")
            sha256_config = FinderConfig(
                calculateChecksums=True, checksumAlgorithm="sha256"
            )
            sha256_result = benchmark_configuration(sha256_config, root, runs=5)
            print(format_benchmark_result("SHA256 checksums", sha256_result, baseline))

            # Summary
            xxh3_overhead = (
                (xxh3_result["mean"] - baseline["mean"]) / baseline["mean"] * 100
            )
            sha256_overhead = (
                (sha256_result["mean"] - baseline["mean"]) / baseline["mean"] * 100
            )

            print(f"\n{'Summary':<40} {'Overhead':<15} {'Status'}")
            print("-" * 70)
            print(
                f"{'XXH3-128':<40} {xxh3_overhead:>6.1f}%        {'✓ PASS' if xxh3_overhead < 10 else '✗ FAIL (>10%)'}"
            )
            print(f"{'SHA256':<40} {sha256_overhead:>6.1f}%        {'(documented)'}")

    print("\n" + "=" * 70)
    print("Benchmark complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
