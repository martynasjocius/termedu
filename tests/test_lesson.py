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


def test_correct_answer_evaluation() -> None:
    assert is_correct_answer(Question(left=4, right=3), "12") is True


def test_incorrect_answer_evaluation() -> None:
    assert is_correct_answer(Question(left=4, right=3), "11") is False


def test_non_numeric_answer_is_incorrect() -> None:
    assert is_correct_answer(Question(left=4, right=3), "") is False
