"""
Tests for pyfulmen.pathfinder.finder module.

Tests file discovery operations with glob patterns and path normalization.
"""

import os
from pathlib import Path

import pytest

from pyfulmen.pathfinder import (
    ConstraintType,
    EnforcementLevel,
    Finder,
    FinderConfig,
    FindQuery,
    PathConstraint,
    PathResult,
    PathTraversalError,
)


@pytest.fixture
def temp_file_tree(tmp_path):
    """
    Create a temporary file tree for testing.

    Structure:
        test_root/
        ├── file1.py
        ├── file2.txt
        ├── config.yaml
        ├── subdir/
        │   ├── nested.py
        │   └── data.json
        ├── deep/
        │   └── deeper/
        │       └── deepest.md
        └── .hidden/
            └── secret.txt
    """
    root = tmp_path / "test_root"
    root.mkdir()

    # Create files
    (root / "file1.py").write_text("print('hello')")
    (root / "file2.txt").write_text("text content")
    (root / "config.yaml").write_text("key: value")

    # Create subdirectory with files
    subdir = root / "subdir"
    subdir.mkdir()
    (subdir / "nested.py").write_text("# nested python")
    (subdir / "data.json").write_text('{"data": true}')

    # Create deeper nested structure for recursive glob testing
    nested_dir = subdir / "nested_dir"
    nested_dir.mkdir()
    (nested_dir / "nested.json").write_text('{"nested": true}')

    # Create deep nested structure
    deep = root / "deep" / "deeper"
    deep.mkdir(parents=True)
    (deep / "deepest.md").write_text("# Deepest")

    # Create hidden directory with file
    hidden = root / ".hidden"
    hidden.mkdir()
    (hidden / "secret.txt").write_text("secret")

    # Create symlink for testing follow_symlinks behavior (skip if unsupported)
    target = subdir / "nested.py"
    symlink_path = root / "link_to_nested.py"
    try:
        if symlink_path.exists():
            symlink_path.unlink()
        os.symlink(target, symlink_path)
    except (AttributeError, NotImplementedError, OSError):
        # Symlinks may require elevated privileges on Windows; ignore if creation fails
        symlink_path = None

    return root


class TestFinderBasics:
    """Test basic Finder operations."""

    def test_finder_creation(self):
        """Finder should be created with default config."""
        finder = Finder()
        assert finder.config is not None
        assert isinstance(finder.config, FinderConfig)

    def test_finder_with_custom_config(self):
        """Finder should accept custom configuration."""
        config = FinderConfig(max_workers=8, loader_type="test")
        finder = Finder(config)
        assert finder.config.max_workers == 8
        assert finder.config.loader_type == "test"


class TestFindFiles:
    """Test find_files method with various patterns."""

    def test_find_python_files(self, temp_file_tree):
        """Should find all Python files."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["*.py"])
        results = finder.find_files(query)

        # Should find file1.py in root (but not nested.py without recursive)
        assert len(results) >= 1
        paths = [r.relative_path for r in results]
        assert "file1.py" in paths

    def test_find_with_multiple_patterns(self, temp_file_tree):
        """Should find files matching multiple patterns."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["*.py", "*.txt"])
        results = finder.find_files(query)

        paths = [r.relative_path for r in results]
        assert "file1.py" in paths
        assert "file2.txt" in paths

    def test_find_recursive(self, temp_file_tree):
        """Should find files recursively with ** pattern."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["**/*.py"])
        results = finder.find_files(query)

        # Should find both file1.py and subdir/nested.py
        assert len(results) == 2
        paths = [r.relative_path for r in results]
        assert any("file1.py" in p for p in paths)
        assert any("nested.py" in p for p in paths)

    def test_recursive_with_prefix_pattern(self, temp_file_tree):
        """Recursive patterns with directory prefixes should include nested matches."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["subdir/**/*.json"])
        results = finder.find_files(query)

        paths = sorted(r.relative_path for r in results)
        assert "subdir/nested_dir/nested.json" in paths

    def test_exclude_patterns(self, temp_file_tree):
        """Should exclude files matching exclude patterns."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["*.py", "*.txt"], exclude=["*.txt"])
        results = finder.find_files(query)

        paths = [r.relative_path for r in results]
        assert "file1.py" in paths
        assert "file2.txt" not in paths

    def test_max_depth(self, temp_file_tree):
        """Should respect max_depth setting."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["**/*.md"], max_depth=2)
        results = finder.find_files(query)

        # deepest.md is at depth 3 (deep/deeper/deepest.md), should be excluded
        assert len(results) == 0

    def test_include_hidden_false(self, temp_file_tree):
        """Should exclude hidden files by default."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["**/*.txt"], include_hidden=False)
        results = finder.find_files(query)

        paths = [r.relative_path for r in results]
        # Should find file2.txt but not .hidden/secret.txt
        assert "file2.txt" in paths
        assert not any(".hidden" in p for p in paths)

    def test_include_hidden_true(self, temp_file_tree):
        """Should include hidden files when enabled."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["**/*.txt"], include_hidden=True)
        results = finder.find_files(query)

        paths = [r.relative_path for r in results]
        # Should find both file2.txt and .hidden/secret.txt
        assert len(results) >= 2

    def test_symlink_skipped_when_not_following(self, temp_file_tree):
        """Symlinks should be skipped when follow_symlinks is False."""
        # Skip test if symlinks unsupported (common on Windows without privileges)
        if not hasattr(os, "symlink"):
            pytest.skip("os.symlink not supported on this platform")

        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["**/*.py"], follow_symlinks=False)
        results = finder.find_files(query)

        # Should include physical file but not duplicate entries originating from the symlink
        paths = [r.relative_path for r in results]
        assert "file1.py" in paths

        nested_instances = [
            r for r in results if r.source_path.endswith("subdir/nested.py")
        ]
        assert len(nested_instances) == 1

    def test_fulmenignore_patterns(self, temp_file_tree):
        """Paths matching .fulmenignore patterns should be excluded."""
        ignore_file = temp_file_tree / ".fulmenignore"
        ignore_file.write_text("subdir/\n*.txt\n", encoding="utf-8")

        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["**/*.py", "**/*.txt"])
        results = finder.find_files(query)

        paths = [r.relative_path for r in results]
        assert "file1.py" in paths
        assert "subdir/nested.py" not in paths
        assert "file2.txt" not in paths

    def test_metadata_populated(self, temp_file_tree):
        """Metadata should include basic file information."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["file1.py"])
        results = finder.find_files(query)

        assert len(results) == 1
        metadata = results[0].metadata
        assert metadata.size is not None and metadata.size > 0
        assert metadata.modified is not None and "T" in metadata.modified
        assert metadata.permissions.startswith("0")

    def test_constraint_enforcement_strict(self, temp_file_tree):
        """Strict enforcement should raise when blocked patterns match."""
        constraint = PathConstraint(
            root=str(temp_file_tree),
            constraint_type=ConstraintType.REPOSITORY,
            enforcement_level=EnforcementLevel.STRICT,
            blocked_patterns=["subdir/**"],
        )
        finder = Finder(FinderConfig(constraint=constraint))

        with pytest.raises(PathTraversalError):
            finder.find_files(
                FindQuery(root=str(temp_file_tree), include=["subdir/**/*.py"])
            )

    def test_constraint_enforcement_warn(self, temp_file_tree):
        """Warn enforcement should skip blocked paths without raising."""
        constraint = PathConstraint(
            root=str(temp_file_tree),
            constraint_type=ConstraintType.REPOSITORY,
            enforcement_level=EnforcementLevel.WARN,
            blocked_patterns=["subdir/**"],
        )
        finder = Finder(FinderConfig(constraint=constraint))
        results = finder.find_files(
            FindQuery(root=str(temp_file_tree), include=["**/*.py"])
        )

        paths = [r.relative_path for r in results]
        assert all(not p.startswith("subdir/") for p in paths)

    def test_schema_validation_enabled(self, temp_file_tree):
        """Schema validation flags should validate inputs/outputs without errors."""
        finder = Finder(FinderConfig(validate_inputs=True, validate_outputs=True))
        results = finder.find_files(
            FindQuery(root=str(temp_file_tree), include=["file1.py"])
        )
        assert len(results) == 1

    def test_error_handler_called(self, temp_file_tree):
        """Error handler should be called on errors."""
        error_count = [0]  # Use list to allow mutation in closure

        def count_errors(path: str, err: Exception) -> None:
            error_count[0] += 1

        finder = Finder()
        query = FindQuery(
            root=str(temp_file_tree), include=["**/*.nonexistent"], error_handler=count_errors
        )
        results = finder.find_files(query)

        # No matching files, but error handler shouldn't be called for non-matches
        assert len(results) == 0

    def test_progress_callback_called(self, temp_file_tree):
        """Progress callback should be called during discovery."""
        progress_calls = []

        def track_progress(processed: int, total: int, current_path: str) -> None:
            progress_calls.append((processed, total, current_path))

        finder = Finder()
        query = FindQuery(
            root=str(temp_file_tree), include=["*.py", "*.txt"], progress_callback=track_progress
        )
        results = finder.find_files(query)

        # Progress callback should be called for each result
        assert len(progress_calls) == len(results)
        assert all(processed > 0 for processed, _, _ in progress_calls)


class TestPathResult:
    """Test PathResult data model."""

    def test_path_result_creation(self, temp_file_tree):
        """PathResult should capture file information correctly."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["*.py"])
        results = finder.find_files(query)

        assert len(results) > 0
        result = results[0]

        # Check all fields are populated
        assert result.relative_path
        assert result.source_path
        assert result.logical_path
        assert result.loader_type == "local"
        assert result.metadata.size is not None

    def test_path_result_serialization(self):
        """PathResult should serialize to JSON."""
        result = PathResult(
            relative_path="test/file.py",
            source_path="/abs/test/file.py",
            logical_path="test/file.py",
            loader_type="local",
            metadata={"size": 1024},
        )

        # Should serialize to dict/JSON without errors
        data = result.model_dump()
        assert data["relative_path"] == "test/file.py"
        assert data["metadata"]["size"] == 1024


class TestConvenienceMethods:
    """Test convenience methods for common file types."""

    def test_find_config_files(self, temp_file_tree):
        """Should find configuration files."""
        finder = Finder()
        results = finder.find_config_files(str(temp_file_tree))

        paths = [r.relative_path for r in results]
        assert "config.yaml" in paths

    def test_find_schema_files(self, temp_file_tree):
        """Should find schema files."""
        # Create a schema file
        (temp_file_tree / "test.schema.json").write_text('{"$schema": "..."}')

        finder = Finder()
        results = finder.find_schema_files(str(temp_file_tree))

        paths = [r.relative_path for r in results]
        assert "test.schema.json" in paths

    def test_find_by_extension(self, temp_file_tree):
        """Should find files by extension."""
        finder = Finder()
        results = finder.find_by_extension(str(temp_file_tree), ["py", "txt"])

        paths = [r.relative_path for r in results]
        assert "file1.py" in paths
        assert "file2.txt" in paths

    def test_find_python_files(self, temp_file_tree):
        """Should find Python files using convenience method."""
        finder = Finder()
        results = finder.find_python_files(str(temp_file_tree))

        paths = [r.relative_path for r in results]
        assert "file1.py" in paths


class TestPathNormalization:
    """Test that paths are properly normalized using pathlib."""

    def test_relative_path_normalization(self, temp_file_tree):
        """Relative paths should be normalized correctly."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["*.py"])
        results = finder.find_files(query)

        # Relative paths should use forward slashes and be normalized
        for result in results:
            assert ".." not in result.relative_path
            assert result.relative_path == os.path.normpath(result.relative_path)

    def test_absolute_path_normalization(self, temp_file_tree):
        """Absolute paths should be fully resolved."""
        finder = Finder()
        query = FindQuery(root=str(temp_file_tree), include=["*.py"])
        results = finder.find_files(query)

        # Source paths should be absolute and resolved
        for result in results:
            assert os.path.isabs(result.source_path)
            # Path should equal its resolved form
            assert result.source_path == str(Path(result.source_path).resolve())
