# Tasks – Python Code Snippet Testing

**Feature ID**: 002-python-code-snippet-testing

## Phase 1: Data & Model
- [X] T001: Extend Question model to support `type: "code"`
- [X] T002: Add fields: `starter_code`, `test_cases`, `timeout_seconds`, `points`
- [X] T003: Update question loading logic
- [X] T004: Add at least 2 code questions into `questions.json` (Palindrome + Anagram)

## Phase 2: Code Execution Engine
- [X] T005: Create `CodeExecutionService`
- [X] T006: Implement safe Python code execution with timeout
- [X] T007: Support running multiple test cases
- [X] T008: Return structured result (passed, failed_tests, error_message, score)
- [X] T009: Add basic security restrictions (block dangerous modules)

## Phase 3: API
- [X] T010: Create endpoint `POST /assessment/{session_id}/evaluate-code`
- [X] T011: Integrate code evaluation into normal answer submission flow
- [X] T012: Update scoring service to handle code questions

## Phase 4: Frontend (Streamlit)
- [X] T013: Detect `code` question type
- [X] T014: Display problem description + starter code
- [X] T015: Provide code input area
- [X] T016: Show loading state while evaluating
- [X] T017: Display detailed feedback (passed/failed tests + errors)

## Phase 5: Polish & Testing
- [X] T018: Add 1 more code question (optional)
- [X] T019: End-to-end test with correct and incorrect code
- [X] T020: Handle edge cases (empty code, infinite loops, syntax errors)
- [X] T021: Update documentation

## Definition of Done
- User can receive and answer at least one Python code question
- Correct code gets full marks
- Incorrect code gets clear feedback
- Execution is safe and has timeout
- Integrated cleanly into existing assessment flow