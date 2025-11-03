"""
Foundry - Pattern catalog and Python foundation utilities for pyfulmen.

This module provides:
- Base Pydantic models with Fulmen conventions (FulmenDataModel, FulmenConfigModel, etc.)
- RFC3339Nano timestamp generation
- UUIDv7 correlation ID generation
- Pattern catalog for regex, MIME types, HTTP statuses, country codes
- Exit codes with simplified mode mappings
- Text similarity and normalization utilities (similarity submodule)
"""

from . import similarity
from .catalog import (
    Country,
    FoundryCatalog,
    HttpStatusCode,
    HttpStatusGroup,
    HttpStatusHelper,
    MimeType,
    Pattern,
    PatternAccessor,
    detect_mime_type,
    detect_mime_type_from_file,
    detect_mime_type_from_reader,
    get_country,
    get_country_by_alpha3,
    get_country_by_numeric,
    get_default_catalog,
    get_mime_type,
    get_mime_type_by_extension,
    get_mime_type_by_mime_string,
    get_pattern,
    is_client_error,
    is_informational,
    is_redirect,
    is_server_error,
    is_success,
    is_supported_mime_type,
    list_countries,
    list_mime_types,
    validate_country_code,
)
from .exit_codes import (
    EXIT_CODE_METADATA,
    EXIT_CODES_VERSION,
    ExitCode,
    SimplifiedMode,
    get_detailed_codes,
    get_exit_code_info,
    get_exit_codes_version,
    map_to_simplified,
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
    "Country",
    "FoundryCatalog",
    "PatternAccessor",
    "HttpStatusHelper",
    "get_default_catalog",
    "get_pattern",
    "get_mime_type",
    "get_mime_type_by_extension",
    "get_mime_type_by_mime_string",
    "is_supported_mime_type",
    "list_mime_types",
    "detect_mime_type",
    "detect_mime_type_from_file",
    "detect_mime_type_from_reader",
    "is_success",
    "is_client_error",
    "is_server_error",
    "is_informational",
    "is_redirect",
    "validate_country_code",
    "get_country",
    "get_country_by_alpha3",
    "get_country_by_numeric",
    "list_countries",
    "EXIT_CODE_METADATA",
    "EXIT_CODES_VERSION",
    "ExitCode",
    "SimplifiedMode",
    "get_detailed_codes",
    "get_exit_code_info",
    "get_exit_codes_version",
    "map_to_simplified",
    "similarity",
]
