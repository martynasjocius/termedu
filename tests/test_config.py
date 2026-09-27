from __future__ import annotations

from decimal import Decimal
from dataclasses import fields
from pathlib import Path
import tomllib

import pytest

from termedu.cli import resolve_config
import termedu.config as config_module
from termedu.config import AppConfig, ConfigError, load_config


def test_load_config_defaults_when_file_missing(tmp_path: Path) -> None:
    path = tmp_path / ".termedu"
    config = load_config(path)

    assert config == AppConfig()
    assert path.read_text(encoding="utf-8") == config_module.INITIAL_CONFIG
    assert load_config(path) == AppConfig()


def test_load_config_reads_operand_minima(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('left_min = 2\nright_min = 3\n', encoding="utf-8")
    config = load_config(path)
    assert config.left_min == 2
    assert config.right_min == 3


@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize("value", ["-1", "true", "1.5", '"2"'])
def test_load_config_rejects_invalid_minima(tmp_path: Path, side: str, value: str) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f'{side}_min = {value}\n', encoding="utf-8")
    with pytest.raises(ConfigError, match=f"{side}_min must be a non-negative integer"):
        load_config(path)


@pytest.mark.parametrize("side", ["left", "right"])
def test_load_config_rejects_reversed_range(tmp_path: Path, side: str) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f'{side}_min = 5\n{side}_max = 4\n', encoding="utf-8")
    with pytest.raises(ConfigError, match=f"{side}_min must be <= {side}_max"):
        load_config(path)


def test_initial_config_documents_all_settings(tmp_path: Path) -> None:
    # Uncomment the optional examples to verify they are complete and usable.
    uncommented = "\n".join(
        line[2:] if line.startswith("# ") else line
        for line in config_module.INITIAL_CONFIG.splitlines()
        if not line.startswith("# missing_symbol = ")
        and (not line.startswith("# ") or " = " in line or line in (
            '# Great work today!', '# You reached your coin target.', '# """',
        ))
    )
    raw = tomllib.loads(uncommented)
    assert set(raw) == {field.name for field in fields(AppConfig)}
    path = tmp_path / ".termedu"
    path.write_text(uncommented, encoding="utf-8")
    assert load_config(path).name == "Mia"


def test_load_config_preserves_existing_file(tmp_path: Path) -> None:
    path = tmp_path / ".termedu"
    original = '# My settings\nquestion_mode = "mixed"\n'
    path.write_text(original, encoding="utf-8")
    assert load_config(path).question_mode == "mixed"
    assert path.read_text(encoding="utf-8") == original


def test_load_config_creates_default_home_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config_module.Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert load_config() == AppConfig()
    assert (tmp_path / ".config" / "termedu" / "config.toml").is_file()


def test_load_config_uses_xdg_config_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "settings"))
    assert load_config() == AppConfig()
    assert (tmp_path / "settings" / "termedu" / "config.toml").is_file()


@pytest.mark.parametrize("value", ["", "relative/path"])
def test_default_config_path_ignores_invalid_xdg_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", value)
    monkeypatch.setattr(config_module.Path, "home", lambda: tmp_path)
    assert config_module.default_config_path() == tmp_path / ".config" / "termedu" / "config.toml"


def test_load_config_reports_creation_failure(tmp_path: Path) -> None:
    path = tmp_path / "missing-directory" / ".termedu"
    with pytest.raises(ConfigError, match="Could not create config file"):
        load_config(path)


@pytest.mark.parametrize("mode", ["result", "missing_operand", "mixed"])
def test_load_config_question_modes(tmp_path: Path, mode: str) -> None:
    path = tmp_path / ".termedu"
    path.write_text(f'question_mode = "{mode}"\n', encoding="utf-8")
    assert load_config(path).question_mode == mode


def test_load_config_custom_missing_symbol(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('missing_symbol = "□"\n', encoding="utf-8")
    assert load_config(path).missing_symbol == "□"


@pytest.mark.parametrize("value", ['""', '"   "', '42', 'true'])
def test_load_config_rejects_invalid_missing_symbol(tmp_path: Path, value: str) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f'missing_symbol = {value}\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="missing_symbol"):
        load_config(path)


@pytest.mark.parametrize("value", ['"unknown"', '""', '42', 'true'])
def test_load_config_rejects_invalid_question_modes(tmp_path: Path, value: str) -> None:
    path = tmp_path / ".termedu"
    path.write_text(f'question_mode = {value}\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="question_mode"):
        load_config(path)


def test_load_config_uses_home_directory_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / ".config" / "termedu" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text('name = "Home"\n', encoding="utf-8")
    monkeypatch.setattr(config_module.Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    config = load_config()

    assert config == AppConfig(name="Home")


def test_load_config_reads_valid_toml(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text(
        'name = "Ada"\noperation = "multiplication"\nleft_max = 9\nright_max = 8\nmax_numbers = 4\ncoin_target = 1.5\ncorrect_reward = 0.25\nwrong_penalty = 0.2\nfixed_left = 4\nyes_message = "Ja!"\nno_message = "Nee..."\ngreeting_messages = ["Ready?", "Begin"]\nsuccess_messages = ["Nice", "Good"]\nfailure_messages = ["Try again"]\nfinal_success_message = """\nDone for today!\nYou earned your coin target.\n"""\n',
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config == AppConfig(
        name="Ada",
        operation="multiplication",
        left_max=9,
        right_max=8,
        max_numbers=4,
        coin_target=Decimal("1.5"),
        correct_reward=Decimal("0.25"),
        wrong_penalty=Decimal("0.2"),
        fixed_left=4,
        yes_message="Ja!",
        no_message="Nee...",
        greeting_messages=("Ready?", "Begin"),
        success_messages=("Nice", "Good"),
        failure_messages=("Try again",),
        final_success_message="Done for today!\nYou earned your coin target.",
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


def test_load_config_accepts_addition_operation(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text('operation = "addition"\n', encoding="utf-8")

    config = load_config(config_path)

    assert config.operation == "addition"


def test_load_config_accepts_mixed_operation(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text('operation = "mixed"\n', encoding="utf-8")

    config = load_config(config_path)

    assert config.operation == "mixed"


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


def test_load_config_rejects_too_small_max_numbers(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text("max_numbers = 1\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="max_numbers must be an integer of at least 2"):
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


def test_load_config_rejects_empty_message_options(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text('success_messages = ["  "]\n', encoding="utf-8")

    with pytest.raises(ConfigError, match="success_messages must include at least one non-empty string"):
        load_config(config_path)


@pytest.mark.parametrize("key", ["yes_message", "no_message"])
def test_load_config_rejects_empty_yes_or_no_messages(tmp_path: Path, key: str) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text(f'{key} = "  "\n', encoding="utf-8")

    with pytest.raises(ConfigError, match=f"{key} must be a non-empty string"):
        load_config(config_path)


def test_load_config_rejects_empty_final_success_message(tmp_path: Path) -> None:
    config_path = tmp_path / ".termedu"
    config_path.write_text('final_success_message = "  "\n', encoding="utf-8")

    with pytest.raises(ConfigError, match="final_success_message must be a non-empty string"):
        load_config(config_path)
