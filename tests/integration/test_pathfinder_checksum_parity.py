"""
Cross-language parity tests for Pathfinder checksum calculation.

Validates that pyfulmen Pathfinder produces identical checksums to:
- FulHash test vectors (config/crucible-py/library/fulhash/fixtures.yaml)
- Pathfinder fixtures (tests/fixtures/pathfinder/checksum-fixtures.yaml)
- gofulmen and tsfulmen implementations (via shared fixtures)
"""

from pathlib import Path

import pytest
import yaml

from pyfulmen.pathfinder import Finder, FinderConfig, FindQuery


class TestPathfinderChecksumParity:
    """Parity tests validating Pathfinder checksums against known fixtures."""

    @pytest.fixture(scope="class")
    def fulhash_fixtures(self):
        """Load FulHash fixtures for parity validation."""
        fixtures_path = (
            Path(__file__).parent.parent.parent
            / "config"
            / "crucible-py"
            / "library"
            / "fulhash"
            / "fixtures.yaml"
        )
        with open(fixtures_path) as f:
            return yaml.safe_load(f)

    @pytest.fixture(scope="class")
    def sample_files_dir(self):
        """Path to sample files for testing."""
        return (
            Path(__file__).parent.parent
            / "fixtures"
            / "pathfinder"
            / "sample-files"
        )

    def test_empty_file_xxh3_128_parity(self, sample_files_dir, fulhash_fixtures):
        """Verify empty file checksum matches FulHash empty-input fixture (xxh3-128)."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["empty.txt"])
        )

        assert len(results) == 1
        result = results[0]
        
        # Get expected checksum from FulHash fixtures
        empty_fixture = next(f for f in fulhash_fixtures["fixtures"] if f["name"] == "empty-input")
        expected_checksum = empty_fixture["xxh3_128"]

        assert result.metadata.checksum == expected_checksum
        assert result.metadata.checksum_algorithm == "xxh3-128"
        assert result.metadata.checksum_error is None
        assert result.metadata.size == 0

    def test_empty_file_sha256_parity(self, sample_files_dir, fulhash_fixtures):
        """Verify empty file checksum matches FulHash empty-input fixture (sha256)."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="sha256")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["empty.txt"])
        )

        assert len(results) == 1
        result = results[0]
        
        # Get expected checksum from FulHash fixtures
        empty_fixture = next(f for f in fulhash_fixtures["fixtures"] if f["name"] == "empty-input")
        expected_checksum = empty_fixture["sha256"]

        assert result.metadata.checksum == expected_checksum
        assert result.metadata.checksum_algorithm == "sha256"
        assert result.metadata.checksum_error is None

    def test_hello_world_xxh3_128_parity(self, sample_files_dir, fulhash_fixtures):
        """Verify hello-world.txt checksum matches FulHash hello-world fixture (xxh3-128)."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["hello-world.txt"])
        )

        assert len(results) == 1
        result = results[0]
        
        # Get expected checksum from FulHash fixtures
        hello_fixture = next(f for f in fulhash_fixtures["fixtures"] if f["name"] == "hello-world")
        expected_checksum = hello_fixture["xxh3_128"]

        assert result.metadata.checksum == expected_checksum
        assert result.metadata.checksum_algorithm == "xxh3-128"
        assert result.metadata.checksum_error is None
        assert result.metadata.size == 13

    def test_hello_world_sha256_parity(self, sample_files_dir, fulhash_fixtures):
        """Verify hello-world.txt checksum matches FulHash hello-world fixture (sha256)."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="sha256")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["hello-world.txt"])
        )

        assert len(results) == 1
        result = results[0]
        
        # Get expected checksum from FulHash fixtures
        hello_fixture = next(f for f in fulhash_fixtures["fixtures"] if f["name"] == "hello-world")
        expected_checksum = hello_fixture["sha256"]

        assert result.metadata.checksum == expected_checksum
        assert result.metadata.checksum_algorithm == "sha256"
        assert result.metadata.checksum_error is None

    def test_single_char_xxh3_128_parity(self, sample_files_dir, fulhash_fixtures):
        """Verify single-char.txt checksum matches FulHash single-byte fixture (xxh3-128)."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["single-char.txt"])
        )

        assert len(results) == 1
        result = results[0]
        
        # Get expected checksum from FulHash fixtures
        single_fixture = next(f for f in fulhash_fixtures["fixtures"] if f["name"] == "single-byte")
        expected_checksum = single_fixture["xxh3_128"]

        assert result.metadata.checksum == expected_checksum
        assert result.metadata.checksum_algorithm == "xxh3-128"
        assert result.metadata.checksum_error is None
        assert result.metadata.size == 1

    def test_single_char_sha256_parity(self, sample_files_dir, fulhash_fixtures):
        """Verify single-char.txt checksum matches FulHash single-byte fixture (sha256)."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="sha256")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["single-char.txt"])
        )

        assert len(results) == 1
        result = results[0]
        
        # Get expected checksum from FulHash fixtures
        single_fixture = next(f for f in fulhash_fixtures["fixtures"] if f["name"] == "single-byte")
        expected_checksum = single_fixture["sha256"]

        assert result.metadata.checksum == expected_checksum
        assert result.metadata.checksum_algorithm == "sha256"
        assert result.metadata.checksum_error is None

    def test_unicode_emoji_xxh3_128_parity(self, sample_files_dir, fulhash_fixtures):
        """Verify unicode-emoji.txt checksum matches FulHash unicode-emoji fixture (xxh3-128)."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["unicode-emoji.txt"])
        )

        assert len(results) == 1
        result = results[0]
        
        # Get expected checksum from FulHash fixtures
        unicode_fixture = next(
            f for f in fulhash_fixtures["fixtures"] if f["name"] == "unicode-emoji"
        )
        expected_checksum = unicode_fixture["xxh3_128"]

        assert result.metadata.checksum == expected_checksum
        assert result.metadata.checksum_algorithm == "xxh3-128"
        assert result.metadata.checksum_error is None
        # UTF-8: "Hello " (6) + "🔥" (4 bytes) + " World" (6) = 16 bytes
        assert result.metadata.size == 16

    def test_unicode_emoji_sha256_parity(self, sample_files_dir, fulhash_fixtures):
        """Verify unicode-emoji.txt checksum matches FulHash unicode-emoji fixture (sha256)."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="sha256")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["unicode-emoji.txt"])
        )

        assert len(results) == 1
        result = results[0]
        
        # Get expected checksum from FulHash fixtures
        unicode_fixture = next(
            f for f in fulhash_fixtures["fixtures"] if f["name"] == "unicode-emoji"
        )
        expected_checksum = unicode_fixture["sha256"]

        assert result.metadata.checksum == expected_checksum
        assert result.metadata.checksum_algorithm == "sha256"
        assert result.metadata.checksum_error is None

    def test_all_sample_files_xxh3_128(self, sample_files_dir, fulhash_fixtures):
        """Batch validate all sample files with xxh3-128."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["*.txt"])
        )

        # Should find all 4 sample files
        assert len(results) >= 4
        
        # All should have valid checksums
        for result in results:
            assert result.metadata.checksum is not None
            assert result.metadata.checksum.startswith("xxh3-128:")
            assert result.metadata.checksum_algorithm == "xxh3-128"
            assert result.metadata.checksum_error is None

    def test_all_sample_files_sha256(self, sample_files_dir, fulhash_fixtures):
        """Batch validate all sample files with sha256."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="sha256")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["*.txt"])
        )

        # Should find all 4 sample files
        assert len(results) >= 4
        
        # All should have valid checksums
        for result in results:
            assert result.metadata.checksum is not None
            assert result.metadata.checksum.startswith("sha256:")
            assert result.metadata.checksum_algorithm == "sha256"
            assert result.metadata.checksum_error is None


class TestPathfinderCaseInsensitiveAlgorithms:
    """Test case-insensitive algorithm handling per fixture spec."""

    @pytest.fixture(scope="class")
    def sample_files_dir(self):
        """Path to sample files for testing."""
        return (
            Path(__file__).parent.parent
            / "fixtures"
            / "pathfinder"
            / "sample-files"
        )

    def test_uppercase_xxh3_128_normalized(self, sample_files_dir):
        """Verify XXH3-128 (uppercase) is normalized to xxh3-128."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="XXH3-128")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["hello-world.txt"])
        )

        assert len(results) == 1
        result = results[0]

        # Should match the normalized lowercase checksum
        assert result.metadata.checksum == "xxh3-128:531df2844447dd5077db03842cd75395"
        assert result.metadata.checksum_algorithm == "xxh3-128"  # Normalized
        assert result.metadata.checksum_error is None

    def test_mixed_case_sha256_normalized(self, sample_files_dir):
        """Verify Sha256 (mixed case) is normalized to sha256."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="Sha256")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["hello-world.txt"])
        )

        assert len(results) == 1
        result = results[0]

        # Should match the normalized lowercase checksum
        expected = "sha256:dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert result.metadata.checksum == expected
        assert result.metadata.checksum_algorithm == "sha256"  # Normalized
        assert result.metadata.checksum_error is None

    def test_uppercase_sha256_normalized(self, sample_files_dir):
        """Verify SHA256 (all uppercase) is normalized to sha256."""
        finder = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="SHA256")
        )
        results = finder.find_files(
            FindQuery(root=str(sample_files_dir), include=["single-char.txt"])
        )

        assert len(results) == 1
        result = results[0]

        # Should match the normalized lowercase checksum
        expected = "sha256:559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd"
        assert result.metadata.checksum == expected
        assert result.metadata.checksum_algorithm == "sha256"  # Normalized
        assert result.metadata.checksum_error is None


class TestPathfinderChecksumConsistency:
    """Test checksum consistency across multiple runs and algorithms."""

    @pytest.fixture(scope="class")
    def sample_files_dir(self):
        """Path to sample files for testing."""
        return (
            Path(__file__).parent.parent
            / "fixtures"
            / "pathfinder"
            / "sample-files"
        )

    def test_deterministic_checksums_across_runs(self, sample_files_dir):
        """Verify checksums are deterministic across multiple runs."""
        config = FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128")
        query = FindQuery(root=str(sample_files_dir), include=["hello-world.txt"])

        # Run 3 times
        results1 = Finder(config).find_files(query)
        results2 = Finder(config).find_files(query)
        results3 = Finder(config).find_files(query)

        # All runs should produce identical checksums
        assert results1[0].metadata.checksum == results2[0].metadata.checksum
        assert results2[0].metadata.checksum == results3[0].metadata.checksum

    def test_different_algorithms_different_checksums(self, sample_files_dir):
        """Verify different algorithms produce different checksums for same file."""
        query = FindQuery(root=str(sample_files_dir), include=["hello-world.txt"])

        xxh3_results = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="xxh3-128")
        ).find_files(query)

        sha256_results = Finder(
            FinderConfig(calculateChecksums=True, checksumAlgorithm="sha256")
        ).find_files(query)

        # Same file, different algorithms -> different checksums
        assert xxh3_results[0].metadata.checksum != sha256_results[0].metadata.checksum
        assert xxh3_results[0].metadata.checksum.startswith("xxh3-128:")
        assert sha256_results[0].metadata.checksum.startswith("sha256:")
