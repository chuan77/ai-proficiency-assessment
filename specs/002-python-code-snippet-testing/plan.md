# Plan – Python Code Snippet Testing

**Feature ID**: 002-python-code-snippet-testing

## 1. Approach

We will extend the existing assessment system to support a new question type: `code`.

### High-Level Flow
1. Frontend detects `type: "code"` question
2. Shows problem description + starter code + code editor
3. User submits code
4. Backend receives code + question_id
5. Backend runs the code in a **safe sandbox** against predefined test cases
6. Returns score + detailed feedback
7. Frontend displays result

## 2. Technical Design

### New Question Type
```json
{
  "id": "q21",
  "type": "code",
  "topic": "Practical Application",
  "difficulty": "intermediate",
  "question": "Write a function that checks whether a given string is a palindrome...",
  "starter_code": "def is_palindrome(s: str) -> bool:\n    pass",
  "test_cases": [
    {"input": ["racecar"], "expected": true},
    {"input": ["hello"], "expected": false},
    {"input": ["A man a plan a canal Panama"], "expected": true}
  ],
  "timeout_seconds": 3,
  "points": 10
}
```

### Backend Changes
Add new field support in Question model
Create CodeExecutionService
Safe execution options (choose one):
Recommended for MVP: subprocess + timeout + restricted environment
Better: Use docker (overkill for MVP)
Alternative: RestrictedPython or exec with heavy restrictions

### Frontend Changes (Streamlit)
Detect type == "code"
Show st.text_area or better code editor component
Display starter code
Show test results after submission

### 3. Safety Requirements
Timeout (default 3 seconds)
No os, sys, subprocess, open, network, etc.
Memory limit if possible
Catch all exceptions and return clean error messages

### 4. Scoring Logic
All test cases passed → 100% of question points
Any test case failed or exception → 0 points (simple version)
Future: Partial scoring

### 5. Implementation Phases
Data model + question bank update
Safe code execution service
API endpoint for code evaluation
Frontend support for code questions
Add 2–3 good code questions
End-to-end testing