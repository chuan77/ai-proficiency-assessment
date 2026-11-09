"""Load the question bank from JSON into the database."""

import json
from pathlib import Path

from sqlmodel import Session

from app.models.question import Question

DIFFICULTIES = ("beginner", "intermediate", "advanced", "expert")


def seed_questions(session: Session, path: Path) -> int:
    """Insert or update questions from a JSON file; returns the number processed."""
    items = json.loads(path.read_text(encoding="utf-8"))
    for item in items:
        if item.get("difficulty") not in DIFFICULTIES:
            raise ValueError(
                f"Question {item.get('id')} has invalid difficulty {item.get('difficulty')!r}"
            )
    for item in items:
        session.merge(
            Question(
                id=item["id"],
                type=item["type"],
                topic=item["topic"],
                difficulty=item["difficulty"],
                text=item["question"],
                options=item.get("options"),
                correct_answer=item.get("correct_answer"),
                explanation=item.get("explanation"),
                evaluation_criteria=item.get("evaluation_criteria"),
                starter_code=item.get("starter_code"),
                test_cases=item.get("test_cases"),
                timeout_seconds=item.get("timeout_seconds"),
                points=item.get("points"),
            )
        )
    session.commit()
    return len(items)
