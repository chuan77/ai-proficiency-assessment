"""Pydantic request/response schemas for the API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.code import CodeResult

MAX_ANSWER_LENGTH = 4000


class QuestionOut(BaseModel):
    """A question as shown to the user (never includes the correct answer)."""

    id: str
    index: int
    type: Literal["mcq", "open", "code"]
    topic: str
    text: str
    difficulty: str | None = None
    options: list[str] | None = None
    starter_code: str | None = None


class StartIn(BaseModel):
    """Optional request body for starting a session."""

    mode: Literal["fixed", "adaptive"] = "fixed"


class SessionState(BaseModel):
    """Current state of a session plus the question at the requested index."""

    session_id: str
    status: Literal["in_progress", "completed"]
    mode: Literal["fixed", "adaptive"] = "fixed"
    total_questions: int
    max_questions: int | None = None
    ready_to_submit: bool = False
    current_question_index: int
    answered_question_ids: list[str]
    question: QuestionOut
    saved_answer: str | None = None
    saved_code_result: CodeResult | None = None


class AnswerIn(BaseModel):
    """Request body for saving one answer."""

    question_id: str
    answer: str = Field(min_length=1, max_length=MAX_ANSWER_LENGTH)


class CodeEvalIn(BaseModel):
    """Request body for running a code answer against the tests."""

    question_id: str
    code: str = Field(min_length=1, max_length=MAX_ANSWER_LENGTH)


class AnswerSaved(BaseModel):
    """Acknowledgement after saving an answer."""

    question_id: str
    answered_count: int
    total_questions: int


class TopicScore(BaseModel):
    """Score, level and counts for a single topic."""

    topic: str
    score_percent: float
    level: str = "Beginner"
    questions_answered: int = 0
    questions_total: int = 0
    earned_points: float = 0.0
    max_points: float = 0.0


class ResultOut(BaseModel):
    """Final score, level and feedback."""

    session_id: str
    total_score: float
    proficiency_level: str
    feedback_text: str
    mcq_correct: int
    mcq_total: int
    open_average: float | None
    code_passed: int = 0
    code_total: int = 0
    mode: Literal["fixed", "adaptive"] = "fixed"
    questions_answered: int = 0
    topic_scores: list[TopicScore]
    completed_at: datetime


class ReviewItem(BaseModel):
    """One question with the user's answer and its evaluation."""

    index: int
    question_id: str
    type: Literal["mcq", "open", "code"]
    topic: str
    text: str
    options: list[str] | None
    user_answer: str | None
    correct_answer: str | None
    is_correct: bool | None
    llm_score: float | None
    llm_feedback: str | None
    explanation: str | None
    code_result: CodeResult | None = None
    difficulty_served: str | None = None


class ReviewOut(BaseModel):
    """All answers for a completed session."""

    session_id: str
    items: list[ReviewItem]
