from __future__ import annotations

from dataclasses import dataclass


DEFAULT_SESSION_TARGET = 24
HAPPY_STREAK = 5
SAD_STREAK = 3
HAPPY_KAOMOJI = "(^_^)"
SAD_KAOMOJI = "(T_T)"


@dataclass(frozen=True)
class AnswerOutcome:
    is_correct: bool
    total_correct: int
    correct_streak: int
    incorrect_streak: int
    feedback: str | None
    completed: bool


@dataclass
class SessionState:
    target_correct: int = DEFAULT_SESSION_TARGET
    total_correct: int = 0
    correct_streak: int = 0
    incorrect_streak: int = 0

    def record_answer(self, is_correct: bool) -> AnswerOutcome:
        """Record one answer and emit repeated feedback on uninterrupted streak milestones."""
        feedback = None

        if is_correct:
            self.total_correct += 1
            self.correct_streak += 1
            self.incorrect_streak = 0

            if self.correct_streak > 0 and self.correct_streak % HAPPY_STREAK == 0:
                feedback = HAPPY_KAOMOJI
        else:
            self.incorrect_streak += 1
            self.correct_streak = 0

            if self.incorrect_streak > 0 and self.incorrect_streak % SAD_STREAK == 0:
                feedback = SAD_KAOMOJI

        return AnswerOutcome(
            is_correct=is_correct,
            total_correct=self.total_correct,
            correct_streak=self.correct_streak,
            incorrect_streak=self.incorrect_streak,
            feedback=feedback,
            completed=self.total_correct >= self.target_correct,
        )
