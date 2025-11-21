"""Example usage of the Fulpack archive module."""

import shutil
from pathlib import Path

from pyfulmen import fulpack
from pyfulmen.fulpack import ArchiveFormat, CreateOptions, ExtractOptions


def main():
    """Run fulpack examples."""
    # Setup test data
    source_dir = Path("example_data")
    if source_dir.exists():
        shutil.rmtree(source_dir)
    source_dir.mkdir()

    (source_dir / "hello.txt").write_text("Hello World")
    (source_dir / "data.csv").write_text("id,name\n1,Test")
    (source_dir / "nested").mkdir()
    (source_dir / "nested" / "config.json").write_text("{}")

    print("--- Creating Archives ---")

    # 1. Create TAR.GZ
    print("\nCreating TAR.GZ...")
    info_tar = fulpack.create(
        source=[str(source_dir)],
        output="example.tar.gz",
        format=ArchiveFormat.TAR_GZ,
        options=CreateOptions(compression_level=6),
    )
    print(f"Created {info_tar.format} with {info_tar.entry_count} entries")
    print(f"Compression ratio: {info_tar.compression_ratio:.2f}x")

    # 2. Create ZIP
    print("\nCreating ZIP...")
    info_zip = fulpack.create(source=[str(source_dir)], output="example.zip", format=ArchiveFormat.ZIP)
    print(f"Created {info_zip.format} with {info_zip.entry_count} entries")

    # 3. Create GZIP (single file)
    print("\nCreating GZIP...")
    info_gz = fulpack.create(source=[str(source_dir / "data.csv")], output="data.csv.gz", format=ArchiveFormat.GZIP)
    print(f"Created {info_gz.format} from single file")

    print("\n--- Scanning Archives ---")

    # Scan ZIP
    print("\nScanning ZIP contents:")
    entries = fulpack.scan("example.zip")
    for entry in entries:
        print(f"- {entry.path} ({entry.size} bytes)")

    print("\n--- Extracting Archives ---")

    # Extract TAR.GZ
    output_dir = Path("output_tar")
    print(f"\nExtracting to {output_dir}...")
    result = fulpack.extract(
        archive="example.tar.gz", destination=str(output_dir), options=ExtractOptions(max_entries=100)
    )
    print(f"Extracted {result.extracted_count} files")

    if result.error_count > 0:
        print(f"Errors: {result.errors}")

    print("\n--- Verification ---")

    # Verify ZIP
    print("\nVerifying ZIP integrity...")
    val_result = fulpack.verify("example.zip")
    if val_result.valid:
        print("Archive is valid")
        print(f"Verified {val_result.checksums_verified} checksums")
    else:
        print(f"Validation failed: {val_result.errors}")

    # Cleanup
    print("\nCleaning up...")
    shutil.rmtree(source_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    Path("example.tar.gz").unlink()
    Path("example.zip").unlink()
    Path("data.csv.gz").unlink()
    print("Done.")


if __name__ == "__main__":
    main()
