"""Tests for foundry base models and utilities."""

import re
from datetime import UTC, datetime

import pytest
from pydantic import Field, ValidationError

from pyfulmen.foundry import (
    FulmenBaseModel,
    FulmenCatalogModel,
    FulmenConfigModel,
    FulmenDataModel,
    generate_correlation_id,
    utc_now_rfc3339nano,
)


class TestUtilityFunctions:
    """Test RFC3339Nano and UUIDv7 utility functions."""

    def test_utc_now_rfc3339nano_format(self):
        """RFC3339Nano timestamp should match expected format."""
        timestamp = utc_now_rfc3339nano()
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"
        assert re.match(
            pattern, timestamp
        ), f"Timestamp {timestamp} doesn't match RFC3339Nano format"

    def test_utc_now_rfc3339nano_utc(self):
        """RFC3339Nano timestamp should end with Z (UTC indicator)."""
        timestamp = utc_now_rfc3339nano()
        assert timestamp.endswith("Z")

    def test_utc_now_rfc3339nano_parseable(self):
        """RFC3339Nano timestamp should be parseable back to datetime."""
        timestamp = utc_now_rfc3339nano()
        # Remove Z and parse
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert dt.tzinfo == UTC

    def test_generate_correlation_id_format(self):
        """Correlation ID should be valid UUID format."""
        corr_id = generate_correlation_id()
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        assert re.match(
            uuid_pattern, corr_id
        ), f"Correlation ID {corr_id} doesn't match UUIDv7 format"

    def test_generate_correlation_id_version_7(self):
        """Correlation ID should be UUIDv7 (version bit = 7)."""
        corr_id = generate_correlation_id()
        # Check version field (13th hex digit should be 7)
        assert corr_id[14] == "7", f"UUID version should be 7, got {corr_id[14]}"

    def test_generate_correlation_id_uniqueness(self):
        """Multiple correlation IDs should be unique."""
        ids = [generate_correlation_id() for _ in range(100)]
        assert len(set(ids)) == 100, "Correlation IDs should be unique"

    def test_generate_correlation_id_time_sortable(self):
        """UUIDv7 should be time-sortable (later IDs are greater)."""
        import time

        id1 = generate_correlation_id()
        time.sleep(0.001)  # 1ms delay
        id2 = generate_correlation_id()
        assert id1 < id2, "UUIDv7 should be time-sortable"


class TestFulmenDataModel:
    """Test FulmenDataModel immutable data model."""

    def test_data_model_creation(self):
        """FulmenDataModel should allow creation with valid data."""

        class TestEvent(FulmenDataModel):
            message: str
            count: int = 0

        event = TestEvent(message="test", count=5)
        assert event.message == "test"
        assert event.count == 5

    def test_data_model_immutable(self):
        """FulmenDataModel should be immutable (frozen=True)."""

        class TestEvent(FulmenDataModel):
            message: str

        event = TestEvent(message="test")
        with pytest.raises(ValidationError, match="Instance is frozen"):
            event.message = "changed"

    def test_data_model_strict_schema(self):
        """FulmenDataModel should reject unknown fields (extra='forbid')."""

        class TestEvent(FulmenDataModel):
            message: str

        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            TestEvent(message="test", unknown_field="value")

    def test_data_model_enum_values(self):
        """FulmenDataModel should serialize enum values as strings."""
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        class TestEvent(FulmenDataModel):
            status: Status

        event = TestEvent(status=Status.ACTIVE)
        json_dict = event.to_json_dict()
        assert json_dict["status"] == "active"

    def test_data_model_to_json_dict(self):
        """FulmenDataModel should convert to JSON dict correctly."""

        class TestEvent(FulmenDataModel):
            message: str
            optional_field: str | None = None

        event = TestEvent(message="test")
        json_dict = event.to_json_dict()
        assert json_dict == {"message": "test"}
        assert "optional_field" not in json_dict  # exclude_none=True

    def test_data_model_to_json_dict_include_none(self):
        """FulmenDataModel should include None values when requested."""

        class TestEvent(FulmenDataModel):
            message: str
            optional_field: str | None = None

        event = TestEvent(message="test")
        json_dict = event.to_json_dict(exclude_none=False)
        assert json_dict == {"message": "test", "optional_field": None}

    def test_data_model_to_json_str(self):
        """FulmenDataModel should convert to JSON string."""

        class TestEvent(FulmenDataModel):
            message: str
            count: int

        event = TestEvent(message="test", count=5)
        json_str = event.to_json_str()
        # JSON may have spaces, check for keys and values
        assert '"message"' in json_str
        assert '"test"' in json_str
        assert '"count"' in json_str
        assert '5' in json_str

    def test_data_model_strip_whitespace(self):
        """FulmenDataModel should strip whitespace from string fields."""

        class TestEvent(FulmenDataModel):
            message: str

        event = TestEvent(message="  test  ")
        assert event.message == "test"

    def test_data_model_with_default_factory(self):
        """FulmenDataModel should support Field with default_factory."""

        class TestEvent(FulmenDataModel):
            message: str
            correlation_id: str = Field(default_factory=generate_correlation_id)

        event = TestEvent(message="test")
        assert len(event.correlation_id) == 36  # UUID format


class TestFulmenConfigModel:
    """Test FulmenConfigModel flexible configuration model."""

    def test_config_model_creation(self):
        """FulmenConfigModel should allow creation with valid data."""

        class TestConfig(FulmenConfigModel):
            service: str
            level: str = "INFO"

        config = TestConfig(service="myapp", level="DEBUG")
        assert config.service == "myapp"
        assert config.level == "DEBUG"

    def test_config_model_mutable(self):
        """FulmenConfigModel should be mutable (frozen=False)."""

        class TestConfig(FulmenConfigModel):
            service: str
            level: str = "INFO"

        config = TestConfig(service="myapp")
        config.level = "DEBUG"
        assert config.level == "DEBUG"

    def test_config_model_extra_allowed(self):
        """FulmenConfigModel should accept unknown fields (extra='allow')."""

        class TestConfig(FulmenConfigModel):
            service: str

        config = TestConfig(service="myapp", unknown_field="value")
        assert config.service == "myapp"
        assert hasattr(config, "unknown_field")

    def test_config_model_merge_simple(self):
        """FulmenConfigModel should merge configs correctly."""

        class TestConfig(FulmenConfigModel):
            service: str
            level: str = "INFO"

        base = TestConfig(service="myapp", level="INFO")
        override = TestConfig(service="myapp", level="DEBUG")
        merged = base.merge_with(override)

        assert merged.service == "myapp"
        assert merged.level == "DEBUG"

    def test_config_model_merge_nested(self):
        """FulmenConfigModel should deep merge nested dictionaries."""

        class TestConfig(FulmenConfigModel):
            service: str
            settings: dict = Field(default_factory=dict)

        base = TestConfig(service="myapp", settings={"logging": {"level": "INFO"}})
        override = TestConfig(service="myapp", settings={"logging": {"format": "json"}})
        merged = base.merge_with(override)

        assert merged.settings["logging"]["level"] == "INFO"
        assert merged.settings["logging"]["format"] == "json"

    def test_config_model_merge_with_extras(self):
        """FulmenConfigModel should merge extra fields correctly."""

        class TestConfig(FulmenConfigModel):
            service: str

        base = TestConfig(service="myapp", extra1="value1")
        override = TestConfig(service="myapp", extra2="value2")
        merged = base.merge_with(override)

        assert hasattr(merged, "extra1")
        assert hasattr(merged, "extra2")

    def test_config_model_populate_by_name(self):
        """FulmenConfigModel should support both field names and aliases."""

        class TestConfig(FulmenConfigModel):
            service_name: str = Field(alias="serviceName")

        # Should work with both snake_case and camelCase
        config1 = TestConfig(service_name="myapp")
        config2 = TestConfig(serviceName="myapp")
        assert config1.service_name == "myapp"
        assert config2.service_name == "myapp"


class TestFulmenCatalogModel:
    """Test FulmenCatalogModel immutable catalog entries."""

    def test_catalog_model_creation(self):
        """FulmenCatalogModel should allow creation with valid data."""

        class TestCatalogEntry(FulmenCatalogModel):
            id: str
            name: str
            value: int

        entry = TestCatalogEntry(id="test", name="Test Entry", value=42)
        assert entry.id == "test"
        assert entry.name == "Test Entry"
        assert entry.value == 42

    def test_catalog_model_immutable(self):
        """FulmenCatalogModel should be immutable (frozen=True)."""

        class TestCatalogEntry(FulmenCatalogModel):
            id: str

        entry = TestCatalogEntry(id="test")
        with pytest.raises(ValidationError, match="Instance is frozen"):
            entry.id = "changed"

    def test_catalog_model_ignore_extra(self):
        """FulmenCatalogModel should ignore unknown fields (extra='ignore')."""

        class TestCatalogEntry(FulmenCatalogModel):
            id: str

        entry = TestCatalogEntry(id="test", unknown_field="value")
        assert entry.id == "test"
        assert not hasattr(entry, "unknown_field")

    def test_catalog_model_enum_values(self):
        """FulmenCatalogModel should serialize enum values."""
        from enum import Enum

        class CategoryType(str, Enum):
            PATTERN = "pattern"
            MIME = "mime"

        class TestCatalogEntry(FulmenCatalogModel):
            category: CategoryType

        entry = TestCatalogEntry(category=CategoryType.PATTERN)
        assert entry.category == "pattern"


class TestFulmenBaseModel:
    """Test FulmenBaseModel common functionality."""

    def test_base_model_validate_assignment(self):
        """FulmenBaseModel should validate assignments."""

        class TestModel(FulmenBaseModel):
            count: int

        # Note: FulmenBaseModel itself is not frozen, but validation applies
        model = TestModel(count=5)
        assert model.count == 5

    def test_base_model_enum_values(self):
        """FulmenBaseModel should use enum values."""
        from enum import Enum

        class Status(str, Enum):
            ACTIVE = "active"

        class TestModel(FulmenBaseModel):
            status: Status

        model = TestModel(status=Status.ACTIVE)
        dict_data = model.model_dump()
        assert dict_data["status"] == "active"

    def test_base_model_strip_whitespace(self):
        """FulmenBaseModel should strip whitespace."""

        class TestModel(FulmenBaseModel):
            name: str

        model = TestModel(name="  test  ")
        assert model.name == "test"


class TestComputedFields:
    """Test computed field handling with Pydantic @computed_field decorator."""

    def test_computed_field_accessible(self):
        """Computed fields should be accessible as properties."""
        from pydantic import computed_field

        class TestEvent(FulmenDataModel):
            message: str
            count: int

            @computed_field
            @property
            def total_length(self) -> int:
                return len(self.message) + self.count

        event = TestEvent(message="test", count=5)
        assert event.total_length == 9

    def test_computed_field_excluded_by_default(self):
        """Computed fields should be excluded from to_json_dict() by default."""
        from pydantic import computed_field

        class TestEvent(FulmenDataModel):
            message: str

            @computed_field
            @property
            def message_length(self) -> int:
                return len(self.message)

        event = TestEvent(message="test")
        json_dict = event.to_json_dict()
        assert "message" in json_dict
        assert "message_length" not in json_dict

    def test_computed_field_roundtrip_safe(self):
        """Models should roundtrip correctly with computed fields excluded."""
        from pydantic import computed_field

        class TestEvent(FulmenDataModel):
            message: str

            @computed_field
            @property
            def message_upper(self) -> str:
                return self.message.upper()

        event = TestEvent(message="test")
        data = event.to_json_dict()

        # Should not raise ValidationError about extra fields
        reconstructed = TestEvent(**data)
        assert reconstructed.message == event.message
        assert reconstructed.message_upper == "TEST"

    def test_computed_field_include_explicit(self):
        """Computed fields should be included when explicitly requested."""
        from pydantic import computed_field

        class TestEvent(FulmenDataModel):
            message: str
            count: int

            @computed_field
            @property
            def total(self) -> int:
                return self.count * 2

        event = TestEvent(message="test", count=5)

        # Include via parameter
        json_dict = event.to_json_dict(include_computed=True)
        assert "total" in json_dict
        assert json_dict["total"] == 10

    def test_computed_field_convenience_method(self):
        """to_json_dict_with_computed() should include computed fields."""
        from pydantic import computed_field

        class TestEvent(FulmenDataModel):
            message: str

            @computed_field
            @property
            def message_length(self) -> int:
                return len(self.message)

        event = TestEvent(message="test")
        json_dict = event.to_json_dict_with_computed()
        assert "message_length" in json_dict
        assert json_dict["message_length"] == 4

    def test_computed_field_to_json_str(self):
        """to_json_str() should handle computed fields correctly."""
        from pydantic import computed_field

        class TestEvent(FulmenDataModel):
            message: str

            @computed_field
            @property
            def length(self) -> int:
                return len(self.message)

        event = TestEvent(message="test")

        # Excluded by default
        json_str = event.to_json_str()
        assert "length" not in json_str

        # Included when requested
        json_str_with_computed = event.to_json_str(include_computed=True)
        assert "length" in json_str_with_computed
        assert '"length"' in json_str_with_computed and '4' in json_str_with_computed

    def test_get_computed_field_names(self):
        """Should return all computed field names."""
        from pydantic import computed_field

        class TestEvent(FulmenDataModel):
            message: str

            @computed_field
            @property
            def length(self) -> int:
                return len(self.message)

            @computed_field
            @property
            def upper(self) -> str:
                return self.message.upper()

        event = TestEvent(message="test")
        computed_names = event.get_computed_field_names()
        assert computed_names == {"length", "upper"}

    def test_computed_field_with_multiple_models(self):
        """Multiple models should independently track their computed fields."""
        from pydantic import computed_field

        class EventA(FulmenDataModel):
            value: int

            @computed_field
            @property
            def doubled(self) -> int:
                return self.value * 2

        class EventB(FulmenDataModel):
            value: int

            @computed_field
            @property
            def tripled(self) -> int:
                return self.value * 3

        a = EventA(value=5)
        b = EventB(value=5)

        assert a.get_computed_field_names() == {"doubled"}
        assert b.get_computed_field_names() == {"tripled"}
        assert a.doubled == 10
        assert b.tripled == 15

    def test_computed_field_with_none_values(self):
        """Computed fields should work with exclude_none parameter."""
        from pydantic import computed_field

        class TestEvent(FulmenDataModel):
            message: str
            optional: str | None = None

            @computed_field
            @property
            def has_optional(self) -> bool:
                return self.optional is not None

        event = TestEvent(message="test")

        # With exclude_none=True (default)
        json_dict = event.to_json_dict(include_computed=True)
        assert "optional" not in json_dict
        assert json_dict["has_optional"] is False

        # With exclude_none=False
        json_dict = event.to_json_dict(exclude_none=False, include_computed=True)
        assert json_dict["optional"] is None
        assert json_dict["has_optional"] is False


class TestCrossModelIntegration:
    """Test interactions between different model types."""

    def test_data_model_in_config(self):
        """Config models should be able to contain data models."""

        class LogEvent(FulmenDataModel):
            message: str
            timestamp: str = Field(default_factory=utc_now_rfc3339nano)

        class LoggingConfig(FulmenConfigModel):
            service: str
            sample_event: LogEvent | None = None

        event = LogEvent(message="test")
        config = LoggingConfig(service="myapp", sample_event=event)
        assert config.sample_event.message == "test"

    def test_catalog_in_config(self):
        """Config models should be able to reference catalog entries."""

        class Pattern(FulmenCatalogModel):
            id: str
            regex: str

        class AppConfig(FulmenConfigModel):
            service: str
            validation_pattern: Pattern

        pattern = Pattern(id="email", regex=r"^[\w\.\-]+@[\w\.\-]+\.\w+$")
        config = AppConfig(service="myapp", validation_pattern=pattern)
        assert config.validation_pattern.id == "email"
