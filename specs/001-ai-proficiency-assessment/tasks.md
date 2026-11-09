
---

### 3. `specs/001-ai-proficiency-assessment/tasks.md`

```markdown
# Tasks – AI Proficiency Assessment App

**Feature ID**: 001-ai-proficiency-assessment

## Phase 1: Project Setup
- [X] T001: Create project structure (backend/ and frontend/ folders)
- [X] T002: Initialize backend with FastAPI + SQLModel + httpx
- [X] T003: Create `backend/app/core/config.py` (LM Studio URL, model name, etc.)
- [X] T004: Create SQLite database connection and session management
- [X] T005: Create initial `data/questions.json` with 10–12 seed questions

## Phase 2: Data Layer
- [X] T006: Define SQLModel models (Question, AssessmentSession, Answer, Result)
- [X] T007: Create database initialization script / startup event
- [X] T008: Implement function to seed questions from JSON into database
- [X] T009: Create Pydantic schemas for API request/response

## Phase 3: Core Backend Services
- [X] T010: Implement AssessmentService (start session, get next question, save answer)
- [X] T011: Implement ScoringService (deterministic MCQ scoring)
- [X] T012: Implement LLM client (`core/llm.py`) pointing to LM Studio
- [X] T013: Implement EvaluationService (open-ended scoring + feedback generation)
- [X] T014: Create prompt templates in `/prompts`

## Phase 4: API Endpoints
- [X] T015: POST /assessment/start
- [X] T016: GET /assessment/{session_id}
- [X] T017: POST /assessment/{session_id}/answer
- [X] T018: POST /assessment/{session_id}/submit
- [X] T019: GET /assessment/{session_id}/result
- [X] T020: GET /assessment/{session_id}/review
- [X] T021: Add proper error handling and HTTP status codes

## Phase 5: Streamlit Frontend
- [X] T022: Create main Streamlit app entry point
- [X] T023: Build “Start Assessment” page
- [X] T024: Build Question page with navigation and progress bar
- [X] T025: Implement answer submission logic
- [X] T026: Build Results page (score + level + feedback)
- [X] T027: Build Review Answers page
- [X] T028: Add loading spinners for LLM calls
- [X] T029: Handle session_id in Streamlit session state

## Phase 6: Integration & Polish
- [X] T030: End-to-end test of full assessment flow
- [X] T031: Improve open-ended evaluation prompts
- [X] T032: Add basic input validation and error messages
- [X] T033: Write README with setup instructions (LM Studio + how to run)
- [ ] T034: Final manual testing and bug fixes

## Definition of Done
- All tasks above are completed
- Full assessment flow works end-to-end
- MCQ scoring is correct
- Open-ended answers are evaluated via LM Studio
- Results and review pages work
- Code follows the project constitution