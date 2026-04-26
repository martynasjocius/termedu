from __future__ import annotations

from pathlib import Path

import pytest

from termedu.cli import resolve_config
import termedu.config as config_module
from termedu.config import AppConfig, ConfigError, load_config


def test_load_config_defaults_when_file_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path / ".termedu")

    assert config == AppConfig()


def test_load_config_uses_home_directory_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text('name = "Home"\n', encoding="utf-8")
    monkeypatch.setattr(config_module.Path, "home", lambda: tmp_path)

    config = load_config()

    assert config == AppConfig(name="Home")


def test_load_config_reads_valid_toml(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text(
        'name = "Ada"\noperation = "multiplication"\nleft_max = 9\nright_max = 8\nfixed_left = 4\n',
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config == AppConfig(
        name="Ada",
        operation="multiplication",
        left_max=9,
        right_max=8,
        fixed_left=4,
    )


def test_load_config_rejects_invalid_toml(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text("name = \n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(config_path)


def test_cli_name_overrides_config(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text('name = "Config Name"\nfixed_right = 7\n', encoding="utf-8")

    config = resolve_config(["CLI Name"], config_path=config_path)

    assert config == AppConfig(name="CLI Name", fixed_right=7)


def test_load_config_rejects_negative_fixed_operand(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text("fixed_left = -1\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(config_path)
