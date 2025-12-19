"""
Unit tests for embedded identity functionality.

Tests the embedded identity registration and fallback mechanism
for distributed Python packages (wheels, installed CLIs).
"""

import threading
from unittest.mock import patch

import pytest
import yaml

from pyfulmen.appidentity import (
    AppIdentity,
    clear_embedded_identity,
    get_embedded_identity,
    is_embedded_identity_registered,
    load,
    register_embedded_identity_yaml,
)
from pyfulmen.appidentity.errors import (
    AppIdentityNotFoundError,
    AppIdentityValidationError,
    EmbeddedIdentityAlreadyRegisteredError,
)


# Valid app.yaml content for testing
VALID_APP_YAML = """
app:
  binary_name: testapp
  vendor: testvendor
  env_prefix: TESTAPP_
  config_name: testapp
  description: Test application for embedded identity

metadata:
  license: MIT
  repository_category: library
  telemetry_namespace: testapp_embedded
  python:
    distribution_name: testapp
    package_name: testapp
"""

MINIMAL_APP_YAML = """
app:
  binary_name: minimal
  vendor: minimalvendor
  env_prefix: MINIMAL_
  config_name: minimal
  description: Minimal test app
"""


class TestEmbeddedIdentityRegistration:
    """Test embedded identity registration API."""

    def setup_method(self):
        """Clear embedded identity before each test."""
        clear_embedded_identity()

    def teardown_method(self):
        """Clear embedded identity after each test."""
        clear_embedded_identity()

    def test_register_valid_identity(self):
        """Test registering a valid embedded identity."""
        data = VALID_APP_YAML.encode("utf-8")
        register_embedded_identity_yaml(data)

        assert is_embedded_identity_registered()
        identity = get_embedded_identity()
        assert identity is not None
        assert identity.binary_name == "testapp"
        assert identity.vendor == "testvendor"
        assert identity.env_prefix == "TESTAPP_"

    def test_register_minimal_identity(self):
        """Test registering a minimal embedded identity."""
        data = MINIMAL_APP_YAML.encode("utf-8")
        register_embedded_identity_yaml(data)

        identity = get_embedded_identity()
        assert identity is not None
        assert identity.binary_name == "minimal"

    def test_first_wins_semantics(self):
        """Test that first registration wins, subsequent registrations raise."""
        first_data = VALID_APP_YAML.encode("utf-8")
        second_data = MINIMAL_APP_YAML.encode("utf-8")

        # First registration succeeds
        register_embedded_identity_yaml(first_data)

        # Second registration raises
        with pytest.raises(EmbeddedIdentityAlreadyRegisteredError):
            register_embedded_identity_yaml(second_data)

        # First identity is preserved
        identity = get_embedded_identity()
        assert identity.binary_name == "testapp"  # First registration

    def test_validation_on_registration(self):
        """Test that YAML is validated on registration."""
        # Missing required field
        invalid_yaml = """
app:
  binary_name: test
  vendor: vendor
  # Missing env_prefix, config_name, description
"""
        data = invalid_yaml.encode("utf-8")

        with pytest.raises(AppIdentityValidationError):
            register_embedded_identity_yaml(data)

        # Should not be registered after validation failure
        assert not is_embedded_identity_registered()

    def test_empty_data_raises(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            register_embedded_identity_yaml(b"")

        assert not is_embedded_identity_registered()

    def test_invalid_yaml_raises(self):
        """Test that invalid YAML raises error."""
        invalid_yaml = b"not: valid: yaml: [["

        with pytest.raises(yaml.YAMLError):
            register_embedded_identity_yaml(invalid_yaml)

        assert not is_embedded_identity_registered()

    def test_non_dict_yaml_raises(self):
        """Test that non-dictionary YAML raises ValueError."""
        non_dict = b"- list\n- items"

        with pytest.raises(ValueError, match="dictionary"):
            register_embedded_identity_yaml(non_dict)


class TestEmbeddedIdentityRetrieval:
    """Test embedded identity retrieval."""

    def setup_method(self):
        clear_embedded_identity()

    def teardown_method(self):
        clear_embedded_identity()

    def test_get_returns_none_when_not_registered(self):
        """Test get_embedded_identity returns None when not registered."""
        assert get_embedded_identity() is None
        assert not is_embedded_identity_registered()

    def test_get_returns_identity_when_registered(self):
        """Test get_embedded_identity returns identity when registered."""
        register_embedded_identity_yaml(VALID_APP_YAML.encode())

        identity = get_embedded_identity()
        assert identity is not None
        assert isinstance(identity, AppIdentity)

    def test_provenance_indicates_embedded_source(self):
        """Test that provenance indicates embedded source."""
        register_embedded_identity_yaml(VALID_APP_YAML.encode())

        identity = get_embedded_identity()
        provenance = identity.provenance

        assert provenance.get("source_path") == "<embedded>"
        assert provenance.get("source_type") == "embedded"
        assert "loaded_at" in provenance


class TestEmbeddedIdentityClear:
    """Test clearing embedded identity."""

    def setup_method(self):
        clear_embedded_identity()

    def teardown_method(self):
        clear_embedded_identity()

    def test_clear_allows_re_registration(self):
        """Test that clear allows re-registration."""
        # First registration
        register_embedded_identity_yaml(VALID_APP_YAML.encode())
        assert get_embedded_identity().binary_name == "testapp"

        # Clear
        clear_embedded_identity()
        assert get_embedded_identity() is None
        assert not is_embedded_identity_registered()

        # Re-register with different identity
        register_embedded_identity_yaml(MINIMAL_APP_YAML.encode())
        assert get_embedded_identity().binary_name == "minimal"


class TestEmbeddedIdentityDiscoveryFallback:
    """Test that embedded identity works as discovery fallback."""

    def setup_method(self):
        clear_embedded_identity()

    def teardown_method(self):
        clear_embedded_identity()

    def test_load_uses_embedded_fallback(self, tmp_path, monkeypatch):
        """Test that load() uses embedded identity when filesystem discovery fails."""
        # Register embedded identity
        register_embedded_identity_yaml(VALID_APP_YAML.encode())

        # Change to empty directory (no .fulmen/app.yaml)
        monkeypatch.chdir(tmp_path)

        # load() should use embedded identity
        identity = load()
        assert identity.binary_name == "testapp"
        assert identity.provenance.get("source_type") == "embedded"

    def test_filesystem_takes_precedence_over_embedded(self, tmp_path, monkeypatch):
        """Test that filesystem identity takes precedence over embedded."""
        # Register embedded identity
        register_embedded_identity_yaml(VALID_APP_YAML.encode())

        # Create filesystem identity
        fulmen_dir = tmp_path / ".fulmen"
        fulmen_dir.mkdir()
        app_yaml = fulmen_dir / "app.yaml"
        app_yaml.write_text(MINIMAL_APP_YAML)

        # Change to directory with .fulmen/app.yaml
        monkeypatch.chdir(tmp_path)

        # load() should use filesystem identity, not embedded
        identity = load()
        assert identity.binary_name == "minimal"  # From filesystem
        assert identity.provenance.get("source_type") != "embedded"

    def test_raises_when_no_identity_anywhere(self, tmp_path, monkeypatch):
        """Test that load() raises when no identity is found anywhere."""
        # No embedded identity registered
        # Change to empty directory
        monkeypatch.chdir(tmp_path)

        with pytest.raises(AppIdentityNotFoundError) as exc_info:
            load()

        # Error should mention embedded identity was checked
        assert "embedded" in str(exc_info.value.searched_paths[-1]).lower()


class TestEmbeddedIdentityThreadSafety:
    """Test thread safety of embedded identity operations."""

    def setup_method(self):
        clear_embedded_identity()

    def teardown_method(self):
        clear_embedded_identity()

    def test_concurrent_registration_first_wins(self):
        """Test that concurrent registrations result in first-wins."""
        results = {"registered": 0, "already_registered": 0}
        lock = threading.Lock()

        def try_register():
            try:
                register_embedded_identity_yaml(VALID_APP_YAML.encode())
                with lock:
                    results["registered"] += 1
            except EmbeddedIdentityAlreadyRegisteredError:
                with lock:
                    results["already_registered"] += 1

        threads = [threading.Thread(target=try_register) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly one should succeed
        assert results["registered"] == 1
        assert results["already_registered"] == 9

    def test_concurrent_get_after_registration(self):
        """Test that concurrent gets work correctly after registration."""
        register_embedded_identity_yaml(VALID_APP_YAML.encode())

        results = []
        lock = threading.Lock()

        def get_identity():
            identity = get_embedded_identity()
            with lock:
                results.append(identity.binary_name if identity else None)

        threads = [threading.Thread(target=get_identity) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should get the same identity
        assert all(name == "testapp" for name in results)
