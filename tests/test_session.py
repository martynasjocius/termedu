from __future__ import annotations

from termedu.session import HAPPY_KAOMOJI, SAD_KAOMOJI, SESSION_TARGET, SessionState


def test_happy_feedback_after_five_correct_answers() -> None:
    session = SessionState()

    outcome = None
    for _ in range(5):
        outcome = session.record_answer(True)

    assert outcome is not None
    assert outcome.feedback == HAPPY_KAOMOJI
    assert outcome.correct_streak == 5
    assert outcome.incorrect_streak == 0


def test_happy_feedback_repeats_on_longer_correct_streaks() -> None:
    session = SessionState()

    feedback_answers: list[int] = []
    for answer_number in range(1, 11):
        outcome = session.record_answer(True)
        if outcome.feedback == HAPPY_KAOMOJI:
            feedback_answers.append(answer_number)

    assert feedback_answers == [5, 10]


def test_sad_feedback_after_three_incorrect_answers() -> None:
    session = SessionState()

    outcome = None
    for _ in range(3):
        outcome = session.record_answer(False)

    assert outcome is not None
    assert outcome.feedback == SAD_KAOMOJI
    assert outcome.correct_streak == 0
    assert outcome.incorrect_streak == 3


def test_sad_feedback_repeats_on_longer_incorrect_streaks() -> None:
    session = SessionState()

    feedback_answers: list[int] = []
    for answer_number in range(1, 7):
        outcome = session.record_answer(False)
        if outcome.feedback == SAD_KAOMOJI:
            feedback_answers.append(answer_number)

    assert feedback_answers == [3, 6]


def test_session_completes_after_twenty_four_correct_answers() -> None:
    session = SessionState()

    outcome = None
    for _ in range(SESSION_TARGET):
        outcome = session.record_answer(True)

    assert outcome is not None
    assert outcome.completed is True
    assert outcome.total_correct == SESSION_TARGET
