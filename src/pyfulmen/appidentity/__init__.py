"""
PyFulmen Application Identity Module

This module provides canonical application metadata following the Crucible
app identity standard. It offers zero-dependency discovery, validation, and
caching of application identity configuration.

Discovery precedence:
1. Explicit path parameter (load_from_path)
2. Environment variable FULMEN_APP_IDENTITY_PATH
3. Filesystem discovery (CWD ancestor search for .fulmen/app.yaml)
4. Embedded identity fallback (registered via register_embedded_identity_yaml)
5. Raise AppIdentityNotFoundError

Example:
    >>> from pyfulmen.appidentity import get_identity
    >>> identity = get_identity()
    >>> print(f"Binary: {identity.binary_name}")
    >>> print(f"Vendor: {identity.vendor}")

For distributed packages (wheels, installed CLIs), register embedded identity
at package import time to enable standalone execution:

    >>> from importlib.resources import files
    >>> from pyfulmen.appidentity import register_embedded_identity_yaml
    >>> data = files("mypackage").joinpath("_assets/app.yaml").read_bytes()
    >>> register_embedded_identity_yaml(data)
"""

from ._cache import IdentityCache, override_identity_for_testing
from ._embedded import (
    clear_embedded_identity,
    get_embedded_identity,
    is_embedded_identity_registered,
    register_embedded_identity_yaml,
)
from ._loader import load, load_from_path
from .errors import (
    AppIdentityError,
    AppIdentityNotFoundError,
    AppIdentityValidationError,
    EmbeddedIdentityAlreadyRegisteredError,
)
from .models import AppIdentity

__all__ = [
    # Core types
    "AppIdentity",
    # Exceptions
    "AppIdentityError",
    "AppIdentityNotFoundError",
    "AppIdentityValidationError",
    "EmbeddedIdentityAlreadyRegisteredError",
    # Loading functions
    "load",
    "load_from_path",
    # High-level API with caching
    "get_identity",
    "reload_identity",
    "clear_identity_cache",
    # Embedded identity (for distributed packages)
    "register_embedded_identity_yaml",
    "get_embedded_identity",
    "clear_embedded_identity",
    "is_embedded_identity_registered",
    # Testing utilities
    "override_identity_for_testing",
]


def get_identity() -> AppIdentity:
    """
    Get the application identity with caching.

    This function provides the primary interface for accessing application
    identity. It uses process-level caching for performance and includes
    automatic discovery following the Crucible standard precedence:

    1. Environment variable override (FULMEN_APP_IDENTITY_PATH)
    2. Ancestor search for .fulmen/app.yaml

    Returns:
        The application identity

    Raises:
        AppIdentityNotFoundError: If no identity configuration is found
        AppIdentityValidationError: If the configuration is invalid
        AppIdentityError: For other loading errors

    Example:
        >>> from pyfulmen.appidentity import get_identity
        >>> identity = get_identity()
        >>> print(f"Binary: {identity.binary_name}")
        >>> print(f"Vendor: {identity.vendor}")
    """
    cache = IdentityCache()

    # Try to get from cache or override
    identity = cache.get("default")
    if identity is not None:
        return identity

    # Load using discovery
    identity = load()

    # Cache the result
    cache.set("default", identity)

    return identity


def reload_identity() -> AppIdentity:
    """
    Reload the application identity, bypassing cache.

    This function forces a fresh load of the application identity,
    clearing any cached values and returning the newly loaded identity.

    Returns:
        The freshly loaded application identity

    Raises:
        AppIdentityNotFoundError: If no identity configuration is found
        AppIdentityValidationError: If the configuration is invalid
        AppIdentityError: For other loading errors
    """
    cache = IdentityCache()
    cache.reload()

    # Load fresh identity
    identity = load()

    # Cache the new result
    cache.set("default", identity)

    return identity


def clear_identity_cache() -> None:
    """
    Clear the application identity cache.

    This function clears all cached application identities. The next call
    to get_identity() will trigger a fresh load.
    """
    cache = IdentityCache()
    cache.clear()
