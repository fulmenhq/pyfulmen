"""
Unit tests for app identity models.
"""

import json
from uuid import uuid4

import pytest

from pyfulmen.appidentity.models import AppIdentity


class TestAppIdentity:
    """Test AppIdentity dataclass."""

    def test_minimal_creation(self):
        """Test creating identity with minimal required fields."""
        identity = AppIdentity(
            binary_name="pyfulmen",
            vendor="fulmenhq",
            env_prefix="FULMEN_",
            config_name="pyfulmen",
            description="Python Fulmen libraries",
        )

        assert identity.binary_name == "pyfulmen"
        assert identity.vendor == "fulmenhq"
        assert identity.env_prefix == "FULMEN_"
        assert identity.config_name == "pyfulmen"
        assert identity.description == "Python Fulmen libraries"
        assert identity.project_url is None
        assert identity.registry_id is None

    def test_full_creation(self):
        """Test creating identity with all fields."""
        registry_id = uuid4()
        identity = AppIdentity(
            binary_name="pyfulmen",
            vendor="fulmenhq",
            env_prefix="FULMEN_",
            config_name="pyfulmen",
            description="Python Fulmen libraries",
            project_url="https://github.com/fulmenhq/pyfulmen",
            support_email="dev@3leaps.net",
            license="MIT",
            repository_category="library",
            telemetry_namespace="fulmenhq.pyfulmen",
            registry_id=registry_id,
            python_distribution="pyfulmen",
            python_package="pyfulmen",
            console_scripts=[{"name": "pyfulmen", "entry_point": "pyfulmen.cli:main"}],
        )

        assert identity.registry_id == registry_id
        assert identity.python_distribution == "pyfulmen"
        assert identity.console_scripts == [{"name": "pyfulmen", "entry_point": "pyfulmen.cli:main"}]

    def test_env_prefix_validation(self):
        """Test that env_prefix must be uppercase letters followed by underscore."""
        # Test missing underscore
        with pytest.raises(ValueError, match="must be uppercase letters followed by '_'"):
            AppIdentity(
                binary_name="test",
                vendor="vendor",
                env_prefix="INVALID",  # Missing underscore
                config_name="test",
                description="Test app",
            )

        # Test lowercase letters
        with pytest.raises(ValueError, match="must be uppercase letters followed by '_'"):
            AppIdentity(
                binary_name="test",
                vendor="vendor",
                env_prefix="invalid_",  # Lowercase letters
                config_name="test",
                description="Test app",
            )

        # Test mixed case
        with pytest.raises(ValueError, match="must be uppercase letters followed by '_'"):
            AppIdentity(
                binary_name="test",
                vendor="vendor",
                env_prefix="Invalid_",  # Mixed case
                config_name="test",
                description="Test app",
            )

        # Test special characters
        with pytest.raises(ValueError, match="must be uppercase letters followed by '_'"):
            AppIdentity(
                binary_name="test",
                vendor="vendor",
                env_prefix="APP123_",  # Numbers not allowed
                config_name="test",
                description="Test app",
            )

    def test_env_prefix_valid(self):
        """Test that valid env_prefix values work."""
        valid_prefixes = ["FULMEN_", "APP_", "TEST_"]

        for prefix in valid_prefixes:
            identity = AppIdentity(
                binary_name="test", vendor="vendor", env_prefix=prefix, config_name="test", description="Test app"
            )
            assert identity.env_prefix == prefix

    def test_to_json(self):
        """Test JSON serialization."""
        registry_id = uuid4()
        identity = AppIdentity(
            binary_name="pyfulmen",
            vendor="fulmenhq",
            env_prefix="FULMEN_",
            config_name="pyfulmen",
            description="Python Fulmen libraries",
            registry_id=registry_id,
        )

        json_str = identity.to_json()
        data = json.loads(json_str)

        assert data["binary_name"] == "pyfulmen"
        assert data["vendor"] == "fulmenhq"
        assert data["registry_id"] == str(registry_id)
        assert "_raw_metadata" not in data
        assert "_provenance" not in data

    def test_app_name_property(self):
        """Test app_name property."""
        identity = AppIdentity(
            binary_name="myapp", vendor="vendor", env_prefix="APP_", config_name="myapp", description="Test app"
        )

        assert identity.app_name == "myapp"

    def test_env_vars_property(self):
        """Test env_vars property."""
        identity = AppIdentity(
            binary_name="myapp", vendor="vendor", env_prefix="MYAPP_", config_name="myapp", description="Test app"
        )

        env_vars = identity.env_vars
        assert env_vars["config"] == "MYAPP_CONFIG"
        assert env_vars["log_level"] == "MYAPP_LOG_LEVEL"
        assert env_vars["debug"] == "MYAPP_DEBUG"

    def test_frozen_dataclass(self):
        """Test that AppIdentity is frozen."""
        identity = AppIdentity(
            binary_name="test", vendor="vendor", env_prefix="TEST_", config_name="test", description="Test app"
        )

        # Should raise FrozenInstanceError when trying to modify
        from dataclasses import FrozenInstanceError

        with pytest.raises(FrozenInstanceError):
            identity.binary_name = "modified"

    def test_slots_optimization(self):
        """Test that slots optimization is working."""
        identity = AppIdentity(
            binary_name="test", vendor="vendor", env_prefix="TEST_", config_name="test", description="Test app"
        )

        # Should not have __dict__ when using slots
        assert not hasattr(identity, "__dict__")
