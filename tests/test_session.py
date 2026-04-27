from __future__ import annotations

from termedu import session as session_module
from termedu.session import DEFAULT_SESSION_TARGET, HAPPY_KAOMOJI, SAD_KAOMOJI, SessionState


def test_kaomoji_pools_have_minimum_size() -> None:
    assert len(HAPPY_KAOMOJI) >= 4
    assert len(SAD_KAOMOJI) >= 4


def test_happy_feedback_uses_happy_pool_at_streak_triggers(monkeypatch) -> None:
    session = SessionState()
    seen_pools: list[tuple[str, ...]] = []

    def fake_choice(pool: tuple[str, ...]) -> str:
        seen_pools.append(pool)
        return pool[1]

    monkeypatch.setattr(session_module.random, "choice", fake_choice)

    feedback_answers: list[int] = []
    feedback_values: list[str] = []
    for answer_number in range(1, 11):
        outcome = session.record_answer(True)
        if outcome.feedback is not None:
            feedback_answers.append(answer_number)
            feedback_values.append(outcome.feedback)

    assert feedback_answers == [5, 10]
    assert feedback_values == [HAPPY_KAOMOJI[1], HAPPY_KAOMOJI[1]]
    assert seen_pools == [HAPPY_KAOMOJI, HAPPY_KAOMOJI]


def test_sad_feedback_uses_sad_pool_at_streak_triggers(monkeypatch) -> None:
    session = SessionState()
    seen_pools: list[tuple[str, ...]] = []

    def fake_choice(pool: tuple[str, ...]) -> str:
        seen_pools.append(pool)
        return pool[2]

    monkeypatch.setattr(session_module.random, "choice", fake_choice)

    feedback_answers: list[int] = []
    feedback_values: list[str] = []
    for answer_number in range(1, 7):
        outcome = session.record_answer(False)
        if outcome.feedback is not None:
            feedback_answers.append(answer_number)
            feedback_values.append(outcome.feedback)

    assert feedback_answers == [3, 6]
    assert feedback_values == [SAD_KAOMOJI[2], SAD_KAOMOJI[2]]
    assert seen_pools == [SAD_KAOMOJI, SAD_KAOMOJI]


def test_session_completes_after_twenty_four_correct_answers() -> None:
    session = SessionState()

    outcome = None
    for _ in range(DEFAULT_SESSION_TARGET):
        outcome = session.record_answer(True)

    assert outcome is not None
    assert outcome.completed is True
    assert outcome.total_correct == DEFAULT_SESSION_TARGET


def test_session_completes_after_custom_target() -> None:
    session = SessionState(target_correct=2)

    first_outcome = session.record_answer(True)
    second_outcome = session.record_answer(True)

    assert first_outcome.completed is False
    assert second_outcome.completed is True
