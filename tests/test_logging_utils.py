from __future__ import annotations

from datetime import datetime
from pathlib import Path

from termedu.logging_utils import build_session_log_path, sanitize_learner_name


def test_sanitize_learner_name_replaces_unsafe_characters() -> None:
    assert sanitize_learner_name("Ada Lovelace / Group #1") == "Ada-Lovelace-Group-1"


def test_sanitize_learner_name_uses_anonymous_for_blank_values() -> None:
    assert sanitize_learner_name("   ") == "anonymous"
    assert sanitize_learner_name(None) == "anonymous"


def test_build_session_log_path_uses_home_directory_and_safe_timestamp(tmp_path: Path) -> None:
    started_at = datetime(2026, 4, 26, 13, 14, 15)

    log_path = build_session_log_path("Ada / Babbage", started_at, home_dir=tmp_path)

    assert log_path == tmp_path / "termedu-Ada-Babbage-20260426T131415.txt"
