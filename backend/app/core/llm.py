"""Client for the local LM Studio server (OpenAI-compatible chat API)."""

import httpx

from app.core.config import settings


class LLMUnavailableError(RuntimeError):
    """Raised when the LLM server cannot be reached or returns an unusable reply."""


class LLMClient:
    """Thin async wrapper around LM Studio's /chat/completions endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = (base_url or settings.lm_studio_url).rstrip("/")
        self._model = model or settings.lm_studio_model
        self._timeout = timeout or settings.llm_timeout_seconds
        self._transport = transport

    async def chat(self, system: str, user: str) -> str:
        """Send one system+user exchange and return the assistant's text."""
        payload = {
            "model": self._model,
            "temperature": settings.llm_temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post(f"{self._base_url}/chat/completions", json=payload)
                response.raise_for_status()
                return str(response.json()["choices"][0]["message"]["content"])
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMUnavailableError(f"LLM request failed: {type(exc).__name__}") from exc


def get_llm_client() -> LLMClient:
    """FastAPI dependency returning the LLM client."""
    return LLMClient()
