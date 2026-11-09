"""FastAPI application entry point.

Run from the backend/ directory:  uvicorn app.main:app --port 8000
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session

from app.api.errors import register_error_handlers
from app.api.routes.assessment import router as assessment_router
from app.core.config import settings
from app.db.seed import seed_questions
from app.db.session import engine, init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create tables and load the question bank on startup."""
    init_db()
    with Session(engine) as session:
        seed_questions(session, settings.questions_path)
    yield


app = FastAPI(title="AI Proficiency Assessment", lifespan=lifespan)
register_error_handlers(app)
app.include_router(assessment_router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
