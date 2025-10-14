"""Sink implementations for log output destinations.

Provides base sink interface and concrete implementations for console,
file, and rolling file outputs. Sinks handle the final emission of
formatted log events to their destinations.

Example:
    >>> from pyfulmen.logging.sinks import ConsoleSink, FileSink
    >>> from pyfulmen.logging.formatter import JSONFormatter
    >>>
    >>> # Console sink to stderr
    >>> console = ConsoleSink(formatter=JSONFormatter())
    >>>
    >>> # File sink with JSON output
    >>> file_sink = FileSink(path="/var/log/myapp.log", formatter=JSONFormatter())
    >>>
    >>> # Emit event
    >>> event = {"timestamp": "...", "severity": "INFO", "message": "test"}
    >>> console.emit(event)
    >>> file_sink.emit(event)
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from typing import Any, TextIO


class Sink(ABC):
    """Base sink interface for log output destinations.

    Sinks are responsible for emitting formatted log events to their
    configured destinations (console, files, network, etc.). Each sink
    uses a formatter to convert events to their final output format.

    Attributes:
        formatter: Formatter instance for event serialization
    """

    def __init__(self, formatter: Any):
        """Initialize sink with formatter.

        Args:
            formatter: Formatter instance (JSONFormatter, TextFormatter, etc.)
        """
        self.formatter = formatter

    @abstractmethod
    def emit(self, event: dict[str, Any]) -> None:
        """Emit log event to destination.

        Args:
            event: Log event dictionary to emit

        Note:
            Implementations should handle errors gracefully and not
            raise exceptions that would disrupt logging.
        """

    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered output to destination.

        Called periodically or during shutdown to ensure all events
        are written to the destination.
        """

    @abstractmethod
    def close(self) -> None:
        """Close sink and release resources.

        Should be called when sink is no longer needed. After closing,
        the sink should not accept new events.
        """


class ConsoleSink(Sink):
    """Console sink that writes to stderr.

    Emits formatted log events to stderr (per progressive logging standard).
    Thread-safe with automatic flushing after each write.

    Example:
        >>> from pyfulmen.logging.sinks import ConsoleSink
        >>> from pyfulmen.logging.formatter import JSONFormatter
        >>>
        >>> sink = ConsoleSink(formatter=JSONFormatter())
        >>> event = {"timestamp": "...", "severity": "INFO", "message": "test"}
        >>> sink.emit(event)
    """

    def __init__(self, formatter: Any, stream: TextIO | None = None):
        """Initialize console sink.

        Args:
            formatter: Formatter instance for event serialization
            stream: Output stream (default: sys.stderr, dynamically resolved)
        """
        super().__init__(formatter)
        self._stream = stream  # None means use sys.stderr dynamically
        self._lock = Lock()

    def emit(self, event: dict[str, Any]) -> None:
        """Emit formatted event to stderr.

        Args:
            event: Log event dictionary to emit

        Note:
            Automatically flushes after write. Handles errors by
            printing to stderr if formatting fails.
        """
        try:
            with self._lock:
                formatted = self.formatter.format(event)
                # Use sys.stderr dynamically if no custom stream provided
                stream = self._stream if self._stream is not None else sys.stderr
                print(formatted, file=stream, flush=True)
        except Exception as e:
            # Last resort error handling - don't let logging break the app
            print(
                f"ConsoleSink: Failed to emit event: {e}",
                file=sys.stderr,
                flush=True,
            )

    def flush(self) -> None:
        """Flush stderr stream.

        Note:
            Console sink auto-flushes after each write, so this is
            primarily for explicit flush requests.
        """
        try:
            with self._lock:
                stream = self._stream if self._stream is not None else sys.stderr
                stream.flush()
        except Exception:
            pass

    def close(self) -> None:
        """Close console sink.

        Note:
            Does not close stderr stream as it's a shared resource.
            Only flushes pending output.
        """
        self.flush()


class FileSink(Sink):
    """File sink that writes to a specified path.

    Emits formatted log events to a file with thread-safe writes.
    Creates parent directories if they don't exist. Appends to
    existing files by default.

    Example:
        >>> from pyfulmen.logging.sinks import FileSink
        >>> from pyfulmen.logging.formatter import JSONFormatter
        >>>
        >>> sink = FileSink(
        ...     path="/var/log/myapp.log",
        ...     formatter=JSONFormatter()
        ... )
        >>> event = {"timestamp": "...", "severity": "INFO", "message": "test"}
        >>> sink.emit(event)
    """

    def __init__(
        self,
        path: str | Path,
        formatter: Any,
        mode: str = "a",
        encoding: str = "utf-8",
    ):
        """Initialize file sink.

        Args:
            path: Path to log file
            formatter: Formatter instance for event serialization
            mode: File open mode (default: "a" for append)
            encoding: File encoding (default: "utf-8")

        Raises:
            OSError: If file cannot be opened or parent directory cannot be created
        """
        super().__init__(formatter)
        self.path = Path(path)
        self.mode = mode
        self.encoding = encoding
        self._lock = Lock()
        self._file: TextIO | None = None

        # Create parent directory if it doesn't exist
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Open file
        self._open()

    def _open(self) -> None:
        """Open log file for writing.

        Raises:
            OSError: If file cannot be opened
        """
        self._file = open(  # noqa: SIM115 - intentionally not using context manager (kept open)
            self.path, self.mode, encoding=self.encoding
        )  # type: ignore[assignment]

    def emit(self, event: dict[str, Any]) -> None:
        """Emit formatted event to file.

        Args:
            event: Log event dictionary to emit

        Note:
            Thread-safe with automatic flushing. Handles errors by
            printing to stderr if write fails.
        """
        try:
            with self._lock:
                if self._file and not self._file.closed:
                    formatted = self.formatter.format(event)
                    self._file.write(formatted + "\n")
                    self._file.flush()
        except Exception as e:
            # Last resort error handling
            print(
                f"FileSink: Failed to emit event to {self.path}: {e}",
                file=sys.stderr,
                flush=True,
            )

    def flush(self) -> None:
        """Flush file buffer to disk."""
        try:
            with self._lock:
                if self._file and not self._file.closed:
                    self._file.flush()
        except Exception:
            pass

    def close(self) -> None:
        """Close file sink and release file handle."""
        try:
            with self._lock:
                if self._file and not self._file.closed:
                    self._file.flush()
                    self._file.close()
        except Exception:
            pass


__all__ = [
    "Sink",
    "ConsoleSink",
    "FileSink",
]
