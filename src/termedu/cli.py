from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from pathlib import Path
import random
import sys

from termedu.config import AppConfig, ConfigError, load_config
from termedu.lesson import generate_question, is_correct_answer
from termedu.logging_utils import (
    LogWriteError,
    build_session_log_path,
    render_session_log,
    write_session_log,
)
from termedu.session import SESSION_TARGET, SessionState

CORRECT_VERDICT = "YES"
INCORRECT_VERDICT = "NO"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="termedu", description="Run a termedu session.")
    parser.add_argument("name", nargs="?", help="Learner name.")
    return parser


def resolve_config(argv: Sequence[str] | None = None, *, config_path: Path | None = None) -> AppConfig:
    args = build_parser().parse_args(argv)
    config = load_config(config_path)

    if args.name:
        return replace(config, name=args.name)

    return config


def _supports_tty(stream: object) -> bool:
    return bool(getattr(stream, "isatty", lambda: False)())


def _write_answer_line(output: object, prompt: str, answer_text: str, verdict: str) -> None:
    if _supports_tty(output):
        output.write("\033[F")
        output.write("\033[2K")

    output.write(f"{prompt}{answer_text} {verdict}\n")


def _normalize_answer_text(raw_answer: str) -> str:
    return raw_answer.rstrip("\r\n")


def run_lesson(
    config: AppConfig,
    *,
    input_stream: object = sys.stdin,
    output: object = sys.stdout,
    rng: random.Random | None = None,
    log_home_dir: Path | None = None,
    started_at: datetime | None = None,
) -> None:
    lesson_rng = rng or random.Random()
    session = SessionState()
    session_started_at = started_at or datetime.now()
    transcript_lines: list[str] = []

    while session.total_correct < SESSION_TARGET:
        question = generate_question(config, lesson_rng)
        output.write(question.prompt)
        output.flush()

        raw_answer = input_stream.readline()
        if raw_answer == "":
            raise EOFError("Input ended before the lesson completed.")

        answer_text = _normalize_answer_text(raw_answer)
        outcome = session.record_answer(is_correct_answer(question, answer_text))
        verdict = CORRECT_VERDICT if outcome.is_correct else INCORRECT_VERDICT

        _write_answer_line(output, question.prompt, answer_text, verdict)
        transcript_lines.append(f"{question.prompt}{answer_text} {verdict}")

        if outcome.feedback:
            output.write(f"\n{outcome.feedback}\n\n")
            transcript_lines.extend(["", outcome.feedback, ""])

        output.flush()

    log_path = build_session_log_path(config.name, session_started_at, home_dir=log_home_dir)
    log_content = render_session_log(config.name, session_started_at, transcript_lines)

    write_session_log(log_path, log_content)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        config = resolve_config(argv)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        run_lesson(config)
    except (EOFError, LogWriteError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
