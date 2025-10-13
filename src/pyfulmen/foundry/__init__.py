"""
Foundry - Pattern catalog and Python foundation utilities for pyfulmen.

This module provides:
- Base Pydantic models with Fulmen conventions (FulmenDataModel, FulmenConfigModel, etc.)
- RFC3339Nano timestamp generation
- UUIDv7 correlation ID generation
- Pattern catalog for regex, MIME types, HTTP statuses, country codes
"""

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
]
