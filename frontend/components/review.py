"""Review page."""

from typing import Any

import streamlit as st

from components.code_feedback import render_code_result


def _status(item: dict[str, Any]) -> str:
    if item["type"] == "mcq":
        return "✅ Correct" if item["is_correct"] else "❌ Incorrect"
    if item["type"] == "code":
        return "✅ All tests passed" if item["is_correct"] else "❌ Tests failed"
    if item["llm_score"] is None:
        return "⚪ Not answered"
    return f"📝 Score {item['llm_score']:g} / 10"


def render_review(review: dict[str, Any]) -> None:
    """List every question with the user's answer and its evaluation."""
    st.header("Review your answers")
    for item in review["items"]:
        with st.expander(f"Q{item['index'] + 1}. {item['text']} — {_status(item)}"):
            st.markdown(f"**Topic:** {item['topic']}")
            if item["type"] == "code":
                st.markdown("**Your code:**")
                st.code(item["user_answer"] or "# No code submitted", language="python")
                if item["code_result"]:
                    render_code_result(item["code_result"])
            else:
                st.markdown(f"**Your answer:** {item['user_answer'] or 'No answer given'}")
            if item["type"] == "mcq":
                st.markdown(f"**Correct answer:** {item['correct_answer']}")
            if item["llm_feedback"]:
                st.markdown(f"**Feedback:** {item['llm_feedback']}")
            if item["explanation"]:
                st.markdown(f"**Explanation:** {item['explanation']}")
