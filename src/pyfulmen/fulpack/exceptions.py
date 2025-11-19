"""Exception classes for fulpack module."""


class FulpackError(Exception):
    """Base exception for fulpack operations.

    All fulpack exceptions derive from this base class.
    Includes optional context dict for structured error information.

    Attributes:
        message: Error message
        context: Optional context dict with error details
        code: Optional error code (from Foundry exit codes)
    """

    def __init__(
        self,
        message: str,
        *,
        context: dict | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize FulpackError.

        Args:
            message: Error message
            context: Optional context dict
            code: Optional error code
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.code = code


class PathTraversalError(FulpackError):
    """Raised when path traversal attack is detected."""

    pass


class DecompressionBombError(FulpackError):
    """Raised when decompression bomb is detected."""

    pass


class SymlinkError(FulpackError):
    """Raised when symlink validation fails."""

    pass


class ChecksumMismatchError(FulpackError):
    """Raised when checksum verification fails."""

    pass


class InvalidFormatError(FulpackError):
    """Raised when archive format is invalid or unsupported."""

    pass
