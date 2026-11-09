"""Shared fixtures: in-memory DB, fake LLM, and a TestClient."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.deps import get_evaluation_service
from app.core.config import settings
from app.db.seed import seed_questions
from app.db.session import get_session, init_db
from app.main import app
from app.services.evaluation import EvaluationService


class FakeLLM:
    """Stands in for LM Studio; records calls and returns canned replies."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.fail = False
        self.open_score = 8

    async def chat(self, system: str, user: str) -> str:
        from app.core.llm import LLMUnavailableError

        self.calls.append(user)
        if self.fail:
            raise LLMUnavailableError("down")
        if "Respond with ONLY a JSON object" in user:
            return f'Sure!\n{{"score": {self.open_score}, "feedback": "Good structure."}}'
        return "You did well overall."


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def client(fake_llm: FakeLLM, tmp_path: Path) -> Iterator[TestClient]:
    from sqlmodel import create_engine

    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    init_db(engine)
    with Session(engine) as session:
        seed_questions(session, settings.questions_path)

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_evaluation_service] = lambda: EvaluationService(fake_llm)  # type: ignore[arg-type]
    yield TestClient(app)
    app.dependency_overrides.clear()
