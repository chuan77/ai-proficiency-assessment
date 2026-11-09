"""HTTP endpoints for the assessment flow."""

from typing import Annotated

from fastapi import APIRouter, Body, Query, status

from app.api.deps import AssessmentDep, EvaluationDep
from app.schemas.assessment import (
    AnswerIn,
    AnswerSaved,
    CodeEvalIn,
    ResultOut,
    ReviewOut,
    SessionState,
    StartIn,
)
from app.schemas.code import CodeResult

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.post("/start", response_model=SessionState, status_code=status.HTTP_201_CREATED)
def start_assessment(
    service: AssessmentDep, body: Annotated[StartIn | None, Body()] = None
) -> SessionState:
    """Create a new session (`mode` fixed or adaptive) and return its first question."""
    return service.start(body)


@router.get("/{session_id}", response_model=SessionState)
def get_assessment(
    session_id: str, service: AssessmentDep, index: int | None = Query(default=None, ge=0)
) -> SessionState:
    """Return session state and the question at `index` (default: current position)."""
    return service.get_state(session_id, index)


@router.post("/{session_id}/answer", response_model=AnswerSaved)
def save_answer(session_id: str, body: AnswerIn, service: AssessmentDep) -> AnswerSaved:
    """Save (or replace) the answer to one question."""
    return service.save_answer(session_id, body.question_id, body.answer)


@router.post("/{session_id}/next", response_model=SessionState)
async def next_question(
    session_id: str, service: AssessmentDep, evaluator: EvaluationDep
) -> SessionState:
    """Adaptive mode: grade the latest answer and serve the next question (or finish)."""
    return await service.next_question(session_id, evaluator)


@router.post("/{session_id}/evaluate-code", response_model=CodeResult)
def evaluate_code(session_id: str, body: CodeEvalIn, service: AssessmentDep) -> CodeResult:
    """Save a code answer and run it against the hidden tests in the sandbox."""
    return service.evaluate_code(session_id, body.question_id, body.code)


@router.post("/{session_id}/submit", response_model=ResultOut)
async def submit_assessment(
    session_id: str, service: AssessmentDep, evaluator: EvaluationDep
) -> ResultOut:
    """Finalise the session: score MCQs, evaluate open answers via the LLM, write feedback."""
    return await service.submit(session_id, evaluator)


@router.get("/{session_id}/result", response_model=ResultOut)
def get_result(session_id: str, service: AssessmentDep) -> ResultOut:
    """Return the final score, level and feedback."""
    return service.get_result(session_id)


@router.get("/{session_id}/review", response_model=ReviewOut)
def get_review(session_id: str, service: AssessmentDep) -> ReviewOut:
    """Return all answers with correctness and explanations."""
    return service.get_review(session_id)
