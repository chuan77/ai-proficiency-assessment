"""Results page."""

from typing import Any

import streamlit as st

LEVEL_COLORS = {
    "Beginner": "red",
    "Intermediate": "orange",
    "Advanced": "green",
    "Expert": "blue",
}


def render_skill_breakdown(topic_scores: list[dict[str, Any]]) -> None:
    """Show one labelled progress bar per topic, weakest first."""
    if not topic_scores:
        return
    st.subheader("Skill breakdown")
    for topic in sorted(topic_scores, key=lambda t: t["score_percent"]):
        level = topic.get("level", "")
        color = LEVEL_COLORS.get(level, "gray")
        total = topic.get("questions_total")
        counts = f" · {topic['questions_answered']}/{total} answered" if total else ""
        st.markdown(f"**{topic['topic']}** — {topic['score_percent']}% :{color}[{level}]{counts}")
        st.progress(topic["score_percent"] / 100)


def render_results(result: dict[str, Any]) -> None:
    """Show score, level, topic breakdown and feedback."""
    st.header("Your result")
    left, right = st.columns(2)
    left.metric("Score", f"{result['total_score']} / 100")
    right.metric("Proficiency level", result["proficiency_level"])
    st.write(
        f"Multiple choice: **{result['mcq_correct']} of {result['mcq_total']}** correct."
        + (
            f" Open-ended average: **{result['open_average']} / 10**."
            if result["open_average"] is not None
            else ""
        )
    )
    if result.get("code_total"):
        st.write(
            f"Code questions fully passed: **{result['code_passed']} of {result['code_total']}**."
        )
    render_skill_breakdown(result.get("topic_scores", []))
    st.subheader("Feedback")
    st.write(result["feedback_text"])
