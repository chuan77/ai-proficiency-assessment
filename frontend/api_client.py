"""HTTP client for the FastAPI backend. The frontend holds no business logic."""

import os
from typing import Any

import httpx

DEFAULT_BACKEND_URL = "http://localhost:8000"
SUBMIT_TIMEOUT_SECONDS = 600.0
DEFAULT_TIMEOUT_SECONDS = 30.0
CODE_TIMEOUT_SECONDS = 60.0


class ApiError(Exception):
    """A user-presentable error from the backend or the network."""


class BackendClient:
    """Wraps the assessment endpoints and converts failures to ApiError."""

    def __init__(
        self, base_url: str | None = None, transport: httpx.BaseTransport | None = None
    ) -> None:
        self._base_url = (base_url or os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL)).rstrip("/")
        self._transport = transport

    def _request(
        self,
        method: str,
        path: str,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            with httpx.Client(
                base_url=self._base_url, timeout=timeout, transport=self._transport
            ) as client:
                response = client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise ApiError(
                "Cannot reach the assessment server. Make sure the backend is running."
            ) from exc
        if response.is_error:
            raise ApiError(_detail(response))
        return dict(response.json())

    def start(self, mode: str = "fixed") -> dict[str, Any]:
        """Create a new session (`fixed` or `adaptive`)."""
        return self._request("POST", "/assessment/start", json={"mode": mode})

    def next_question(self, session_id: str) -> dict[str, Any]:
        """Adaptive mode: grade the latest answer and fetch the next question."""
        return self._request(
            "POST", f"/assessment/{session_id}/next", timeout=SUBMIT_TIMEOUT_SECONDS
        )

    def get_state(self, session_id: str, index: int | None = None) -> dict[str, Any]:
        """Fetch session state and the question at `index`."""
        params = {} if index is None else {"index": index}
        return self._request("GET", f"/assessment/{session_id}", params=params)

    def save_answer(self, session_id: str, question_id: str, answer: str) -> dict[str, Any]:
        """Save an answer."""
        body = {"question_id": question_id, "answer": answer}
        return self._request("POST", f"/assessment/{session_id}/answer", json=body)

    def evaluate_code(self, session_id: str, question_id: str, code: str) -> dict[str, Any]:
        """Save code and run it against the question's tests."""
        body = {"question_id": question_id, "code": code}
        return self._request(
            "POST",
            f"/assessment/{session_id}/evaluate-code",
            json=body,
            timeout=CODE_TIMEOUT_SECONDS,
        )

    def submit(self, session_id: str) -> dict[str, Any]:
        """Submit the assessment (slow: waits for LLM evaluation)."""
        return self._request(
            "POST", f"/assessment/{session_id}/submit", timeout=SUBMIT_TIMEOUT_SECONDS
        )

    def get_result(self, session_id: str) -> dict[str, Any]:
        """Fetch the final result."""
        return self._request("GET", f"/assessment/{session_id}/result")

    def get_review(self, session_id: str) -> dict[str, Any]:
        """Fetch the answer review."""
        return self._request("GET", f"/assessment/{session_id}/review")


def _detail(response: httpx.Response) -> str:
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list) and detail:
        return "Please check your answer: " + str(detail[0].get("msg", "invalid input"))
    return f"Unexpected server error ({response.status_code})."
