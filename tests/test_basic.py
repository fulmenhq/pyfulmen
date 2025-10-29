"""Basic smoke tests for pyfulmen."""

import pyfulmen


def test_version():
    """Test that version is defined."""
    assert hasattr(pyfulmen, "__version__")
    assert pyfulmen.__version__ == "0.1.8"
