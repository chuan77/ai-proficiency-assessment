"""API and end-to-end tests using a fake LLM."""

import json

from fastapi.testclient import TestClient

from app.core.config import settings

BANK = {q["id"]: q for q in json.loads(settings.questions_path.read_text())}


SOLUTIONS = {
    "q21": "def is_palindrome(s):\n    t = [c.lower() for c in s if c.isalnum()]\n    return t == t[::-1]",
    "q22": (
        "from collections import Counter\n"
        "def are_anagrams(str1, str2):\n"
        "    f = lambda x: Counter(x.replace(' ', '').lower())\n"
        "    return f(str1) == f(str2)"
    ),
    "q23": (
        "import re\nfrom collections import Counter\n"
        "def most_common_word(text):\n"
        "    c = Counter(re.findall(r'[a-z0-9]+', text.lower()))\n"
        "    return min(c, key=lambda w: (-c[w], w))"
    ),
}
WRONG_CODE = "def nope(x):\n    return 1"


def _start(client: TestClient) -> dict:
    response = client.post("/assessment/start")
    assert response.status_code == 201
    return response.json()


def _answer_all(client: TestClient, session_id: str, *, correct: bool) -> None:
    total = client.get(f"/assessment/{session_id}").json()["total_questions"]
    for index in range(total):
        question = client.get(f"/assessment/{session_id}", params={"index": index}).json()[
            "question"
        ]
        source = BANK[question["id"]]
        if question["type"] == "mcq":
            options = source["options"]
            pick = (
                source["correct_answer"]
                if correct
                else next(o for o in options if o != source["correct_answer"])
            )
        elif question["type"] == "code":
            pick = SOLUTIONS[question["id"]] if correct else WRONG_CODE
        else:
            pick = "A detailed, specific answer."
        r = client.post(
            f"/assessment/{session_id}/answer", json={"question_id": question["id"], "answer": pick}
        )
        assert r.status_code == 200


def test_start_hides_correct_answer(client: TestClient) -> None:
    state = _start(client)
    assert state["total_questions"] == settings.questions_per_session == 10
    assert state["question"]["index"] == 0
    assert "correct_answer" not in state["question"]


def test_full_flow_all_correct(client: TestClient, fake_llm) -> None:
    session_id = _start(client)["session_id"]
    _answer_all(client, session_id, correct=True)
    result = client.post(f"/assessment/{session_id}/submit")
    assert result.status_code == 200
    body = result.json()
    review = client.get(f"/assessment/{session_id}/review").json()["items"]
    total = len(review)
    open_count = sum(1 for i in review if i["type"] == "open")
    code_count = sum(1 for i in review if i["type"] == "code")
    mcq_count = total - open_count - code_count
    assert total == 10 and open_count > 0 and mcq_count > 0 and code_count >= 1
    assert body["mcq_correct"] == body["mcq_total"] == mcq_count
    assert body["open_average"] == 8.0
    assert body["code_passed"] == body["code_total"] == code_count
    expected = round((mcq_count + open_count * 0.8 + code_count) / total * 100, 1)
    assert body["total_score"] == expected
    assert body["proficiency_level"] == "Expert"
    assert body["feedback_text"] == "You did well overall."
    assert client.get(f"/assessment/{session_id}/result").json() == body

    assert all(i["is_correct"] for i in review if i["type"] == "mcq")
    assert all(i["llm_feedback"] == "Good structure." for i in review if i["type"] == "open")


def test_all_wrong_mcq_scores_zero_for_mcq(client: TestClient) -> None:
    session_id = _start(client)["session_id"]
    _answer_all(client, session_id, correct=False)
    body = client.post(f"/assessment/{session_id}/submit").json()
    assert body["mcq_correct"] == 0


def test_unanswered_questions_score_zero(client: TestClient, fake_llm) -> None:
    session_id = _start(client)["session_id"]
    body = client.post(f"/assessment/{session_id}/submit").json()
    assert body["total_score"] == 0.0
    assert body["proficiency_level"] == "Beginner"
    assert not any("Respond with ONLY a JSON object" in c for c in fake_llm.calls)


def test_submit_is_idempotent(client: TestClient, fake_llm) -> None:
    session_id = _start(client)["session_id"]
    _answer_all(client, session_id, correct=True)
    first = client.post(f"/assessment/{session_id}/submit").json()
    calls = len(fake_llm.calls)
    assert client.post(f"/assessment/{session_id}/submit").json() == first
    assert len(fake_llm.calls) == calls


def test_navigation_and_saved_answer(client: TestClient) -> None:
    state = _start(client)
    sid, first = state["session_id"], state["question"]
    client.post(
        f"/assessment/{sid}/answer",
        json={"question_id": first["id"], "answer": first["options"][0]},
    )
    again = client.get(f"/assessment/{sid}", params={"index": 0}).json()
    assert again["saved_answer"] == first["options"][0]
    assert again["answered_question_ids"] == [first["id"]]
    assert client.get(f"/assessment/{sid}", params={"index": 999}).status_code == 404


def test_answer_can_be_replaced(client: TestClient) -> None:
    state = _start(client)
    sid, q = state["session_id"], state["question"]
    for option in q["options"][:2]:
        client.post(f"/assessment/{sid}/answer", json={"question_id": q["id"], "answer": option})
    saved = client.get(f"/assessment/{sid}", params={"index": 0}).json()
    assert saved["saved_answer"] == q["options"][1]
    assert len(saved["answered_question_ids"]) == 1


def test_validation_errors(client: TestClient) -> None:
    state = _start(client)
    sid, q = state["session_id"], state["question"]
    post = lambda body: client.post(f"/assessment/{sid}/answer", json=body)
    assert post({"question_id": q["id"], "answer": ""}).status_code == 422
    assert post({"question_id": q["id"], "answer": "   "}).status_code == 422
    assert post({"question_id": q["id"], "answer": "not an option"}).status_code == 422
    assert post({"question_id": q["id"], "answer": "x" * 4001}).status_code == 422
    assert post({"question_id": "nope", "answer": "x"}).status_code == 404


def test_not_found_and_conflict(client: TestClient) -> None:
    assert client.get("/assessment/missing").status_code == 404
    assert client.post("/assessment/missing/submit").status_code == 404
    sid = _start(client)["session_id"]
    assert client.get(f"/assessment/{sid}/result").status_code == 409
    assert client.get(f"/assessment/{sid}/review").status_code == 409
    client.post(f"/assessment/{sid}/submit")
    q = client.get(f"/assessment/{sid}").json()["question"]
    r = client.post(f"/assessment/{sid}/answer", json={"question_id": q["id"], "answer": "x"})
    assert r.status_code == 409


def test_llm_down_returns_503_and_allows_retry(client: TestClient, fake_llm) -> None:
    sid = _start(client)["session_id"]
    _answer_all(client, sid, correct=True)
    fake_llm.fail = True
    assert client.post(f"/assessment/{sid}/submit").status_code == 503
    assert client.get(f"/assessment/{sid}/result").status_code == 409
    fake_llm.fail = False
    assert client.post(f"/assessment/{sid}/submit").status_code == 200


def test_feedback_falls_back_when_llm_fails_only_for_feedback(client: TestClient, fake_llm) -> None:
    sid = _start(client)["session_id"]
    _answer_all(client, sid, correct=True)
    original = fake_llm.chat

    async def flaky(system: str, user: str) -> str:
        if "AI-skills coach" in user:
            fake_llm.fail = True
        return await original(system, user)

    fake_llm.chat = flaky  # type: ignore[method-assign]
    body = client.post(f"/assessment/{sid}/submit").json()
    assert "strongest topic" in body["feedback_text"]


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_concurrent_submit_does_not_crash(client: TestClient) -> None:
    """Two submits racing (e.g. double click) must both succeed with one result."""
    from concurrent.futures import ThreadPoolExecutor

    sid = _start(client)["session_id"]
    _answer_all(client, sid, correct=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: client.post(f"/assessment/{sid}/submit"), range(2)))
    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].json()["total_score"] == responses[1].json()["total_score"]


def _code_question(client: TestClient, sid: str) -> dict:
    total = client.get(f"/assessment/{sid}").json()["total_questions"]
    for index in range(total):
        question = client.get(f"/assessment/{sid}", params={"index": index}).json()["question"]
        if question["type"] == "code":
            return question
    raise AssertionError("session has no code question")


def test_every_session_has_a_code_question_with_starter(client: TestClient) -> None:
    for _ in range(5):
        question = _code_question(client, _start(client)["session_id"])
        assert "def " in question["starter_code"]
        assert "test_cases" not in question


def _evaluate(client: TestClient, sid: str, qid: str, code: str):
    return client.post(f"/assessment/{sid}/evaluate-code", json={"question_id": qid, "code": code})


def test_evaluate_code_correct_and_incorrect(client: TestClient) -> None:
    sid = _start(client)["session_id"]
    question = _code_question(client, sid)
    good = _evaluate(client, sid, question["id"], SOLUTIONS[question["id"]]).json()
    assert (
        good["score"] == 1.0 and good["passed"] == good["total"] and good["error_message"] is None
    )
    bad = _evaluate(client, sid, question["id"], WRONG_CODE).json()
    assert bad["score"] == 0.0
    assert "was not found" in bad["error_message"]


def test_hidden_tests_do_not_leak(client: TestClient) -> None:
    sid = _start(client)["session_id"]
    question = _code_question(client, sid)
    always_false = "def {}(*a):\n    return False".format(
        question["starter_code"].split("(")[0].replace("def ", "")
    )
    result = _evaluate(client, sid, question["id"], always_false).json()
    hidden = [t for t in result["tests"] if not t["visible"]]
    shown = [t for t in result["tests"] if t["visible"]]
    assert hidden and shown
    assert all(t["input"] is None and t["expected"] is None and t["actual"] is None for t in hidden)
    assert all(t["input"] and t["expected"] for t in shown)


def test_code_answer_is_saved_and_returned_with_result(client: TestClient) -> None:
    sid = _start(client)["session_id"]
    question = _code_question(client, sid)
    _evaluate(client, sid, question["id"], SOLUTIONS[question["id"]])
    state = client.get(f"/assessment/{sid}", params={"index": question["index"]}).json()
    assert state["saved_answer"] == SOLUTIONS[question["id"]]
    assert state["saved_code_result"]["score"] == 1.0
    client.post(
        f"/assessment/{sid}/answer",
        json={"question_id": question["id"], "answer": WRONG_CODE},
    )
    state = client.get(f"/assessment/{sid}", params={"index": question["index"]}).json()
    assert state["saved_code_result"] is None  # editing invalidates the old run


def test_submit_evaluates_unrun_code_and_review_shows_result(client: TestClient) -> None:
    sid = _start(client)["session_id"]
    question = _code_question(client, sid)
    client.post(
        f"/assessment/{sid}/answer",
        json={"question_id": question["id"], "answer": SOLUTIONS[question["id"]]},
    )
    body = client.post(f"/assessment/{sid}/submit").json()
    assert body["code_passed"] == 1
    item = next(
        i for i in client.get(f"/assessment/{sid}/review").json()["items"] if i["type"] == "code"
    )
    assert item["is_correct"] is True and item["code_result"]["score"] == 1.0


def test_evaluate_code_errors(client: TestClient) -> None:
    state = _start(client)
    sid = state["session_id"]
    code_q = _code_question(client, sid)
    mcq = next(
        client.get(f"/assessment/{sid}", params={"index": i}).json()["question"]
        for i in range(10)
        if client.get(f"/assessment/{sid}", params={"index": i}).json()["question"]["type"] == "mcq"
    )
    assert _evaluate(client, sid, mcq["id"], "x = 1").status_code == 422
    assert _evaluate(client, sid, "nope", "x = 1").status_code == 404
    assert _evaluate(client, sid, code_q["id"], "   ").status_code == 422
    assert _evaluate(client, "missing", code_q["id"], "x").status_code == 404
    client.post(f"/assessment/{sid}/submit")
    assert _evaluate(client, sid, code_q["id"], "x = 1").status_code == 409


def test_result_has_topic_breakdown_with_code_questions(client: TestClient) -> None:
    session_id = _start(client)["session_id"]
    _answer_all(client, session_id, correct=True)
    body = client.post(f"/assessment/{session_id}/submit").json()
    topics = body["topic_scores"]
    assert topics and all(t["level"] and t["questions_total"] > 0 for t in topics)
    assert (
        sum(t["questions_total"] for t in topics)
        == client.get(f"/assessment/{session_id}").json()["total_questions"]
    )
    from app.services.scoring import proficiency_level

    assert all(t["level"] == proficiency_level(t["score_percent"]) for t in topics)
    assert all(t["earned_points"] <= t["max_points"] for t in topics)


def test_old_result_without_stored_topic_scores_is_recomputed(client: TestClient) -> None:
    from sqlmodel import Session, select

    from app.db.session import get_session
    from app.main import app
    from app.models import Result

    session_id = _start(client)["session_id"]
    _answer_all(client, session_id, correct=False)
    first = client.post(f"/assessment/{session_id}/submit").json()
    db: Session = next(app.dependency_overrides[get_session]())
    row = db.exec(select(Result).where(Result.session_id == session_id)).one()
    row.topic_scores = None
    db.add(row)
    db.commit()
    again = client.get(f"/assessment/{session_id}/result").json()
    assert again["topic_scores"] == first["topic_scores"]
