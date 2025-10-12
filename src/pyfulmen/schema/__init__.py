"""Schema validation utilities for PyFulmen.

Provides helpers for validating data against JSON schemas from Crucible.

Example:
    >>> from pyfulmen import schema
    >>> schema.validator.validate_against_schema(
    ...     data={'severity': 'info'},
    ...     category='observability/logging',
    ...     version='v1.0.0',
    ...     name='logger-config'
    ... )
"""

from . import validator

__all__ = [
    "validator",
]
