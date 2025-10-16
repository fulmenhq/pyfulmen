"""MIME type detection from byte signatures (magic numbers).

Provides content-based MIME type identification to complement extension-based
detection. Implements byte signature detection for JSON, XML, YAML, CSV, and
plain text formats with full gofulmen v0.1.1 API parity.
"""

import io
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .catalog import MimeType

__all__ = [
    "detect_mime_type",
    "detect_mime_type_from_reader",
    "detect_mime_type_from_file",
]


def _trim_bom_and_whitespace(data: bytes) -> bytes:
    """Remove byte order marks (BOM) and leading whitespace.

    Critical for accurate MIME detection since real-world files often
    start with BOM or whitespace.

    Handles:
    - UTF-8 BOM: EF BB BF
    - UTF-16 LE BOM: FF FE
    - UTF-16 BE BOM: FE FF
    - Leading whitespace: space, tab, newline, carriage return

    Args:
        data: Raw bytes

    Returns:
        Trimmed bytes with BOM and whitespace removed

    Example:
        >>> data = b"\\xef\\xbb\\xbf  {\\"key\\": \\"value\\"}"
        >>> _trim_bom_and_whitespace(data)
        b'{"key": "value"}'
    """
    # Remove UTF-8 BOM (EF BB BF)
    if len(data) >= 3 and data[:3] == b"\xef\xbb\xbf":
        data = data[3:]

    # Remove UTF-16 BOM (FF FE or FE FF)
    if len(data) >= 2 and data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        data = data[2:]

    # Trim leading whitespace
    start = 0
    while start < len(data):
        if data[start] in (ord(" "), ord("\t"), ord("\n"), ord("\r")):
            start += 1
        else:
            break

    return data[start:]


def _is_text_content(data: bytes) -> bool:
    """Check if data is printable text (>80% printable).

    Uses heuristic: if more than 80% of bytes are printable ASCII or valid
    UTF-8, consider the content as text.

    Args:
        data: Raw bytes to check

    Returns:
        True if content appears to be text, False otherwise

    Example:
        >>> _is_text_content(b"Hello, world!")
        True
        >>> _is_text_content(b"\\x00\\x01\\x02\\xFF\\xFE")
        False
    """
    if not data:
        return False

    printable_count = 0
    for byte in data:
        # Printable ASCII (32-126) or whitespace or UTF-8 continuation/multi-byte (>=128)
        if (32 <= byte <= 126) or byte in (ord("\n"), ord("\r"), ord("\t")) or byte >= 128:
            printable_count += 1

    # If more than 80% is printable, consider it text
    return (printable_count / len(data)) > 0.8


def _detect_json(trimmed: bytes) -> bool:
    """Detect JSON from content signature.

    JSON detection heuristic:
    - Starts with '{' (object) or '[' (array)
    - Contains JSON structural characters in first 50 bytes

    Args:
        trimmed: BOM/whitespace-trimmed bytes

    Returns:
        True if content appears to be JSON
    """
    if not trimmed:
        return False

    # Check for JSON start characters
    if trimmed[0] in (ord("{"), ord("[")):
        # Validate JSON-like structure in first 50 bytes
        sample = trimmed[: min(len(trimmed), 50)]
        # Look for JSON structural characters
        for byte in sample:
            if byte in (ord("{"), ord("["), ord('"'), ord(":")):
                return True

    return False


def _detect_xml(trimmed: bytes) -> bool:
    """Detect XML from content signature.

    XML detection: looks for '<?xml' declaration at start.

    Args:
        trimmed: BOM/whitespace-trimmed bytes

    Returns:
        True if content appears to be XML
    """
    if len(trimmed) < 5:
        return False

    # Check for XML declaration
    return trimmed[0] == ord("<") and trimmed[:5] == b"<?xml"


def _detect_yaml(trimmed: bytes) -> bool:
    """Detect YAML from content heuristics.

    YAML detection heuristic:
    - Does NOT start with '{', '[', or '<'
    - Contains 'key: value' patterns (colon followed by space or newline)

    Args:
        trimmed: BOM/whitespace-trimmed bytes

    Returns:
        True if content appears to be YAML
    """
    if not trimmed or trimmed[0] in (ord("{"), ord("["), ord("<")):
        return False

    # Look for YAML key: value patterns in first 200 bytes
    sample = trimmed[: min(len(trimmed), 200)]
    try:
        text = sample.decode("utf-8", errors="ignore")
    except Exception:
        return False

    # Check for colon followed by space or newline
    return any(text[i] == ":" and text[i + 1] in (" ", "\n") for i in range(len(text) - 1))


def _detect_csv(data: bytes) -> bool:
    """Detect CSV from comma patterns.

    CSV detection heuristic:
    - First line contains 2 or more commas

    Args:
        data: Raw bytes (not trimmed)

    Returns:
        True if content appears to be CSV
    """
    # Get first line (up to 200 bytes)
    first_line = data[: min(len(data), 200)]
    newline_idx = first_line.find(b"\n")
    if newline_idx != -1:
        first_line = first_line[:newline_idx]

    # Count commas (CSV needs at least 2)
    comma_count = first_line.count(b",")
    return comma_count >= 2


def detect_mime_type(data: bytes) -> "MimeType | None":
    """Detect MIME type from raw bytes.

    Performs content-based detection using magic numbers and patterns.
    Returns None if content cannot be identified (not an error).

    Detection order:
    1. JSON (starts with { or [)
    2. XML (starts with <?xml)
    3. YAML (has key: value patterns)
    4. CSV (2+ commas in first line)
    5. Plain text (>80% printable)
    6. Unknown (returns None)

    Args:
        data: Raw bytes to analyze

    Returns:
        MimeType instance if detected, None if unknown

    Example:
        >>> data = b'{"key": "value"}'
        >>> mime = detect_mime_type(data)
        >>> mime.mime
        'application/json'

        >>> binary_data = b'\\x00\\x01\\x02\\xFF\\xFE'
        >>> detect_mime_type(binary_data)
        None
    """
    from .catalog import get_default_catalog

    # Empty input returns None
    if not data:
        return None

    # Get catalog
    catalog = get_default_catalog()

    # Trim BOM and whitespace for accurate signature detection
    trimmed = _trim_bom_and_whitespace(data)
    if not trimmed:
        return None

    # Check for common file signatures (detection order matters)

    # JSON: starts with { or [
    if _detect_json(trimmed):
        return catalog.get_mime_type("json")

    # XML: starts with <?xml
    if _detect_xml(trimmed):
        return catalog.get_mime_type("xml")

    # YAML: has key: value patterns
    if _detect_yaml(trimmed):
        return catalog.get_mime_type("yaml")

    # CSV: has 2+ commas in first line
    if _detect_csv(data):  # Use original data, not trimmed
        return catalog.get_mime_type("csv")

    # Plain text: >80% printable
    if _is_text_content(data[: min(len(data), 512)]):
        return catalog.get_mime_type("plain-text")

    # Unknown/binary
    return None


def detect_mime_type_from_reader(
    reader: io.IOBase, max_bytes: int = 512
) -> tuple["MimeType | None", io.IOBase]:
    """Detect MIME type from streaming data without consuming stream.

    Reads up to max_bytes from reader, detects MIME type, and returns
    a new reader that includes the already-read bytes for continued processing.

    This is critical for HTTP request body inspection and streaming scenarios
    where the data needs to be processed after detection.

    Args:
        reader: Input stream (file-like object supporting read())
        max_bytes: Maximum bytes to read for detection (default 512)
                   If <= 0, uses 512 as default

    Returns:
        Tuple of (MimeType or None, new_reader with buffered bytes)

    Raises:
        IOError: If reading from stream fails

    Example:
        >>> with open('upload.dat', 'rb') as f:
        ...     mime, reader = detect_mime_type_from_reader(f)
        ...     if mime and mime.id == 'json':
        ...         # Continue processing with reader
        ...         data = json.load(reader)

        >>> # HTTP request body detection
        >>> mime, body_reader = detect_mime_type_from_reader(request.body, 512)
        >>> if mime and mime.id == 'json':
        ...     process_json(body_reader)
    """
    # Default maxBytes if not specified or invalid
    if max_bytes <= 0:
        max_bytes = 512

    # Read detection buffer
    try:
        buf = reader.read(max_bytes)
    except Exception as e:
        raise OSError(f"Failed to read from stream: {e}") from e

    # Detect MIME type from buffer
    mime_type = detect_mime_type(buf)

    # Create new reader with buffered bytes + remaining stream
    # Python pattern: Chain BytesIO with original reader
    if hasattr(reader, "read"):
        # Create a chained reader that returns buffered bytes first,
        # then continues with original reader (mirrors Go's MultiReader).
        class ChainedReader:
            def __init__(self, first: bytes, second: io.IOBase):
                self._first = io.BytesIO(first)
                self._first_len = len(first)
                self._second = second
                self._first_exhausted = False

            def readable(self) -> bool:
                return True

            def read(self, size: int = -1) -> bytes:
                if not self._first_exhausted:
                    data = self._first.read(size)
                    if size == -1:
                        self._first_exhausted = True
                        return data + self._second.read()
                    if len(data) == size:
                        if self._first.tell() >= self._first_len:
                            self._first_exhausted = True
                        return data
                    self._first_exhausted = True
                    remaining = size - len(data)
                    return data + self._second.read(remaining)
                return self._second.read(size)

            def readline(self, size: int = -1) -> bytes:
                if not self._first_exhausted:
                    line = self._first.readline(size)
                    if line:
                        if size != -1 and len(line) >= size:
                            if self._first.tell() >= self._first_len:
                                self._first_exhausted = True
                            return line[:size]
                        if line.endswith(b"\n") or self._first.tell() >= self._first_len:
                            if self._first.tell() >= self._first_len:
                                self._first_exhausted = True
                            return line
                        self._first_exhausted = True
                        remainder_size = -1 if size == -1 else size - len(line)
                        second_line = (
                            self._second.readline(remainder_size)
                            if hasattr(self._second, "readline")
                            else self._second.read(remainder_size)
                        )
                        return line + second_line
                    self._first_exhausted = True
                if hasattr(self._second, "readline"):
                    return self._second.readline(size)
                return self._second.read(size)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                if hasattr(self._second, "__exit__"):
                    return self._second.__exit__(*args)
                return None

            def close(self) -> None:
                try:
                    self._first.close()
                finally:
                    if hasattr(self._second, "close"):
                        self._second.close()

        new_reader = ChainedReader(buf, reader)
    else:
        # Fallback: just return BytesIO with buffered data
        new_reader = io.BytesIO(buf)

    return mime_type, new_reader


def detect_mime_type_from_file(path: str | Path) -> "MimeType | None":
    """Detect MIME type from file path.

    Opens file, reads beginning for detection, closes file.
    Returns None for empty files (not an error).

    Args:
        path: File path (string or Path object)

    Returns:
        MimeType instance if detected, None if unknown or empty

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read

    Example:
        >>> mime = detect_mime_type_from_file('config.json')
        >>> if mime:
        ...     print(f'Detected: {mime.mime}')
        Detected: application/json

        >>> # Empty file returns None (not error)
        >>> detect_mime_type_from_file('empty.txt')
        None
    """
    path = Path(path) if isinstance(path, str) else path

    # Open and read first 512 bytes
    try:
        with path.open("rb") as f:
            data = f.read(512)
    except FileNotFoundError:
        raise
    except Exception as e:
        raise OSError(f"Failed to read file: {e}") from e

    # Empty file returns None (not an error)
    if not data:
        return None

    # Detect from bytes
    return detect_mime_type(data)
