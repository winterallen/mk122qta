from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import yaml

from mk_common.errors import ConfigurationError


def load_env_value(name: str, *, required: bool = False, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if required and not value:
        raise ConfigurationError(f"Required environment variable is missing: {name}")
    return value


def load_yaml_config(*paths: Path) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for path in paths:
        if not path.exists():
            continue

        with path.open("r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file) or {}

        if not isinstance(loaded, Mapping):
            raise ConfigurationError(f"Config file must contain a mapping: {path}")

        merged = deep_merge(merged, dict(loaded))

    return cast(dict[str, Any], resolve_env_refs(merged))


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = deep_merge(dict(result[key]), dict(value))
        else:
            result[key] = value
    return result


def resolve_env_refs(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        name = value[2:-1]
        return load_env_value(name, required=True)
    if isinstance(value, Mapping):
        return {key: resolve_env_refs(item) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_env_refs(item) for item in value]
    return value
