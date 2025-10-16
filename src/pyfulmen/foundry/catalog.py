"""Foundry catalog models and accessors.

Provides access to curated pattern catalogs, MIME types, HTTP status groups,
and country codes from Crucible configuration.
"""

import re
from typing import TYPE_CHECKING, Any

from pydantic import Field, computed_field, field_validator

from .models import FulmenCatalogModel

if TYPE_CHECKING:
    from ..config.loader import ConfigLoader


class Pattern(FulmenCatalogModel):
    """Immutable pattern definition from Foundry catalog.

    Represents a compiled regex, glob, or literal pattern with metadata
    for validation and documentation.

    Example:
        >>> pattern = Pattern(
        ...     id="email",
        ...     name="Email Address",
        ...     kind="regex",
        ...     pattern=r"^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$",
        ...     description="Email validation pattern"
        ... )
        >>> pattern.match("user@example.com")
        True
        >>> pattern("invalid.email")  # Can also call directly
        False
    """

    id: str = Field(description="Unique pattern identifier")
    name: str = Field(description="Human-readable pattern name")
    kind: str = Field(description="Pattern type: regex, glob, or literal")
    pattern: str = Field(description="Pattern string")
    description: str = Field(default="", description="Pattern description")
    examples: list[str] = Field(default_factory=list, description="Valid example strings")
    non_examples: list[str] = Field(default_factory=list, description="Invalid example strings")
    flags: dict[str, Any] = Field(
        default_factory=dict,
        description="Language-specific regex flags (python, go, typescript, etc.)",
    )

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        """Ensure kind is one of: regex, glob, literal."""
        if v not in {"regex", "glob", "literal"}:
            raise ValueError(f"Pattern kind must be regex/glob/literal, got: {v}")
        return v

    @computed_field
    @property
    def compiled_pattern(self) -> re.Pattern[str]:
        """Lazily compiled regex pattern.

        Returns:
            Compiled regex pattern with appropriate flags

        Note:
            Only valid for kind='regex'. Glob and literal patterns
            are handled differently.
        """
        if self.kind != "regex":
            raise ValueError(f"Cannot compile non-regex pattern of kind: {self.kind}")

        # Extract Python-specific flags
        flags = 0
        if python_flags := self.flags.get("python"):
            if python_flags.get("ignoreCase"):
                flags |= re.IGNORECASE
            if python_flags.get("multiline"):
                flags |= re.MULTILINE
            if python_flags.get("dotall"):
                flags |= re.DOTALL
            if python_flags.get("unicode"):
                flags |= re.UNICODE

        return re.compile(self.pattern, flags)

    def match(self, value: str) -> bool:
        """Test if value matches this pattern.

        Args:
            value: String to test against pattern

        Returns:
            True if value matches pattern, False otherwise

        Example:
            >>> email_pattern.match("user@example.com")
            True
            >>> email_pattern.match("invalid")
            False
        """
        if self.kind == "regex":
            return bool(self.compiled_pattern.match(value))
        elif self.kind == "literal":
            return value == self.pattern
        elif self.kind == "glob":
            # Convert glob to regex
            import fnmatch

            return fnmatch.fnmatch(value, self.pattern)
        else:
            raise ValueError(f"Unknown pattern kind: {self.kind}")

    def search(self, value: str) -> bool:
        """Search for pattern anywhere in value (not just at start).

        Args:
            value: String to search

        Returns:
            True if pattern found in value

        Example:
            >>> email_pattern.search("Contact: user@example.com for info")
            True
        """
        if self.kind == "regex":
            return bool(self.compiled_pattern.search(value))
        elif self.kind == "literal":
            return self.pattern in value
        elif self.kind == "glob":
            # Glob doesn't have "search" semantic - use match
            return self.match(value)
        else:
            raise ValueError(f"Unknown pattern kind: {self.kind}")

    def __call__(self, value: str) -> bool:
        """Allow pattern to be called directly: pattern(value).

        This is a Python-specific convenience that makes patterns
        feel more like functions.

        Args:
            value: String to test

        Returns:
            True if value matches pattern

        Example:
            >>> email_pattern = patterns.email()
            >>> if email_pattern("user@example.com"):
            ...     print("Valid email")
        """
        return self.match(value)

    def describe(self) -> str:
        """Get formatted pattern description with examples.

        Returns:
            Multi-line string with pattern details

        Example:
            >>> print(email_pattern.describe())
            Email Address (email)
            Pattern: ^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$
            Description: Email validation pattern

            Valid examples:
              - user@example.com
              - admin@company.org

            Invalid examples:
              - invalid.email
              - @example.com
        """
        lines = [
            f"{self.name} ({self.id})",
            f"Pattern: {self.pattern}",
        ]

        if self.description:
            lines.append(f"Description: {self.description}")

        if self.examples:
            lines.append("")
            lines.append("Valid examples:")
            for example in self.examples:
                lines.append(f"  - {example}")

        if self.non_examples:
            lines.append("")
            lines.append("Invalid examples:")
            for ex in self.non_examples:
                lines.append(f"  - {ex}")

        return "\n".join(lines)


class MimeType(FulmenCatalogModel):
    """Immutable MIME type definition from Foundry catalog.

    Represents a MIME type with extensions for file type detection.

    Example:
        >>> mime_type = MimeType(
        ...     id="json",
        ...     mime="application/json",
        ...     name="JSON",
        ...     extensions=["json", "map"],
        ...     description="JavaScript Object Notation"
        ... )
        >>> "json" in mime_type.extensions
        True
    """

    id: str = Field(description="Unique MIME type identifier")
    mime: str = Field(description="MIME type string (e.g., application/json)")
    name: str = Field(description="Human-readable name")
    extensions: list[str] = Field(
        default_factory=list, description="File extensions for this MIME type"
    )
    description: str = Field(default="", description="MIME type description")

    def matches_extension(self, extension: str) -> bool:
        """Check if given extension matches this MIME type.

        Args:
            extension: File extension (with or without leading dot)

        Returns:
            True if extension matches

        Example:
            >>> json_mime.matches_extension("json")
            True
            >>> json_mime.matches_extension(".json")
            True
        """
        ext = extension.lstrip(".")
        return ext.lower() in [e.lower() for e in self.extensions]


class HttpStatusCode(FulmenCatalogModel):
    """Individual HTTP status code with reason phrase.

    Example:
        >>> status = HttpStatusCode(value=200, reason="OK")
        >>> status.value
        200
    """

    value: int = Field(description="HTTP status code (e.g., 200, 404)")
    reason: str = Field(description="HTTP reason phrase (e.g., OK, Not Found)")


class HttpStatusGroup(FulmenCatalogModel):
    """Immutable HTTP status code group from Foundry catalog.

    Represents a group of related HTTP status codes (e.g., 2xx success).

    Example:
        >>> group = HttpStatusGroup(
        ...     id="success",
        ...     name="Successful Responses",
        ...     description="2xx HTTP status codes",
        ...     codes=[
        ...         HttpStatusCode(value=200, reason="OK"),
        ...         HttpStatusCode(value=201, reason="Created")
        ...     ]
        ... )
        >>> group.contains(200)
        True
    """

    id: str = Field(description="Unique group identifier")
    name: str = Field(description="Human-readable group name")
    description: str = Field(default="", description="Group description")
    codes: list[HttpStatusCode] = Field(
        default_factory=list, description="Status codes in this group"
    )

    def contains(self, status_code: int) -> bool:
        """Check if status code is in this group.

        Args:
            status_code: HTTP status code to check

        Returns:
            True if code is in this group

        Example:
            >>> success_group.contains(200)
            True
            >>> success_group.contains(404)
            False
        """
        return any(code.value == status_code for code in self.codes)

    def get_reason(self, status_code: int) -> str | None:
        """Get reason phrase for status code.

        Args:
            status_code: HTTP status code

        Returns:
            Reason phrase or None if not found

        Example:
            >>> success_group.get_reason(200)
            'OK'
        """
        for code in self.codes:
            if code.value == status_code:
                return code.reason
        return None


class Country(FulmenCatalogModel):
    """Immutable ISO 3166-1 country code definition from Foundry catalog.

    Represents a country with Alpha-2, Alpha-3, and Numeric codes.

    Example:
        >>> country = Country(
        ...     alpha2="US",
        ...     alpha3="USA",
        ...     numeric="840",
        ...     name="United States of America",
        ...     official_name="United States of America"
        ... )
        >>> country.alpha2
        'US'
    """

    alpha2: str = Field(description="ISO 3166-1 alpha-2 two-letter country code (e.g., US, CA)")
    alpha3: str = Field(description="ISO 3166-1 alpha-3 three-letter country code (e.g., USA, CAN)")
    numeric: str = Field(description="ISO 3166-1 numeric country code as string (e.g., 840, 076)")
    name: str = Field(description="Common English name of the country")
    official_name: str | None = Field(
        None, alias="officialName", description="Official name of the country"
    )

    def matches_code(self, code: str) -> bool:
        """Check if given code matches this country's codes (case-insensitive).

        Args:
            code: Country code to check (alpha-2, alpha-3, or numeric)

        Returns:
            True if code matches any of this country's codes

        Example:
            >>> us_country.matches_code("us")
            True
            >>> us_country.matches_code("USA")
            True
            >>> us_country.matches_code("840")
            True
        """
        code_upper = code.upper()
        return (
            self.alpha2.upper() == code_upper
            or self.alpha3.upper() == code_upper
            or self.numeric == code
            or (code.isdigit() and self.numeric == code.zfill(3))
        )


class FoundryCatalog:
    """Immutable catalog loader for Foundry pattern datasets.

    Loads patterns, MIME types, HTTP statuses from Crucible configuration.
    Uses lazy loading for performance.

    Example:
        >>> from pyfulmen.config.loader import ConfigLoader
        >>> loader = ConfigLoader(app_name="fulmen")
        >>> catalog = FoundryCatalog(loader)
        >>> pattern = catalog.get_pattern("ansi-email")
        >>> pattern.match("user@example.com")
        True
    """

    def __init__(self, config_loader: "ConfigLoader"):
        """Initialize catalog with config loader.

        Args:
            config_loader: ConfigLoader instance for accessing Crucible data
        """
        from ..config.loader import ConfigLoader

        if not isinstance(config_loader, ConfigLoader):
            raise TypeError("config_loader must be ConfigLoader instance")

        self._config_loader = config_loader
        self._patterns: dict[str, Pattern] | None = None
        self._mime_types: dict[str, MimeType] | None = None
        self._http_groups: dict[str, HttpStatusGroup] | None = None
        self._http_code_to_group: dict[int, str] | None = None
        self._countries: dict[str, Country] | None = None  # Keyed by uppercase Alpha-2
        self._countries_alpha3: dict[str, Country] | None = None  # Keyed by uppercase Alpha-3
        self._countries_numeric: dict[str, Country] | None = None  # Keyed by zero-padded numeric

    def _load_patterns(self) -> dict[str, Pattern]:
        """Load patterns from Crucible (lazy loading).

        Returns:
            Dictionary mapping pattern ID to Pattern instance
        """
        if self._patterns is not None:
            return self._patterns

        config = self._config_loader.load("library/foundry/patterns")
        patterns = {}

        for pattern_data in config.get("patterns", []):
            pattern = Pattern(**pattern_data)
            patterns[pattern.id] = pattern

        self._patterns = patterns
        return patterns

    def _load_mime_types(self) -> dict[str, MimeType]:
        """Load MIME types from Crucible (lazy loading).

        Returns:
            Dictionary mapping MIME type ID to MimeType instance
        """
        if self._mime_types is not None:
            return self._mime_types

        config = self._config_loader.load("library/foundry/mime-types")
        mime_types = {}

        for mime_data in config.get("types", []):
            mime_type = MimeType(**mime_data)
            mime_types[mime_type.id] = mime_type

        self._mime_types = mime_types
        return mime_types

    def _load_http_groups(self) -> dict[str, HttpStatusGroup]:
        """Load HTTP status groups from Crucible (lazy loading).

        Returns:
            Dictionary mapping group ID to HttpStatusGroup instance
        """
        if self._http_groups is not None:
            return self._http_groups

        config = self._config_loader.load("library/foundry/http-statuses")
        groups = {}
        code_to_group = {}

        for group_data in config.get("groups", []):
            group = HttpStatusGroup(**group_data)
            groups[group.id] = group

            for code in group.codes:
                code_to_group[code.value] = group.id

        self._http_groups = groups
        self._http_code_to_group = code_to_group
        return groups

    def _load_countries(self) -> tuple[dict[str, Country], dict[str, Country], dict[str, Country]]:
        """Load countries from Crucible (lazy loading).

        Builds three precomputed indexes for O(1) lookups:
        - Alpha-2 (uppercase, e.g., "US")
        - Alpha-3 (uppercase, e.g., "USA")
        - Numeric (zero-padded to 3 digits, e.g., "840")

        Returns:
            Tuple of (alpha2_dict, alpha3_dict, numeric_dict)
        """
        if self._countries is not None:
            return self._countries, self._countries_alpha3, self._countries_numeric  # type: ignore

        config = self._config_loader.load("library/foundry/country-codes")
        countries = {}
        countries_alpha3 = {}
        countries_numeric = {}

        for country_data in config.get("countries", []):
            country = Country(**country_data)

            # Build primary index (Alpha-2, uppercase)
            if country.alpha2:
                normalized_alpha2 = country.alpha2.upper()
                countries[normalized_alpha2] = country

            # Build secondary index (Alpha-3, uppercase)
            if country.alpha3:
                normalized_alpha3 = country.alpha3.upper()
                countries_alpha3[normalized_alpha3] = country

            # Build tertiary index (Numeric, zero-padded to 3 digits)
            if country.numeric:
                # Ensure numeric code is zero-padded to 3 digits
                numeric_code = country.numeric.zfill(3)
                countries_numeric[numeric_code] = country

        self._countries = countries
        self._countries_alpha3 = countries_alpha3
        self._countries_numeric = countries_numeric
        return countries, countries_alpha3, countries_numeric

    def get_pattern(self, pattern_id: str) -> Pattern | None:
        """Get pattern by ID.

        Args:
            pattern_id: Pattern identifier (e.g., "ansi-email", "slug")

        Returns:
            Pattern instance or None if not found

        Example:
            >>> pattern = catalog.get_pattern("ansi-email")
            >>> pattern.match("user@example.com")
            True
        """
        patterns = self._load_patterns()
        return patterns.get(pattern_id)

    def get_all_patterns(self) -> dict[str, Pattern]:
        """Get all available patterns.

        Returns:
            Dictionary mapping pattern ID to Pattern instance

        Example:
            >>> patterns = catalog.get_all_patterns()
            >>> len(patterns) > 0
            True
        """
        return self._load_patterns().copy()

    def get_mime_type(self, mime_id: str) -> MimeType | None:
        """Get MIME type by ID.

        Args:
            mime_id: MIME type identifier (e.g., "json", "yaml")

        Returns:
            MimeType instance or None if not found

        Example:
            >>> mime_type = catalog.get_mime_type("json")
            >>> mime_type.mime
            'application/json'
        """
        mime_types = self._load_mime_types()
        return mime_types.get(mime_id)

    def get_mime_type_by_mime_string(self, mime_string: str) -> MimeType | None:
        """Get MIME type by MIME string (e.g., "application/json").

        Args:
            mime_string: MIME type string

        Returns:
            MimeType instance or None if not found

        Example:
            >>> mime_type = catalog.get_mime_type_by_mime_string("application/json")
            >>> mime_type.id
            'json'
        """
        mime_types = self._load_mime_types()
        mime_lower = mime_string.lower()

        for mime_type in mime_types.values():
            if mime_type.mime.lower() == mime_lower:
                return mime_type

        return None

    def get_mime_type_by_extension(self, extension: str) -> MimeType | None:
        """Get MIME type by file extension.

        Args:
            extension: File extension (with or without leading dot)

        Returns:
            MimeType instance or None if not found

        Example:
            >>> mime_type = catalog.get_mime_type_by_extension("json")
            >>> mime_type.mime
            'application/json'
        """
        mime_types = self._load_mime_types()
        ext = extension.lstrip(".").lower()

        for mime_type in mime_types.values():
            if mime_type.matches_extension(ext):
                return mime_type

        return None

    def get_all_mime_types(self) -> dict[str, MimeType]:
        """Get all available MIME types.

        Returns:
            Dictionary mapping MIME type ID to MimeType instance
        """
        return self._load_mime_types().copy()

    def get_http_status_group(self, group_id: str) -> HttpStatusGroup | None:
        """Get HTTP status group by ID.

        Args:
            group_id: Group identifier (e.g., "success", "client-error")

        Returns:
            HttpStatusGroup instance or None if not found

        Example:
            >>> group = catalog.get_http_status_group("success")
            >>> group.contains(200)
            True
        """
        groups = self._load_http_groups()
        return groups.get(group_id)

    def get_http_status_group_for_code(self, status_code: int) -> HttpStatusGroup | None:
        """Get HTTP status group for a specific status code.

        Args:
            status_code: HTTP status code (e.g., 200, 404)

        Returns:
            HttpStatusGroup instance or None if not found

        Example:
            >>> group = catalog.get_http_status_group_for_code(200)
            >>> group.id
            'success'
        """
        self._load_http_groups()
        if self._http_code_to_group is None:
            return None

        group_id = self._http_code_to_group.get(status_code)
        if group_id is None:
            return None

        return self._http_groups.get(group_id) if self._http_groups else None

    def get_all_http_groups(self) -> dict[str, HttpStatusGroup]:
        """Get all HTTP status groups.

        Returns:
            Dictionary mapping group ID to HttpStatusGroup instance
        """
        return self._load_http_groups().copy()

    def get_country(self, alpha2: str) -> Country | None:
        """Get country by Alpha-2 code (case-insensitive).

        Args:
            alpha2: ISO 3166-1 alpha-2 code (e.g., "US", "us")

        Returns:
            Country instance or None if not found

        Example:
            >>> country = catalog.get_country("US")
            >>> country.name
            'United States of America'
        """
        countries, _, _ = self._load_countries()
        normalized = alpha2.upper()
        return countries.get(normalized)

    def get_country_by_alpha3(self, alpha3: str) -> Country | None:
        """Get country by Alpha-3 code (case-insensitive).

        Args:
            alpha3: ISO 3166-1 alpha-3 code (e.g., "USA", "usa")

        Returns:
            Country instance or None if not found

        Example:
            >>> country = catalog.get_country_by_alpha3("USA")
            >>> country.name
            'United States of America'
        """
        _, countries_alpha3, _ = self._load_countries()
        normalized = alpha3.upper()
        return countries_alpha3.get(normalized)

    def get_country_by_numeric(self, numeric: str) -> Country | None:
        """Get country by numeric ISO 3166-1 code.

        The code is normalized to zero-padded 3-digit string.
        Accepts numeric codes with or without leading zeros.

        Args:
            numeric: Numeric country code (e.g., "840", "76")

        Returns:
            Country instance or None if not found

        Example:
            >>> country = catalog.get_country_by_numeric("840")
            >>> country.name
            'United States of America'
            >>> country = catalog.get_country_by_numeric("76")  # Brazil
            >>> country.name
            'Brazil'
        """
        _, _, countries_numeric = self._load_countries()
        # Normalize to 3 digits with zero-padding
        normalized = numeric.zfill(3)
        return countries_numeric.get(normalized)

    def list_countries(self) -> list[Country]:
        """List all countries from catalog.

        Returns:
            List of all Country instances

        Example:
            >>> countries = catalog.list_countries()
            >>> len(countries) > 0
            True
        """
        countries, _, _ = self._load_countries()
        return list(countries.values())


class PatternAccessor:
    """Helper for convenient pattern access and validation.

    Provides named methods for common patterns instead of looking up by ID.

    Example:
        >>> accessor = PatternAccessor(catalog)
        >>> email_pattern = accessor.email()
        >>> email_pattern.match("user@example.com")
        True
    """

    def __init__(self, catalog: FoundryCatalog):
        """Initialize accessor with catalog.

        Args:
            catalog: FoundryCatalog instance
        """
        self._catalog = catalog

    def email(self) -> Pattern | None:
        """Get internationalized email validation pattern.

        Returns:
            Pattern for RFC 5322 email addresses with Unicode support
        """
        return self._catalog.get_pattern("ansi-email")

    def slug(self) -> Pattern | None:
        """Get slug pattern (kebab-case or snake_case).

        Returns:
            Pattern for lowercase slugs with hyphen/underscore
        """
        return self._catalog.get_pattern("slug")

    def path_segment(self) -> Pattern | None:
        """Get path segment pattern.

        Returns:
            Pattern for URL path segments
        """
        return self._catalog.get_pattern("path-segment")

    def identifier(self) -> Pattern | None:
        """Get identifier pattern.

        Returns:
            Pattern for camelCase/snake_case identifiers
        """
        return self._catalog.get_pattern("identifier")

    def domain_name(self) -> Pattern | None:
        """Get fully qualified domain name pattern.

        Returns:
            Pattern for FQDN validation
        """
        return self._catalog.get_pattern("domain-name")

    def ipv6(self) -> Pattern | None:
        """Get IPv6 address pattern.

        Returns:
            Pattern for IPv6 addresses (full and compressed)
        """
        return self._catalog.get_pattern("ipv6")

    def uuid_v4(self) -> Pattern | None:
        """Get UUID v4 pattern.

        Returns:
            Pattern for RFC 4122 UUID v4
        """
        return self._catalog.get_pattern("uuid-v4")

    def semantic_version(self) -> Pattern | None:
        """Get semantic version pattern.

        Returns:
            Pattern for SemVer 2.0.0 versions
        """
        return self._catalog.get_pattern("semantic-version")

    def iso_date(self) -> Pattern | None:
        """Get ISO 8601 date pattern.

        Returns:
            Pattern for YYYY-MM-DD dates
        """
        return self._catalog.get_pattern("strict-iso-date")

    def iso_timestamp_utc(self) -> Pattern | None:
        """Get ISO 8601 UTC timestamp pattern.

        Returns:
            Pattern for UTC timestamps with optional fractional seconds
        """
        return self._catalog.get_pattern("iso-timestamp-z")

    def get_all_patterns(self) -> dict[str, Pattern]:
        """Get all available patterns.

        Returns:
            Dictionary mapping pattern ID to Pattern instance
        """
        return self._catalog.get_all_patterns()


class HttpStatusHelper:
    """HTTP status code helper utilities.

    Provides convenient methods for checking status code ranges and groups.

    Example:
        >>> helper = HttpStatusHelper(catalog)
        >>> helper.is_success(200)
        True
        >>> helper.is_client_error(404)
        True
    """

    def __init__(self, catalog: FoundryCatalog):
        """Initialize helper with catalog.

        Args:
            catalog: FoundryCatalog instance
        """
        self._catalog = catalog

    def is_informational(self, status_code: int) -> bool:
        """Check if status code is informational (1xx).

        Args:
            status_code: HTTP status code

        Returns:
            True if code is in 100-199 range

        Example:
            >>> helper.is_informational(100)
            True
        """
        group = self._catalog.get_http_status_group_for_code(status_code)
        return group is not None and group.id == "informational"

    def is_success(self, status_code: int) -> bool:
        """Check if status code is successful (2xx).

        Args:
            status_code: HTTP status code

        Returns:
            True if code is in 200-299 range

        Example:
            >>> helper.is_success(200)
            True
            >>> helper.is_success(201)
            True
        """
        group = self._catalog.get_http_status_group_for_code(status_code)
        return group is not None and group.id == "success"

    def is_redirect(self, status_code: int) -> bool:
        """Check if status code is redirection (3xx).

        Args:
            status_code: HTTP status code

        Returns:
            True if code is in 300-399 range

        Example:
            >>> helper.is_redirect(301)
            True
        """
        group = self._catalog.get_http_status_group_for_code(status_code)
        return group is not None and group.id == "redirect"

    def is_client_error(self, status_code: int) -> bool:
        """Check if status code is client error (4xx).

        Args:
            status_code: HTTP status code

        Returns:
            True if code is in 400-499 range

        Example:
            >>> helper.is_client_error(404)
            True
            >>> helper.is_client_error(400)
            True
        """
        group = self._catalog.get_http_status_group_for_code(status_code)
        return group is not None and group.id == "client-error"

    def is_server_error(self, status_code: int) -> bool:
        """Check if status code is server error (5xx).

        Args:
            status_code: HTTP status code

        Returns:
            True if code is in 500-599 range

        Example:
            >>> helper.is_server_error(500)
            True
            >>> helper.is_server_error(503)
            True
        """
        group = self._catalog.get_http_status_group_for_code(status_code)
        return group is not None and group.id == "server-error"

    def get_reason_phrase(self, status_code: int) -> str | None:
        """Get reason phrase for status code.

        Args:
            status_code: HTTP status code

        Returns:
            Reason phrase or None if not found

        Example:
            >>> helper.get_reason_phrase(200)
            'OK'
            >>> helper.get_reason_phrase(404)
            'Not Found'
        """
        group = self._catalog.get_http_status_group_for_code(status_code)
        if group is None:
            return None
        return group.get_reason(status_code)


_default_catalog: FoundryCatalog | None = None


def get_default_catalog() -> FoundryCatalog:
    """Get default Foundry catalog instance (singleton).

    Lazily initializes catalog on first access using ConfigLoader
    with 'fulmen' as app name.

    Returns:
        Singleton FoundryCatalog instance

    Example:
        >>> catalog = get_default_catalog()
        >>> pattern = catalog.get_pattern("slug")
    """
    global _default_catalog
    if _default_catalog is None:
        from ..config.loader import ConfigLoader

        loader = ConfigLoader(app_name="fulmen")
        _default_catalog = FoundryCatalog(loader)
    return _default_catalog


def get_pattern(pattern_id: str) -> Pattern | None:
    """Get pattern from default catalog by ID.

    Convenience function that uses the default catalog singleton.

    Args:
        pattern_id: Pattern identifier (e.g., "ansi-email", "slug")

    Returns:
        Pattern instance or None if not found

    Example:
        >>> from pyfulmen.foundry import get_pattern
        >>> email = get_pattern("ansi-email")
        >>> if email and email.match("user@example.com"):
        ...     print("Valid email")
    """
    catalog = get_default_catalog()
    return catalog.get_pattern(pattern_id)


def get_mime_type(mime_id: str) -> MimeType | None:
    """Get MIME type from default catalog by ID.

    Convenience function that uses the default catalog singleton.

    Args:
        mime_id: MIME type identifier (e.g., "json", "yaml")

    Returns:
        MimeType instance or None if not found

    Example:
        >>> from pyfulmen.foundry import get_mime_type
        >>> json_mime = get_mime_type("json")
        >>> print(json_mime.mime)
        application/json
    """
    catalog = get_default_catalog()
    return catalog.get_mime_type(mime_id)


def get_mime_type_by_extension(extension: str) -> MimeType | None:
    """Get MIME type from default catalog by file extension.

    Convenience function that uses the default catalog singleton.

    Args:
        extension: File extension (with or without leading dot)

    Returns:
        MimeType instance or None if not found

    Example:
        >>> from pyfulmen.foundry import get_mime_type_by_extension
        >>> mime = get_mime_type_by_extension("json")
        >>> print(mime.mime)
        application/json
    """
    catalog = get_default_catalog()
    return catalog.get_mime_type_by_extension(extension)


def get_mime_type_by_mime_string(mime_string: str) -> MimeType | None:
    """Get MIME type from default catalog by MIME string.

    Convenience function that uses the default catalog singleton.

    Args:
        mime_string: MIME type string (e.g., "application/json")

    Returns:
        MimeType instance or None if not found

    Example:
        >>> from pyfulmen.foundry import get_mime_type_by_mime_string
        >>> mime = get_mime_type_by_mime_string("application/json")
        >>> print(mime.id)
        json
    """
    catalog = get_default_catalog()
    return catalog.get_mime_type_by_mime_string(mime_string)


def is_supported_mime_type(mime_string: str) -> bool:
    """Check if MIME type string is supported in catalog.

    Convenience function that uses the default catalog singleton.

    Args:
        mime_string: MIME type string to check

    Returns:
        True if MIME type is in catalog, False otherwise

    Example:
        >>> from pyfulmen.foundry import is_supported_mime_type
        >>> is_supported_mime_type("application/json")
        True
        >>> is_supported_mime_type("application/x-unknown")
        False
    """
    catalog = get_default_catalog()
    return catalog.get_mime_type_by_mime_string(mime_string) is not None


def list_mime_types() -> list[MimeType]:
    """List all MIME types from default catalog.

    Convenience function that uses the default catalog singleton.

    Returns:
        List of all MIME type instances

    Example:
        >>> from pyfulmen.foundry import list_mime_types
        >>> types = list_mime_types()
        >>> len(types) > 0
        True
    """
    catalog = get_default_catalog()
    return list(catalog.get_all_mime_types().values())


def is_success(status_code: int) -> bool:
    """Check if HTTP status code is successful (2xx).

    Convenience function that uses the default catalog singleton.

    Args:
        status_code: HTTP status code

    Returns:
        True if code is in 200-299 range

    Example:
        >>> from pyfulmen.foundry import is_success
        >>> if is_success(200):
        ...     print("Request succeeded")
    """
    catalog = get_default_catalog()
    helper = HttpStatusHelper(catalog)
    return helper.is_success(status_code)


def is_client_error(status_code: int) -> bool:
    """Check if HTTP status code is client error (4xx).

    Convenience function that uses the default catalog singleton.

    Args:
        status_code: HTTP status code

    Returns:
        True if code is in 400-499 range

    Example:
        >>> from pyfulmen.foundry import is_client_error
        >>> if is_client_error(404):
        ...     print("Resource not found")
    """
    catalog = get_default_catalog()
    helper = HttpStatusHelper(catalog)
    return helper.is_client_error(status_code)


def is_server_error(status_code: int) -> bool:
    """Check if HTTP status code is server error (5xx).

    Convenience function that uses the default catalog singleton.

    Args:
        status_code: HTTP status code

    Returns:
        True if code is in 500-599 range

    Example:
        >>> from pyfulmen.foundry import is_server_error
        >>> if is_server_error(500):
        ...     print("Server error occurred")
    """
    catalog = get_default_catalog()
    helper = HttpStatusHelper(catalog)
    return helper.is_server_error(status_code)


def is_informational(status_code: int) -> bool:
    """Check if HTTP status code is informational (1xx).

    Convenience function that uses the default catalog singleton.

    Args:
        status_code: HTTP status code

    Returns:
        True if code is in 100-199 range

    Example:
        >>> from pyfulmen.foundry import is_informational
        >>> if is_informational(100):
        ...     print("Continue response")
    """
    catalog = get_default_catalog()
    helper = HttpStatusHelper(catalog)
    return helper.is_informational(status_code)


def is_redirect(status_code: int) -> bool:
    """Check if HTTP status code is redirect (3xx).

    Convenience function that uses the default catalog singleton.

    Args:
        status_code: HTTP status code

    Returns:
        True if code is in 300-399 range

    Example:
        >>> from pyfulmen.foundry import is_redirect
        >>> if is_redirect(301):
        ...     print("Moved permanently")
    """
    catalog = get_default_catalog()
    helper = HttpStatusHelper(catalog)
    return helper.is_redirect(status_code)


def validate_country_code(code: str) -> bool:
    """Check if country code is valid (Alpha-2, Alpha-3, or Numeric).

    Convenience function that uses the default catalog singleton.
    Supports all three ISO 3166-1 formats with case-insensitive matching.

    Args:
        code: Country code to validate (alpha-2, alpha-3, or numeric)

    Returns:
        True if code is valid, False otherwise

    Example:
        >>> from pyfulmen.foundry import validate_country_code
        >>> if validate_country_code("US"):
        ...     print("Valid country code")
        >>> if validate_country_code("usa"):  # Case-insensitive
        ...     print("Valid country code")
        >>> if validate_country_code("76"):  # Brazil numeric
        ...     print("Valid country code")
    """
    if not code:
        return False

    catalog = get_default_catalog()

    # Try Alpha-2 lookup
    if catalog.get_country(code) is not None:
        return True

    # Try Alpha-3 lookup
    if catalog.get_country_by_alpha3(code) is not None:
        return True

    # Try Numeric lookup
    return code.isdigit() and catalog.get_country_by_numeric(code) is not None


def get_country(alpha2: str) -> Country | None:
    """Get country from default catalog by Alpha-2 code.

    Convenience function that uses the default catalog singleton.

    Args:
        alpha2: ISO 3166-1 alpha-2 code (e.g., "US", "us")

    Returns:
        Country instance or None if not found

    Example:
        >>> from pyfulmen.foundry import get_country
        >>> country = get_country("US")
        >>> if country:
        ...     print(country.name)
        United States of America
    """
    catalog = get_default_catalog()
    return catalog.get_country(alpha2)


def get_country_by_alpha3(alpha3: str) -> Country | None:
    """Get country from default catalog by Alpha-3 code.

    Convenience function that uses the default catalog singleton.

    Args:
        alpha3: ISO 3166-1 alpha-3 code (e.g., "USA", "usa")

    Returns:
        Country instance or None if not found

    Example:
        >>> from pyfulmen.foundry import get_country_by_alpha3
        >>> country = get_country_by_alpha3("USA")
        >>> if country:
        ...     print(country.name)
        United States of America
    """
    catalog = get_default_catalog()
    return catalog.get_country_by_alpha3(alpha3)


def get_country_by_numeric(numeric: str) -> Country | None:
    """Get country from default catalog by numeric code.

    Convenience function that uses the default catalog singleton.
    Numeric codes are zero-padded to 3 digits automatically.

    Args:
        numeric: Numeric country code (e.g., "840", "76")

    Returns:
        Country instance or None if not found

    Example:
        >>> from pyfulmen.foundry import get_country_by_numeric
        >>> country = get_country_by_numeric("840")
        >>> if country:
        ...     print(country.name)
        United States of America
        >>> country = get_country_by_numeric("76")  # Brazil
        >>> if country:
        ...     print(country.name)
        Brazil
    """
    catalog = get_default_catalog()
    return catalog.get_country_by_numeric(numeric)


def list_countries() -> list[Country]:
    """List all countries from default catalog.

    Convenience function that uses the default catalog singleton.

    Returns:
        List of all Country instances

    Example:
        >>> from pyfulmen.foundry import list_countries
        >>> countries = list_countries()
        >>> for country in countries:
        ...     print(f"{country.alpha2}: {country.name}")
        US: United States of America
        CA: Canada
        ...
    """
    catalog = get_default_catalog()
    return catalog.list_countries()


def detect_mime_type(data: bytes) -> MimeType | None:
    """Detect MIME type from raw bytes.

    Convenience function that uses content-based detection.
    See mime_detection.detect_mime_type for full documentation.

    Args:
        data: Raw bytes to analyze

    Returns:
        MimeType instance if detected, None if unknown

    Example:
        >>> from pyfulmen.foundry import detect_mime_type
        >>> data = b'{"key": "value"}'
        >>> mime = detect_mime_type(data)
        >>> print(mime.mime)
        application/json
    """
    from .mime_detection import detect_mime_type as _detect

    return _detect(data)


def detect_mime_type_from_file(path: str) -> MimeType | None:
    """Detect MIME type from file path.

    Convenience function that uses content-based detection.
    See mime_detection.detect_mime_type_from_file for full documentation.

    Args:
        path: File path (string or Path object)

    Returns:
        MimeType instance if detected, None if unknown or empty

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read

    Example:
        >>> from pyfulmen.foundry import detect_mime_type_from_file
        >>> mime = detect_mime_type_from_file('config.json')
        >>> if mime:
        ...     print(f'Detected: {mime.mime}')
    """
    from .mime_detection import detect_mime_type_from_file as _detect_file

    return _detect_file(path)


def detect_mime_type_from_reader(reader, max_bytes: int = 512) -> tuple[MimeType | None, any]:
    """Detect MIME type from streaming data.

    Convenience function that uses content-based detection.
    See mime_detection.detect_mime_type_from_reader for full documentation.

    Args:
        reader: Input stream
        max_bytes: Maximum bytes to read for detection (default 512)

    Returns:
        Tuple of (MimeType or None, new_reader with buffered bytes)

    Example:
        >>> from pyfulmen.foundry import detect_mime_type_from_reader
        >>> with open('data.bin', 'rb') as f:
        ...     mime, reader = detect_mime_type_from_reader(f)
        ...     if mime:
        ...         process_file(reader, mime)
    """
    from .mime_detection import detect_mime_type_from_reader as _detect_reader

    return _detect_reader(reader, max_bytes)


__all__ = [
    "Pattern",
    "MimeType",
    "HttpStatusCode",
    "HttpStatusGroup",
    "Country",
    "FoundryCatalog",
    "PatternAccessor",
    "HttpStatusHelper",
    "get_default_catalog",
    "get_pattern",
    "get_mime_type",
    "get_mime_type_by_extension",
    "get_mime_type_by_mime_string",
    "is_supported_mime_type",
    "list_mime_types",
    "detect_mime_type",
    "detect_mime_type_from_file",
    "detect_mime_type_from_reader",
    "is_success",
    "is_client_error",
    "is_server_error",
    "is_informational",
    "is_redirect",
    "validate_country_code",
    "get_country",
    "get_country_by_alpha3",
    "get_country_by_numeric",
    "list_countries",
]
