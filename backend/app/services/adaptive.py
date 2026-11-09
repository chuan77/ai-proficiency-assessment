"""Rule-based adaptive difficulty: pick the next target level and the next question."""

import logging
import random
from dataclasses import dataclass

from app.core.config import settings
from app.models import Question

logger = logging.getLogger(__name__)

DIFFICULTY_ORDER: tuple[str, ...] = ("beginner", "intermediate", "advanced", "expert")
# Harder questions count for more so a strong user is not penalised for being served them.
DIFFICULTY_WEIGHTS: dict[str, float] = {
    "beginner": 1.0,
    "intermediate": 2.0,
    "advanced": 3.0,
    "expert": 4.0,
}


@dataclass(frozen=True)
class AdaptiveConfig:
    """Tunable rules for adaptive sessions."""

    min_questions: int = 8
    max_questions: int = 15
    start_difficulty: str = "intermediate"
    performance_window: int = 2
    topic_balancing: bool = True
    correct_threshold: float = 0.6

    @classmethod
    def from_settings(cls) -> AdaptiveConfig:
        """Build the config from environment-driven settings."""
        return cls(
            min_questions=settings.adaptive_min_questions,
            max_questions=settings.adaptive_max_questions,
            start_difficulty=settings.adaptive_start_difficulty,
            performance_window=settings.adaptive_performance_window,
            topic_balancing=settings.adaptive_topic_balancing,
            correct_threshold=settings.adaptive_correct_threshold,
        )


def difficulty_weight(difficulty: str) -> float:
    """Scoring weight of a question; unknown difficulties count as 1."""
    return DIFFICULTY_WEIGHTS.get(difficulty, 1.0)


def _level(difficulty: str) -> int:
    return DIFFICULTY_ORDER.index(difficulty) if difficulty in DIFFICULTY_ORDER else 1


class AdaptiveEngine:
    """Decides difficulty, question choice and when to stop (no database access)."""

    def __init__(self, config: AdaptiveConfig, rng: random.Random | None = None) -> None:
        self.config = config
        self._rng = rng or random.Random()

    def effective_max(self, bank_size: int) -> int:
        """Maximum questions for a session, never more than the bank holds."""
        return max(1, min(self.config.max_questions, bank_size))

    def next_difficulty(self, current: str, correct: bool) -> str:
        """Move one level up after a correct answer, one down after a wrong one."""
        step = 1 if correct else -1
        level = min(max(_level(current) + step, 0), len(DIFFICULTY_ORDER) - 1)
        return DIFFICULTY_ORDER[level]

    def is_stable(self, history: list[bool], difficulty: str) -> bool:
        """True when recent answers bracket the user's level or hit a ceiling/floor."""
        window = history[-self.config.performance_window :]
        if len(window) < self.config.performance_window:
            return False
        if len(set(window)) > 1:
            return True  # alternating results: the level is bracketed
        if all(window):
            return difficulty == DIFFICULTY_ORDER[-1]
        return difficulty == DIFFICULTY_ORDER[0]

    def should_stop(
        self, history: list[bool], difficulty: str, bank_size: int, remaining: int
    ) -> bool:
        """Stop at the maximum, when nothing is left, or at the minimum once stable."""
        served = len(history)
        if served >= self.effective_max(bank_size) or remaining == 0:
            return True
        return served >= self.config.min_questions and self.is_stable(history, difficulty)

    def select_next(
        self,
        candidates: list[Question],
        served: list[Question],
        target: str,
        slots_left: int,
    ) -> Question | None:
        """Pick the unseen question closest to `target`, keeping topics reasonably balanced."""
        if not candidates:
            return None
        pool = self._topic_pool(candidates, served, slots_left)
        counts = {q.topic: sum(1 for s in served if s.topic == q.topic) for q in pool}
        distance = _level(target)
        ranked = sorted(
            pool,
            key=lambda q: (
                abs(_level(q.difficulty) - distance),
                counts[q.topic] if self.config.topic_balancing else 0,
                _level(q.difficulty),
                self._rng.random(),
            ),
        )
        chosen = ranked[0]
        if chosen.difficulty != target:
            logger.info(
                "No unused %s question available; serving %s instead", target, chosen.difficulty
            )
        return chosen

    def _topic_pool(
        self, candidates: list[Question], served: list[Question], slots_left: int
    ) -> list[Question]:
        """Force unseen topics in once the remaining slots would otherwise run out."""
        if not self.config.topic_balancing:
            return candidates
        seen = {q.topic for q in served}
        unseen = {q.topic for q in candidates} - seen
        if unseen and slots_left <= len(unseen):
            return [q for q in candidates if q.topic in unseen]
        return candidates
