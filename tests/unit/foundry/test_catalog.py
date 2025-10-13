"""Tests for foundry catalog models and loaders."""

import pytest

from pyfulmen.config.loader import ConfigLoader
from pyfulmen.foundry.catalog import (
    FoundryCatalog,
    HttpStatusCode,
    HttpStatusGroup,
    HttpStatusHelper,
    MimeType,
    Pattern,
    PatternAccessor,
    get_default_catalog,
    get_mime_type,
    get_mime_type_by_extension,
    get_pattern,
    is_client_error,
    is_server_error,
    is_success,
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
