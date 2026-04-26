from __future__ import annotations

import importlib.machinery
import importlib.util
from io import StringIO
import os
from pathlib import Path
import random
import subprocess
import sys

from termedu.cli import run_lesson
from termedu.config import AppConfig


class TtyStringIO(StringIO):
    def isatty(self) -> bool:
        return True


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
