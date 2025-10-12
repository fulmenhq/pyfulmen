"""Config merging utilities.

Provides deep merge functionality for combining configuration dictionaries,
where later configs override earlier ones.
"""

from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries.

    Later dictionary (override) takes precedence over base. Nested dicts
    are merged recursively, lists and primitives are replaced.

    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary

    Returns:
        Merged dictionary

    Example:
        >>> base = {'a': 1, 'b': {'c': 2, 'd': 3}}
        >>> override = {'b': {'c': 99}, 'e': 4}
        >>> deep_merge(base, override)
        {'a': 1, 'b': {'c': 99, 'd': 3}, 'e': 4}
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = deep_merge(result[key], value)
        else:
            # Override with new value
            result[key] = value

    return result


def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple configuration dictionaries.

    Configs are merged left-to-right, with later configs taking precedence.

    Args:
        *configs: Variable number of config dictionaries

    Returns:
        Merged configuration

    Example:
        >>> merge_configs({'a': 1}, {'b': 2}, {'a': 3})
        {'a': 3, 'b': 2}
    """
    if not configs:
        return {}

    result = configs[0].copy()
    for config in configs[1:]:
        result = deep_merge(result, config)

    return result


__all__ = [
    "deep_merge",
    "merge_configs",
]
