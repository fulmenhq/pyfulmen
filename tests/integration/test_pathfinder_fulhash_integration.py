"""
Integration tests for Pathfinder with FulHash checksum support.

Tests the integration between pyfulmen.pathfinder and pyfulmen.fulhash
for file discovery with checksum calculation.
"""

import tempfile
from pathlib import Path

import pytest

from pyfulmen.pathfinder import Finder, FinderConfig, FindQuery


class TestPathfinderFulHashIntegration:
    """Integration tests for Pathfinder with FulHash checksum calculation."""

    @pytest.fixture
    def test_file_tree(self):
        """Create a temporary file tree with various file types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "test_root"
            root.mkdir()

            # Create test files with different content
            (root / "file1.py").write_text("print('hello world')\n")
            (root / "file2.txt").write_text("This is a text file\nwith multiple lines\n")
            (root / "file3.json").write_text('{"key": "value", "number": 42}\n')

            # Create subdirectory with nested files
            subdir = root / "subdir"
            subdir.mkdir()
            (subdir / "nested.py").write_text("# Nested Python file\ndef hello():\n    pass\n")
            (subdir / "data.csv").write_text("name,age\nAlice,30\nBob,25\n")

            # Create empty file
            (root / "empty.txt").write_text("")

            # Create large file (for streaming tests)
            large_content = "x" * 1024 * 10  # 10KB of 'x' characters
            (root / "large.txt").write_text(large_content)

            yield root

    def test_xxh3_128_checksum_calculation(self, test_file_tree):
        """Test xxh3-128 checksum calculation for various file types."""
        finder = Finder(FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128"))

        results = finder.find_files(
            FindQuery(
                root=str(test_file_tree),
                include=[
                    "*.txt",
                    "*.json",
                    "**/*.csv",
                    "**/*.py",
                ],  # Exclude root *.py to avoid overlap with **/*.py
            )
        )

        assert len(results) == 7  # 3 txt files + file3.json + data.csv + file1.py + nested.py

        for result in results:
            assert result.metadata.checksum is not None
            assert result.metadata.checksum.startswith("xxh3-128:")
            assert (
                len(result.metadata.checksum) == len("xxh3-128:") + 32
            )  # 32 hex chars for 128-bit
            assert result.metadata.checksum_algorithm == "xxh3-128"
            assert result.metadata.checksum_error is None

    def test_sha256_checksum_calculation(self, test_file_tree):
        """Test sha256 checksum calculation for various file types."""
        finder = Finder(FinderConfig(calculateChecksums=True, checksumAlgorithm="sha256"))

        results = finder.find_files(
            FindQuery(root=str(test_file_tree), include=["*.py", "*.txt", "*.json"])
        )

        assert len(results) == 5  # Python, text, and JSON files

        for result in results:
            assert result.metadata.checksum is not None
            assert result.metadata.checksum.startswith("sha256:")
            assert len(result.metadata.checksum) == len("sha256:") + 64  # 64 hex chars for 256-bit
            assert result.metadata.checksum_algorithm == "sha256"
            assert result.metadata.checksum_error is None

    def test_checksum_consistency_across_calls(self, test_file_tree):
        """Test that checksums are consistent across multiple calls."""
        config = FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128")

        # First scan
        finder1 = Finder(config)
        results1 = finder1.find_files(FindQuery(root=str(test_file_tree), include=["file1.py"]))

        # Second scan
        finder2 = Finder(config)
        results2 = finder2.find_files(FindQuery(root=str(test_file_tree), include=["file1.py"]))

        assert len(results1) == 1
        assert len(results2) == 1
        assert results1[0].metadata.checksum == results2[0].metadata.checksum

    def test_large_file_streaming_performance(self, test_file_tree):
        """Test that large files are handled efficiently with streaming."""
        finder = Finder(FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128"))

        results = finder.find_files(FindQuery(root=str(test_file_tree), include=["large.txt"]))

        assert len(results) == 1
        result = results[0]

        assert result.relative_path == "large.txt"
        assert result.metadata.size == 1024 * 10  # 10KB
        assert result.metadata.checksum is not None
        assert result.metadata.checksum.startswith("xxh3-128:")
        assert result.metadata.checksum_error is None

    def test_empty_file_checksum(self, test_file_tree):
        """Test checksum calculation for empty files."""
        finder = Finder(FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128"))

        results = finder.find_files(FindQuery(root=str(test_file_tree), include=["empty.txt"]))

        assert len(results) == 1
        result = results[0]

        assert result.relative_path == "empty.txt"
        assert result.metadata.size == 0
        assert result.metadata.checksum is not None
        assert result.metadata.checksum.startswith("xxh3-128:")
        assert result.metadata.checksum_error is None

    def test_mixed_file_types_same_checksum_algorithm(self, test_file_tree):
        """Test that different file types work with the same algorithm."""
        finder = Finder(FinderConfig(calculateChecksums=True, checksumAlgorithm="sha256"))

        results = finder.find_files(
            FindQuery(
                root=str(test_file_tree),
                include=["*.json", "**/*.csv", "**/*.py"],  # Exclude root *.py to avoid overlap
            )
        )

        assert len(results) == 4  # file3.json + data.csv + file1.py + nested.py

        checksums = [r.metadata.checksum for r in results]
        algorithms = [r.metadata.checksum_algorithm for r in results]

        # All should have checksums
        assert all(checksum is not None for checksum in checksums)
        assert all(alg == "sha256" for alg in algorithms)

        # Checksums should be unique (different content)
        assert len(set(checksums)) == 4

    def test_checksum_with_exclude_patterns(self, test_file_tree):
        """Test checksum calculation with exclude patterns."""
        finder = Finder(FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128"))

        results = finder.find_files(
            FindQuery(
                root=str(test_file_tree),
                include=["*.py", "*.txt"],
                exclude=["large.txt"],  # Exclude the large file
            )
        )

        # Should find Python and text files, but not large.txt
        paths = [r.relative_path for r in results]
        assert "file1.py" in paths
        assert "file2.txt" in paths
        assert "large.txt" not in paths

        # All found files should have checksums
        for result in results:
            assert result.metadata.checksum is not None
            assert result.metadata.checksum_algorithm == "xxh3-128"

    def test_checksum_with_recursive_patterns(self, test_file_tree):
        """Test checksum calculation with recursive glob patterns."""
        finder = Finder(FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128"))

        results = finder.find_files(
            FindQuery(
                root=str(test_file_tree),
                include=["**/*.py"],  # Recursive pattern
            )
        )

        # Should find both root and nested Python files
        paths = [r.relative_path for r in results]
        assert "file1.py" in paths
        assert "subdir/nested.py" in paths
        assert len(results) == 2

        # All should have checksums
        for result in results:
            assert result.metadata.checksum is not None
            assert result.metadata.checksum_algorithm == "xxh3-128"


class TestPathfinderFulHashErrorHandling:
    """Test error handling in Pathfinder with FulHash integration."""

    @pytest.fixture
    def test_file(self):
        """Create a single test file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('test')\n")
            yield tmpdir, test_file

    def test_invalid_algorithm_error_handling(self):
        """Test error handling for invalid checksum algorithms."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('test')\n")

            finder = Finder(
                FinderConfig(calculateChecksums=True, checksumAlgorithm="invalid-algorithm")
            )

            results = finder.find_files(FindQuery(root=str(tmpdir), include=["*.py"]))

            assert len(results) == 1
            result = results[0]

            assert result.metadata.checksum is None
            assert result.metadata.checksum_algorithm is None
            assert (
                result.metadata.checksum_error
                == "Unsupported checksum algorithm: invalid-algorithm"
            )


class TestPathfinderFulHashPerformance:
    """Performance tests for Pathfinder with FulHash checksum calculation."""

    def test_checksum_calculation_performance_overhead(self):
        """Test that checksum calculation doesn't add excessive overhead."""
        import time

        # Create a directory with multiple files
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create 20 files of ~1KB each
            for i in range(20):
                (root / f"file_{i}.txt").write_text("x" * 1024)

            # Test without checksums
            finder_no_checksum = Finder(FinderConfig(calculateChecksums=False))
            start = time.time()
            results_no_checksum = finder_no_checksum.find_files(
                FindQuery(root=str(root), include=["*.txt"])
            )
            time_no_checksum = time.time() - start

            # Test with checksums
            finder_with_checksum = Finder(
                FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128")
            )
            start = time.time()
            results_with_checksum = finder_with_checksum.find_files(
                FindQuery(root=str(root), include=["*.txt"])
            )
            time_with_checksum = time.time() - start

            # Both should find the same files
            assert len(results_no_checksum) == len(results_with_checksum) == 20

            # Checksum calculation should add some overhead but not excessive
            overhead = time_with_checksum - time_no_checksum
            overhead_ratio = overhead / time_no_checksum if time_no_checksum > 0 else 0

            # Allow up to 150% overhead (generous for initial implementation + timing variance)
            assert overhead_ratio < 1.5, f"Checksum overhead too high: {overhead_ratio:.1%}"

            # Verify checksums were actually calculated
            for result in results_with_checksum:
                assert result.metadata.checksum is not None
                assert result.metadata.checksum_algorithm == "xxh3-128"
