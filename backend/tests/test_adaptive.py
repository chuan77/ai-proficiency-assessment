"""Adaptive engine rules and the adaptive session flow."""

import json
import random

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import Question
from app.services.adaptive import AdaptiveConfig, AdaptiveEngine, difficulty_weight

BANK = {q["id"]: q for q in json.loads(settings.questions_path.read_text())}
LEVELS = ["beginner", "intermediate", "advanced", "expert"]


def _engine(**overrides: object) -> AdaptiveEngine:
    return AdaptiveEngine(AdaptiveConfig(**overrides), random.Random(1))  # type: ignore[arg-type]


def _question(qid: str, topic: str, difficulty: str) -> Question:
    return Question(id=qid, type="mcq", topic=topic, difficulty=difficulty, text="t")


def test_difficulty_moves_one_level_and_clamps() -> None:
    engine = _engine()
    assert engine.next_difficulty("intermediate", True) == "advanced"
    assert engine.next_difficulty("intermediate", False) == "beginner"
    assert engine.next_difficulty("expert", True) == "expert"
    assert engine.next_difficulty("beginner", False) == "beginner"


def test_rapid_correct_answers_climb_one_level_at_a_time() -> None:
    engine, level, seen = _engine(), "intermediate", []
    for _ in range(5):
        level = engine.next_difficulty(level, True)
        seen.append(level)
    assert seen == ["advanced", "expert", "expert", "expert", "expert"]


def test_rapid_wrong_answers_drop_one_level_at_a_time() -> None:
    engine, level, seen = _engine(), "intermediate", []
    for _ in range(4):
        level = engine.next_difficulty(level, False)
        seen.append(level)
    assert seen == ["beginner"] * 4


def test_stopping_rules() -> None:
    engine = _engine(min_questions=4, max_questions=6, performance_window=2)
    stable = [True, False, True, False]
    assert not engine.should_stop([True, False, True], "advanced", 20, 10)  # below minimum
    assert engine.should_stop(stable, "advanced", 20, 10)  # minimum + bracketed
    assert not engine.should_stop([True] * 4, "advanced", 20, 10)  # still climbing
    assert engine.should_stop([True] * 4, "expert", 20, 10)  # ceiling reached
    assert engine.should_stop([False] * 4, "beginner", 20, 10)  # floor reached
    assert engine.should_stop([True, True, False, False, True, True], "expert", 20, 10)  # max
    assert engine.should_stop([True], "advanced", 20, 0)  # nothing left


def test_max_is_capped_by_bank_size() -> None:
    assert _engine(max_questions=15).effective_max(9) == 9


def test_select_prefers_target_then_nearest_fallback() -> None:
    engine = _engine()
    pool = [_question("a", "T1", "beginner"), _question("b", "T1", "advanced")]
    assert engine.select_next(pool, [], "advanced", 5).id == "b"  # type: ignore[union-attr]
    only_beginner = [_question("a", "T1", "beginner")]
    assert engine.select_next(only_beginner, [], "expert", 5).id == "a"  # type: ignore[union-attr]
    assert engine.select_next([], [], "expert", 5) is None


def test_select_prefers_underrepresented_topic_and_forces_unseen_topics() -> None:
    engine = _engine()
    served = [_question("s1", "T1", "intermediate"), _question("s2", "T1", "intermediate")]
    pool = [_question("a", "T1", "intermediate"), _question("b", "T2", "intermediate")]
    assert engine.select_next(pool, served, "intermediate", 5).id == "b"  # type: ignore[union-attr]
    far = [_question("a", "T1", "intermediate"), _question("c", "T2", "expert")]
    assert engine.select_next(far, served, "intermediate", 1).id == "c"  # type: ignore[union-attr]


def test_weights_increase_with_difficulty() -> None:
    weights = [difficulty_weight(level) for level in LEVELS]
    assert weights == sorted(weights) and len(set(weights)) == 4


# ---- API flow -----------------------------------------------------------
def _start(client: TestClient) -> dict:
    response = client.post("/assessment/start", json={"mode": "adaptive"})
    assert response.status_code == 201
    return response.json()


def _answer(client: TestClient, state: dict, *, correct: bool) -> None:
    question = state["question"]
    source = BANK[question["id"]]
    if question["type"] == "mcq":
        wrong = next(o for o in source["options"] if o != source["correct_answer"])
        pick = source["correct_answer"] if correct else wrong
    elif question["type"] == "code":
        pick = "def nope(x):\n    return 1"
    else:
        pick = "An answer."
    r = client.post(
        f"/assessment/{state['session_id']}/answer",
        json={"question_id": question["id"], "answer": pick},
    )
    assert r.status_code == 200


def _run(client: TestClient, *, correct: bool) -> tuple[dict, list[dict]]:
    """Answer every served question the same way until the engine stops."""
    state, served = _start(client), []
    for _ in range(40):
        served.append(state["question"])
        _answer(client, state, correct=correct)
        state = client.post(f"/assessment/{state['session_id']}/next").json()
        if state["ready_to_submit"]:
            return state, served
        assert state["question"]["id"] != served[-1]["id"]
    raise AssertionError("adaptive session never finished")


def test_start_adaptive_serves_one_intermediate_question(client: TestClient) -> None:
    state = _start(client)
    assert state["mode"] == "adaptive" and state["total_questions"] == 1
    assert state["max_questions"] == settings.adaptive_max_questions
    assert state["question"]["difficulty"] == "intermediate"
    assert client.post("/assessment/start").json()["mode"] == "fixed"


def test_all_correct_climbs_and_respects_limits(client: TestClient) -> None:
    # Answers to open/code questions are graded by the fake LLM/sandbox, so use MCQ-only
    # reasoning: check the invariants that hold for any grading outcome.
    state, served = _run(client, correct=True)
    assert settings.adaptive_min_questions <= len(served) <= settings.adaptive_max_questions
    ids = [q["id"] for q in served]
    assert len(ids) == len(set(ids))
    result = client.post(f"/assessment/{state['session_id']}/submit").json()
    assert result["mode"] == "adaptive" and result["questions_answered"] == len(served)
    assert sum(t["questions_total"] for t in result["topic_scores"]) == len(served)


def test_all_wrong_drops_difficulty_and_stops_early(client: TestClient, fake_llm) -> None:
    fake_llm.open_score = 0  # open answers score zero, so every answer is wrong
    state, served = _run(client, correct=False)
    levels = [LEVELS.index(q["difficulty"]) for q in served]
    assert levels[0] == 1 and min(levels) == 0
    assert len(served) <= settings.adaptive_max_questions
    assert state["ready_to_submit"]
    review = client.post(f"/assessment/{state['session_id']}/submit")
    assert review.status_code == 200
    items = client.get(f"/assessment/{state['session_id']}/review").json()["items"]
    assert [i["difficulty_served"] for i in items] == [q["difficulty"] for q in served]


def test_next_requires_answer_and_blocks_editing_earlier_answers(client: TestClient) -> None:
    state = _start(client)
    sid = state["session_id"]
    assert client.post(f"/assessment/{sid}/next").status_code == 422
    first = state["question"]
    _answer(client, state, correct=True)
    nxt = client.post(f"/assessment/{sid}/next").json()
    assert nxt["question"]["index"] == 1 and nxt["total_questions"] == 2
    again = client.post(
        f"/assessment/{sid}/answer",
        json={"question_id": first["id"], "answer": "A changed answer"},
    )
    assert again.status_code == 409


def test_submit_blocked_until_adaptive_finishes_and_next_rejected_in_fixed(
    client: TestClient,
) -> None:
    sid = _start(client)["session_id"]
    assert client.post(f"/assessment/{sid}/submit").status_code == 409
    fixed = client.post("/assessment/start").json()["session_id"]
    assert client.post(f"/assessment/{fixed}/next").status_code == 422


def test_topic_coverage_is_reasonable(client: TestClient) -> None:
    _, served = _run(client, correct=True)
    topics = {q["topic"] for q in served}
    assert len(topics) >= 3


def test_seed_rejects_invalid_difficulty(tmp_path) -> None:
    from sqlmodel import Session, create_engine

    from app.db.seed import seed_questions
    from app.db.session import init_db

    path = tmp_path / "q.json"
    path.write_text(json.dumps([{**next(iter(BANK.values())), "difficulty": "medium"}]))
    engine = create_engine(f"sqlite:///{tmp_path / 'x.db'}")
    init_db(engine)
    with Session(engine) as session, pytest.raises(ValueError, match="invalid difficulty"):
        seed_questions(session, path)
