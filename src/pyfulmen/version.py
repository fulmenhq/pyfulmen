"""Version management utilities for PyFulmen.

This module provides utilities for reading and validating version information
across the repository. The single source of truth is the VERSION file, which
should be kept in sync with pyproject.toml and __init__.py.

Example:
    >>> from pyfulmen.version import read_version, get_version_info
    >>> read_version()
    '0.1.0'
    >>> get_version_info()
    {'version': '0.1.0', 'source': 'VERSION'}
"""

import re
from pathlib import Path
from typing import Any

# Locate repository root (where VERSION file lives)
_REPO_ROOT = Path(__file__).parent.parent.parent


def read_version() -> str:
    """Read version from VERSION file.

    Returns:
        Version string (e.g., "0.1.0")

    Raises:
        FileNotFoundError: If VERSION file doesn't exist
        ValueError: If VERSION file is empty or malformed
    """
    version_file = _REPO_ROOT / "VERSION"

    if not version_file.exists():
        raise FileNotFoundError(f"VERSION file not found at {version_file}")

    version = version_file.read_text().strip()

    if not version:
        raise ValueError("VERSION file is empty")

    return version


def get_version_info() -> dict[str, Any]:
    """Get detailed version information.

    Returns:
        Dictionary with version metadata:
        - version: Version string from VERSION file
        - source: Source file (always "VERSION")
        - valid: Whether version format is valid

    Example:
        >>> get_version_info()
        {'version': '0.1.0', 'source': 'VERSION', 'valid': True}
    """
    version = read_version()

    # Simple validation: SemVer or CalVer format
    # SemVer: X.Y.Z or X.Y.Z-suffix
    # CalVer: YYYY.MM.PATCH or similar
    semver_pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$"
    calver_pattern = r"^\d{4}\.\d{1,2}\.\d+(-[a-zA-Z0-9.-]+)?$"

    is_valid = bool(re.match(semver_pattern, version) or re.match(calver_pattern, version))

    return {
        "version": version,
        "source": "VERSION",
        "valid": is_valid,
    }


def validate_version_sync() -> dict[str, Any]:
    """Validate that VERSION is synced across all files.

    Checks that VERSION file matches:
    - pyproject.toml [project] version
    - src/pyfulmen/__init__.py __version__

    Returns:
        Dictionary with sync status:
        - synced: Whether all versions match
        - version_file: Version from VERSION
        - pyproject_version: Version from pyproject.toml
        - init_version: Version from __init__.py
        - mismatches: List of files with mismatched versions

    Example:
        >>> validate_version_sync()
        {'synced': True, 'version_file': '0.1.0', ...}
    """
    version_file = read_version()
    mismatches = []

    # Check pyproject.toml
    pyproject_path = _REPO_ROOT / "pyproject.toml"
    pyproject_version = None
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        # Parse version from [project] section
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if match:
            pyproject_version = match.group(1)
            if pyproject_version != version_file:
                mismatches.append("pyproject.toml")

    # Check __init__.py
    init_path = _REPO_ROOT / "src" / "pyfulmen" / "__init__.py"
    init_version = None
    if init_path.exists():
        content = init_path.read_text()
        match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if match:
            init_version = match.group(1)
            if init_version != version_file:
                mismatches.append("__init__.py")

    return {
        "synced": len(mismatches) == 0,
        "version_file": version_file,
        "pyproject_version": pyproject_version,
        "init_version": init_version,
        "mismatches": mismatches,
    }


__all__ = [
    "read_version",
    "get_version_info",
    "validate_version_sync",
]
