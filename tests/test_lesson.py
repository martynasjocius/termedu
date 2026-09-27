from __future__ import annotations

import random
import pytest

from termedu.config import AppConfig
from termedu.lesson import Question, generate_question, is_correct_answer


def test_generate_question_uses_ranged_operands() -> None:
    question = generate_question(AppConfig(left_max=3, right_max=4), random.Random(0))

    assert question.left == 3
    assert question.right == 3


@pytest.mark.parametrize("operation", ["multiplication", "addition", "mixed"])
@pytest.mark.parametrize("mode", ["result", "missing_operand", "mixed"])
def test_generate_question_honors_minima(operation: str, mode: str) -> None:
    rng = random.Random(0)
    config = AppConfig(
        operation=operation, question_mode=mode,
        left_min=2, left_max=4, right_min=7, right_max=9,
    )
    for _ in range(50):
        question = generate_question(config, rng)
        for index, number in enumerate(question.numbers):
            if operation == "mixed":
                operators = question.operators or ()
                right_factor = index > 0 and operators[index - 1] == "*"
                left_factor = index < len(operators) and operators[index] == "*"
                uses_right_range = right_factor and not left_factor
            else:
                uses_right_range = index == 1
            if uses_right_range:
                assert 7 <= number <= 9
            else:
                assert 2 <= number <= 4


def test_equal_range_endpoints_and_fixed_operand_override() -> None:
    question = generate_question(AppConfig(
        left_min=3, left_max=3, right_min=5, right_max=5,
    ), random.Random(0))
    assert question.numbers == (3, 5)
    question = generate_question(AppConfig(
        left_min=3, right_min=5, fixed_left=1, fixed_right=0,
    ), random.Random(0))
    assert question.numbers == (1, 0)


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


@pytest.mark.parametrize("index,prompt,answer", [
    (0, "_ x 6 = 12  -->  _ = ", 2),
    (1, "2 x _ = 12  -->  _ = ", 6),
])
def test_missing_operand_answers(index: int, prompt: str, answer: int) -> None:
    question = Question(left=2, right=6, missing_index=index)
    assert question.prompt == prompt
    assert is_correct_answer(question, str(answer))
    assert not is_correct_answer(question, "12")


def test_missing_operand_in_mixed_expression() -> None:
    question = Question(
        left=2, right=6, operation="mixed", operands=(2, 6, 3),
        operators=("*", "+"), missing_index=1,
    )
    assert question.prompt == "2 x _ + 3 = 15  -->  _ = "
    assert question.answer == 6


@pytest.mark.parametrize("operation", ["multiplication", "addition", "mixed"])
@pytest.mark.parametrize("symbol", ["?", "□", "[blank]"])
def test_generated_questions_use_custom_missing_symbol(operation: str, symbol: str) -> None:
    rng = random.Random(0)
    questions = [generate_question(AppConfig(
        operation=operation, question_mode="missing_operand", missing_symbol=symbol,
        fixed_left=2, fixed_right=6,
    ), rng) for _ in range(20)]
    for question in questions:
        assert symbol in question.prompt
        assert "_" not in question.prompt
        assert is_correct_answer(question, str(question.numbers[question.missing_index]))


@pytest.mark.parametrize("operation", ["multiplication", "addition", "mixed"])
def test_missing_mode_generates_blanks(operation: str) -> None:
    rng = random.Random(0)
    questions = [generate_question(AppConfig(
        operation=operation, question_mode="missing_operand", fixed_left=2, fixed_right=6,
    ), rng) for _ in range(50)]
    assert all(question.missing_index is not None for question in questions)
    assert {question.missing_index for question in questions} >= {0, 1}


def test_mixed_question_mode_generates_both_styles() -> None:
    rng = random.Random(0)
    questions = [generate_question(AppConfig(
        question_mode="mixed", fixed_left=2, fixed_right=6,
    ), rng) for _ in range(50)]
    assert any(question.missing_index is None for question in questions)
    assert any(question.missing_index is not None for question in questions)


@pytest.mark.parametrize("left,right,index", [(0, 6, 0), (2, 0, 1), (0, 0, None)])
def test_missing_mode_avoids_ambiguous_zero_products(
    left: int, right: int, index: int | None,
) -> None:
    question = generate_question(AppConfig(
        question_mode="missing_operand", fixed_left=left, fixed_right=right,
    ), random.Random(0))
    assert question.missing_index == index


def test_mixed_expression_does_not_hide_factor_in_zero_product() -> None:
    rng = random.Random(0)
    questions = [generate_question(AppConfig(
        operation="mixed", question_mode="missing_operand", fixed_left=0, fixed_right=0,
    ), rng) for _ in range(50)]
    for question in questions:
        if question.missing_index is not None:
            assert question.operators is not None
            index = question.missing_index
            assert index == 0 or question.operators[index - 1] != "*"
            assert index == len(question.operators) or question.operators[index] != "*"
