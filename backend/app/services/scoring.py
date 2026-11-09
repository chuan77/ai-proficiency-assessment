"""Deterministic scoring rules (no LLM involved)."""

LEVELS: list[tuple[float, str]] = [
    (85.0, "Expert"),
    (65.0, "Advanced"),
    (40.0, "Intermediate"),
    (0.0, "Beginner"),
]
MAX_OPEN_SCORE = 10.0


def score_mcq(user_answer: str, correct_answer: str) -> bool:
    """Exact (whitespace-trimmed) match between the chosen option and the key."""
    return user_answer.strip() == correct_answer.strip()


def question_points(
    question_type: str,
    *,
    is_correct: bool | None = None,
    llm_score: float | None = None,
    code_score: float | None = None,
) -> float:
    """Return 0.0-1.0 credit for one question; unanswered/unscored counts as 0."""
    if question_type == "mcq":
        return 1.0 if is_correct else 0.0
    if question_type == "code":
        return max(0.0, min(code_score or 0.0, 1.0))
    if llm_score is None:
        return 0.0
    return max(0.0, min(llm_score, MAX_OPEN_SCORE)) / MAX_OPEN_SCORE


def percent(points: list[float]) -> float:
    """Average credit as a 0-100 percentage, rounded to one decimal."""
    if not points:
        return 0.0
    return round(sum(points) / len(points) * 100, 1)


def weighted_percent(points: list[float], weights: list[float]) -> float:
    """Weighted average credit as a 0-100 percentage, rounded to one decimal."""
    total = sum(weights)
    if not points or total <= 0:
        return 0.0
    return round(sum(p * w for p, w in zip(points, weights, strict=True)) / total * 100, 1)


def proficiency_level(total_score: float) -> str:
    """Map a 0-100 score to Beginner/Intermediate/Advanced/Expert."""
    for threshold, name in LEVELS:
        if total_score >= threshold:
            return name
    return "Beginner"


def topic_breakdown(
    items: list[tuple[str, float, bool, float]],
) -> list[dict[str, str | int | float]]:
    """Group (topic, credit, answered, weight) tuples into per-topic score summaries.

    Fixed sessions weight every question 1, so max_points equals the question count.
    Topics without questions never appear. Order follows first appearance.
    """
    grouped: dict[str, list[tuple[float, bool, float]]] = {}
    for topic, credit, answered, weight in items:
        grouped.setdefault(topic, []).append((credit, answered, weight))
    summaries: list[dict[str, str | int | float]] = []
    for topic, entries in grouped.items():
        score = weighted_percent([e[0] for e in entries], [e[2] for e in entries])
        summaries.append(
            {
                "topic": topic,
                "score_percent": score,
                "level": proficiency_level(score),
                "questions_answered": sum(1 for e in entries if e[1]),
                "questions_total": len(entries),
                "earned_points": round(sum(e[0] * e[2] for e in entries), 2),
                "max_points": float(sum(e[2] for e in entries)),
            }
        )
    return summaries
