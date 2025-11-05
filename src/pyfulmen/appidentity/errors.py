"""
Custom exceptions for the app identity module.

These exceptions provide detailed error information for app identity
discovery, validation, and loading operations.
"""

from __future__ import annotations

from pathlib import Path


class AppIdentityError(Exception):
    """Base exception for app identity errors."""

    pass


class AppIdentityNotFoundError(AppIdentityError):
    """Raised when no identity file can be found."""

    def __init__(self, searched_paths: list[Path]) -> None:
        self.searched_paths = searched_paths
        paths_str = ", ".join(str(p) for p in searched_paths)
        guidance = (
            "Create a .fulmen/app.yaml file in your project root or set FULMEN_APP_IDENTITY_PATH environment variable. "
            "See: https://docs.fulmenhq.com/crucible-py/standards/app-identity/"
        )
        super().__init__(f"App identity not found. Searched: {paths_str}. {guidance}")


class AppIdentityValidationError(AppIdentityError):
    """Raised when identity file fails schema validation."""

    def __init__(self, path: Path, validation_errors: list[str]) -> None:
        self.path = path
        self.validation_errors = validation_errors
        errors_str = "; ".join(validation_errors)
        guidance = "See schema reference: https://docs.fulmenhq.com/crucible-py/standards/app-identity/"
        super().__init__(f"Invalid app identity at {path}: {errors_str}. {guidance}")


class AppIdentityLoadError(AppIdentityError):
    """Raised when identity file cannot be loaded or parsed."""

    def __init__(self, path: Path, cause: Exception) -> None:
        self.path = path
        self.cause = cause
        guidance = (
            "Check file format and permissions. See: https://docs.fulmenhq.com/crucible-py/standards/app-identity/"
        )
        super().__init__(f"Failed to load app identity from {path}: {cause}. {guidance}")
