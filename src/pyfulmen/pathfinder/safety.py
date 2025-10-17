"""
Path safety validation for pyfulmen.pathfinder.

Provides validation functions to prevent path traversal attacks
and ensure safe filesystem operations.
"""

import os
from pathlib import Path


class PathTraversalError(Exception):
    """Raised when path traversal attempts are detected."""

    pass


class InvalidPathError(Exception):
    """Raised when a path is invalid or unsafe."""

    pass


def validate_path(path: str) -> None:
    """
    Validate that a path is safe to access.

    Checks for path traversal attempts, empty paths, and overly broad paths.

    Args:
        path: The path string to validate

    Raises:
        PathTraversalError: If path traversal is detected
        InvalidPathError: If path is invalid, empty, or too broad

    Examples:
        >>> validate_path("valid/path/to/file.txt")  # OK
        >>> validate_path("../escape")  # Raises PathTraversalError
        >>> validate_path("")  # Raises InvalidPathError
        >>> validate_path("/")  # Raises InvalidPathError
    """
    # Check for path traversal attempts in ORIGINAL path first
    # (before normalization, since normpath resolves "..")
    if ".." in path:
        raise PathTraversalError(f"Path traversal detected: {path}")

    # Clean the path using os.path for consistency with Go filepath.Clean
    clean_path = os.path.normpath(path)

    # Check for empty or current directory path
    if clean_path in ("", "."):
        raise InvalidPathError(f"Invalid path (empty or current directory): {path}")

    # Check for root path (too broad, but technically safe)
    if clean_path in ("/", "\\"):
        raise InvalidPathError(f"Invalid path (root directory too broad): {path}")


def is_safe_path(path: str) -> bool:
    """
    Check if a path is safe without raising an exception.

    Args:
        path: The path string to check

    Returns:
        True if path is safe, False otherwise

    Examples:
        >>> is_safe_path("valid/path")
        True
        >>> is_safe_path("../escape")
        False
    """
    try:
        validate_path(path)
        return True
    except (PathTraversalError, InvalidPathError):
        return False
