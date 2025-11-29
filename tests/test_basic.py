"""Basic smoke tests for pyfulmen."""

import pyfulmen
from pyfulmen.version import read_version


def test_version():
    """Test that version metadata matches VERSION file."""
    assert hasattr(pyfulmen, "__version__")
    assert pyfulmen.__version__ == read_version()
