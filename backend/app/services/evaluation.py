"""LLM-backed evaluation of open-ended answers and overall feedback."""

import json
import logging
import re
from pathlib import Path
from string import Template

from app.core.config import settings
from app.core.llm import LLMClient, LLMUnavailableError
from app.services.scoring import MAX_OPEN_SCORE

logger = logging.getLogger(__name__)
SYSTEM_PROMPT = "You are a precise assistant. Follow the output format exactly."


def load_prompt(name: str, prompts_dir: Path | None = None) -> Template:
    """Load a prompt template from the prompts directory."""
    path = (prompts_dir or settings.prompts_dir) / name
    return Template(path.read_text(encoding="utf-8"))


def parse_evaluation(raw: str) -> tuple[float, str]:
    """Extract (score, feedback) from the model reply; raises LLMUnavailableError if invalid."""
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if match is None:
        raise LLMUnavailableError("LLM reply contained no JSON object")
    try:
        data = json.loads(match.group(0))
        score = float(data["score"])
        feedback = str(data.get("feedback", "")).strip()
    except (ValueError, KeyError, TypeError) as exc:
        raise LLMUnavailableError("LLM reply was not valid evaluation JSON") from exc
    return max(0.0, min(score, MAX_OPEN_SCORE)), feedback


class EvaluationService:
    """Scores open-ended answers and writes the overall feedback summary."""

    def __init__(self, llm: LLMClient, prompts_dir: Path | None = None) -> None:
        self._llm = llm
        self._prompts_dir = prompts_dir

    async def evaluate_open_answer(
        self, question: str, criteria: str | None, answer: str
    ) -> tuple[float, str]:
        """Return (score 0-10, short feedback) for one open-ended answer."""
        template = load_prompt("evaluate_open_ended.txt", self._prompts_dir)
        prompt = template.safe_substitute(
            question=question,
            criteria=criteria or "Judge accuracy, clarity and specificity.",
            answer=answer,
        )
        return parse_evaluation(await self._llm.chat(SYSTEM_PROMPT, prompt))

    async def generate_feedback(
        self, total_score: float, level: str, topic_scores: dict[str, float]
    ) -> str:
        """Return a personalised summary; falls back to a plain summary if the LLM fails."""
        breakdown = "\n".join(f"- {topic}: {score}%" for topic, score in topic_scores.items())
        template = load_prompt("generate_feedback.txt", self._prompts_dir)
        prompt = template.safe_substitute(
            total_score=total_score, level=level, topic_breakdown=breakdown
        )
        try:
            return (await self._llm.chat(SYSTEM_PROMPT, prompt)).strip()
        except LLMUnavailableError:
            logger.warning("Feedback generation failed; using fallback summary")
            return fallback_feedback(total_score, level, topic_scores)


def fallback_feedback(total_score: float, level: str, topic_scores: dict[str, float]) -> str:
    """Deterministic summary used when the LLM cannot write feedback."""
    if not topic_scores:
        return f"You scored {total_score}/100 ({level})."
    best = max(topic_scores, key=lambda t: topic_scores[t])
    worst = min(topic_scores, key=lambda t: topic_scores[t])
    return (
        f"You scored {total_score}/100, which is {level} level. "
        f"Your strongest topic was {best}; focus next on {worst}."
    )
