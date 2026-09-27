from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import os
from pathlib import Path
import tomllib


INITIAL_CONFIG = '''# termedu settings (TOML). Edit this file before your next session.
# Lines starting with # are comments; remove # to enable an optional setting.

# Operation: "multiplication", "addition", or "mixed".
operation = "multiplication"
# Question style: "result", "missing_operand", or "mixed" (both styles).
question_mode = "result"
# Symbol marking the missing operand, for example "?" or "□".
missing_symbol = "_"
# Alternative missing-operand symbols (uncomment one, replacing the value above):
# missing_symbol = "?"
# missing_symbol = "□"
# missing_symbol = "…"
# missing_symbol = "[ ]"

# Random operand ranges, inclusive. Each minimum must be <= its maximum.
left_min = 0
left_max = 12
right_min = 0
right_max = 12
# Maximum numbers per mixed-operation expression (at least 2).
max_numbers = 3

# Finish when earned coins reach the target. All amounts must be positive.
coin_target = 1.0
correct_reward = 0.05
wrong_penalty = 0.1

# Feedback after each answer. %a is replaced with the correct answer.
yes_message = "Yes!"
no_message = "No... %a"

# Optional learner name (a name on the command line overrides this).
# name = "Mia"

# Optional fixed operands, replacing the corresponding random range.
# fixed_left = 4
# fixed_right = 7

# Optional messages. Each list must contain at least one non-empty string.
# greeting_messages = ["Ready?", "Let's practice!"]
# success_messages = ["Nice work", "You got it"]
# failure_messages = ["Try again", "Keep thinking"]

# Optional message after reaching the coin target; multiline strings work too.
# final_success_message = """
# Great work today!
# You reached your coin target.
# """
'''


class ConfigError(Exception):
    """Raised when user config cannot be loaded."""


@dataclass(frozen=True)
class AppConfig:
    name: str | None = None
    operation: str = "multiplication"
    question_mode: str = "result"
    missing_symbol: str = "_"
    left_min: int = 0
    left_max: int = 12
    right_min: int = 0
    right_max: int = 12
    max_numbers: int = 3
    coin_target: Decimal = Decimal("1.0")
    correct_reward: Decimal = Decimal("0.05")
    wrong_penalty: Decimal = Decimal("0.1")
    fixed_left: int | None = None
    fixed_right: int | None = None
    yes_message: str = "Yes!"
    no_message: str = "No... %a"
    greeting_messages: tuple[str, ...] = ()
    success_messages: tuple[str, ...] = ()
    failure_messages: tuple[str, ...] = ()
    final_success_message: str | None = None


def default_config_path() -> Path:
    configured_home = os.environ.get("XDG_CONFIG_HOME", "")
    config_home = Path(configured_home)
    if not configured_home or not config_home.is_absolute():
        config_home = Path.home() / ".config"
    return config_home / "termedu" / "config.toml"


def _read_optional_string(raw: dict[str, object], key: str, config_path: Path) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigError(f"Invalid config file at {config_path}: {key} must be a string.")
    return value


def _read_required_non_empty_string(
    raw: dict[str, object],
    key: str,
    config_path: Path,
    *,
    default: str,
) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str):
        raise ConfigError(f"Invalid config file at {config_path}: {key} must be a string.")

    stripped_value = value.strip()
    if not stripped_value:
        raise ConfigError(
            f"Invalid config file at {config_path}: {key} must be a non-empty string."
        )

    return stripped_value


def _read_optional_non_empty_string(
    raw: dict[str, object], key: str, config_path: Path
) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigError(f"Invalid config file at {config_path}: {key} must be a string.")

    stripped_value = value.strip()
    if not stripped_value:
        raise ConfigError(
            f"Invalid config file at {config_path}: {key} must be a non-empty string."
        )

    return stripped_value


def _read_optional_string_options(
    raw: dict[str, object], key: str, config_path: Path
) -> tuple[str, ...]:
    value = raw.get(key)
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(option, str) for option in value):
        raise ConfigError(f"Invalid config file at {config_path}: {key} must be an array of strings.")

    options = tuple(option.strip() for option in value if option.strip())
    if not options:
        raise ConfigError(
            f"Invalid config file at {config_path}: {key} must include at least one non-empty string."
        )

    return options


def _read_required_non_negative_int(
    raw: dict[str, object],
    key: str,
    config_path: Path,
    *,
    default: int,
) -> int:
    value = raw.get(key, default)
    if type(value) is not int or value < 0:
        raise ConfigError(
            f"Invalid config file at {config_path}: {key} must be a non-negative integer."
        )
    return value


def _read_required_positive_int(
    raw: dict[str, object],
    key: str,
    config_path: Path,
    *,
    default: int,
) -> int:
    value = raw.get(key, default)
    if type(value) is not int or value <= 0:
        raise ConfigError(
            f"Invalid config file at {config_path}: {key} must be a positive integer."
        )
    return value


def _read_required_min_int(
    raw: dict[str, object],
    key: str,
    config_path: Path,
    *,
    default: int,
    minimum: int,
) -> int:
    value = raw.get(key, default)
    if type(value) is not int or value < minimum:
        raise ConfigError(
            f"Invalid config file at {config_path}: {key} must be an integer of at least {minimum}."
        )
    return value


def _read_required_positive_decimal(
    raw: dict[str, object],
    key: str,
    config_path: Path,
    *,
    default: Decimal,
) -> Decimal:
    value = raw.get(key, default)
    if type(value) not in (int, float, Decimal) or value <= 0:
        raise ConfigError(
            f"Invalid config file at {config_path}: {key} must be a positive number."
        )
    return Decimal(str(value))


def _read_optional_non_negative_int(
    raw: dict[str, object], key: str, config_path: Path
) -> int | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or value < 0:
        raise ConfigError(
            f"Invalid config file at {config_path}: {key} must be a non-negative integer."
        )
    return value


def load_config(config_path: Path | None = None) -> AppConfig:
    resolved_path = config_path or default_config_path()

    if not resolved_path.exists():
        try:
            if config_path is None:
                resolved_path.parent.mkdir(parents=True, exist_ok=True)
            with resolved_path.open("x", encoding="utf-8") as config_file:
                config_file.write(INITIAL_CONFIG)
        except FileExistsError:
            # Another process created it; read its settings without overwriting them.
            pass
        except OSError as exc:
            raise ConfigError(f"Could not create config file at {resolved_path}: {exc}") from exc

    try:
        raw = tomllib.loads(resolved_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid config file at {resolved_path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Could not read config file at {resolved_path}: {exc}") from exc

    if "session_target" in raw:
        raise ConfigError(
            f"Invalid config file at {resolved_path}: session_target is deprecated; use coin_target instead."
        )

    name = _read_optional_string(raw, "name", resolved_path)
    operation = _read_optional_string(raw, "operation", resolved_path) or "multiplication"
    question_mode = _read_required_non_empty_string(
        raw, "question_mode", resolved_path, default="result"
    )
    missing_symbol = _read_required_non_empty_string(
        raw, "missing_symbol", resolved_path, default="_"
    )
    if question_mode not in ("result", "missing_operand", "mixed"):
        raise ConfigError(
            f"Invalid config file at {resolved_path}: question_mode must be 'result', 'missing_operand', or 'mixed'."
        )
    left_min = _read_required_non_negative_int(raw, "left_min", resolved_path, default=0)
    right_min = _read_required_non_negative_int(raw, "right_min", resolved_path, default=0)
    left_max = _read_required_non_negative_int(raw, "left_max", resolved_path, default=12)
    right_max = _read_required_non_negative_int(raw, "right_max", resolved_path, default=12)
    for side, minimum, maximum in (
        ("left", left_min, left_max), ("right", right_min, right_max),
    ):
        if minimum > maximum:
            raise ConfigError(
                f"Invalid config file at {resolved_path}: {side}_min must be <= {side}_max."
            )
    max_numbers = _read_required_min_int(
        raw, "max_numbers", resolved_path, default=3, minimum=2
    )
    coin_target = _read_required_positive_decimal(
        raw,
        "coin_target",
        resolved_path,
        default=Decimal("1.0"),
    )
    correct_reward = _read_required_positive_decimal(
        raw,
        "correct_reward",
        resolved_path,
        default=Decimal("0.05"),
    )
    wrong_penalty = _read_required_positive_decimal(
        raw,
        "wrong_penalty",
        resolved_path,
        default=Decimal("0.1"),
    )
    fixed_left = _read_optional_non_negative_int(raw, "fixed_left", resolved_path)
    fixed_right = _read_optional_non_negative_int(raw, "fixed_right", resolved_path)
    yes_message = _read_required_non_empty_string(
        raw,
        "yes_message",
        resolved_path,
        default="Yes!",
    )
    no_message = _read_required_non_empty_string(
        raw,
        "no_message",
        resolved_path,
        default="No... %a",
    )
    greeting_messages = _read_optional_string_options(raw, "greeting_messages", resolved_path)
    success_messages = _read_optional_string_options(raw, "success_messages", resolved_path)
    failure_messages = _read_optional_string_options(raw, "failure_messages", resolved_path)
    final_success_message = _read_optional_non_empty_string(
        raw, "final_success_message", resolved_path
    )

    if operation not in ("multiplication", "addition", "mixed"):
        raise ConfigError(
            f"Invalid config file at {resolved_path}: operation must be 'multiplication', 'addition', or 'mixed'."
        )

    return AppConfig(
        name=name,
        operation=operation,
        question_mode=question_mode,
        missing_symbol=missing_symbol,
        left_min=left_min,
        left_max=left_max,
        right_min=right_min,
        right_max=right_max,
        max_numbers=max_numbers,
        coin_target=coin_target,
        correct_reward=correct_reward,
        wrong_penalty=wrong_penalty,
        fixed_left=fixed_left,
        fixed_right=fixed_right,
        yes_message=yes_message,
        no_message=no_message,
        greeting_messages=greeting_messages,
        success_messages=success_messages,
        failure_messages=failure_messages,
        final_success_message=final_success_message,
    )
