"""Unit tests for deterministic scoring rules."""

import pytest

from app.services import scoring


@pytest.mark.parametrize(
    ("score", "level"),
    [
        (0, "Beginner"),
        (39.9, "Beginner"),
        (40, "Intermediate"),
        (64.9, "Intermediate"),
        (65, "Advanced"),
        (84.9, "Advanced"),
        (85, "Expert"),
        (100, "Expert"),
    ],
)
def test_level_boundaries(score: float, level: str) -> None:
    assert scoring.proficiency_level(score) == level


def test_mcq_exact_match_only() -> None:
    assert scoring.score_mcq(" Large Language Model ", "Large Language Model")
    assert not scoring.score_mcq("large language model", "Large Language Model")


def test_question_points() -> None:
    assert scoring.question_points("mcq", is_correct=True) == 1.0
    assert scoring.question_points("mcq", is_correct=False) == 0.0
    assert scoring.question_points("mcq") == 0.0
    assert scoring.question_points("open", llm_score=5) == 0.5
    assert scoring.question_points("open", llm_score=99) == 1.0
    assert scoring.question_points("open") == 0.0
    assert scoring.question_points("code", code_score=1.0) == 1.0
    assert scoring.question_points("code", code_score=0.5) == 0.5
    assert scoring.question_points("code") == 0.0


def test_percent() -> None:
    assert scoring.percent([]) == 0.0
    assert scoring.percent([1.0, 0.0, 0.5]) == 50.0


def test_topic_breakdown_uneven_and_partial_credit() -> None:
    items = [
        ("A", 1.0, True, 1.0),
        ("A", 0.5, True, 1.0),
        ("A", 0.0, False, 1.0),
        ("B", 0.9, True, 1.0),
    ]
    by_topic = {t["topic"]: t for t in scoring.topic_breakdown(items)}
    assert by_topic["A"]["score_percent"] == 50.0
    assert by_topic["A"]["level"] == "Intermediate"
    assert (by_topic["A"]["questions_answered"], by_topic["A"]["questions_total"]) == (2, 3)
    assert by_topic["A"]["earned_points"] == 1.5 and by_topic["A"]["max_points"] == 3.0
    assert by_topic["B"]["level"] == "Expert"


def test_topic_breakdown_empty() -> None:
    assert scoring.topic_breakdown([]) == []


def test_topic_breakdown_applies_weights() -> None:
    items = [("A", 1.0, True, 1.0), ("A", 0.0, True, 3.0)]
    topic = scoring.topic_breakdown(items)[0]
    assert topic["score_percent"] == 25.0
    assert topic["earned_points"] == 1.0 and topic["max_points"] == 4.0
    assert scoring.weighted_percent([1.0, 0.0], [1.0, 3.0]) == 25.0
