"""An existing database created before code questions must be upgraded in place."""

import sqlite3

from sqlalchemy import inspect
from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.db.seed import seed_questions
from app.db.session import init_db
from app.models import Question


def test_old_schema_gets_new_columns(tmp_path) -> None:
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE question (id VARCHAR PRIMARY KEY, type VARCHAR, topic VARCHAR,
              difficulty VARCHAR, text VARCHAR, options JSON, correct_answer VARCHAR,
              explanation VARCHAR, evaluation_criteria VARCHAR);
            CREATE TABLE answer (id INTEGER PRIMARY KEY, session_id VARCHAR, question_id VARCHAR,
              user_answer VARCHAR, is_correct BOOLEAN, llm_score FLOAT, llm_feedback VARCHAR);
            """
        )
    engine = create_engine(f"sqlite:///{path}")
    init_db(engine)
    columns = {c["name"] for c in inspect(engine).get_columns("question")}
    assert {"starter_code", "test_cases", "timeout_seconds", "points"} <= columns
    assert "code_result" in {c["name"] for c in inspect(engine).get_columns("answer")}
    with Session(engine) as session:
        seed_questions(session, settings.questions_path)
        code_questions = session.exec(select(Question).where(Question.type == "code")).all()
        assert len(code_questions) >= 3 and code_questions[0].test_cases


def test_old_session_rows_are_treated_as_fixed(tmp_path) -> None:
    from fastapi.testclient import TestClient

    from app.api.deps import get_evaluation_service  # noqa: F401
    from app.db.session import get_session
    from app.main import app

    path = tmp_path / "old_sessions.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE assessmentsession (id VARCHAR PRIMARY KEY, created_at DATETIME,
              status VARCHAR, current_question_index INTEGER, question_ids JSON);
            INSERT INTO assessmentsession VALUES
              ('old1', '2025-01-01 00:00:00', 'in_progress', 0, '["q01"]');
            """
        )
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    init_db(engine)
    with Session(engine) as session:
        seed_questions(session, settings.questions_path)

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override
    try:
        state = TestClient(app).get("/assessment/old1").json()
    finally:
        app.dependency_overrides.clear()
    assert state["mode"] == "fixed" and state["max_questions"] is None
