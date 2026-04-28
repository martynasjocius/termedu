from __future__ import annotations

import importlib.machinery
import importlib.util
from decimal import Decimal
from io import StringIO
import os
from pathlib import Path
import random
import subprocess
import sys
from datetime import datetime

from termedu.cli import INTERRUPTED_MESSAGE, LessonInterrupted, main, run_lesson
from termedu.config import AppConfig
from termedu.logging_utils import LogWriteError
from termedu.session import HAPPY_KAOMOJI, SAD_KAOMOJI


class TtyStringIO(StringIO):
    def isatty(self) -> bool:
        return True


class InterruptingInputStream:
    def __init__(self, responses: list[str]) -> None:
        self._responses = iter(responses)

    def readline(self) -> str:
        response = next(self._responses)

        if response == "__interrupt__":
            raise KeyboardInterrupt

        return response


def load_wrapper_module():
    script_path = Path(__file__).resolve().parents[1] / "termedu"
    spec = importlib.util.spec_from_file_location(
        "termedu_wrapper",
        script_path,
        loader=importlib.machinery.SourceFileLoader("termedu_wrapper", str(script_path)),
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_lesson_uses_fixed_operands_and_finishes_after_twenty_four_correct_answers() -> None:
    config = AppConfig(fixed_left=4, fixed_right=3)
    input_stream = StringIO("12\n" * 20)
    output = StringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert transcript.count("4 x 3 = 12 Yes!\n") == 20
    assert "4 x 3 = 4 x 3 = 12 Yes!\n" not in transcript
    assert any(kaomoji in transcript for kaomoji in HAPPY_KAOMOJI)


def test_run_lesson_stops_after_configured_coin_target() -> None:
    config = AppConfig(
        fixed_left=4,
        fixed_right=3,
        coin_target=Decimal("0.15"),
    )
    input_stream = StringIO("12\n" * 20)
    output = StringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert transcript.count("4 x 3 = 12 Yes!\n") == 3


def test_run_lesson_prints_custom_greeting_and_feedback_messages() -> None:
    config = AppConfig(
        fixed_left=4,
        fixed_right=3,
        greeting_messages=("Ready?",),
        success_messages=("Nice work",),
        coin_target=Decimal("0.25"),
    )
    input_stream = StringIO("12\n" * 5)
    output = StringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert transcript.startswith("Ready?\n\n4 x 3 = ")
    assert any(f"Nice work {kaomoji}" in transcript for kaomoji in HAPPY_KAOMOJI)


def test_run_lesson_prints_correct_answer_for_incorrect_answers_and_continues() -> None:
    config = AppConfig(fixed_left=4, fixed_right=3)
    input_stream = StringIO("11\n11\n11\n" + ("12\n" * 26))
    output = StringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert "4 x 3 = 11 No... 12\n" in transcript
    assert "4 x 3 = 4 x 3 = 11 No... 12\n" not in transcript
    assert sum(transcript.count(kaomoji) for kaomoji in SAD_KAOMOJI) == 1
    assert transcript.endswith("4 x 3 = 12 Yes!\n")


def test_run_lesson_rewrites_the_previous_line_for_tty_output() -> None:
    config = AppConfig(fixed_left=4, fixed_right=3)
    input_stream = StringIO("12\n" * 20)
    output = TtyStringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert "\033[F\033[2K4 x 3 = 12 Yes!\n" in transcript


def test_run_lesson_rewrites_the_previous_line_for_tty_incorrect_answers() -> None:
    config = AppConfig(fixed_left=4, fixed_right=3)
    input_stream = StringIO("11\n" + ("12\n" * 22))
    output = TtyStringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert "\033[F\033[2K4 x 3 = 11 No... 12\n" in transcript


def test_run_lesson_normalizes_crlf_answers_before_rendering_verdict() -> None:
    config = AppConfig(fixed_left=4, fixed_right=3)
    input_stream = StringIO("12\r\n" * 20)
    output = StringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert "4 x 3 = 12\r Yes!\n" not in transcript
    assert transcript.count("4 x 3 = 12 Yes!\n") == 20


def test_run_lesson_repeats_blank_and_invalid_answers_without_scoring(tmp_path: Path) -> None:
    config = AppConfig(
        name="Ada",
        fixed_left=4,
        fixed_right=3,
        coin_target=Decimal("0.1"),
    )
    input_stream = StringIO("\nabc\n12\n12\n")
    output = StringIO()
    started_at = datetime(2026, 4, 26, 13, 14, 15)

    run_lesson(
        config,
        input_stream=input_stream,
        output=output,
        rng=random.Random(0),
        log_home_dir=tmp_path,
        started_at=started_at,
    )

    transcript = output.getvalue()
    log_path = tmp_path / "termedu-Ada-20260426T131415.txt"
    log_lines = log_path.read_text(encoding="utf-8").splitlines()

    assert transcript.count("4 x 3 = ") == 4
    assert transcript.count("12 Yes!\n") == 2
    assert "No..." not in transcript
    assert log_lines.count("4 x 3 = 12 Yes!") == 2
    assert not any("abc" in line for line in log_lines)
    assert not any("No..." in line for line in log_lines)
    assert "earned_coins: 0.1" in log_lines
    assert "total_correct: 2" in log_lines


def test_run_lesson_retries_the_same_ranged_question_after_invalid_answers(tmp_path: Path) -> None:
    config = AppConfig(
        name="Ada",
        left_max=9,
        right_max=9,
        coin_target=Decimal("0.05"),
    )
    input_stream = StringIO("\nabc\n36\n")
    output = StringIO()
    started_at = datetime(2026, 4, 26, 13, 14, 15)

    run_lesson(
        config,
        input_stream=input_stream,
        output=output,
        rng=random.Random(0),
        log_home_dir=tmp_path,
        started_at=started_at,
    )

    transcript = output.getvalue()
    log_path = tmp_path / "termedu-Ada-20260426T131415.txt"
    log_lines = log_path.read_text(encoding="utf-8").splitlines()

    assert transcript == "6 x 6 = 6 x 6 = 6 x 6 = 36 Yes!\n"
    assert log_lines.count("6 x 6 = 36 Yes!") == 1
    assert not any("abc" in line for line in log_lines)
    assert "earned_coins: 0.05" in log_lines
    assert "total_correct: 1" in log_lines


def test_run_lesson_writes_correct_answer_for_incorrect_answers_to_session_log(tmp_path: Path) -> None:
    config = AppConfig(name="Ada", fixed_left=4, fixed_right=3)
    input_stream = StringIO("11\n" + ("12\n" * 23))
    output = StringIO()
    started_at = datetime(2026, 4, 26, 13, 14, 15)

    run_lesson(
        config,
        input_stream=input_stream,
        output=output,
        rng=random.Random(0),
        log_home_dir=tmp_path,
        started_at=started_at,
    )

    log_path = tmp_path / "termedu-Ada-20260426T131415.txt"
    log_lines = log_path.read_text(encoding="utf-8").splitlines()

    assert "4 x 3 = 11 No... 12" in log_lines
    assert "earned_coins: 1.0" in log_lines
    assert "total_correct: 22" in log_lines


def test_run_lesson_writes_session_log_in_home_directory(tmp_path: Path) -> None:
    config = AppConfig(name="Ada / Babbage", fixed_left=4, fixed_right=3)
    input_stream = StringIO("12\n" * 20)
    output = StringIO()
    started_at = datetime(2026, 4, 26, 13, 14, 15)

    run_lesson(
        config,
        input_stream=input_stream,
        output=output,
        rng=random.Random(0),
        log_home_dir=tmp_path,
        started_at=started_at,
    )

    log_path = tmp_path / "termedu-Ada-Babbage-20260426T131415.txt"

    assert log_path.exists()
    assert (
        log_path.read_text(encoding="utf-8").splitlines()[:2]
        == ["learner: Ada-Babbage", "started_at: 2026-04-26T13:14:15"]
    )


def test_run_lesson_interrupts_cleanly_and_persists_partial_log(tmp_path: Path) -> None:
    config = AppConfig(name="Ada", fixed_left=4, fixed_right=3)
    input_stream = InterruptingInputStream(["12\n", "__interrupt__"])
    output = StringIO()
    started_at = datetime(2026, 4, 26, 13, 14, 15)

    try:
        run_lesson(
            config,
            input_stream=input_stream,
            output=output,
            rng=random.Random(0),
            log_home_dir=tmp_path,
            started_at=started_at,
        )
    except LessonInterrupted as exc:
        assert str(exc) == INTERRUPTED_MESSAGE
    else:
        raise AssertionError("run_lesson should raise LessonInterrupted on ctrl-c")

    transcript = output.getvalue()
    log_path = tmp_path / "termedu-Ada-20260426T131415.txt"

    assert transcript.endswith("\nLesson interrupted.\n")
    assert log_path.exists()

    log_lines = log_path.read_text(encoding="utf-8").splitlines()

    assert "4 x 3 = 12 Yes!" in log_lines
    assert INTERRUPTED_MESSAGE in log_lines
    assert "earned_coins: 0.05" in log_lines
    assert "total_correct: 1" in log_lines


def test_main_reports_log_write_failures(monkeypatch) -> None:
    def fake_run_lesson(config: AppConfig) -> None:
        raise LogWriteError("Could not write session log at /tmp/example.log: disk full")

    monkeypatch.setattr("termedu.cli.run_lesson", fake_run_lesson)

    stderr = StringIO()
    stdout = StringIO()
    original_stderr = sys.stderr
    original_stdout = sys.stdout

    try:
        sys.stderr = stderr
        sys.stdout = stdout
        exit_code = main([])
    finally:
        sys.stderr = original_stderr
        sys.stdout = original_stdout

    assert exit_code == 1
    assert "Could not write session log at /tmp/example.log: disk full" in stderr.getvalue()


def test_main_returns_130_for_keyboard_interrupt(monkeypatch) -> None:
    def fake_run_lesson(config: AppConfig) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("termedu.cli.run_lesson", fake_run_lesson)

    stderr = StringIO()
    stdout = StringIO()
    original_stderr = sys.stderr
    original_stdout = sys.stdout

    try:
        sys.stderr = stderr
        sys.stdout = stdout
        exit_code = main([])
    finally:
        sys.stderr = original_stderr
        sys.stdout = original_stdout

    assert exit_code == 130
    assert stderr.getvalue() == "Lesson interrupted.\n"


def test_repo_root_wrapper_delegates_argv_to_packaged_main(monkeypatch) -> None:
    wrapper = load_wrapper_module()
    observed: list[str] = []

    def fake_packaged_main(argv):
        observed.extend(argv)
        return 17

    monkeypatch.setattr(wrapper, "packaged_main", fake_packaged_main)

    assert wrapper.main(["Alice"]) == 17
    assert observed == ["Alice"]


def test_repo_root_wrapper_runs_from_outside_repo(tmp_path) -> None:
    script_path = Path(__file__).resolve().parents[1] / "termedu"

    result = subprocess.run(
        [str(script_path), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )

    assert result.returncode == 0
    assert "Run a termedu session." in result.stdout
