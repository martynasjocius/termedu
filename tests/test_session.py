from __future__ import annotations

from decimal import Decimal

from termedu import session as session_module
from termedu.session import DEFAULT_COIN_TARGET, HAPPY_KAOMOJI, SAD_KAOMOJI, SessionState


def test_kaomoji_pools_have_minimum_size() -> None:
    assert len(HAPPY_KAOMOJI) >= 8
    assert len(SAD_KAOMOJI) >= 8


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


def test_custom_feedback_messages_are_printed_with_kaomoji(monkeypatch) -> None:
    session = SessionState(
        success_messages=("Nice work",),
        failure_messages=("Try again",),
    )

    def fake_choice(pool: tuple[str, ...]) -> str:
        return pool[0]

    monkeypatch.setattr(session_module.random, "choice", fake_choice)

    success_outcome = None
    for _ in range(5):
        success_outcome = session.record_answer(True)

    failure_outcome = None
    for _ in range(3):
        failure_outcome = session.record_answer(False)

    assert success_outcome is not None
    assert failure_outcome is not None
    assert success_outcome.feedback == f"Nice work {HAPPY_KAOMOJI[0]}"
    assert failure_outcome.feedback == f"Try again {SAD_KAOMOJI[0]}"


def test_session_completes_after_default_coin_target() -> None:
    session = SessionState()

    outcome = None
    for _ in range(20):
        outcome = session.record_answer(True)

    assert outcome is not None
    assert outcome.completed is True
    assert outcome.total_correct == 20
    assert outcome.earned_coins == DEFAULT_COIN_TARGET


def test_session_completes_after_custom_coin_target() -> None:
    session = SessionState(coin_target=Decimal("0.15"))

    first_outcome = session.record_answer(True)
    second_outcome = session.record_answer(True)
    third_outcome = session.record_answer(True)

    assert first_outcome.completed is False
    assert second_outcome.completed is False
    assert third_outcome.completed is True


def test_session_subtracts_penalty_for_incorrect_answers() -> None:
    session = SessionState()

    correct_outcome = session.record_answer(True)
    incorrect_outcome = session.record_answer(False)

    assert correct_outcome.earned_coins == Decimal("0.05")
    assert incorrect_outcome.earned_coins == Decimal("-0.05")
    assert incorrect_outcome.completed is False
