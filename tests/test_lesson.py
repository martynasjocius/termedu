from __future__ import annotations

import random

from termedu.config import AppConfig
from termedu.lesson import Question, generate_question, is_correct_answer


def test_generate_question_uses_ranged_operands() -> None:
    question = generate_question(AppConfig(left_max=3, right_max=4), random.Random(0))

    assert question.left == 3
    assert question.right == 3


def test_generate_question_uses_fixed_left() -> None:
    question = generate_question(AppConfig(left_max=12, right_max=5, fixed_left=4), random.Random(0))

    assert question.left == 4
    assert question.right == 3


def test_generate_question_uses_fixed_right() -> None:
    question = generate_question(AppConfig(left_max=5, right_max=12, fixed_right=7), random.Random(0))

    assert question.left == 3
    assert question.right == 7


def test_generate_question_uses_configured_addition_operation() -> None:
    question = generate_question(
        AppConfig(operation="addition", left_max=3, right_max=4),
        random.Random(0),
    )

    assert question.operation == "addition"
    assert question.prompt == "3 + 3 = "
    assert question.answer == 6


def test_generate_question_builds_mixed_operation_expressions() -> None:
    rng = random.Random(0)
    questions = [
        generate_question(AppConfig(operation="mixed", fixed_left=4, fixed_right=3), rng)
        for _ in range(5)
    ]

    assert [question.prompt for question in questions] == [
        "4 + 4 x 3 = ",
        "4 + 4 + 4 = ",
        "4 + 4 + 4 = ",
        "4 x 3 = ",
        "4 x 3 + 4 = ",
    ]
    assert [question.answer for question in questions] == [16, 12, 12, 12, 16]


def test_generate_question_avoids_three_number_multiplication_only_expressions() -> None:
    rng = random.Random(0)
    questions = [
        generate_question(AppConfig(operation="mixed", fixed_left=7, fixed_right=3), rng)
        for _ in range(50)
    ]

    assert all(
        "+" in (question.operators or ()) or len(question.operands or ()) == 2
        for question in questions
    )


def test_generate_question_uses_left_range_for_left_mixed_multiplication_factors() -> None:
    rng = random.Random(0)
    questions = [
        generate_question(AppConfig(operation="mixed", left_max=4, right_max=12), rng)
        for _ in range(50)
    ]

    for question in questions:
        assert question.operands is not None
        assert question.operators is not None
        for index, operator in enumerate(question.operators):
            if operator == "*":
                assert question.operands[index] <= 4


def test_generate_question_honors_configured_mixed_max_numbers() -> None:
    rng = random.Random(0)
    questions = [
        generate_question(
            AppConfig(operation="mixed", fixed_left=4, fixed_right=3, max_numbers=4),
            rng,
        )
        for _ in range(10)
    ]
    number_counts = [len(question.operands or ()) for question in questions]

    assert max(number_counts) == 4
    assert min(number_counts) >= 2


def test_correct_answer_evaluation() -> None:
    assert is_correct_answer(Question(left=4, right=3), "12") is True


def test_correct_addition_answer_evaluation() -> None:
    assert is_correct_answer(Question(left=4, right=3, operation="addition"), "7") is True


def test_incorrect_answer_evaluation() -> None:
    assert is_correct_answer(Question(left=4, right=3), "11") is False


def test_non_numeric_answer_is_incorrect() -> None:
    assert is_correct_answer(Question(left=4, right=3), "") is False
