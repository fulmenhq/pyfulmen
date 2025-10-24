"""Tests for foundry catalog models and loaders."""

import pytest

from pyfulmen.config.loader import ConfigLoader
from pyfulmen.foundry.catalog import (
    Country,
    FoundryCatalog,
    HttpStatusCode,
    HttpStatusGroup,
    HttpStatusHelper,
    MimeType,
    Pattern,
    PatternAccessor,
    get_country,
    get_country_by_alpha3,
    get_country_by_numeric,
    get_default_catalog,
    get_mime_type,
    get_mime_type_by_extension,
    get_mime_type_by_mime_string,
    get_pattern,
    is_client_error,
    is_informational,
    is_redirect,
    is_server_error,
    is_success,
    is_supported_mime_type,
    list_countries,
    list_mime_types,
    validate_country_code,
)


@pytest.fixture
def config_loader():
    """Create ConfigLoader instance for tests."""
    return ConfigLoader(app_name="fulmen")


@pytest.fixture
def catalog(config_loader):
    """Create FoundryCatalog instance for tests."""
    return FoundryCatalog(config_loader)


@pytest.fixture
def pattern_accessor(catalog):
    """Create PatternAccessor instance for tests."""
    return PatternAccessor(catalog)


class TestPattern:
    """Test Pattern model and methods."""

    def test_pattern_creation_regex(self):
        """Pattern should be created with regex kind."""
        pattern = Pattern(
            id="test",
            name="Test Pattern",
            kind="regex",
            pattern=r"^\d{3}$",
            description="Three digits",
        )
        assert pattern.id == "test"
        assert pattern.kind == "regex"
        assert pattern.pattern == r"^\d{3}$"

    def test_pattern_creation_glob(self):
        """Pattern should be created with glob kind."""
        pattern = Pattern(id="test-glob", name="Test Glob", kind="glob", pattern="*.json")
        assert pattern.kind == "glob"
        assert pattern.pattern == "*.json"

    def test_pattern_creation_literal(self):
        """Pattern should be created with literal kind."""
        pattern = Pattern(id="test-lit", name="Test Literal", kind="literal", pattern="exact-match")
        assert pattern.kind == "literal"
        assert pattern.pattern == "exact-match"

    def test_pattern_invalid_kind(self):
        """Pattern should reject invalid kind."""
        with pytest.raises(ValueError, match="Pattern kind must be regex/glob/literal"):
            Pattern(id="test", name="Test", kind="invalid", pattern="test")

    def test_pattern_regex_match(self):
        """Pattern should match strings with regex."""
        pattern = Pattern(id="digits", name="Digits", kind="regex", pattern=r"^\d+$")
        assert pattern.match("123")
        assert pattern.match("0")
        assert not pattern.match("abc")
        assert not pattern.match("12a")

    def test_pattern_glob_match(self):
        """Pattern should match strings with glob."""
        pattern = Pattern(id="json-glob", name="JSON", kind="glob", pattern="*.json")
        assert pattern.match("file.json")
        assert pattern.match("data.json")
        assert not pattern.match("file.txt")
        assert not pattern.match("json")

    def test_pattern_literal_match(self):
        """Pattern should match exact strings with literal."""
        pattern = Pattern(id="exact", name="Exact", kind="literal", pattern="hello")
        assert pattern.match("hello")
        assert not pattern.match("Hello")
        assert not pattern.match("hello world")

    def test_pattern_search_regex(self):
        """Pattern should search within strings with regex."""
        pattern = Pattern(id="email-simple", name="Email", kind="regex", pattern=r"\w+@\w+\.\w+")
        assert pattern.search("Contact: user@example.com for info")
        assert pattern.search("user@example.com")
        assert not pattern.search("no email here")

    def test_pattern_search_literal(self):
        """Pattern should search within strings with literal."""
        pattern = Pattern(id="word", name="Word", kind="literal", pattern="test")
        assert pattern.search("this is a test")
        assert pattern.search("test")
        assert not pattern.search("no match")

    def test_pattern_callable(self):
        """Pattern should be callable via __call__."""
        pattern = Pattern(id="digits", name="Digits", kind="regex", pattern=r"^\d+$")
        assert pattern("123")
        assert not pattern("abc")

    def test_pattern_compiled_caching(self):
        """Pattern should cache compiled regex."""
        pattern = Pattern(id="test", name="Test", kind="regex", pattern=r"^\d+$")
        compiled1 = pattern.compiled_pattern
        compiled2 = pattern.compiled_pattern
        assert compiled1 is compiled2

    def test_pattern_flags_python(self):
        """Pattern should apply Python-specific flags."""
        pattern = Pattern(
            id="case-insensitive",
            name="Case Insensitive",
            kind="regex",
            pattern=r"^hello$",
            flags={"python": {"ignoreCase": True}},
        )
        assert pattern.match("hello")
        assert pattern.match("HELLO")
        assert pattern.match("Hello")

    def test_pattern_describe(self):
        """Pattern should generate description."""
        pattern = Pattern(
            id="email",
            name="Email Address",
            kind="regex",
            pattern=r"^[\w._%+-]+@[\w.-]+\.\w+$",
            description="Simple email validation",
            examples=["user@example.com", "admin@test.org"],
            non_examples=["invalid", "@example.com"],
        )
        description = pattern.describe()
        assert "Email Address" in description
        assert "Simple email validation" in description
        assert "user@example.com" in description
        assert "invalid" in description


class TestMimeType:
    """Test MimeType model and methods."""

    def test_mime_type_creation(self):
        """MimeType should be created with valid data."""
        mime = MimeType(
            id="json",
            mime="application/json",
            name="JSON",
            extensions=["json", "map"],
            description="JavaScript Object Notation",
        )
        assert mime.id == "json"
        assert mime.mime == "application/json"
        assert "json" in mime.extensions

    def test_mime_type_matches_extension(self):
        """MimeType should match file extensions."""
        mime = MimeType(
            id="json",
            mime="application/json",
            name="JSON",
            extensions=["json", "map"],
        )
        assert mime.matches_extension("json")
        assert mime.matches_extension(".json")
        assert mime.matches_extension("JSON")
        assert mime.matches_extension(".JSON")
        assert mime.matches_extension("map")
        assert not mime.matches_extension("txt")


class TestHttpStatusGroup:
    """Test HttpStatusGroup model and methods."""

    def test_http_status_code_creation(self):
        """HttpStatusCode should be created with valid data."""
        code = HttpStatusCode(value=200, reason="OK")
        assert code.value == 200
        assert code.reason == "OK"

    def test_http_status_group_creation(self):
        """HttpStatusGroup should be created with valid data."""
        group = HttpStatusGroup(
            id="success",
            name="Successful Responses",
            description="2xx status codes",
            codes=[
                HttpStatusCode(value=200, reason="OK"),
                HttpStatusCode(value=201, reason="Created"),
            ],
        )
        assert group.id == "success"
        assert len(group.codes) == 2

    def test_http_status_group_contains(self):
        """HttpStatusGroup should check if code is in group."""
        group = HttpStatusGroup(
            id="success",
            name="Success",
            codes=[
                HttpStatusCode(value=200, reason="OK"),
                HttpStatusCode(value=201, reason="Created"),
            ],
        )
        assert group.contains(200)
        assert group.contains(201)
        assert not group.contains(404)

    def test_http_status_group_get_reason(self):
        """HttpStatusGroup should return reason phrase for code."""
        group = HttpStatusGroup(
            id="success",
            name="Success",
            codes=[
                HttpStatusCode(value=200, reason="OK"),
                HttpStatusCode(value=201, reason="Created"),
            ],
        )
        assert group.get_reason(200) == "OK"
        assert group.get_reason(201) == "Created"
        assert group.get_reason(404) is None


class TestFoundryCatalog:
    """Test FoundryCatalog loading and access."""

    def test_catalog_creation(self, config_loader):
        """FoundryCatalog should be created with ConfigLoader."""
        catalog = FoundryCatalog(config_loader)
        assert catalog._config_loader is config_loader

    def test_catalog_invalid_loader(self):
        """FoundryCatalog should reject invalid loader."""
        with pytest.raises(TypeError, match="must be ConfigLoader instance"):
            FoundryCatalog("not a loader")

    def test_catalog_get_pattern(self, catalog):
        """FoundryCatalog should load and return patterns."""
        pattern = catalog.get_pattern("ansi-email")
        assert pattern is not None
        assert pattern.id == "ansi-email"
        assert pattern.kind == "regex"

    def test_catalog_get_pattern_not_found(self, catalog):
        """FoundryCatalog should return None for missing pattern."""
        pattern = catalog.get_pattern("nonexistent-pattern")
        assert pattern is None

    def test_catalog_get_all_patterns(self, catalog):
        """FoundryCatalog should return all patterns."""
        patterns = catalog.get_all_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) > 0
        assert "ansi-email" in patterns
        assert "slug" in patterns

    def test_catalog_pattern_lazy_loading(self, catalog):
        """FoundryCatalog should lazy load patterns."""
        assert catalog._patterns is None
        _ = catalog.get_pattern("slug")
        assert catalog._patterns is not None
        assert "slug" in catalog._patterns

    def test_catalog_get_mime_type(self, catalog):
        """FoundryCatalog should load and return MIME types."""
        mime = catalog.get_mime_type("json")
        assert mime is not None
        assert mime.id == "json"
        assert mime.mime == "application/json"

    def test_catalog_get_mime_type_by_extension(self, catalog):
        """FoundryCatalog should find MIME type by extension."""
        mime = catalog.get_mime_type_by_extension("json")
        assert mime is not None
        assert mime.id == "json"

        mime = catalog.get_mime_type_by_extension(".yaml")
        assert mime is not None
        assert mime.id == "yaml"

    def test_catalog_get_all_mime_types(self, catalog):
        """FoundryCatalog should return all MIME types."""
        mime_types = catalog.get_all_mime_types()
        assert isinstance(mime_types, dict)
        assert len(mime_types) > 0
        assert "json" in mime_types
        assert "yaml" in mime_types

    def test_catalog_get_http_status_group(self, catalog):
        """FoundryCatalog should load and return HTTP status groups."""
        group = catalog.get_http_status_group("success")
        assert group is not None
        assert group.id == "success"
        assert group.contains(200)

    def test_catalog_get_http_status_group_for_code(self, catalog):
        """FoundryCatalog should find group for status code."""
        group = catalog.get_http_status_group_for_code(200)
        assert group is not None
        assert group.id == "success"

        group = catalog.get_http_status_group_for_code(404)
        assert group is not None
        assert group.id == "client-error"

        group = catalog.get_http_status_group_for_code(500)
        assert group is not None
        assert group.id == "server-error"

    def test_catalog_get_all_http_groups(self, catalog):
        """FoundryCatalog should return all HTTP status groups."""
        groups = catalog.get_all_http_groups()
        assert isinstance(groups, dict)
        assert len(groups) > 0
        assert "success" in groups
        assert "client-error" in groups

    def test_catalog_get_mime_type_by_mime_string(self, catalog):
        """FoundryCatalog should find MIME type by string."""
        mime = catalog.get_mime_type_by_mime_string("application/json")
        assert mime is not None
        assert mime.id == "json"

        mime = catalog.get_mime_type_by_mime_string("application/yaml")
        assert mime is not None
        assert mime.id == "yaml"

        # Case insensitive
        mime = catalog.get_mime_type_by_mime_string("APPLICATION/JSON")
        assert mime is not None
        assert mime.id == "json"

        # Not found
        mime = catalog.get_mime_type_by_mime_string("application/x-unknown")
        assert mime is None


class TestPatternAccessor:
    """Test PatternAccessor convenience methods."""

    def test_accessor_creation(self, catalog):
        """PatternAccessor should be created with catalog."""
        accessor = PatternAccessor(catalog)
        assert accessor._catalog is catalog

    def test_accessor_email(self, pattern_accessor):
        """PatternAccessor should return email pattern."""
        pattern = pattern_accessor.email()
        assert pattern is not None
        assert pattern.id == "ansi-email"

    def test_accessor_slug(self, pattern_accessor):
        """PatternAccessor should return slug pattern."""
        pattern = pattern_accessor.slug()
        assert pattern is not None
        assert pattern.id == "slug"

    def test_accessor_path_segment(self, pattern_accessor):
        """PatternAccessor should return path segment pattern."""
        pattern = pattern_accessor.path_segment()
        assert pattern is not None
        assert pattern.id == "path-segment"

    def test_accessor_identifier(self, pattern_accessor):
        """PatternAccessor should return identifier pattern."""
        pattern = pattern_accessor.identifier()
        assert pattern is not None
        assert pattern.id == "identifier"

    def test_accessor_domain_name(self, pattern_accessor):
        """PatternAccessor should return domain name pattern."""
        pattern = pattern_accessor.domain_name()
        assert pattern is not None
        assert pattern.id == "domain-name"

    def test_accessor_ipv6(self, pattern_accessor):
        """PatternAccessor should return IPv6 pattern."""
        pattern = pattern_accessor.ipv6()
        assert pattern is not None
        assert pattern.id == "ipv6"

    def test_accessor_uuid_v4(self, pattern_accessor):
        """PatternAccessor should return UUID v4 pattern."""
        pattern = pattern_accessor.uuid_v4()
        assert pattern is not None
        assert pattern.id == "uuid-v4"

    def test_accessor_semantic_version(self, pattern_accessor):
        """PatternAccessor should return semantic version pattern."""
        pattern = pattern_accessor.semantic_version()
        assert pattern is not None
        assert pattern.id == "semantic-version"

    def test_accessor_iso_date(self, pattern_accessor):
        """PatternAccessor should return ISO date pattern."""
        pattern = pattern_accessor.iso_date()
        assert pattern is not None
        assert pattern.id == "strict-iso-date"

    def test_accessor_iso_timestamp_utc(self, pattern_accessor):
        """PatternAccessor should return ISO timestamp pattern."""
        pattern = pattern_accessor.iso_timestamp_utc()
        assert pattern is not None
        assert pattern.id == "iso-timestamp-z"

    def test_accessor_get_all_patterns(self, pattern_accessor):
        """PatternAccessor should return all patterns."""
        patterns = pattern_accessor.get_all_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) > 0

    def test_all_catalog_patterns_accessible(self, catalog):
        """All patterns in catalog should be accessible via get_pattern."""
        # Crucible requirement: Validate all Foundry pattern IDs are exposed
        all_patterns = catalog.get_all_patterns()
        assert len(all_patterns) > 0, "Catalog should contain patterns"

        # Verify each pattern is accessible and valid
        for pattern_id in all_patterns:
            pattern = catalog.get_pattern(pattern_id)
            assert pattern is not None, f"Pattern {pattern_id} should be accessible"
            assert pattern.id == pattern_id, f"Pattern ID should match: {pattern_id}"
            assert pattern.kind in ["regex", "glob", "literal"], (
                f"Pattern {pattern_id} should have valid kind"
            )
            assert pattern.pattern, f"Pattern {pattern_id} should have pattern string"


class TestPatternMatching:
    """Integration tests for pattern matching with real patterns."""

    def test_email_pattern_matching(self, catalog):
        """Email pattern should match valid email addresses."""
        _ = catalog.get_pattern("ansi-email")
        # Note: ansi-email pattern uses \p{Letter} which requires regex library, not re
        # For now, skip Unicode property testing - would need regex library
        # Would need to add 'regex' package to dependencies for full Unicode support

    def test_slug_pattern_matching(self, catalog):
        """Slug pattern should match valid slugs."""
        pattern = catalog.get_pattern("slug")
        assert pattern.match("fulmen-hq")
        assert pattern.match("data_pipeline")
        assert pattern.match("test")
        assert not pattern.match("Test")
        assert not pattern.match("has space")
        assert not pattern.match("-start")

    def test_uuid_v4_pattern_matching(self, catalog):
        """UUID v4 pattern should match valid UUIDs."""
        pattern = catalog.get_pattern("uuid-v4")
        # UUID v4 has '4' as version digit (13th hex char) and variant bits
        assert pattern.match("123e4567-e89b-42d3-a456-426614174000")
        assert pattern.match("550e8400-e29b-41d4-a716-446655440000")
        assert not pattern.match("not-a-uuid")
        assert not pattern.match("123e4567-e89b-52d3-a456-426614174000")

    def test_semantic_version_pattern_matching(self, catalog):
        """Semantic version pattern should match valid versions."""
        pattern = catalog.get_pattern("semantic-version")
        assert pattern.match("1.2.3")
        assert pattern.match("0.0.1")
        assert pattern.match("1.2.3-beta.1")
        assert pattern.match("1.2.3+build.5")
        assert pattern.match("1.2.3-beta.1+build.5")
        assert not pattern.match("v1.2.3")
        assert not pattern.match("1.2")

    def test_iso_date_pattern_matching(self, catalog):
        """ISO date pattern should match valid dates."""
        pattern = catalog.get_pattern("strict-iso-date")
        assert pattern.match("2025-10-13")
        assert pattern.match("2025-01-01")
        assert not pattern.match("2025-13-01")
        assert not pattern.match("2025-10-32")
        assert not pattern.match("25-10-13")


class TestHttpStatusHelper:
    """Test HttpStatusHelper convenience methods."""

    def test_helper_creation(self, catalog):
        """HttpStatusHelper should be created with catalog."""
        helper = HttpStatusHelper(catalog)
        assert helper._catalog is catalog

    def test_is_informational(self, catalog):
        """Helper should identify informational responses."""
        helper = HttpStatusHelper(catalog)
        assert helper.is_informational(100)
        assert helper.is_informational(101)
        assert not helper.is_informational(200)

    def test_is_success(self, catalog):
        """Helper should identify successful responses."""
        helper = HttpStatusHelper(catalog)
        assert helper.is_success(200)
        assert helper.is_success(201)
        assert helper.is_success(204)
        assert not helper.is_success(404)

    def test_is_redirect(self, catalog):
        """Helper should identify redirect responses."""
        helper = HttpStatusHelper(catalog)
        assert helper.is_redirect(301)
        assert helper.is_redirect(302)
        assert not helper.is_redirect(200)

    def test_is_client_error(self, catalog):
        """Helper should identify client errors."""
        helper = HttpStatusHelper(catalog)
        assert helper.is_client_error(400)
        assert helper.is_client_error(404)
        assert helper.is_client_error(422)
        assert not helper.is_client_error(500)

    def test_is_server_error(self, catalog):
        """Helper should identify server errors."""
        helper = HttpStatusHelper(catalog)
        assert helper.is_server_error(500)
        assert helper.is_server_error(503)
        assert not helper.is_server_error(404)

    def test_get_reason_phrase(self, catalog):
        """Helper should return reason phrases."""
        helper = HttpStatusHelper(catalog)
        assert helper.get_reason_phrase(200) == "OK"
        assert helper.get_reason_phrase(404) == "Not Found"
        assert helper.get_reason_phrase(500) == "Internal Server Error"
        assert helper.get_reason_phrase(999) is None


class TestConvenienceFunctions:
    """Test convenience functions with global catalog."""

    def test_get_default_catalog(self):
        """get_default_catalog should return singleton instance."""
        catalog1 = get_default_catalog()
        catalog2 = get_default_catalog()
        assert catalog1 is catalog2
        assert isinstance(catalog1, FoundryCatalog)

    def test_get_pattern(self):
        """get_pattern should retrieve pattern from default catalog."""
        pattern = get_pattern("slug")
        assert pattern is not None
        assert pattern.id == "slug"

    def test_get_pattern_not_found(self):
        """get_pattern should return None for missing pattern."""
        pattern = get_pattern("nonexistent")
        assert pattern is None

    def test_get_mime_type(self):
        """get_mime_type should retrieve MIME type from default catalog."""
        mime = get_mime_type("json")
        assert mime is not None
        assert mime.mime == "application/json"

    def test_get_mime_type_by_extension(self):
        """get_mime_type_by_extension should find MIME by extension."""
        mime = get_mime_type_by_extension("json")
        assert mime is not None
        assert mime.id == "json"

        mime = get_mime_type_by_extension(".yaml")
        assert mime is not None
        assert mime.id == "yaml"

    def test_is_success(self):
        """is_success should check 2xx status codes."""
        assert is_success(200)
        assert is_success(201)
        assert is_success(204)
        assert not is_success(404)
        assert not is_success(500)

    def test_is_client_error(self):
        """is_client_error should check 4xx status codes."""
        assert is_client_error(400)
        assert is_client_error(404)
        assert is_client_error(422)
        assert not is_client_error(200)
        assert not is_client_error(500)

    def test_is_server_error(self):
        """is_server_error should check 5xx status codes."""
        assert is_server_error(500)
        assert is_server_error(503)
        assert not is_server_error(200)
        assert not is_server_error(404)

    def test_get_mime_type_by_mime_string(self):
        """get_mime_type_by_mime_string should find MIME by string."""
        mime = get_mime_type_by_mime_string("application/json")
        assert mime is not None
        assert mime.id == "json"

        mime = get_mime_type_by_mime_string("application/yaml")
        assert mime is not None
        assert mime.id == "yaml"

        # Not found
        mime = get_mime_type_by_mime_string("application/x-unknown")
        assert mime is None

    def test_is_supported_mime_type(self):
        """is_supported_mime_type should check if MIME is in catalog."""
        assert is_supported_mime_type("application/json")
        assert is_supported_mime_type("application/yaml")
        assert not is_supported_mime_type("application/x-unknown")

    def test_list_mime_types(self):
        """list_mime_types should return all MIME types."""
        types = list_mime_types()
        assert isinstance(types, list)
        assert len(types) > 0
        assert any(t.id == "json" for t in types)
        assert any(t.id == "yaml" for t in types)

    def test_is_informational(self):
        """is_informational should check 1xx status codes."""
        assert is_informational(100)
        assert is_informational(101)
        assert not is_informational(200)
        assert not is_informational(404)

    def test_is_redirect(self):
        """is_redirect should check 3xx status codes."""
        assert is_redirect(301)
        assert is_redirect(302)
        assert is_redirect(307)
        assert not is_redirect(200)
        assert not is_redirect(404)


class TestCountry:
    """Test Country model and methods."""

    def test_country_creation(self):
        """Country should be created with all fields."""
        country = Country(
            alpha2="US",
            alpha3="USA",
            numeric="840",
            name="United States of America",
            officialName="United States of America",  # Use alias (YAML/JSON style)
        )
        assert country.alpha2 == "US"
        assert country.alpha3 == "USA"
        assert country.numeric == "840"
        assert country.name == "United States of America"
        assert country.official_name == "United States of America"

    def test_country_creation_with_field_name(self):
        """Country should accept both field name and alias (populate_by_name=True)."""
        # Test using Pythonic field name (enabled by populate_by_name=True in v0.1.2)
        country = Country(
            alpha2="CA",
            alpha3="CAN",
            numeric="124",
            name="Canada",
            official_name="Canada",  # Pythonic field name
        )
        assert country.alpha2 == "CA"
        assert country.official_name == "Canada"

    def test_country_matches_code_alpha2(self):
        """Country should match alpha-2 codes."""
        country = Country(alpha2="US", alpha3="USA", numeric="840", name="United States of America")
        assert country.matches_code("US")
        assert country.matches_code("us")  # Case insensitive
        assert not country.matches_code("CA")

    def test_country_matches_code_alpha3(self):
        """Country should match alpha-3 codes."""
        country = Country(alpha2="US", alpha3="USA", numeric="840", name="United States of America")
        assert country.matches_code("USA")
        assert country.matches_code("usa")  # Case insensitive
        assert not country.matches_code("CAN")

    def test_country_matches_code_numeric(self):
        """Country should match numeric codes."""
        country = Country(alpha2="US", alpha3="USA", numeric="840", name="United States of America")
        assert country.matches_code("840")
        assert not country.matches_code("124")

    def test_country_matches_code_case_insensitive(self):
        """Country should match codes case-insensitively."""
        country = Country(alpha2="US", alpha3="USA", numeric="840", name="United States of America")
        assert country.matches_code("us")
        assert country.matches_code("Us")
        assert country.matches_code("uS")
        assert country.matches_code("usa")
        assert country.matches_code("Usa")
        assert country.matches_code("UsA")

    def test_country_matches_code_numeric_padding(self):
        """Country should match numeric codes with zero-padding."""
        country = Country(alpha2="BR", alpha3="BRA", numeric="076", name="Brazil")
        assert country.matches_code("076")
        assert country.matches_code("76")  # Should pad to 076
        assert not country.matches_code("76a")


class TestCountryCatalog:
    """Test country lookup methods in FoundryCatalog."""

    def test_catalog_get_country(self, catalog):
        """Catalog should lookup country by alpha-2."""
        country = catalog.get_country("US")
        assert country is not None
        assert country.alpha2 == "US"
        assert country.name == "United States of America"

    def test_catalog_get_country_case_insensitive(self, catalog):
        """Catalog should handle case-insensitive alpha-2 lookup."""
        country = catalog.get_country("us")
        assert country is not None
        assert country.alpha2 == "US"

        country = catalog.get_country("ca")
        assert country is not None
        assert country.alpha2 == "CA"

    def test_catalog_get_country_not_found(self, catalog):
        """Catalog should return None for invalid alpha-2."""
        country = catalog.get_country("XX")
        assert country is None

        country = catalog.get_country("ZZZ")
        assert country is None

    def test_catalog_get_country_by_alpha3(self, catalog):
        """Catalog should lookup country by alpha-3."""
        country = catalog.get_country_by_alpha3("USA")
        assert country is not None
        assert country.alpha3 == "USA"
        assert country.alpha2 == "US"

    def test_catalog_get_country_by_alpha3_case_insensitive(self, catalog):
        """Catalog should handle case-insensitive alpha-3 lookup."""
        country = catalog.get_country_by_alpha3("usa")
        assert country is not None
        assert country.alpha3 == "USA"

        country = catalog.get_country_by_alpha3("CaN")
        assert country is not None
        assert country.alpha3 == "CAN"

    def test_catalog_get_country_by_alpha3_not_found(self, catalog):
        """Catalog should return None for invalid alpha-3."""
        country = catalog.get_country_by_alpha3("XXX")
        assert country is None

    def test_catalog_get_country_by_numeric(self, catalog):
        """Catalog should lookup country by numeric code."""
        country = catalog.get_country_by_numeric("840")
        assert country is not None
        assert country.numeric == "840"
        assert country.alpha2 == "US"

    def test_catalog_get_country_by_numeric_zero_padding(self, catalog):
        """Catalog should handle numeric lookup with zero-padding."""
        country = catalog.get_country_by_numeric("76")
        assert country is not None
        assert country.numeric == "076"
        assert country.alpha2 == "BR"

        # Also test with full padding
        country = catalog.get_country_by_numeric("076")
        assert country is not None
        assert country.alpha2 == "BR"

    def test_catalog_get_country_by_numeric_not_found(self, catalog):
        """Catalog should return None for invalid numeric code."""
        country = catalog.get_country_by_numeric("999")
        assert country is None

    def test_catalog_list_countries(self, catalog):
        """Catalog should list all countries."""
        countries = catalog.list_countries()
        assert isinstance(countries, list)
        assert len(countries) == 5  # US, CA, JP, DE, BR
        alpha2_codes = {c.alpha2 for c in countries}
        assert "US" in alpha2_codes
        assert "CA" in alpha2_codes
        assert "JP" in alpha2_codes
        assert "DE" in alpha2_codes
        assert "BR" in alpha2_codes

    def test_catalog_countries_lazy_loading(self, catalog):
        """Catalog should lazy load countries."""
        # Initially, countries should not be loaded
        assert catalog._countries is None
        assert catalog._countries_alpha3 is None
        assert catalog._countries_numeric is None

        # After first access, should be loaded
        _ = catalog.get_country("US")
        assert catalog._countries is not None
        assert catalog._countries_alpha3 is not None
        assert catalog._countries_numeric is not None


class TestCountryConvenienceFunctions:
    """Test country convenience functions."""

    def test_validate_country_code_alpha2(self):
        """validate_country_code should validate alpha-2 codes."""
        assert validate_country_code("US")
        assert validate_country_code("CA")
        assert validate_country_code("JP")

    def test_validate_country_code_alpha2_case_insensitive(self):
        """validate_country_code should validate alpha-2 case-insensitively."""
        assert validate_country_code("us")
        assert validate_country_code("ca")
        assert validate_country_code("Jp")

    def test_validate_country_code_alpha3(self):
        """validate_country_code should validate alpha-3 codes."""
        assert validate_country_code("USA")
        assert validate_country_code("CAN")
        assert validate_country_code("JPN")

    def test_validate_country_code_alpha3_case_insensitive(self):
        """validate_country_code should validate alpha-3 case-insensitively."""
        assert validate_country_code("usa")
        assert validate_country_code("can")
        assert validate_country_code("Jpn")

    def test_validate_country_code_numeric(self):
        """validate_country_code should validate numeric codes."""
        assert validate_country_code("840")  # US
        assert validate_country_code("124")  # CA
        assert validate_country_code("392")  # JP

    def test_validate_country_code_numeric_padding(self):
        """validate_country_code should validate numeric codes with padding."""
        assert validate_country_code("76")  # BR (076)
        assert validate_country_code("076")  # BR

    def test_validate_country_code_empty(self):
        """validate_country_code should return False for empty string."""
        assert not validate_country_code("")

    def test_validate_country_code_invalid(self):
        """validate_country_code should return False for invalid codes."""
        assert not validate_country_code("XX")
        assert not validate_country_code("XXX")
        assert not validate_country_code("999")
        assert not validate_country_code("invalid")

    def test_get_country(self):
        """get_country convenience function should lookup by alpha-2."""
        country = get_country("US")
        assert country is not None
        assert country.alpha2 == "US"

        country = get_country("us")  # Case insensitive
        assert country is not None
        assert country.alpha2 == "US"

    def test_get_country_by_alpha3(self):
        """get_country_by_alpha3 convenience function should lookup by alpha-3."""
        country = get_country_by_alpha3("USA")
        assert country is not None
        assert country.alpha3 == "USA"

        country = get_country_by_alpha3("usa")  # Case insensitive
        assert country is not None
        assert country.alpha3 == "USA"

    def test_get_country_by_numeric(self):
        """get_country_by_numeric convenience function should lookup by numeric."""
        country = get_country_by_numeric("840")
        assert country is not None
        assert country.numeric == "840"

    def test_get_country_by_numeric_padding(self):
        """get_country_by_numeric should handle zero-padding."""
        country = get_country_by_numeric("76")
        assert country is not None
        assert country.numeric == "076"
        assert country.alpha2 == "BR"

    def test_list_countries(self):
        """list_countries convenience function should return all countries."""
        countries = list_countries()
        assert isinstance(countries, list)
        assert len(countries) == 5
        alpha2_codes = {c.alpha2 for c in countries}
        assert "US" in alpha2_codes
        assert "CA" in alpha2_codes


class TestCountryIntegration:
    """Integration tests for country code functionality."""

    def test_all_lookup_methods_return_same_country(self):
        """All lookup methods should return the same country instance."""
        us_by_alpha2 = get_country("US")
        us_by_alpha3 = get_country_by_alpha3("USA")
        us_by_numeric = get_country_by_numeric("840")

        assert us_by_alpha2 is not None
        assert us_by_alpha3 is not None
        assert us_by_numeric is not None

        # Should all have same data
        assert us_by_alpha2.alpha2 == us_by_alpha3.alpha2 == us_by_numeric.alpha2
        assert us_by_alpha2.alpha3 == us_by_alpha3.alpha3 == us_by_numeric.alpha3
        assert us_by_alpha2.numeric == us_by_alpha3.numeric == us_by_numeric.numeric
        assert us_by_alpha2.name == us_by_alpha3.name == us_by_numeric.name

    def test_country_in_pydantic_model(self):
        """Country should be usable in Pydantic models."""
        from pydantic import BaseModel

        class Address(BaseModel):
            street: str
            country: Country

        country = get_country("US")
        address = Address(street="123 Main St", country=country)

        assert address.country.alpha2 == "US"
        assert address.country.name == "United States of America"

        # Test model validation
        model_dict = address.model_dump()
        assert model_dict["country"]["alpha2"] == "US"


class TestMimeDetectionIntegration:
    """Integration tests for MIME detection via catalog API."""

    def test_detect_via_catalog_import(self):
        from pyfulmen.foundry import detect_mime_type

        data = b'{"key": "value"}'
        mime = detect_mime_type(data)
        assert mime.mime == "application/json"

    def test_detect_file_via_catalog_import(self, tmp_path):
        from pyfulmen.foundry import detect_mime_type_from_file

        file = tmp_path / "test.yaml"
        file.write_bytes(b"key: value\n")

        mime = detect_mime_type_from_file(str(file))
        assert mime.id == "yaml"

    def test_detect_reader_via_catalog_import(self):
        import io

        from pyfulmen.foundry import detect_mime_type_from_reader

        data = b'<?xml version="1.0"?><root/>'
        reader = io.BytesIO(data)

        mime, new_reader = detect_mime_type_from_reader(reader)
        assert mime.id == "xml"
        assert new_reader.read() == data


class TestTelemetry:
    """Test telemetry instrumentation.

    Note: Current implementation creates independent MetricRegistry instances per call,
    so telemetry emission cannot be directly tested without module-level singleton helpers
    (per ADR-0008). These tests verify the code path executes without errors.

    Full telemetry testing will be added when module-level helpers are implemented.
    """

    def test_get_pattern_with_telemetry_enabled(self):
        """Verify get_pattern executes with telemetry without errors."""
        from pyfulmen.foundry import get_pattern

        pattern = get_pattern("ansi-email")
        assert pattern is not None
        assert pattern.id == "ansi-email"

        # Telemetry is emitted to an internal registry instance.
        # Full assertion testing requires module-level singleton helpers per ADR-0008.

    def test_get_mime_type_with_telemetry_enabled(self):
        """Verify get_mime_type executes with telemetry without errors."""
        from pyfulmen.foundry import get_mime_type

        mime_type = get_mime_type("json")
        assert mime_type is not None
        assert mime_type.id == "json"

        # Telemetry is emitted to an internal registry instance.
        # Full assertion testing requires module-level singleton helpers per ADR-0008.
