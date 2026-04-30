from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import random


DEFAULT_COIN_TARGET = Decimal("1.0")
DEFAULT_CORRECT_REWARD = Decimal("0.05")
DEFAULT_WRONG_PENALTY = Decimal("0.1")
HAPPY_STREAK = 5
SAD_STREAK = 3
HAPPY_KAOMOJI = (
    "(^_^)",
    "(^o^)",
    "(^-^)",
    "(^_~)",
    "(*^_^*)",
    "(^w^)",
    "(^.^)",
    "\\(^o^)/",
)
SAD_KAOMOJI = (
    "(T_T)",
    "(;_;)",
    "(>_<)",
    "(-_-;)",
    "(T-T)",
    "(u_u)",
    "(x_x)",
    "(._.;)",
)


@dataclass(frozen=True)
class AnswerOutcome:
    is_correct: bool
    earned_coins: Decimal
    total_correct: int
    correct_streak: int
    incorrect_streak: int
    feedback: str | None
    completed: bool


@dataclass
class SessionState:
    coin_target: Decimal = DEFAULT_COIN_TARGET
    correct_reward: Decimal = DEFAULT_CORRECT_REWARD
    wrong_penalty: Decimal = DEFAULT_WRONG_PENALTY
    success_messages: tuple[str, ...] = ()
    failure_messages: tuple[str, ...] = ()
    earned_coins: Decimal = Decimal("0.0")
    total_correct: int = 0
    correct_streak: int = 0
    incorrect_streak: int = 0

    def _build_feedback(self, message_pool: tuple[str, ...], kaomoji_pool: tuple[str, ...]) -> str:
        kaomoji = random.choice(kaomoji_pool)
        if not message_pool:
            return kaomoji

        return f"{random.choice(message_pool)} {kaomoji}"

    def record_answer(self, is_correct: bool) -> AnswerOutcome:
        """Record one answer and emit repeated feedback on uninterrupted streak milestones."""
        feedback = None

        if is_correct:
            self.earned_coins += self.correct_reward
            self.total_correct += 1
            self.correct_streak += 1
            self.incorrect_streak = 0

            if self.correct_streak > 0 and self.correct_streak % HAPPY_STREAK == 0:
                feedback = self._build_feedback(self.success_messages, HAPPY_KAOMOJI)
        else:
            self.earned_coins -= self.wrong_penalty
            self.incorrect_streak += 1
            self.correct_streak = 0

            if self.incorrect_streak > 0 and self.incorrect_streak % SAD_STREAK == 0:
                feedback = self._build_feedback(self.failure_messages, SAD_KAOMOJI)

        return AnswerOutcome(
            is_correct=is_correct,
            earned_coins=self.earned_coins,
            total_correct=self.total_correct,
            correct_streak=self.correct_streak,
            incorrect_streak=self.incorrect_streak,
            feedback=feedback,
            completed=self.earned_coins >= self.coin_target,
        )
