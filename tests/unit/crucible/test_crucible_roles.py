"""Tests for pyfulmen.crucible role catalog.

Tests use invariant-based assertions (sorted slugs, core slugs present,
internal consistency) rather than brittle exact counts that break when
roles are added or removed upstream.
"""

import pytest

from pyfulmen.crucible import (
    AssetNotFoundError,
    RequiredReading,
    RequiredReadingFile,
    RoleEscalation,
    RoleExample,
    RoleMindset,
    RolePrompt,
    list_role_slugs,
    load_role,
    load_role_catalog,
)

# --- list_role_slugs ---


def test_list_role_slugs_returns_sorted():
    """Slugs are returned in sorted order."""
    slugs = list_role_slugs()
    assert slugs == sorted(slugs)


def test_list_role_slugs_excludes_readme():
    """README.md must not appear as a slug."""
    slugs = list_role_slugs()
    assert "README" not in slugs
    assert "README.md" not in slugs


def test_list_role_slugs_contains_core_roles():
    """Core roles that all FulmenHQ repos depend on must be present."""
    slugs = list_role_slugs()
    for core in ("devlead", "devrev", "secrev", "infoarch"):
        assert core in slugs, f"core role {core!r} missing from catalog"


def test_list_role_slugs_contains_releng():
    """releng must be present (exercises new schema fields)."""
    slugs = list_role_slugs()
    assert "releng" in slugs


# --- load_role: devlead (basic) ---


def test_load_role_devlead_basic_fields():
    """devlead has required fields populated."""
    role = load_role("devlead")
    assert isinstance(role, RolePrompt)
    assert role.slug == "devlead"
    assert role.name == "Development Lead"
    assert len(role.responsibilities) > 0
    assert len(role.escalates_to) > 0
    assert len(role.scope) > 0
    assert len(role.does_not) > 0


# --- load_role: mindset ---


def test_load_role_mindset():
    """devlead has a mindset with populated focus and principles."""
    role = load_role("devlead")
    assert role.mindset is not None
    assert isinstance(role.mindset, RoleMindset)
    assert len(role.mindset.focus) > 0
    assert len(role.mindset.principles) > 0


# --- load_role: escalation ---


def test_load_role_escalation():
    """Escalation entries have target and when fields."""
    role = load_role("devlead")
    assert len(role.escalates_to) > 0
    for esc in role.escalates_to:
        assert isinstance(esc, RoleEscalation)
        assert esc.target, "escalation target must not be empty"
        assert esc.when, "escalation when must not be empty"


# --- load_role: examples ---


def test_load_role_examples():
    """devlead has at least one example with populated fields."""
    role = load_role("devlead")
    assert len(role.examples) > 0
    for ex in role.examples:
        assert isinstance(ex, RoleExample)
        assert ex.type
        assert ex.title
        assert ex.content


# --- load_role: error paths ---


def test_load_role_invalid_slug_raises_value_error():
    """Invalid slug format raises ValueError, not AssetNotFoundError."""
    with pytest.raises(ValueError, match="Invalid role slug"):
        load_role("INVALID")


def test_load_role_invalid_slug_number_start():
    """Slug starting with a digit is invalid."""
    with pytest.raises(ValueError, match="Invalid role slug"):
        load_role("1bad")


def test_load_role_invalid_slug_hyphen():
    """Slug with hyphens is invalid per schema regex."""
    with pytest.raises(ValueError, match="Invalid role slug"):
        load_role("dev-lead")


def test_load_role_not_found_raises_asset_not_found():
    """Non-existent slug raises AssetNotFoundError with suggestions."""
    with pytest.raises(AssetNotFoundError) as exc_info:
        load_role("devleadx")
    assert exc_info.value.category == "roles"
    assert isinstance(exc_info.value.suggestions, list)


# --- load_role: releng (exercises new schema fields) ---


def test_load_role_releng_pre_push_checklist():
    """releng has a non-empty pre_push_checklist."""
    role = load_role("releng")
    assert len(role.pre_push_checklist) > 0
    assert all(isinstance(item, str) for item in role.pre_push_checklist)


def test_load_role_releng_required_reading():
    """releng has required_reading as a RequiredReading object with files."""
    role = load_role("releng")
    assert role.required_reading is not None
    assert isinstance(role.required_reading, RequiredReading)
    assert role.required_reading.description is not None
    assert len(role.required_reading.files) > 0
    for f in role.required_reading.files:
        assert isinstance(f, RequiredReadingFile)
        assert f.path
        assert f.reason


def test_load_role_releng_cross_role_note():
    """releng has a cross_role_note."""
    role = load_role("releng")
    assert role.cross_role_note is not None
    assert len(role.cross_role_note) > 0


# --- load_role: checklists ---


def test_load_role_secrev_checklists():
    """secrev has a checklists dict with at least one checklist."""
    role = load_role("secrev")
    assert isinstance(role.checklists, dict)
    assert len(role.checklists) > 0
    for name, items in role.checklists.items():
        assert isinstance(name, str)
        assert isinstance(items, list)
        assert len(items) > 0


# --- load_role_catalog ---


def test_load_role_catalog_returns_dict():
    """Catalog returns a non-empty dict."""
    catalog = load_role_catalog()
    assert isinstance(catalog, dict)
    assert len(catalog) > 0


def test_load_role_catalog_length_matches_slugs():
    """Catalog length matches list_role_slugs() length (internal consistency)."""
    catalog = load_role_catalog()
    slugs = list_role_slugs()
    assert len(catalog) == len(slugs)


def test_load_role_catalog_keys_match_slugs():
    """Catalog keys are the slug field from parsed YAML, not filenames."""
    catalog = load_role_catalog()
    for key, role in catalog.items():
        assert key == role.slug, f"catalog key {key!r} != role.slug {role.slug!r}"


def test_role_slug_consistency():
    """Every slug from list_role_slugs() appears as a key in the catalog."""
    slugs = list_role_slugs()
    catalog = load_role_catalog()
    for slug in slugs:
        assert slug in catalog, f"slug {slug!r} from list not in catalog"
