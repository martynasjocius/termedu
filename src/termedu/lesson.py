from __future__ import annotations

from dataclasses import dataclass
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

    @property
    def prompt(self) -> str:
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
                else rng.randint(0, config.right_max)
            )
        else:
            operand = (
                config.fixed_left
                if config.fixed_left is not None
                else rng.randint(0, config.left_max)
            )
        operands.append(operand)

    return Question(
        left=operands[0],
        right=operands[1],
        operation="mixed",
        operands=tuple(operands),
        operators=tuple(operators),
    )


def generate_question(config: AppConfig, rng: random.Random) -> Question:
    if config.operation == "mixed":
        return _generate_mixed_question(config, rng)

    left = config.fixed_left if config.fixed_left is not None else rng.randint(0, config.left_max)
    right = (
        config.fixed_right if config.fixed_right is not None else rng.randint(0, config.right_max)
    )
    return Question(left=left, right=right, operation=config.operation)


def is_correct_answer(question: Question, answer_text: str) -> bool:
    try:
        answer = int(answer_text.strip())
    except ValueError:
        return False

    return answer == question.answer
