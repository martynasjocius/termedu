from __future__ import annotations

from io import StringIO
import random

from termedu.cli import run_lesson
from termedu.config import AppConfig


class TtyStringIO(StringIO):
    def isatty(self) -> bool:
        return True


def test_run_lesson_uses_fixed_operands_and_finishes_after_twenty_four_correct_answers() -> None:
    config = AppConfig(fixed_left=4, fixed_right=3)
    input_stream = StringIO("12\n" * 24)
    output = StringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert transcript.count("4 x 3 = 12 YES\n") == 24
    assert "(^_^)" in transcript


def test_run_lesson_prints_no_for_incorrect_answers_and_continues() -> None:
    config = AppConfig(fixed_left=4, fixed_right=3)
    input_stream = StringIO("11\n11\n11\n" + ("12\n" * 24))
    output = StringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert "4 x 3 = 11 NO\n" in transcript
    assert transcript.count("(T_T)") == 1
    assert transcript.endswith("4 x 3 = 12 YES\n")


def test_run_lesson_rewrites_the_previous_line_for_tty_output() -> None:
    config = AppConfig(fixed_left=4, fixed_right=3)
    input_stream = StringIO("12\n" * 24)
    output = TtyStringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert "\033[F\033[2K4 x 3 = 12 YES\n" in transcript


def test_run_lesson_normalizes_crlf_answers_before_rendering_verdict() -> None:
    config = AppConfig(fixed_left=4, fixed_right=3)
    input_stream = StringIO("12\r\n" * 24)
    output = StringIO()

    run_lesson(config, input_stream=input_stream, output=output, rng=random.Random(0))

    transcript = output.getvalue()

    assert "4 x 3 = 12\r YES\n" not in transcript
    assert transcript.count("4 x 3 = 12 YES\n") == 24
