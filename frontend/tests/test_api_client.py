"""Tests for the frontend's backend client."""

import httpx
import pytest

from api_client import ApiError, BackendClient


def _client(handler) -> BackendClient:
    return BackendClient("http://backend", transport=httpx.MockTransport(handler))


def test_start_returns_json() -> None:
    client = _client(lambda r: httpx.Response(201, json={"session_id": "abc"}))
    assert client.start() == {"session_id": "abc"}


def test_error_detail_is_surfaced() -> None:
    client = _client(lambda r: httpx.Response(503, json={"detail": "LM Studio down"}))
    with pytest.raises(ApiError, match="LM Studio down"):
        client.submit("abc")


def test_validation_error_is_friendly() -> None:
    body = {"detail": [{"msg": "String should have at most 4000 characters"}]}
    client = _client(lambda r: httpx.Response(422, json=body))
    with pytest.raises(ApiError, match="at most 4000"):
        client.save_answer("s", "q", "x")


def test_network_failure_is_friendly() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(ApiError, match="Cannot reach"):
        _client(boom).get_state("s")


def test_index_sent_as_query_param() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json={})

    _client(handler).get_state("s", 3)
    assert seen == ["http://backend/assessment/s?index=3"]


def test_start_sends_mode_and_next_question_posts() -> None:
    seen: list[tuple[str, str, bytes]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.content))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.start("adaptive")
    client.next_question("abc")
    assert seen[0][1] == "/assessment/start" and b'"adaptive"' in seen[0][2]
    assert seen[1][:2] == ("POST", "/assessment/abc/next")
