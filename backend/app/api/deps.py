"""FastAPI dependencies wiring services together."""

from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.core.llm import LLMClient, get_llm_client
from app.db.session import get_session
from app.services.assessment import AssessmentService
from app.services.evaluation import EvaluationService

SessionDep = Annotated[Session, Depends(get_session)]
LLMDep = Annotated[LLMClient, Depends(get_llm_client)]


def get_assessment_service(db: SessionDep) -> AssessmentService:
    """Build the assessment service for one request."""
    return AssessmentService(db)


def get_evaluation_service(llm: LLMDep) -> EvaluationService:
    """Build the evaluation service for one request."""
    return EvaluationService(llm)


AssessmentDep = Annotated[AssessmentService, Depends(get_assessment_service)]
EvaluationDep = Annotated[EvaluationService, Depends(get_evaluation_service)]
