"""Typed role catalog for Crucible agentic roles.

Loads role definitions from synced YAML files in config/crucible-py/agentic/roles/
and returns them as typed dataclasses. This is pyfulmen's own implementation — it
does NOT use the vendored src/crucible/agentic.py (which resolves paths differently).

Example:
    >>> from pyfulmen.crucible import load_role, list_role_slugs
    >>> slugs = list_role_slugs()
    >>> role = load_role("devlead")
    >>> print(f"{role.name}: {role.description}")
    Development Lead: Architecture, implementation, and code review for FulmenHQ ecosystem
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

from .. import foundry
from . import _paths
from .errors import AssetNotFoundError

_ROLES_DIR = _paths.CONFIG_DIR / "agentic" / "roles"

# Matches the slug pattern defined in role-prompt.schema.json:
# lowercase letters and digits only, must start with a letter.
_ROLE_SLUG_RE = re.compile(r"^[a-z][a-z0-9]*$")


@dataclass
class RoleMindset:
    """Focus questions and principles that guide a role's thinking."""

    focus: list[str] = field(default_factory=list)
    principles: list[str] = field(default_factory=list)


@dataclass
class RoleEscalation:
    """Describes when a role should escalate to another target."""

    target: str = ""
    when: str = ""


@dataclass
class RoleExample:
    """Example artifact (commit, review, etc.) demonstrating the role in action."""

    type: str = ""
    title: str = ""
    content: str = ""


@dataclass
class RequiredReadingFile:
    """A specific file that must be read before starting work."""

    path: str = ""
    reason: str = ""


@dataclass
class RequiredReading:
    """Required reading block for a role — files that must be read before starting."""

    description: str | None = None
    pattern: str | None = None
    files: list[RequiredReadingFile] = field(default_factory=list)


@dataclass
class RolePrompt:
    """Typed representation of a role definition from the Crucible agentic role catalog."""

    slug: str = ""
    name: str = ""
    description: str = ""
    version: str = ""
    status: str = ""
    scope: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    escalates_to: list[RoleEscalation] = field(default_factory=list)
    does_not: list[str] = field(default_factory=list)
    author: str | None = None
    category: str | None = None
    extends: str | None = None
    domains: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    context: str | None = None
    mindset: RoleMindset | None = None
    examples: list[RoleExample] = field(default_factory=list)
    checklists: dict[str, list[str]] = field(default_factory=dict)
    pre_push_checklist: list[str] = field(default_factory=list)
    required_reading: RequiredReading | None = None
    cross_role_note: str | None = None


def _parse_role(data: dict) -> RolePrompt:
    """Parse a raw YAML dict into a typed RolePrompt dataclass tree."""
    mindset = None
    if "mindset" in data and data["mindset"]:
        m = data["mindset"]
        mindset = RoleMindset(
            focus=m.get("focus") or [],
            principles=m.get("principles") or [],
        )

    escalates_to = [
        RoleEscalation(target=e.get("target", ""), when=e.get("when", "")) for e in (data.get("escalates_to") or [])
    ]

    examples = [
        RoleExample(
            type=e.get("type", ""),
            title=e.get("title", ""),
            content=e.get("content", ""),
        )
        for e in (data.get("examples") or [])
    ]

    required_reading = None
    rr = data.get("required_reading")
    if isinstance(rr, dict) and rr:
        files = [
            RequiredReadingFile(path=f.get("path", ""), reason=f.get("reason", ""))
            for f in (rr.get("files") or [])
            if isinstance(f, dict)
        ]
        required_reading = RequiredReading(
            description=rr.get("description"),
            pattern=rr.get("pattern"),
            files=files,
        )

    return RolePrompt(
        slug=data.get("slug", ""),
        name=data.get("name", ""),
        description=data.get("description", ""),
        version=data.get("version", ""),
        status=data.get("status", ""),
        author=data.get("author"),
        category=data.get("category"),
        extends=data.get("extends"),
        domains=data.get("domains") or [],
        tags=data.get("tags") or [],
        context=data.get("context"),
        scope=data.get("scope") or [],
        mindset=mindset,
        responsibilities=data.get("responsibilities") or [],
        escalates_to=escalates_to,
        does_not=data.get("does_not") or [],
        examples=examples,
        checklists=data.get("checklists") or {},
        pre_push_checklist=data.get("pre_push_checklist") or [],
        required_reading=required_reading,
        cross_role_note=data.get("cross_role_note"),
    )


def list_role_slugs() -> list[str]:
    """Return sorted slugs of all available roles. README.md is excluded.

    Returns:
        Sorted list of role slug strings.

    Example:
        >>> slugs = list_role_slugs()
        >>> "devlead" in slugs
        True
    """
    return [f.stem for f in sorted(_ROLES_DIR.iterdir()) if f.suffix == ".yaml"]


def load_role(slug: str) -> RolePrompt:
    """Load and parse a single role by slug.

    Args:
        slug: Role slug (e.g., "devlead", "secrev"). Must match ``^[a-z][a-z0-9]*$``.

    Returns:
        Typed RolePrompt dataclass.

    Raises:
        ValueError: If slug format is invalid.
        AssetNotFoundError: If role not found (includes similarity suggestions).

    Example:
        >>> role = load_role("devlead")
        >>> print(role.name)
        Development Lead
    """
    if not _ROLE_SLUG_RE.fullmatch(slug):
        raise ValueError(f"Invalid role slug: {slug!r}")

    role_file = _ROLES_DIR / f"{slug}.yaml"
    if not role_file.exists():
        available = list_role_slugs()
        suggestions = foundry.similarity.suggest(slug, available, min_score=0.6, max_suggestions=3, normalize_text=True)
        raise AssetNotFoundError(
            slug,
            category="roles",
            suggestions=[s.value for s in suggestions],
        )

    with role_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return _parse_role(data)


def load_role_catalog() -> dict[str, RolePrompt]:
    """Load all roles from the embedded catalog.

    Returns:
        Dict keyed by slug from the parsed YAML (not the filename).

    Example:
        >>> catalog = load_role_catalog()
        >>> "devlead" in catalog
        True
    """
    catalog: dict[str, RolePrompt] = {}
    for slug in list_role_slugs():
        role = load_role(slug)
        catalog[role.slug] = role
    return catalog


__all__ = [
    "RoleMindset",
    "RoleEscalation",
    "RoleExample",
    "RequiredReadingFile",
    "RequiredReading",
    "RolePrompt",
    "list_role_slugs",
    "load_role",
    "load_role_catalog",
]
