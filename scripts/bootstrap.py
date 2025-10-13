#!/usr/bin/env python3
"""Bootstrap script for installing Goneat and other required tools.

This script:
1. Prefers .goneat/tools.local.yaml (local dev) over tools.yaml (production)
2. Parses the manifest and installs tools to bin/
3. Supports install types: link, download
4. Verifies checksums for downloads
5. Makes binaries executable

Usage:
    python scripts/bootstrap.py [--force]

Options:
    --force    Reinstall even if binary already exists
"""

import argparse
import hashlib
import platform
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("❌ Error: PyYAML is required for bootstrap")
    print("Install it with: pip install pyyaml")
    print("Or run: uv sync")
    sys.exit(1)


def get_platform_info() -> tuple[str, str]:
    """Get current OS and architecture in FulDX format."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize OS name
    if system == "darwin":
        os_name = "darwin"
    elif system == "linux":
        os_name = "linux"
    elif system == "windows":
        os_name = "windows"
    else:
        raise ValueError(f"Unsupported OS: {system}")

    # Normalize architecture
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise ValueError(f"Unsupported architecture: {machine}")

    return os_name, arch


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def install_via_link(source: str, destination: Path, bin_name: str) -> None:
    """Install tool by copying from local source."""
    source_path = Path(source).expanduser().resolve()

    if not source_path.exists():
        raise FileNotFoundError(f"Source binary not found: {source_path}")

    if not source_path.is_file():
        raise ValueError(f"Source is not a file: {source_path}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    dest_file = destination.parent / bin_name

    print(f"  📦 Copying from {source_path}")
    shutil.copy2(source_path, dest_file)

    # Make executable
    dest_file.chmod(0o755)
    print(f"  ✓ Installed to {dest_file}")


def install_via_download(
    url: str,
    destination: Path,
    bin_name: str,
    checksum: dict[str, str] | None = None,
) -> None:
    """Install tool by downloading from URL."""
    os_name, arch = get_platform_info()
    platform_key = f"{os_name}-{arch}"

    # Substitute platform variables in URL
    download_url = url.replace("{{os}}", os_name).replace("{{arch}}", arch)

    destination.parent.mkdir(parents=True, exist_ok=True)
    dest_file = destination.parent / bin_name
    temp_file = dest_file.with_suffix(".tmp")

    try:
        print(f"  📥 Downloading from {download_url}")
        urllib.request.urlretrieve(download_url, temp_file)

        # Verify checksum if provided
        if checksum and platform_key in checksum:
            expected = checksum[platform_key]
            # Skip verification for provisional checksums (all zeros)
            if expected != "0" * 64:
                actual = compute_sha256(temp_file)
                if actual != expected:
                    raise ValueError(
                        f"Checksum mismatch!\n  Expected: {expected}\n  Got:      {actual}"
                    )
                print("  ✓ Checksum verified")
            else:
                print("  ⚠️  Skipping checksum (provisional placeholder)")

        # Move to final location and make executable
        shutil.move(temp_file, dest_file)
        dest_file.chmod(0o755)
        print(f"  ✓ Installed to {dest_file}")

    except Exception as e:
        # Clean up temp file on error
        if temp_file.exists():
            temp_file.unlink()
        raise e


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load and parse tools manifest YAML."""
    with open(manifest_path) as f:
        return yaml.safe_load(f)


def bootstrap_tools(force: bool = False) -> None:
    """Bootstrap tools from manifest."""
    repo_root = Path(__file__).parent.parent

    # Prefer local override, fall back to production manifest
    local_manifest = repo_root / ".goneat" / "tools.local.yaml"
    prod_manifest = repo_root / ".goneat" / "tools.yaml"

    if local_manifest.exists():
        manifest_path = local_manifest
        print(f"🔧 Using local development manifest: {local_manifest}")
    elif prod_manifest.exists():
        manifest_path = prod_manifest
        print(f"🔧 Using production manifest: {prod_manifest}")
    else:
        print("❌ No tools manifest found!")
        print(f"  Expected: {prod_manifest}")
        sys.exit(1)

    # Load manifest
    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        print(f"❌ Failed to parse manifest: {e}")
        sys.exit(1)

    # Get bin directory
    bin_dir = repo_root / manifest.get("binDir", "./bin")

    # Process each tool
    tools = manifest.get("tools", [])
    if not tools:
        print("⚠️  No tools defined in manifest")
        return

    print(f"\n📦 Installing {len(tools)} tool(s)...")

    for tool in tools:
        tool_id = tool.get("id", "unknown")
        install_config = tool.get("install", {})
        install_type = install_config.get("type")
        bin_name = install_config.get("binName", tool_id)
        dest_path = bin_dir / bin_name

        print(f"\n🔨 {tool_id}")

        # Check if already installed
        if dest_path.exists() and not force:
            print(f"  ✓ Already installed at {dest_path}")
            continue

        # Install based on type
        try:
            if install_type == "link":
                source = install_config.get("source")
                if not source:
                    print("  ❌ Missing 'source' for type: link")
                    continue
                install_via_link(source, dest_path, bin_name)

            elif install_type == "download":
                url = install_config.get("url")
                checksum = install_config.get("checksum")
                if not url:
                    print("  ❌ Missing 'url' for type: download")
                    continue
                install_via_download(url, dest_path, bin_name, checksum)

            else:
                print(f"  ⚠️  Unsupported install type: {install_type}")
                continue

        except Exception as e:
            print(f"  ❌ Installation failed: {e}")
            if tool.get("required", False):
                sys.exit(1)

    print("\n✅ Bootstrap complete!\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Goneat and required tools")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reinstall even if binary already exists",
    )
    args = parser.parse_args()

    bootstrap_tools(force=args.force)


if __name__ == "__main__":
    main()
