from __future__ import annotations

from decimal import Decimal
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
        'name = "Ada"\noperation = "multiplication"\nleft_max = 9\nright_max = 8\ncoin_target = 1.5\ncorrect_reward = 0.25\nwrong_penalty = 0.2\nfixed_left = 4\n',
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config == AppConfig(
        name="Ada",
        operation="multiplication",
        left_max=9,
        right_max=8,
        coin_target=Decimal("1.5"),
        correct_reward=Decimal("0.25"),
        wrong_penalty=Decimal("0.2"),
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


def test_load_config_rejects_non_positive_coin_target(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text("coin_target = 0\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="coin_target must be a positive number"):
        load_config(config_path)


def test_load_config_rejects_non_positive_correct_reward(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text("correct_reward = -0.5\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="correct_reward must be a positive number"):
        load_config(config_path)


def test_load_config_rejects_non_positive_wrong_penalty(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text("wrong_penalty = 0\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="wrong_penalty must be a positive number"):
        load_config(config_path)


def test_load_config_rejects_deprecated_session_target(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text("session_target = 24\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="session_target is deprecated; use coin_target instead"):
        load_config(config_path)
