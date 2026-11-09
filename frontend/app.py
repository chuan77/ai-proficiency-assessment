"""Streamlit UI: Start -> Questions -> Results -> Review.

Run from the repo root:  streamlit run frontend/app.py
All logic lives in the backend; this file only renders and calls the API.
"""

from typing import Any, NamedTuple

import streamlit as st

from api_client import ApiError, BackendClient
from components.code_feedback import render_code_result
from components.question import render_progress, render_question
from components.results import render_results
from components.review import render_review

st.set_page_config(page_title="AI Proficiency Assessment", page_icon="🧠", layout="centered")
client = BackendClient()


def _goto(view: str, index: int | None = None) -> None:
    st.session_state["view"] = view
    if index is not None:
        st.session_state["index"] = index


def _set_session(session_id: str) -> None:
    st.session_state["session_id"] = session_id
    st.query_params["session"] = session_id


def _resume_from_url() -> None:
    """Restore an in-progress or finished session after a page refresh."""
    session_id = st.query_params.get("session")
    if "session_id" in st.session_state or not session_id:
        return
    try:
        state = client.get_state(session_id)
    except ApiError:
        st.query_params.clear()
        return
    st.session_state["session_id"] = session_id
    st.session_state["index"] = state["current_question_index"]
    st.session_state["view"] = "result" if state["status"] == "completed" else "question"


def start_page() -> None:
    """Landing page with the Start button."""
    st.title("AI Proficiency Assessment")
    st.write(
        "Test your practical understanding of working with AI. You will answer "
        "multiple-choice and open-ended questions on fundamentals, prompt engineering, "
        "limitations and risks, and practical application. It takes under 20 minutes, "
        "and your answers stay on this computer."
    )
    choice = st.radio(
        "Assessment type",
        ["Classic", "Adaptive"],
        captions=[
            "A fixed set of questions you can move back and forth through.",
            (
                "Question difficulty adapts to your answers. You cannot go back, and it "
                "may finish early once your level is clear."
            ),
        ],
    )
    if st.button("Start assessment", type="primary"):
        try:
            state = client.start("adaptive" if choice == "Adaptive" else "fixed")
        except ApiError as exc:
            st.error(str(exc))
            return
        _set_session(state["session_id"])
        _goto("question", 0)
        st.rerun()


def _save_if_answered(
    session_id: str, question: dict[str, Any], answer: str | None, saved: str | None
) -> bool:
    """Persist the answer when it changed. Returns False if saving failed."""
    if not answer or not answer.strip():
        return True
    if question["type"] == "code":
        answer = answer.strip("\n")
        if saved is None and answer.strip() == (question.get("starter_code") or "").strip():
            return True  # untouched starter code is not an answer
    if answer == saved:
        return True
    try:
        client.save_answer(session_id, question["id"], answer)
    except ApiError as exc:
        st.error(str(exc))
        return False
    return True


class _Clicks(NamedTuple):
    prev: bool
    run: bool
    next: bool


def _nav_buttons(state: dict[str, Any]) -> _Clicks:
    """Render Previous / (Run tests) / Next-or-Submit inside the question form."""
    question = state["question"]
    adaptive = state.get("mode") == "adaptive"
    index, total = question["index"], state["total_questions"]
    is_code = question["type"] == "code"
    columns = st.columns(3 if is_code else 2)
    prev = columns[0].form_submit_button("← Previous", disabled=adaptive or index == 0)
    run = False
    if is_code:
        run = columns[1].form_submit_button("Run tests", icon=":material/play_arrow:")
    if adaptive:
        label = "Continue →"
    else:
        label = "Submit assessment" if index == total - 1 else "Next →"
    return _Clicks(prev, run, columns[-1].form_submit_button(label, type="primary"))


def _run_code(session_id: str, question_id: str, code: str | None) -> dict[str, Any] | None:
    """Save the code and run it against the tests; returns the result or None."""
    if not code or not code.strip():
        st.warning("Write some code first.")
        return None
    with st.spinner("Running your code…"):
        try:
            return client.evaluate_code(session_id, question_id, code.strip("\n"))
        except ApiError as exc:
            st.error(str(exc))
            return None


def question_page() -> None:
    """Show one question with navigation and progress."""
    session_id = st.session_state["session_id"]
    try:
        state = client.get_state(session_id, st.session_state.get("index", 0))
    except ApiError as exc:
        st.error(str(exc))
        return
    st.title("AI Proficiency Assessment")
    render_progress(state)
    question = state["question"]
    # A form sends the typed answer and the button click together, so the first click
    # on Previous/Next/Submit is never swallowed by the text area losing focus.
    with st.form(key=f"form_{question['id']}", border=False):
        answer = render_question(state)
        clicks = _nav_buttons(state)
    code_result = state.get("saved_code_result")
    if clicks.run:
        code_result = _run_code(session_id, question["id"], answer) or code_result
    if question["type"] == "code" and code_result:
        render_code_result(code_result)
    if clicks.prev or clicks.next:
        _navigate(session_id, state, answer, going_back=clicks.prev)


def _navigate(
    session_id: str, state: dict[str, Any], answer: str | None, *, going_back: bool
) -> None:
    question = state["question"]
    index, total = question["index"], state["total_questions"]
    if not _save_if_answered(session_id, question, answer, state["saved_answer"]):
        return
    if state.get("mode") == "adaptive":
        _adaptive_next(session_id)
    elif going_back:
        _goto("question", index - 1)
        st.rerun()
    elif index == total - 1:
        _submit(session_id)
    else:
        _goto("question", index + 1)
        st.rerun()


def _adaptive_next(session_id: str) -> None:
    """Grade the answer and either show the next question or finish the assessment."""
    with st.spinner("Choosing your next question…"):
        try:
            state = client.next_question(session_id)
        except ApiError as exc:
            st.error(str(exc))
            return
    if state["ready_to_submit"]:
        _submit(session_id)
    else:
        _goto("question", state["question"]["index"])
        st.rerun()


def _submit(session_id: str) -> None:
    with st.spinner("Evaluating your answers with the local AI model. This can take a minute…"):
        try:
            client.submit(session_id)
        except ApiError as exc:
            st.error(str(exc))
            return
    _goto("result")
    st.rerun()


def result_page() -> None:
    """Results with a link to the review."""
    try:
        result = client.get_result(st.session_state["session_id"])
    except ApiError as exc:
        st.error(str(exc))
        return
    render_results(result)
    if result.get("mode") == "adaptive":
        st.info(
            f"This adaptive assessment ended after {result['questions_answered']} questions "
            "because your level became clear. Harder questions count for more in your score."
        )
    if st.button("Review my answers"):
        _goto("review")
        st.rerun()
    if st.button("Start a new assessment"):
        _reset()


def review_page() -> None:
    """Answer review."""
    try:
        review = client.get_review(st.session_state["session_id"])
    except ApiError as exc:
        st.error(str(exc))
        return
    render_review(review)
    if st.button("← Back to results"):
        _goto("result")
        st.rerun()


def _reset() -> None:
    for key in ("session_id", "index", "view"):
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.rerun()


def main() -> None:
    """Route to the current view."""
    _resume_from_url()
    view = st.session_state.get("view", "start")
    {"start": start_page, "question": question_page, "result": result_page, "review": review_page}[
        view
    ]()


main()
