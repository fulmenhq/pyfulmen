"""Tests for pyfulmen.config.merger module."""

from pyfulmen.config.merger import deep_merge, merge_configs


def test_deep_merge_simple():
    """Test deep merge with simple values."""
    base = {"a": 1, "b": 2}
    override = {"b": 3, "c": 4}

    result = deep_merge(base, override)

    assert result == {"a": 1, "b": 3, "c": 4}


def test_deep_merge_nested():
    """Test deep merge with nested dictionaries."""
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 99}, "e": 4}

    result = deep_merge(base, override)

    assert result == {"a": 1, "b": {"c": 99, "d": 3}, "e": 4}


def test_deep_merge_deeply_nested():
    """Test deep merge with deeply nested structures."""
    base = {"level1": {"level2": {"level3": {"value": 1, "keep": True}}}}
    override = {"level1": {"level2": {"level3": {"value": 2}}}}

    result = deep_merge(base, override)

    assert result == {"level1": {"level2": {"level3": {"value": 2, "keep": True}}}}


def test_deep_merge_list_replacement():
    """Test that lists are replaced, not merged."""
    base = {"items": [1, 2, 3]}
    override = {"items": [4, 5]}

    result = deep_merge(base, override)

    assert result == {"items": [4, 5]}


def test_deep_merge_empty_base():
    """Test deep merge with empty base."""
    base = {}
    override = {"a": 1, "b": 2}

    result = deep_merge(base, override)

    assert result == {"a": 1, "b": 2}


def test_deep_merge_empty_override():
    """Test deep merge with empty override."""
    base = {"a": 1, "b": 2}
    override = {}

    result = deep_merge(base, override)

    assert result == {"a": 1, "b": 2}


def test_merge_configs_multiple():
    """Test merging multiple configs."""
    config1 = {"a": 1, "b": 2}
    config2 = {"b": 3, "c": 4}
    config3 = {"c": 5, "d": 6}

    result = merge_configs(config1, config2, config3)

    # Later configs override earlier ones
    assert result == {"a": 1, "b": 3, "c": 5, "d": 6}


def test_merge_configs_empty():
    """Test merging with no configs."""
    result = merge_configs()
    assert result == {}


def test_merge_configs_single():
    """Test merging single config."""
    config = {"a": 1, "b": 2}
    result = merge_configs(config)
    assert result == {"a": 1, "b": 2}
