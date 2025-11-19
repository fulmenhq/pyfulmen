"""Fulpack Enums - Generated from Crucible taxonomies.

This file is AUTO-GENERATED from the Fulpack taxonomy schemas.
DO NOT EDIT MANUALLY - changes will be overwritten.

Taxonomy Version: v1.0.0
Last Reviewed: 2025-11-12
Source: schemas/taxonomy/library/fulpack/

See: https://github.com/fulmenhq/crucible/blob/main/docs/standards/library/modules/fulpack.md
"""

from enum import Enum


class ArchiveFormat(str, Enum):
    """ArchiveFormat enum

    Generated from: schemas/taxonomy/library/fulpack/archive-formats/v1.0.0/formats.yaml
    """

    TAR = "tar"

    TAR_GZ = "tar.gz"

    ZIP = "zip"

    GZIP = "gzip"


class EntryType(str, Enum):
    """EntryType enum

    Generated from: schemas/taxonomy/library/fulpack/entry-types/v1.0.0/types.yaml
    """

    FILE = "file"

    DIRECTORY = "directory"

    SYMLINK = "symlink"


class Operation(str, Enum):
    """Operation enum

    Generated from: schemas/taxonomy/library/fulpack/operations/v1.0.0/operations.yaml
    """

    CREATE = "create"

    EXTRACT = "extract"

    SCAN = "scan"

    VERIFY = "verify"

    INFO = "info"
