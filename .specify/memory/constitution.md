# Constitution – AI Proficiency Assessment App

## Project Mission
Build a clean, reliable, and private AI Proficiency Assessment tool that accurately evaluates a user’s practical understanding and ability to work with AI systems. The app must be fast to develop, easy to maintain, and fully runnable on local hardware.

## Tech Stack (Mandatory)
- **Frontend**: Streamlit
- **Backend**: FastAPI + Pydantic + Uvicorn
- **LLM Serving**: LM Studio (OpenAI-compatible API)
- **Database**: SQLite (MVP) → PostgreSQL later if needed
- **ORM**: SQLAlchemy or SQLModel
- **HTTP Client**: httpx
- **Package Management**: uv or poetry
- **Python Version**: 3.11+

## Architectural Principles
- Clear separation between Frontend (Streamlit) and Backend (FastAPI)
- All business logic, scoring, and LLM calls must live in the FastAPI backend
- Streamlit is only responsible for UI and calling backend APIs
- LLM is treated as an external service (via LM Studio)
- Prefer simple and explicit code over clever abstractions
- Every endpoint must have proper request/response Pydantic models

## Non-Negotiable Rules
1. Type hints are mandatory everywhere
2. All LLM prompts must be stored in a dedicated prompts/ folder or constants file
3. Assessment results and user answers are private by default
4. No API keys or secrets in the Streamlit frontend
5. Scoring logic for multiple-choice questions must be deterministic (not LLM-based)
6. LLM is only used for evaluating open-ended answers and generating feedback
7. Every new feature must include basic tests
8. Code must run fully offline once models are loaded in LM Studio
9. Use environment variables for configuration (LM Studio URL, model name, etc.)
10. Keep the UI clean, fast, and focused on the assessment experience

## Coding Conventions
- Use snake_case for Python
- Prefer async endpoints in FastAPI when calling the LLM
- Maximum function length: ~40 lines (split if longer)
- Meaningful variable and function names
- Add docstrings to all public functions and endpoints

## Out of Bounds
- Do not introduce React, Next.js, or any heavy frontend framework
- Do not use cloud LLM APIs in the default configuration
- Do not store assessment data in the browser only
- Avoid over-engineering (no microservices, no Kafka, no complex event systems)