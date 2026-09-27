from __future__ import annotations

from dataclasses import dataclass, replace
import random

from termedu.config import AppConfig

MIXED_OPERATORS = ("*", "+")


def _render_operator(operator: str) -> str:
    if operator == "*":
        return "x"

    return operator


@dataclass(frozen=True)
class Question:
    left: int
    right: int
    operation: str = "multiplication"
    operands: tuple[int, ...] | None = None
    operators: tuple[str, ...] | None = None
    missing_index: int | None = None
    missing_symbol: str = "_"

    @property
    def numbers(self) -> tuple[int, ...]:
        return self.operands if self.operands is not None else (self.left, self.right)

    @property
    def prompt(self) -> str:
        if self.missing_index is not None:
            operators = self.operators if self.operation == "mixed" else (
                "+" if self.operation == "addition" else "*",
            )
            assert operators is not None
            parts = [self.missing_symbol if self.missing_index == 0 else str(self.numbers[0])]
            for index, (operator, operand) in enumerate(
                zip(operators, self.numbers[1:], strict=True), start=1
            ):
                parts.extend([
                    _render_operator(operator),
                    self.missing_symbol if index == self.missing_index else str(operand),
                ])
            return f"{' '.join(parts)} = {self.result}  -->  {self.missing_symbol} = "

        if self.operation == "mixed":
            assert self.operands is not None
            assert self.operators is not None
            parts = [str(self.operands[0])]
            for operator, operand in zip(self.operators, self.operands[1:], strict=True):
                parts.extend([_render_operator(operator), str(operand)])
            return f"{' '.join(parts)} = "

        if self.operation == "addition":
            return f"{self.left} + {self.right} = "

        return f"{self.left} x {self.right} = "

    @property
    def answer(self) -> int:
        if self.missing_index is not None:
            return self.numbers[self.missing_index]
        return self.result

    @property
    def result(self) -> int:
        if self.operation == "mixed":
            assert self.operands is not None
            assert self.operators is not None
            total = 0
            product = self.operands[0]

            for operator, operand in zip(self.operators, self.operands[1:], strict=True):
                if operator == "*":
                    product *= operand
                else:
                    total += product
                    product = operand

            return total + product

        if self.operation == "addition":
            return self.left + self.right

        return self.left * self.right


def _generate_mixed_question(config: AppConfig, rng: random.Random) -> Question:
    number_count = rng.randint(2, config.max_numbers)
    operators = [rng.choice(MIXED_OPERATORS) for _ in range(number_count - 1)]
    if len(operators) > 1 and all(operator == "*" for operator in operators):
        operators[-1] = "+"
    operands = []
    for index in range(number_count):
        is_left_factor = index < len(operators) and operators[index] == "*"
        is_right_factor = index > 0 and operators[index - 1] == "*"
        if is_right_factor and not is_left_factor:
            operand = (
                config.fixed_right
                if config.fixed_right is not None
                else rng.randint(config.right_min, config.right_max)
            )
        else:
            operand = (
                config.fixed_left
                if config.fixed_left is not None
                else rng.randint(config.left_min, config.left_max)
            )
        operands.append(operand)

    return Question(
        left=operands[0],
        right=operands[1],
        operation="mixed",
        operands=tuple(operands),
        operators=tuple(operators),
    )


def _generate_result_question(config: AppConfig, rng: random.Random) -> Question:
    if config.operation == "mixed":
        return _generate_mixed_question(config, rng)

    left = config.fixed_left if config.fixed_left is not None else rng.randint(config.left_min, config.left_max)
    right = (
        config.fixed_right if config.fixed_right is not None else rng.randint(config.right_min, config.right_max)
    )
    return Question(left=left, right=right, operation=config.operation)


def generate_question(config: AppConfig, rng: random.Random) -> Question:
    question = _generate_result_question(config, rng)
    if config.question_mode == "result":
        return question
    if config.question_mode == "mixed" and rng.choice((True, False)):
        return question

    # A blank must affect the result: a factor multiplied by zero has no unique answer.
    candidates = []
    for index, operand in enumerate(question.numbers):
        numbers = list(question.numbers)
        numbers[index] = operand + 1
        changed = replace(
            question, left=numbers[0], right=numbers[1],
            operands=tuple(numbers) if question.operands is not None else None,
        )
        if changed.result != question.result:
            candidates.append(index)

    if not candidates:
        return question
    return replace(
        question, missing_index=rng.choice(candidates), missing_symbol=config.missing_symbol,
    )


def is_correct_answer(question: Question, answer_text: str) -> bool:
    try:
        answer = int(answer_text.strip())
    except ValueError:
        return False

    return answer == question.answer
