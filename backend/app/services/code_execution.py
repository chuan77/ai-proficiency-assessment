"""Run a submitted Python function against test cases in a sandboxed subprocess."""

import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.schemas.code import CodeResult, TestOutcome

RUNNER_PATH = Path(__file__).with_name("sandbox_runner.py")
MARKER = "@@SANDBOX_RESULT@@"
STARTUP_SLACK_SECONDS = 1.0


def entry_point_from(starter_code: str) -> str:
    """Name of the first function defined in the starter code."""
    for node in ast.parse(starter_code).body:
        if isinstance(node, ast.FunctionDef):
            return node.name
    raise ValueError("starter_code must define a function")


def _failure(total: int, message: str) -> CodeResult:
    return CodeResult(passed=0, total=total, score=0.0, error_message=message)


def _spawn(payload: dict[str, Any], timeout: float) -> dict[str, Any] | str:
    """Run the child; returns its parsed result or an error message string."""
    with tempfile.TemporaryDirectory() as workdir:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-S", "-B", str(RUNNER_PATH)],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=timeout + STARTUP_SLACK_SECONDS,
                cwd=workdir,
                env={"PYTHONIOENCODING": "utf-8"},
                check=False,
            )
        except subprocess.TimeoutExpired:
            return f"Time limit exceeded ({timeout:g}s). Check for infinite loops."
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith(MARKER):
            return dict(json.loads(line[len(MARKER) :]))
    return "Your code crashed or exceeded the time or memory limit."


def _text(value: Any) -> str:
    return json.dumps(value)


def _build_outcomes(
    test_cases: list[dict[str, Any]], raw_tests: list[dict[str, Any]]
) -> list[TestOutcome]:
    outcomes: list[TestOutcome] = []
    for case, raw in zip(test_cases, raw_tests, strict=True):
        visible = bool(case.get("visible", False))
        outcomes.append(
            TestOutcome(
                index=raw["index"],
                passed=raw["passed"],
                visible=visible,
                input=_text(case["input"]) if visible else None,
                expected=_text(case["expected"]) if visible else None,
                actual=raw["actual"] if visible else None,
                error=raw["error"] if visible or raw["error"] else None,
            )
        )
    return outcomes


def run_submission(
    code: str,
    starter_code: str,
    test_cases: list[dict[str, Any]],
    timeout_seconds: float,
) -> CodeResult:
    """Execute `code` against `test_cases`; never raises for bad user code."""
    total = len(test_cases)
    if not code.strip():
        return _failure(total, "No code was submitted.")
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return _failure(total, f"SyntaxError: {exc.msg} (line {exc.lineno})")
    payload = {
        "code": code,
        "entry_point": entry_point_from(starter_code),
        "test_cases": test_cases,
        "timeout": timeout_seconds,
    }
    raw = _spawn(payload, timeout_seconds)
    if isinstance(raw, str):
        return _failure(total, raw)
    if raw["error"]:
        return _failure(total, raw["error"])
    outcomes = _build_outcomes(test_cases, raw["tests"])
    passed = sum(1 for o in outcomes if o.passed)
    return CodeResult(
        passed=passed,
        total=total,
        score=_score(passed, total),
        tests=outcomes,
    )


def _score(passed: int, total: int) -> float:
    """All-or-nothing by default; proportional when partial credit is enabled."""
    if total == 0:
        return 0.0
    if passed == total:
        return 1.0
    return round(passed / total, 4) if settings.code_partial_credit else 0.0
