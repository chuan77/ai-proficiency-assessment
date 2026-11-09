"""Schemas for code-question evaluation."""

from pydantic import BaseModel, Field


class TestOutcome(BaseModel):
    """Result of one test case. Hidden tests never expose input/expected/actual."""

    __test__ = False  # not a pytest class

    index: int
    passed: bool
    visible: bool
    input: str | None = None
    expected: str | None = None
    actual: str | None = None
    error: str | None = None


class CodeResult(BaseModel):
    """Outcome of running a submission against all test cases."""

    passed: int
    total: int
    score: float = Field(ge=0.0, le=1.0)
    error_message: str | None = None
    tests: list[TestOutcome] = Field(default_factory=list)
