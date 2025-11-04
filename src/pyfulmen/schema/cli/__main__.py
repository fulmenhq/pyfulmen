"""Entry point for pyfulmen.schema.cli module."""

import sys
from pathlib import Path

# Add src to sys.path so we can import pyfulmen
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from pyfulmen.schema.cli import main

if __name__ == "__main__":
    exit(main())
