"""Tests for LLM reply parsing and the LLM client."""

import httpx
import pytest

from app.core.llm import LLMClient, LLMUnavailableError
from app.services.evaluation import parse_evaluation


def test_parse_plain_and_fenced_json() -> None:
    assert parse_evaluation('{"score": 7, "feedback": "ok"}') == (7.0, "ok")
    assert parse_evaluation('```json\n{"score": 3, "feedback": "x"}\n```') == (3.0, "x")


def test_parse_clamps_score() -> None:
    assert parse_evaluation('{"score": 42, "feedback": ""}')[0] == 10.0
    assert parse_evaluation('{"score": -3, "feedback": ""}')[0] == 0.0


@pytest.mark.parametrize("raw", ["no json", '{"feedback": "x"}', '{"score": "abc"}'])
def test_parse_rejects_bad_replies(raw: str) -> None:
    with pytest.raises(LLMUnavailableError):
        parse_evaluation(raw)


async def test_client_returns_message_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})

    client = LLMClient(base_url="http://x/v1", transport=httpx.MockTransport(handler))
    assert await client.chat("s", "u") == "hi"


async def test_client_wraps_http_errors() -> None:
    client = LLMClient(
        base_url="http://x/v1",
        transport=httpx.MockTransport(lambda r: httpx.Response(500)),
    )
    with pytest.raises(LLMUnavailableError):
        await client.chat("s", "u")
