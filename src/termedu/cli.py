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
from termedu.session import SessionState

CORRECT_VERDICT = "Yes!"
INCORRECT_VERDICT = "No..."
INTERRUPTED_MESSAGE = "Lesson interrupted."


class LessonInterrupted(Exception):
    """Raised when the lesson stops early after a keyboard interrupt."""


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
        return

    output.write(f"{answer_text} {verdict}\n")


def _normalize_answer_text(raw_answer: str) -> str:
    return raw_answer.rstrip("\r\n")


def _is_valid_answer_text(answer_text: str) -> bool:
    try:
        int(answer_text.strip())
    except ValueError:
        return False

    return True


def _build_verdict(is_correct: bool, correct_answer: int) -> str:
    if is_correct:
        return CORRECT_VERDICT

    return f"{INCORRECT_VERDICT} {correct_answer}"


def _write_session_log(
    config: AppConfig,
    session_started_at: datetime,
    transcript_lines: list[str],
    session: SessionState,
    *,
    log_home_dir: Path | None,
) -> None:
    log_path = build_session_log_path(config.name, session_started_at, home_dir=log_home_dir)
    log_content = render_session_log(
        config.name,
        session_started_at,
        transcript_lines,
        earned_coins=session.earned_coins,
        total_correct=session.total_correct,
    )

    write_session_log(log_path, log_content)


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
    session = SessionState(
        coin_target=config.coin_target,
        correct_reward=config.correct_reward,
        wrong_penalty=config.wrong_penalty,
        success_messages=config.success_messages,
        failure_messages=config.failure_messages,
    )
    session_started_at = started_at or datetime.now()
    transcript_lines: list[str] = []
    question = generate_question(config, lesson_rng)

    if config.greeting_messages:
        greeting = lesson_rng.choice(config.greeting_messages)
        output.write(f"{greeting}\n\n")
        transcript_lines.extend([greeting, ""])

    while True:
        output.write(question.prompt)
        output.flush()

        try:
            raw_answer = input_stream.readline()
        except KeyboardInterrupt as exc:
            output.write(f"\n{INTERRUPTED_MESSAGE}\n")
            output.flush()

            transcript_lines.extend(["", INTERRUPTED_MESSAGE])

            _write_session_log(
                config,
                session_started_at,
                transcript_lines,
                session,
                log_home_dir=log_home_dir,
            )

            raise LessonInterrupted(INTERRUPTED_MESSAGE) from exc

        if raw_answer == "":
            raise EOFError("Input ended before the lesson completed.")

        answer_text = _normalize_answer_text(raw_answer)

        if not _is_valid_answer_text(answer_text):
            continue

        outcome = session.record_answer(is_correct_answer(question, answer_text))
        verdict = _build_verdict(outcome.is_correct, question.answer)

        _write_answer_line(output, question.prompt, answer_text, verdict)
        transcript_lines.append(f"{question.prompt}{answer_text} {verdict}")

        if outcome.feedback:
            output.write(f"\n{outcome.feedback}\n\n")
            transcript_lines.extend(["", outcome.feedback, ""])

        output.flush()

        if outcome.completed:
            break

        question = generate_question(config, lesson_rng)

    _write_session_log(
        config,
        session_started_at,
        transcript_lines,
        session,
        log_home_dir=log_home_dir,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        config = resolve_config(argv)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        run_lesson(config)
    except LessonInterrupted:
        return 130
    except KeyboardInterrupt:
        print(INTERRUPTED_MESSAGE, file=sys.stderr)
        return 130
    except (EOFError, LogWriteError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
