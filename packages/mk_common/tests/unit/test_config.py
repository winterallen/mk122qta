from __future__ import annotations

from pathlib import Path

from mk_common.config import deep_merge, load_env_value, load_yaml_config
from mk_common.errors import ConfigurationError


def test_deep_merge_overrides_nested_values() -> None:
    result = deep_merge(
        {"app": {"name": "mk122", "env": "base"}, "debug": False},
        {"app": {"env": "dev"}},
    )

    assert result == {"app": {"name": "mk122", "env": "dev"}, "debug": False}


def test_load_yaml_config_resolves_env_refs(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setenv("MK122_TEST_TOKEN", "secret")  # type: ignore[attr-defined]
    config_path = tmp_path / "config.yaml"
    config_path.write_text("token: ${MK122_TEST_TOKEN}\n", encoding="utf-8")

    assert load_yaml_config(config_path) == {"token": "secret"}


def test_load_env_value_raises_for_missing_required_value() -> None:
    try:
        load_env_value("MK122_MISSING_TEST_VALUE", required=True)
    except ConfigurationError as exc:
        assert exc.code == "mk122.configuration_error"
    else:
        raise AssertionError("missing required env value should raise")
