# Plan – AI Proficiency Assessment App

**Feature ID**: 001-ai-proficiency-assessment

## 1. Architecture Overview┌──────────────────────┐
│   Streamlit Frontend │  (Port 8501)
└──────────┬───────────┘
│ HTTP
▼
┌──────────────────────┐
│   FastAPI Backend    │  (Port 8000)
│  - Assessment logic  │
│  - Scoring engine    │
│  - LLM evaluation    │
└──────────┬───────────┘
│ OpenAI-compatible API
▼
┌──────────────────────┐
│     LM Studio        │  (Port 1234)
│  Local Open-Weight   |
└──────────────────────┘
│
▼
┌──────────────────────┐
│      SQLite          │
└──────────────────────┘text## 2. Tech Stack
- Frontend: Streamlit
- Backend: FastAPI + Pydantic + SQLModel/SQLAlchemy
- LLM: LM Studio (OpenAI-compatible endpoint), use gemma-4-26b-a4b-it-qat-mlx model
- Database: SQLite
- HTTP Client: httpx
- Package Manager: uv

## 3. Project Structure

ai-proficiency-assessment/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/
│   │   │   ├── assessment.py
│   │   │   └── evaluate.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── llm.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── assessment.py
│   │   │   ├── scoring.py
│   │   │   └── evaluation.py
│   │   └── db/
│   └── requirements.txt
├── frontend/
│   ├── app.py
│   ├── components/
│   └── requirements.txt
├── data/
│   └── questions.json
├── prompts/
│   ├── evaluate_open_ended.txt
│   └── generate_feedback.txt
└── specs/001-ai-proficiency-assessment/

### 4. Data Model (SQLite)
Question: id, type (mcq/open), text, options (JSON), correct_answer, topic, difficulty
AssessmentSession: id, created_at, status, current_question_index
Answer: id, session_id, question_id, user_answer, is_correct, llm_score, llm_feedback
Result: id, session_id, total_score, proficiency_level, feedback_text, completed_at

### 5. Key API Endpoints
MethodEndpointDescription 
POST/assessment/startCreate new session and return first questions
GET/assessment/{session_id} Get current session state
POST/assessment/{session_id}/answerSubmit answer for a question
POST/assessment/{session_id}/submitFinalize assessment and generate result
GET/assessment/{session_id}/resultGet final score + feedback
GET/assessment/{session_id}/reviewGet all answers for review

### 6. Risks & Mitigations

LLM response quality → Iterate on prompts aggressively, add few-shot examples
Slow local inference → Show clear loading indicators + consider smaller models for evaluation
Streamlit session state limitations → Keep important state in the backend
Question quality → Start with a solid seed question bank and improve over time

### 7. Next Immediate Steps

Create the repository structure
Implement FastAPI skeleton + config
Create database models
Build the first three API endpoints
Create a minimal Streamlit frontend that can start an assessment