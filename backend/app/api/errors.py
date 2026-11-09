"""Exception handlers mapping domain errors to HTTP status codes."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.llm import LLMUnavailableError
from app.services.errors import ConflictError, InvalidAnswerError, NotFoundError


def _handler(status_code: int, message: str | None = None):
    async def handle(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": message or str(exc)})

    return handle


def register_error_handlers(app: FastAPI) -> None:
    """Attach handlers so services stay HTTP-agnostic."""
    app.add_exception_handler(NotFoundError, _handler(404))
    app.add_exception_handler(ConflictError, _handler(409))
    app.add_exception_handler(InvalidAnswerError, _handler(422))
    app.add_exception_handler(
        LLMUnavailableError,
        _handler(503, "The language model is unavailable. Check that LM Studio is running."),
    )
