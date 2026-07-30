"""Tests for the top-level pyfulmen package export surface."""

import pyfulmen

EXPECTED_SUBMODULES = [
    "appidentity",
    "ascii",
    "config",
    "crucible",
    "docscribe",
    "error_handling",
    "foundry",
    "fulhash",
    "fulpack",
    "logging",
    "pathfinder",
    "schema",
    "signals",
    "similarity",
    "telemetry",
    "version",
]


class TestTopLevelExports:
    """Test pyfulmen.__all__ and eager submodule imports."""

    def test_all_contains_expected_submodules(self):
        for name in EXPECTED_SUBMODULES:
            assert name in pyfulmen.__all__, f"{name} missing from pyfulmen.__all__"

    def test_all_is_alphabetical(self):
        assert list(pyfulmen.__all__) == sorted(pyfulmen.__all__)

    def test_all_entries_resolve(self):
        for name in pyfulmen.__all__:
            assert hasattr(pyfulmen, name), f"pyfulmen.{name} not importable"

    def test_version_exported(self):
        assert "__version__" in pyfulmen.__all__
        assert isinstance(pyfulmen.__version__, str)

    def test_fulhash_accessible_without_explicit_import(self):
        digest = pyfulmen.fulhash.hash_bytes(b"Hello, World!")
        assert digest.formatted == "xxh3-128:531df2844447dd5077db03842cd75395"

    def test_verify_names_are_module_qualified(self):
        """fulhash.verify (checksum) and fulpack.verify (archive) coexist."""
        assert callable(pyfulmen.fulhash.verify)
        assert hasattr(pyfulmen.fulpack, "verify")
        assert pyfulmen.fulhash.verify is not pyfulmen.fulpack.verify
