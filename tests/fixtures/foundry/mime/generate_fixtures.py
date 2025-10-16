"""Generate binary fixtures for MIME detection tests."""

from pathlib import Path

FIXTURE_DIR = Path(__file__).parent


def generate_binary_unknown():
    """Generate binary file with no recognizable pattern."""
    data = bytes([0x00, 0x01, 0x02, 0x03, 0xFF, 0xFE, 0xFD, 0xFC])
    (FIXTURE_DIR / "binary-unknown.bin").write_bytes(data)


def generate_json_with_bom():
    """Generate JSON file with UTF-8 BOM."""
    bom = b"\xef\xbb\xbf"
    json_data = b'{"key": "value", "bom": true}'
    (FIXTURE_DIR / "json-with-utf8-bom.json").write_bytes(bom + json_data)


if __name__ == "__main__":
    generate_binary_unknown()
    generate_json_with_bom()
    print("✅ Fixtures generated")
