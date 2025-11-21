# Fulpack Archive Module

Fulpack provides secure, enterprise-grade archive operations for the PyFulmen library. It implements a canonical façade pattern for standard Python archive libraries (`tarfile`, `zipfile`, `gzip`), enforcing security guardrails by default.

## Features

- **Canonical API**: Consistent `create`, `extract`, `scan`, `verify`, `info` operations across all formats.
- **Security by Default**:
    - **Path Traversal Protection**: Prevents extraction outside the target directory (Zip Slip).
    - **Decompression Bomb Guard**: Detects and blocks massive expansion attacks (Zip Bombs).
    - **Checksum Verification**: Validates integrity where supported.
    - **Symlink Safety**: Validates symlink targets to prevent escapes.
- **Format Support**:
    - `tar.gz` / `tgz` (Common)
    - `zip` (Common)
    - `gzip` / `gz` (Single file)
    - Extensible architecture for future formats (7z, etc.)
- **Pathfinder Integration**: Unified file discovery inside archives (via `scan`).

## Usage

### Basic Operations

```python
from pyfulmen import fulpack
from pyfulmen.fulpack import ArchiveFormat

# Create an archive
info = fulpack.create(
    source=["src/", "docs/"],
    output="release.tar.gz",
    format=ArchiveFormat.TAR_GZ
)
print(f"Created archive with {info.entry_count} entries")

# Extract securely
result = fulpack.extract(
    archive="release.tar.gz",
    destination="/tmp/extracted"
)
print(f"Extracted {result.extracted_count} files")
```

### Scanning Content

Inspect archive contents without extracting them (faster and safer):

```python
# Scan entries
entries = fulpack.scan("release.tar.gz")

for entry in entries:
    print(f"{entry.path} ({entry.size} bytes)")

# Find specific files
csv_files = [e for e in entries if e.path.endswith(".csv")]
```

### Verification

Verify archive integrity and security checks before trusting it:

```python
result = fulpack.verify("upload.zip")

if result.valid:
    print("Archive is safe and valid")
else:
    print(f"Validation failed: {result.errors}")
```

### Metadata Inspection

Get quick stats about an archive:

```python
info = fulpack.info("backup.zip")

print(f"Format: {info.format}")
print(f"Entries: {info.entry_count}")
print(f"Compression Ratio: {info.compression_ratio:.2f}x")
```

## API Reference

### `create()`

Creates an archive from source files or directories.

```python
def create(
    source: str | list[str],
    output: str,
    format: ArchiveFormat,
    options: CreateOptions | None = None
) -> ArchiveInfo:
```

**Options**:
- `compression_level` (int): 0-9 (default 6 for tar/zip, 9 for gzip).
- `checksum_algorithm` (str): "sha256" (default), "sha512", "md5", etc.
- `patterns` (dict): include/exclude glob patterns (not yet implemented in v0.1.11).

### `extract()`

Extracts archive contents to a destination directory.

```python
def extract(
    archive: str,
    destination: str,
    options: ExtractOptions | None = None
) -> ExtractResult:
```

**Options**:
- `max_size` (int): Max uncompressed size for a single entry (default 1GB).
- `max_entries` (int): Max number of entries to extract (default 10,000).
- `overwrite` (bool): Whether to overwrite existing files (default False - NOT IMPLEMENTED yet, currently overwrites).

### `scan()`

Returns a list of archive entries without extracting.

```python
def scan(
    archive: str,
    options: ScanOptions | None = None
) -> list[ArchiveEntry]:
```

### `verify()`

Performs security and integrity checks.

```python
def verify(archive: str) -> ValidationResult:
```

### `info()`

Returns archive metadata.

```python
def info(archive: str) -> ArchiveInfo:
```

## Security Model

Fulpack enforces strict security controls:

1.  **Path Traversal**: All paths are normalized. Any entry attempting to write outside the destination (e.g., `../../etc/passwd`) is rejected.
2.  **Decompression Bombs**: Ratio checks and absolute size limits prevent disk/memory exhaustion. Default limits: 1GB per entry, 10GB total, 100:1 ratio.
3.  **Symlinks**: Symlinks are validated. Escaping symlinks are blocked.

## Extension Architecture

Fulpack uses a pluggable architecture. Format handlers are registered at runtime.

```python
from pyfulmen.fulpack.formats import register_format, FormatHandler
from crucible.fulpack import ArchiveFormat

class MyCustomHandler(FormatHandler):
    ...

register_format(ArchiveFormat.CUSTOM, MyCustomHandler())
```

## Supported Formats

| Format | Extension | Handler | Notes |
|--------|-----------|---------|-------|
| TAR | `.tar` | `TarHandler` | Uncompressed tarball |
| TAR.GZ | `.tar.gz`, `.tgz` | `TarHandler` | Gzip-compressed tarball |
| ZIP | `.zip` | `ZipHandler` | Standard ZIP (deflate) |
| GZIP | `.gz`, `.gzip` | `GzipHandler` | Single file compression |
