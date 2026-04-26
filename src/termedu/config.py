from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


class ConfigError(Exception):
    """Raised when user config cannot be loaded."""


@dataclass(frozen=True)
class AppConfig:
    name: str | None = None


def default_config_path() -> Path:
    return Path.home() / ".termedu"


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

    name = raw.get("name")
    if name is not None and not isinstance(name, str):
        raise ConfigError(
            f"Invalid config file at {resolved_path}: name must be a string."
        )

    return AppConfig(name=name)
