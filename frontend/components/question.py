"""Question page widgets."""

from typing import Any

import streamlit as st

MAX_ANSWER_LENGTH = 4000
CODE_HINT = (
    "Write Python 3 code and keep the function name. Standard-library helpers such as re, "
    "math, collections and itertools can be imported; file, network and system access are "
    "blocked. Use Run tests to check your code before moving on."
)


def render_progress(state: dict[str, Any]) -> None:
    """Show 'Question N of M' plus a progress bar of answered questions."""
    adaptive = state.get("mode") == "adaptive"
    total = state.get("max_questions") if adaptive else state["total_questions"]
    number = state["question"]["index"] + 1
    answered = len(state["answered_question_ids"])
    if adaptive:
        st.progress(
            min(answered / total, 1.0),
            text=f"{answered} answered · up to {total} questions, may finish earlier",
        )
        difficulty = str(state["question"].get("difficulty") or "").capitalize()
        st.caption(
            f"Question {number} of up to {total} · {state['question']['topic']}"
            f" · Difficulty: {difficulty}"
        )
        return
    st.progress(answered / total, text=f"{answered} of {total} answered")
    st.caption(f"Question {number} of {total} · {state['question']['topic']}")


def render_question(state: dict[str, Any]) -> str | None:
    """Render the input for the current question; returns the entered answer or None."""
    question = state["question"]
    saved = state.get("saved_answer")
    key = f"answer_{question['id']}"
    if question["type"] == "mcq":
        options: list[str] = question["options"]
        index = options.index(saved) if saved in options else None
        return st.radio(question["text"], options, index=index, key=key)
    if question["type"] == "code":
        st.caption(CODE_HINT)
        return st.text_area(
            question["text"],
            value=saved if saved is not None else question.get("starter_code", ""),
            height=300,
            max_chars=MAX_ANSWER_LENGTH,
            key=key,
        )
    return st.text_area(
        question["text"],
        value=saved or "",
        height=220,
        max_chars=MAX_ANSWER_LENGTH,
        key=key,
        help="Write a clear, specific answer. It will be evaluated by a local AI model.",
    )
