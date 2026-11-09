"""Display of code-question test results."""

from typing import Any

import streamlit as st


def _test_line(test: dict[str, Any]) -> str:
    label = f"Test {test['index']}" + ("" if test["visible"] else " (hidden)")
    return f"{'✅ Passed' if test['passed'] else '❌ Failed'}: {label}"


def render_code_result(result: dict[str, Any]) -> None:
    """Show pass/fail per test, details for visible tests, and any error message."""
    summary = f"Passed {result['passed']} of {result['total']} tests"
    if result["error_message"]:
        st.error(result["error_message"], icon=":material/error:")
    elif result["score"] >= 1.0:
        st.success(summary + ". Full marks.", icon=":material/check_circle:")
    else:
        st.warning(summary, icon=":material/warning:")
    for test in result["tests"]:
        st.markdown(_test_line(test))
        if not test["passed"] and test["visible"]:
            if test["error"]:
                st.caption(f"Error: {test['error']}")
            else:
                st.caption(
                    f"Input {test['input']} → expected {test['expected']}, got {test['actual']}"
                )
        elif not test["passed"] and test["error"]:
            st.caption(f"Error: {test['error']}")
