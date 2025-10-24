"""Three-layer configuration loader utilities."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .. import crucible
from ..telemetry import MetricRegistry
from . import paths
from .merger import merge_configs

DEFAULT_APP_NAMESPACE = "fulmen"


@dataclass(slots=True)
class ConfigSource:
    """Metadata describing a configuration layer."""

    layer: str  # defaults | user | application
    source: Path | str
    applied: bool


@dataclass(slots=True)
class ConfigLoadResult:
    """Result containing merged configuration and layer metadata."""

    data: dict[str, Any]
    sources: list[ConfigSource]


class ConfigLoader:
    """Load configuration using Crucible defaults + user overrides + BYOC."""

    def __init__(
        self,
        app: str | None = None,
        *,
        vendor: str | None = None,
        app_name: str | None = None,
    ) -> None:
        if app is None:
            app = app_name or DEFAULT_APP_NAMESPACE
        elif app_name and app_name != app:
            raise ValueError("app and app_name arguments refer to different applications")

        self.app = app
        self.vendor = vendor
        self.user_config_dir = paths.get_app_config_dir(app, vendor=vendor)

    def load(self, crucible_path: str, app_config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return merged configuration data (no metadata)."""
        return self.load_with_metadata(crucible_path, app_config=app_config).data

    def load_with_metadata(
        self,
        crucible_path: str,
        app_config: dict[str, Any] | None = None,
    ) -> ConfigLoadResult:
        """
        Load configuration and return metadata about each applied layer.

        Telemetry:
            - Emits config_load_ms histogram (operation duration)
            - Emits config_load_errors counter (on load failure)
        """
        start_time = time.perf_counter()
        registry = MetricRegistry()

        try:
            return self._load_with_metadata_impl(crucible_path, app_config, registry)
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            registry.histogram("config_load_ms").observe(duration_ms)

    def _load_with_metadata_impl(
        self,
        crucible_path: str,
        app_config: dict[str, Any] | None,
        registry: MetricRegistry,
    ) -> ConfigLoadResult:
        """Internal implementation of load_with_metadata without telemetry."""
        sources: list[ConfigSource] = []
        configs: list[dict[str, Any]] = []

        defaults = self._load_crucible_defaults(crucible_path, registry)
        sources.append(
            ConfigSource(
                layer="defaults",
                source=defaults.path if defaults else crucible_path,
                applied=bool(defaults),
            )
        )
        if defaults:
            configs.append(defaults.data)

        user_overrides = self._load_user_overrides(crucible_path, registry)
        sources.append(
            ConfigSource(
                layer="user",
                source=user_overrides.path
                if user_overrides
                else self._user_override_path(crucible_path),
                applied=bool(user_overrides),
            )
        )
        if user_overrides:
            configs.append(user_overrides.data)

        sources.append(
            ConfigSource(layer="application", source="runtime", applied=bool(app_config))
        )
        if app_config:
            configs.append(app_config)

        merged = merge_configs(*configs) if configs else {}
        return ConfigLoadResult(data=merged, sources=sources)

    # Internal helpers -----------------------------------------------------

    @dataclass(slots=True)
    class _LoadedLayer:
        data: dict[str, Any]
        path: Path

    def _parse_crucible_path(self, crucible_path: str) -> tuple[str, str, str] | None:
        parts = crucible_path.split("/")
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        if len(parts) == 2:
            category, name = parts
            versions = crucible.config.list_config_versions(category)
            version = versions[-1] if versions else "v1.0.0"
            return category, version, name
        return None

    def _load_crucible_defaults(
        self, crucible_path: str, registry: MetricRegistry
    ) -> _LoadedLayer | None:
        """Return defaults and source path if available."""
        parsed = self._parse_crucible_path(crucible_path)
        if not parsed:
            return None
        category, version, name = parsed
        try:
            config_path = crucible.config.get_config_path(category, version, name)
            data = crucible.config.load_config_defaults(category, version, name)
            return ConfigLoader._LoadedLayer(data=data or {}, path=config_path)
        except FileNotFoundError:
            return None
        except Exception:
            registry.counter("config_load_errors").inc()
            raise

    def _user_override_candidates(self, crucible_path: str) -> list[Path]:
        base = self.user_config_dir
        candidates = [
            base / f"{crucible_path}.yaml",
            base / f"{crucible_path}.yml",
            base / f"{crucible_path}.json",
            base / crucible_path,
        ]
        return candidates

    def _user_override_path(self, crucible_path: str) -> Path:
        return self.user_config_dir / f"{crucible_path}.yaml"

    def _load_user_overrides(
        self, crucible_path: str, registry: MetricRegistry
    ) -> _LoadedLayer | None:
        for candidate in self._user_override_candidates(crucible_path):
            if not candidate.exists():
                continue
            try:
                with open(candidate) as handle:
                    if candidate.suffix == ".json":
                        data = yaml.safe_load(handle)  # json safe via YAML parser
                    else:
                        data = yaml.safe_load(handle)
                if data is None:
                    data = {}
                return ConfigLoader._LoadedLayer(data=data, path=candidate)
            except yaml.YAMLError:
                registry.counter("config_load_errors").inc()
                continue
            except OSError:
                registry.counter("config_load_errors").inc()
                continue
        return None


__all__ = [
    "ConfigLoader",
    "ConfigLoadResult",
    "ConfigSource",
]
