from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re


LOG_FILENAME_PREFIX = "termedu"
ANONYMOUS_LEARNER = "anonymous"
_INVALID_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


class LogWriteError(Exception):
    """Raised when a session log cannot be written."""


def sanitize_learner_name(name: str | None) -> str:
    if name is None:
        return ANONYMOUS_LEARNER

    sanitized = _INVALID_FILENAME_CHARS.sub("-", name.strip()).strip("._-")

    if not sanitized:
        return ANONYMOUS_LEARNER

    return sanitized


def build_session_log_path(
    learner_name: str | None,
    started_at: datetime,
    *,
    home_dir: Path | None = None,
) -> Path:
    base_dir = home_dir or Path.home()
    safe_name = sanitize_learner_name(learner_name)
    timestamp = started_at.strftime("%Y%m%dT%H%M%S")

    return base_dir / f"{LOG_FILENAME_PREFIX}-{safe_name}-{timestamp}.txt"


def render_session_log(
    learner_name: str | None,
    started_at: datetime,
    transcript_lines: list[str],
) -> str:
    safe_name = sanitize_learner_name(learner_name)
    header_lines = [
        f"learner: {safe_name}",
        f"started_at: {started_at.isoformat(timespec='seconds')}",
        "",
    ]

    return "\n".join(header_lines + transcript_lines) + "\n"


def write_session_log(path: Path, content: str) -> None:
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise LogWriteError(f"Could not write session log at {path}: {exc}") from exc
