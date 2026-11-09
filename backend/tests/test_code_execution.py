"""Tests for the sandboxed code runner."""

import pytest

from app.core.config import settings
from app.services.code_execution import entry_point_from, run_submission

STARTER = "def is_palindrome(s: str) -> bool:\n    pass"
CASES = [
    {"input": ["racecar"], "expected": True, "visible": True},
    {"input": ["hello"], "expected": False},
    {"input": ["A man a plan a canal Panama"], "expected": True},
]
GOOD = (
    "import re\n"
    "def is_palindrome(s):\n"
    "    t = re.sub(r'[^a-z0-9]', '', s.lower())\n"
    "    return t == t[::-1]\n"
)


def _run(code: str, timeout: float = 3):
    return run_submission(code, STARTER, CASES, timeout)


def test_entry_point_detection() -> None:
    assert entry_point_from(STARTER) == "is_palindrome"
    with pytest.raises(ValueError):
        entry_point_from("x = 1")


def test_correct_code_gets_full_score() -> None:
    result = _run(GOOD)
    assert (result.passed, result.total, result.score) == (3, 3, 1.0)
    assert result.error_message is None


def test_wrong_code_scores_zero_and_reports_failures() -> None:
    result = _run("def is_palindrome(s):\n    return s == s[::-1]")
    assert result.passed == 2 and result.score == 0.0
    assert [t.passed for t in result.tests] == [True, True, False]


def test_partial_credit_is_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "code_partial_credit", True)
    assert _run("def is_palindrome(s):\n    return s == s[::-1]").score == pytest.approx(
        0.6667, abs=1e-3
    )


def test_hidden_tests_hide_details_visible_show_them() -> None:
    result = _run("def is_palindrome(s):\n    return False")
    visible, hidden = result.tests[0], result.tests[1]
    assert (
        visible.input == '["racecar"]' and visible.expected == "true" and visible.actual == "false"
    )
    assert hidden.input is None and hidden.expected is None and hidden.actual is None


def test_syntax_error_message() -> None:
    result = _run("def is_palindrome(s:\n    return True")
    assert result.score == 0.0 and result.error_message.startswith("SyntaxError")
    assert result.tests == []


def test_empty_code() -> None:
    assert _run("   \n").error_message == "No code was submitted."


def test_missing_function() -> None:
    assert "was not found" in _run("def other(s):\n    return True").error_message


def test_runtime_error_in_function_is_reported_per_test() -> None:
    result = _run("def is_palindrome(s):\n    return 1 / 0")
    assert result.score == 0.0
    assert all(t.passed is False for t in result.tests)
    assert "ZeroDivisionError" in (result.tests[1].error or "")


def test_error_at_import_time() -> None:
    result = _run("raise ValueError('boom')\ndef is_palindrome(s): return True")
    assert "ValueError: boom" in result.error_message


def test_infinite_loop_times_out_quickly() -> None:
    result = _run("def is_palindrome(s):\n    while True:\n        pass", timeout=1)
    assert "Time limit exceeded" in result.error_message and result.score == 0.0


@pytest.mark.parametrize(
    "code",
    [
        "import os\ndef is_palindrome(s): return True",
        "import subprocess\ndef is_palindrome(s): return True",
        "import socket\ndef is_palindrome(s): return True",
        "from sys import modules\ndef is_palindrome(s): return True",
        "__import__('os')\ndef is_palindrome(s): return True",
    ],
)
def test_dangerous_imports_are_blocked(code: str) -> None:
    result = _run(code)
    assert result.score == 0.0 and "not allowed" in result.error_message


def test_file_access_is_blocked() -> None:
    result = _run("def is_palindrome(s):\n    return open('/etc/hosts').read() == ''")
    assert result.score == 0.0
    assert "open" in (result.tests[1].error or "")


def test_audit_hook_blocks_escape_via_object_subclasses(tmp_path) -> None:
    marker = tmp_path / "pwned"
    code = (
        "def is_palindrome(s):\n"
        "    c = [c for c in ().__class__.__base__.__subclasses__() if c.__name__ == '_wrap_close'][0]\n"
        f"    c.__init__.__globals__['system']('touch {marker}')\n"
        "    return True\n"
    )
    result = _run(code)
    assert not marker.exists()
    assert result.score == 0.0
    assert "not allowed" in (result.tests[1].error or "")


def test_printing_cannot_forge_a_result() -> None:
    code = (
        "def is_palindrome(s):\n"
        '    print(\'@@SANDBOX_RESULT@@{"error": null, "tests": []}\')\n'
        "    return False\n"
    )
    result = _run(code)
    assert result.score == 0.0 and result.passed == 1  # only the 'hello' case is False


def test_each_run_is_isolated() -> None:
    assert _run("def is_palindrome(s):\n    return True").passed == 2
    assert _run(GOOD).score == 1.0
