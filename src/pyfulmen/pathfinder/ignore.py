"""
Ignore pattern handling for pyfulmen.pathfinder.

Provides support for `.fulmenignore` semantics similar to gofulmen, allowing
pathfinder to skip files and directories defined by glob-style patterns.
"""

from __future__ import annotations

from collections.abc import Iterable
from fnmatch import fnmatch
from pathlib import Path


class IgnoreMatcher:
    """Evaluate ignore patterns loaded from `.fulmenignore` files."""

    def __init__(self, root: Path):
        """
        Initialize matcher for a given root directory.

        Args:
            root: Root directory from which relative paths are evaluated.
        """
        self._root = root
        self._patterns: list[str] = []
        self._load_fulmenignore()

    @property
    def patterns(self) -> list[str]:
        """Return loaded ignore patterns."""
        return list(self._patterns)

    def add_patterns(self, patterns: Iterable[str]) -> None:
        """Add custom ignore patterns."""
        for pattern in patterns:
            normalized = pattern.strip()
            if normalized:
                self._patterns.append(normalized.replace("\\", "/"))

    def is_ignored(self, relative_path: Path) -> bool:
        """
        Determine whether a relative path should be ignored.

        Args:
            relative_path: Path relative to the root directory.

        Returns:
            True if the path matches any ignore pattern, else False.
        """
        posix_path = relative_path.as_posix()
        filename = relative_path.name

        for pattern in self._patterns:
            normalized = pattern.rstrip()

            # Directory pattern (trailing slash) ignores directory and descendants.
            if normalized.endswith("/"):
                directory = normalized.rstrip("/")
                if posix_path == directory or posix_path.startswith(f"{directory}/"):
                    return True
                continue

            # Any directory depth pattern.
            if fnmatch(posix_path, normalized):
                return True

            # Gitignore-style filename pattern (no slash) matches in any directory.
            if "/" not in normalized and fnmatch(filename, normalized):
                return True

        return False

    def _load_fulmenignore(self) -> None:
        """Load patterns from `.fulmenignore` if present."""
        ignore_file = self._root / ".fulmenignore"
        if not ignore_file.exists() or not ignore_file.is_file():
            return

        try:
            contents = ignore_file.read_text(encoding="utf-8")
        except OSError:
            # Non-fatal – treat as no ignore patterns.
            return

        for line in contents.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            self._patterns.append(stripped.replace("\\", "/"))


__all__ = ["IgnoreMatcher"]
