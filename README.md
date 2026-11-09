# AI Proficiency Assessment

A fully local app that assesses practical AI proficiency. Multiple-choice questions are scored
deterministically; open-ended answers and the final feedback are produced by a local model
served by [LM Studio](https://lmstudio.ai). Nothing leaves your machine.

- **Frontend:** Streamlit (`frontend/`) — UI only
- **Backend:** FastAPI + SQLModel + SQLite (`backend/`) — all scoring and LLM calls
- **LLM:** LM Studio OpenAI-compatible server (default `gemma-4-26b-a4b-it-qat-mlx`)

## Prerequisites

- Python 3.14 and [uv](https://docs.astral.sh/uv/)
- LM Studio with a model loaded and the local server started (default `http://localhost:1234`)

## Setup

```bash
uv sync
```

## Run

Terminal 1 — backend (port 8000), from the repo root:

```bash
uv run uvicorn app.main:app --app-dir backend --port 8000
```

(Or `cd backend` first and drop `--app-dir backend`. Running without either gives
`ModuleNotFoundError: No module named 'app'`.)

Terminal 2 — frontend (port 8501), from the repo root:

```bash
uv run streamlit run frontend/app.py
```

Open http://localhost:8501. The question bank (`data/questions.json`) is loaded into SQLite
(`assessment.db` in the directory you start the backend from) on backend startup.

## Configuration (environment variables or `.env`)

| Variable | Default | Purpose |
|---|---|---|
| `LM_STUDIO_URL` | `http://localhost:1234/v1` | LM Studio API base URL |
| `LM_STUDIO_MODEL` | `gemma-4-26b-a4b-it-qat-mlx` | Model id (see `GET /v1/models`) |
| `QUESTIONS_PER_SESSION` | `10` | Questions drawn from the bank per assessment |
| `CODE_PARTIAL_CREDIT` | `false` | Give proportional credit for partly passing code |
| `CODE_TIMEOUT_SECONDS` | `3` | Default code run time limit |
| `LLM_TIMEOUT_SECONDS` | `180` | Per-request LLM timeout |
| `DATABASE_URL` | `sqlite:///./assessment.db` | Database location |
| `BACKEND_URL` | `http://localhost:8000` | Used by the frontend |

Prompts live in [prompts/](prompts/) and can be edited without code changes.

## Python code questions

Questions with `"type": "code"` ask the user to write a function. The backend runs it against
the question's `test_cases` and scores it automatically (no LLM). Each code question in
`data/questions.json` has `starter_code`, `test_cases` (`input` = argument list, `expected` =
return value, optional `"visible": true` to show that test's details), `timeout_seconds` and
`points`. Every assessment includes at least one code question.

- Users can press **Run tests** to check their code; hidden tests only report pass/fail.
- All tests pass = full credit; otherwise 0 (set `CODE_PARTIAL_CREDIT=true` for proportional
  credit). Syntax/runtime errors and timeouts score 0 with a clear message.
- `CODE_TIMEOUT_SECONDS` (default 3) is the fallback when a question sets no timeout.

**Sandbox.** Code runs in a separate Python process with an empty environment, a temp working
directory, CPU/file-size limits (plus a memory limit on Linux), a wall-clock timeout, an import
allow-list (`re`, `math`, `collections`, `itertools`, ...), no `open`/`eval`/`exec`, and an
audit hook that blocks file, network and process access. This is a best-effort local safeguard,
**not a hardened jail**: on macOS there is no memory cap, and a determined attacker could look for
escapes. Only use this app with users you trust, or run the backend in a container/VM.

## Test and lint

```bash
uv run pytest
uv run ruff check .
```

Tests use a fake LLM; no LM Studio is needed.

## Scoring

Every question has equal weight. MCQ = 1 or 0; open-ended = LLM score / 10; code = fraction of tests passed (all or nothing by default). Total is the
average, as 0-100: Beginner 0-39, Intermediate 40-64, Advanced 65-84, Expert 85-100.
Unanswered questions score 0. If LM Studio is down at submit time, the API returns 503 and the
session stays open so you can retry.
