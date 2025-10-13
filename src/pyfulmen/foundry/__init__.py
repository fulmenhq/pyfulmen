"""
Foundry - Pattern catalog and Python foundation utilities for pyfulmen.

This module provides:
- Base Pydantic models with Fulmen conventions (FulmenDataModel, FulmenConfigModel, etc.)
- RFC3339Nano timestamp generation
- UUIDv7 correlation ID generation
- Pattern catalog for regex, MIME types, HTTP statuses, country codes
"""

from .catalog import (
    FoundryCatalog,
    HttpStatusCode,
    HttpStatusGroup,
    HttpStatusHelper,
    MimeType,
    Pattern,
    PatternAccessor,
    get_default_catalog,
    get_mime_type,
    get_mime_type_by_extension,
    get_pattern,
    is_client_error,
    is_server_error,
    is_success,
)
from .models import (
    FulmenBaseModel,
    FulmenCatalogModel,
    FulmenConfigModel,
    FulmenDataModel,
    generate_correlation_id,
    utc_now_rfc3339nano,
)

__all__ = [
    "FulmenBaseModel",
    "FulmenDataModel",
    "FulmenConfigModel",
    "FulmenCatalogModel",
    "utc_now_rfc3339nano",
    "generate_correlation_id",
    "Pattern",
    "MimeType",
    "HttpStatusCode",
    "HttpStatusGroup",
    "FoundryCatalog",
    "PatternAccessor",
    "HttpStatusHelper",
    "get_default_catalog",
    "get_pattern",
    "get_mime_type",
    "get_mime_type_by_extension",
    "is_success",
    "is_client_error",
    "is_server_error",
]
