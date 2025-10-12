"""Platform detection utilities for config path resolution.

Internal module - not part of public API.
"""

import platform
from enum import Enum


class Platform(str, Enum):
    """Supported platforms."""

    LINUX = "linux"
    MACOS = "macos"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


def detect_platform() -> Platform:
    """Detect current platform.

    Returns:
        Platform enum value

    Example:
        >>> detect_platform()
        <Platform.MACOS: 'macos'>
    """
    system = platform.system().lower()

    platform_map = {
        "darwin": Platform.MACOS,
        "linux": Platform.LINUX,
        "windows": Platform.WINDOWS,
    }

    return platform_map.get(system, Platform.UNKNOWN)
