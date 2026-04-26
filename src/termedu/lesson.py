from __future__ import annotations

from dataclasses import dataclass
import random

from termedu.config import AppConfig


@dataclass(frozen=True)
class Question:
    left: int
    right: int

    @property
    def prompt(self) -> str:
        return f"{self.left} x {self.right} = "

    @property
    def answer(self) -> int:
        return self.left * self.right


def generate_question(config: AppConfig, rng: random.Random) -> Question:
    left = config.fixed_left if config.fixed_left is not None else rng.randint(0, config.left_max)
    right = (
        config.fixed_right if config.fixed_right is not None else rng.randint(0, config.right_max)
    )
    return Question(left=left, right=right)


def is_correct_answer(question: Question, answer_text: str) -> bool:
    try:
        answer = int(answer_text.strip())
    except ValueError:
        return False

    return answer == question.answer
