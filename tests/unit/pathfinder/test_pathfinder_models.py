"""
Tests for pyfulmen.pathfinder.models module.

Tests Pydantic data models for pathfinder.
"""

import pytest
from pydantic import ValidationError

from pyfulmen.pathfinder.models import (
    ConstraintType,
    EnforcementLevel,
    FinderConfig,
    FindQuery,
    PathConstraint,
    PathMetadata,
    PathResult,
)


class TestFindQuery:
    """Test FindQuery data model."""

    def test_find_query_minimal(self):
        """FindQuery should work with minimal required fields."""
        query = FindQuery(root=".", include=["*.py"])
        assert query.root == "."
        assert query.include == ["*.py"]
        assert query.exclude == []
        assert query.max_depth == 0
        assert query.follow_symlinks is False
        assert query.include_hidden is False

    def test_find_query_full(self):
        """FindQuery should accept all fields."""
        query = FindQuery(
            root="/path/to/root",
            include=["*.py", "*.txt"],
            exclude=["*.pyc"],
            max_depth=5,
            follow_symlinks=True,
            include_hidden=True,
        )
        assert query.root == "/path/to/root"
        assert query.include == ["*.py", "*.txt"]
        assert query.exclude == ["*.pyc"]
        assert query.max_depth == 5
        assert query.follow_symlinks is True
        assert query.include_hidden is True

    def test_find_query_with_callbacks(self):
        """FindQuery should accept callback functions."""

        def error_handler(path: str, err: Exception) -> None:
            pass

        def progress_callback(processed: int, total: int, current: str) -> None:
            pass

        query = FindQuery(
            root=".",
            include=["*.py"],
            error_handler=error_handler,
            progress_callback=progress_callback,
        )
        assert query.error_handler is error_handler
        assert query.progress_callback is progress_callback

    def test_find_query_serialization(self):
        """FindQuery should serialize to JSON (excluding callbacks)."""
        query = FindQuery(root=".", include=["*.py"], exclude=["*.pyc"], max_depth=3)
        data = query.model_dump()
        assert data["root"] == "."
        assert data["include"] == ["*.py"]
        assert data["max_depth"] == 3
        # Callbacks should be excluded from serialization
        assert "error_handler" not in data
        assert "progress_callback" not in data

    def test_find_query_validation_error(self):
        """FindQuery should validate required fields."""
        with pytest.raises(ValidationError):
            FindQuery()  # Missing required 'root' and 'include'


class TestPathResult:
    """Test PathResult data model."""

    def test_path_result_minimal(self):
        """PathResult should work with minimal required fields."""
        result = PathResult(
            relative_path="test/file.py",
            source_path="/abs/test/file.py",
            logical_path="test/file.py",
        )
        assert result.relative_path == "test/file.py"
        assert result.source_path == "/abs/test/file.py"
        assert result.logical_path == "test/file.py"
        assert result.loader_type == "local"  # default
        assert isinstance(result.metadata, PathMetadata)

    def test_path_result_full(self):
        """PathResult should accept all fields."""
        metadata = PathMetadata(size=1024, permissions="0755")
        result = PathResult(
            relative_path="test/file.py",
            source_path="/abs/test/file.py",
            logical_path="logical/path.py",
            loader_type="remote",
            metadata=metadata,
        )
        assert result.relative_path == "test/file.py"
        assert result.source_path == "/abs/test/file.py"
        assert result.logical_path == "logical/path.py"
        assert result.loader_type == "remote"
        assert result.metadata.size == 1024
        assert result.metadata.permissions == "0755"

    def test_path_result_serialization(self):
        """PathResult should serialize to JSON."""
        metadata = PathMetadata(custom={"key": "value"})
        result = PathResult(
            relative_path="test/file.py",
            source_path="/abs/test/file.py",
            logical_path="test/file.py",
            metadata=metadata,
        )
        data = result.model_dump(by_alias=True, exclude_none=True)
        assert data["relativePath"] == "test/file.py"
        assert data["sourcePath"] == "/abs/test/file.py"
        assert data["loaderType"] == "local"
        assert data["metadata"]["custom"]["key"] == "value"

    def test_path_result_validation_error(self):
        """PathResult should validate required fields."""
        with pytest.raises(ValidationError):
            PathResult()  # Missing required fields


class TestFinderConfig:
    """Test FinderConfig data model."""

    def test_finder_config_defaults(self):
        """FinderConfig should have sensible defaults."""
        config = FinderConfig()
        assert config.max_workers == 4
        assert config.cache_enabled is False
        assert config.cache_ttl == 3600
        assert config.loader_type == "local"
        assert config.validate_inputs is False
        assert config.validate_outputs is False

    def test_finder_config_custom(self):
        """FinderConfig should accept custom values."""
        config = FinderConfig(
            max_workers=8,
            cache_enabled=True,
            cache_ttl=7200,
            loader_type="remote",
            validate_inputs=True,
            validate_outputs=True,
        )
        assert config.max_workers == 8
        assert config.cache_enabled is True
        assert config.cache_ttl == 7200
        assert config.loader_type == "remote"
        assert config.validate_inputs is True
        assert config.validate_outputs is True

    def test_finder_config_serialization(self):
        """FinderConfig should serialize to JSON."""
        config = FinderConfig(max_workers=8, loader_type="test")
        data = config.model_dump(by_alias=True)
        assert data["maxWorkers"] == 8
        assert data["loaderType"] == "test"
        assert "cacheEnabled" in data
        assert "validateInputs" in data

    def test_path_constraint_model(self):
        """PathConstraint should support enum fields and aliases."""
        constraint = PathConstraint(
            root="/repo",
            constraint_type=ConstraintType.REPOSITORY,
            enforcement_level=EnforcementLevel.WARN,
            allowed_patterns=["docs/**"],
            blocked_patterns=["secret/**"],
        )
        data = constraint.model_dump(by_alias=True)
        assert data["type"] == "repository"
        assert data["enforcementLevel"] == "warn"
        assert "allowedPatterns" in data
        assert "blockedPatterns" in data


class TestModelInteraction:
    """Test interaction between models."""

    def test_models_work_together(self):
        """Models should work together in typical usage."""
        config = FinderConfig(loader_type="test")
        query = FindQuery(root=".", include=["*.py"])
        result = PathResult(
            relative_path="file.py",
            source_path="/abs/file.py",
            logical_path="file.py",
            loader_type=config.loader_type,
        )

        assert result.loader_type == config.loader_type
        assert query.root == "."

    def test_models_json_roundtrip(self):
        """Models should roundtrip through JSON."""
        # Create original objects
        query = FindQuery(root=".", include=["*.py"], max_depth=3)
        result = PathResult(
            relative_path="test.py", source_path="/abs/test.py", logical_path="test.py"
        )

        # Serialize to dict
        query_data = query.model_dump()
        result_data = result.model_dump()

        # Deserialize back
        query_restored = FindQuery(**query_data)
        result_restored = PathResult(**result_data)

        # Should match originals
        assert query_restored.root == query.root
        assert query_restored.include == query.include
        assert query_restored.max_depth == query.max_depth
        assert result_restored.relative_path == result.relative_path
        assert result_restored.source_path == result.source_path
