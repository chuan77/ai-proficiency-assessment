"""Database models for the assessment."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


def _new_id() -> str:
    return uuid.uuid4().hex


class Question(SQLModel, table=True):
    """A question in the bank (multiple choice or open-ended)."""

    id: str = Field(primary_key=True)
    type: str  # "mcq" | "open"
    topic: str
    difficulty: str
    text: str
    options: list[str] | None = Field(default=None, sa_column=Column(JSON))
    correct_answer: str | None = None
    explanation: str | None = None
    evaluation_criteria: str | None = None
    # code questions
    starter_code: str | None = None
    test_cases: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    timeout_seconds: int | None = None
    points: int | None = None


class AssessmentSession(SQLModel, table=True):
    """One user's attempt; question order is fixed when the session starts."""

    id: str = Field(default_factory=_new_id, primary_key=True)
    created_at: datetime = Field(default_factory=_now)
    status: str = "in_progress"  # "in_progress" | "completed"
    current_question_index: int = 0
    question_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    # adaptive mode (rows created before this feature have NULLs, which mean "fixed")
    mode: str | None = "fixed"  # "fixed" | "adaptive"
    current_difficulty: str | None = None  # target difficulty of the next question
    performance_history: list[bool] | None = Field(default=None, sa_column=Column(JSON))
    adaptive_complete: bool | None = False  # engine decided no more questions are needed


class Answer(SQLModel, table=True):
    """A user's answer, with scoring fields filled in on submission."""

    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="assessmentsession.id", index=True)
    question_id: str = Field(foreign_key="question.id")
    user_answer: str
    is_correct: bool | None = None
    llm_score: float | None = None
    llm_feedback: str | None = None
    code_result: dict | None = Field(default=None, sa_column=Column(JSON))
    difficulty_served: str | None = None


class Result(SQLModel, table=True):
    """Final outcome of a completed session."""

    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="assessmentsession.id", unique=True)
    total_score: float
    proficiency_level: str
    feedback_text: str
    topic_scores: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    completed_at: datetime = Field(default_factory=_now)
