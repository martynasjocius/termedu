from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


class ConfigError(Exception):
    """Raised when user config cannot be loaded."""


@dataclass(frozen=True)
class AppConfig:
    name: str | None = None
    operation: str = "multiplication"
    left_max: int = 12
    right_max: int = 12
    fixed_left: int | None = None
    fixed_right: int | None = None


def default_config_path() -> Path:
    return Path.home() / ".termedu"


def _read_optional_string(raw: dict[str, object], key: str, config_path: Path) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigError(f"Invalid config file at {config_path}: {key} must be a string.")
    return value


def _read_required_non_negative_int(
    raw: dict[str, object],
    key: str,
    config_path: Path,
    *,
    default: int,
) -> int:
    value = raw.get(key, default)
    if not isinstance(value, int) or value < 0:
        raise ConfigError(
            f"Invalid config file at {config_path}: {key} must be a non-negative integer."
        )
    return value


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
        return AppConfig()

    try:
        raw = tomllib.loads(resolved_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid config file at {resolved_path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Could not read config file at {resolved_path}: {exc}") from exc

    name = _read_optional_string(raw, "name", resolved_path)
    operation = _read_optional_string(raw, "operation", resolved_path) or "multiplication"
    left_max = _read_required_non_negative_int(raw, "left_max", resolved_path, default=12)
    right_max = _read_required_non_negative_int(raw, "right_max", resolved_path, default=12)
    fixed_left = _read_optional_non_negative_int(raw, "fixed_left", resolved_path)
    fixed_right = _read_optional_non_negative_int(raw, "fixed_right", resolved_path)

    if operation != "multiplication":
        raise ConfigError(
            f"Invalid config file at {resolved_path}: operation must be 'multiplication'."
        )

    return AppConfig(
        name=name,
        operation=operation,
        left_max=left_max,
        right_max=right_max,
        fixed_left=fixed_left,
        fixed_right=fixed_right,
    )
