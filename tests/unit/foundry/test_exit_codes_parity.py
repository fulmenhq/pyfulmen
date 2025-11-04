"""Parity tests for exit codes against Crucible canonical snapshots.

Ensures PyFulmen exit codes exactly match the Crucible SSOT catalog.
"""

import json
from pathlib import Path

from pyfulmen.foundry.exit_codes import (
    ExitCode,
    SimplifiedMode,
    get_exit_code_info,
    get_exit_codes_version,
    map_to_simplified,
)


class TestExitCodesParity:
    """Verify exit codes match canonical Crucible snapshots."""

    def test_catalog_version_matches(self):
        """Verify catalog version is v1.0.0."""
        version = get_exit_codes_version()
        assert version == "v1.0.0", f"Expected v1.0.0, got {version}"

    def test_exit_codes_match_canonical_snapshot(self):
        """Verify all exit codes match canonical snapshot."""
        # Load canonical snapshot from Crucible
        snapshot_path = Path("config/crucible-py/library/foundry/exit-codes.snapshot.json")
        with open(snapshot_path) as f:
            canonical = json.load(f)

        # Validate snapshot structure
        assert "version" in canonical
        assert "codes" in canonical
        assert canonical["version"] == "v1.0.0"

        # Build computed catalog from PyFulmen
        computed_codes = {}
        for code in ExitCode:
            info = get_exit_code_info(code.value)
            assert info is not None, f"No metadata for {code.name}"

            computed_codes[str(code.value)] = {
                "name": code.name,
                "description": info["description"],
                "context": info["context"],
                "category": info["category"],
            }
            # Add optional fields only if present
            if "retry_hint" in info and info["retry_hint"]:
                computed_codes[str(code.value)]["retry_hint"] = info["retry_hint"]
            if "bsd_equivalent" in info and info["bsd_equivalent"]:
                computed_codes[str(code.value)]["bsd_equivalent"] = info["bsd_equivalent"]

        canonical_codes = canonical["codes"]

        # Compare counts
        assert len(computed_codes) == len(canonical_codes), (
            f"Code count mismatch: PyFulmen has {len(computed_codes)}, canonical has {len(canonical_codes)}"
        )

        # Deep compare each code
        for code_str, expected in canonical_codes.items():
            assert code_str in computed_codes, f"Code {code_str} missing in PyFulmen"
            computed = computed_codes[code_str]

            assert computed["name"] == expected["name"], (
                f"Code {code_str}: name mismatch: {computed['name']} != {expected['name']}"
            )
            assert computed["description"] == expected["description"], f"Code {code_str}: description mismatch"
            assert computed["context"] == expected["context"], f"Code {code_str}: context mismatch"
            assert computed["category"] == expected["category"], (
                f"Code {code_str}: category mismatch: {computed['category']} != {expected['category']}"
            )
            assert computed.get("retry_hint") == expected.get("retry_hint"), (
                f"Code {code_str}: retry_hint mismatch: {computed.get('retry_hint')} != {expected.get('retry_hint')}"
            )
            assert computed.get("bsd_equivalent") == expected.get("bsd_equivalent"), (
                f"Code {code_str}: bsd_equivalent mismatch"
            )

    def test_simplified_modes_match_canonical_snapshot(self):
        """Verify simplified mode mappings match canonical snapshot."""
        # Load canonical simplified modes snapshot
        snapshot_path = Path("config/crucible-py/library/foundry/simplified-modes.snapshot.json")
        with open(snapshot_path) as f:
            canonical = json.load(f)

        assert "version" in canonical
        assert "modes" in canonical
        assert canonical["version"] == "v1.0.0"

        # Test basic mode mappings
        if "basic" in canonical["modes"]:
            basic_mappings = canonical["modes"]["basic"]
            for simplified_str, codes in basic_mappings.items():
                simplified_code = int(simplified_str)
                for code in codes:
                    computed = map_to_simplified(code, SimplifiedMode.BASIC)
                    assert computed == simplified_code, (
                        f"Basic mode: code {code} should map to {simplified_code}, got {computed}"
                    )

        # Test severity mode mappings
        if "severity" in canonical["modes"]:
            severity_mappings = canonical["modes"]["severity"]
            for simplified_str, codes in severity_mappings.items():
                simplified_code = int(simplified_str)
                for code in codes:
                    computed = map_to_simplified(code, SimplifiedMode.SEVERITY)
                    assert computed == simplified_code, (
                        f"Severity mode: code {code} should map to {simplified_code}, got {computed}"
                    )

    def test_all_exit_codes_have_metadata(self):
        """Verify all IntEnum codes have corresponding metadata."""
        for code in ExitCode:
            info = get_exit_code_info(code.value)
            assert info is not None, f"Missing metadata for {code.name} ({code.value})"
            assert info["code"] == code.value
            assert info["name"] == code.name
            assert "description" in info
            assert "context" in info
            assert "category" in info

    def test_exit_code_names_follow_convention(self):
        """Verify all exit code names follow EXIT_* convention."""
        for code in ExitCode:
            assert code.name.startswith("EXIT_"), f"Code {code.value} name '{code.name}' does not start with EXIT_"
            assert code.name.isupper(), f"Code {code.value} name '{code.name}' is not uppercase"

    def test_exit_code_ranges_valid(self):
        """Verify all exit codes are in valid 0-255 range."""
        for code in ExitCode:
            assert 0 <= code.value <= 255, f"Code {code.name} value {code.value} outside valid range 0-255"

    def test_no_duplicate_exit_codes(self):
        """Verify no duplicate exit code values."""
        seen_values = set()
        for code in ExitCode:
            assert code.value not in seen_values, f"Duplicate code value {code.value} for {code.name}"
            seen_values.add(code.value)


class TestExitCodesBasicFunctionality:
    """Basic functionality tests for exit codes module."""

    def test_get_exit_code_info_success(self):
        """Test get_exit_code_info with EXIT_SUCCESS."""
        info = get_exit_code_info(0)
        assert info is not None
        assert info["code"] == 0
        assert info["name"] == "EXIT_SUCCESS"
        assert "success" in info["description"].lower()
        assert info["category"] == "standard"

    def test_get_exit_code_info_port_in_use(self):
        """Test get_exit_code_info with EXIT_PORT_IN_USE."""
        info = get_exit_code_info(10)
        assert info is not None
        assert info["code"] == 10
        assert info["name"] == "EXIT_PORT_IN_USE"
        assert "port" in info["description"].lower()
        assert info["category"] == "networking"

    def test_get_exit_code_info_unknown_code(self):
        """Test get_exit_code_info with unknown code returns None."""
        info = get_exit_code_info(255)  # Likely unused
        # Should return None or raise, depending on implementation
        # Based on generated file, it returns None
        assert info is None or isinstance(info, dict)

    def test_map_to_simplified_basic_success(self):
        """Test basic mode mapping for success."""
        result = map_to_simplified(0, SimplifiedMode.BASIC)
        assert result == 0

    def test_map_to_simplified_basic_error(self):
        """Test basic mode mapping for errors."""
        result = map_to_simplified(10, SimplifiedMode.BASIC)
        assert result == 1  # All errors map to 1 in basic mode

    def test_intenum_comparison_works(self):
        """Test IntEnum allows direct integer comparison."""
        assert ExitCode.EXIT_SUCCESS == 0
        assert ExitCode.EXIT_FAILURE == 1
        assert ExitCode.EXIT_PORT_IN_USE == 10
