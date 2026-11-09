# Spec – Python Code Snippet Testing

**Feature ID**: 002-python-code-snippet-testing  
**Status**: Draft  
**Depends on**: 001-ai-proficiency-assessment

## 1. Overview

Add support for Python code snippet questions in the AI Proficiency Assessment.  
Users will be asked to write short Python functions (e.g. palindrome checker, anagram detector, etc.). The system must execute the submitted code against hidden test cases and score it automatically.

## 2. Goals
- Evaluate practical coding ability related to AI/automation tasks
- At least one question in the assessment must be a Python code snippet question
- Provide clear feedback when code fails (error message + which test cases failed)
- Keep execution safe (sandboxed)

## 3. User Stories

- As a user, I want to write and submit short Python code so my practical skills can be assessed.
- As a user, I want to see whether my code passed the test cases and receive helpful feedback.
- As a user, I want clear instructions and a simple code editor experience.

## 4. Functional Requirements

### Must Have
- FR-001: Support a new question type: `code`
- FR-002: Code questions must include:
  - Problem description
  - Function signature / starter code
  - Visible examples
  - Hidden test cases
- FR-003: User can write Python code in the frontend
- FR-004: On submission, the backend safely executes the code against all test cases
- FR-005: Scoring rules:
  - All test cases passed → full marks
  - Partial passes → partial score (optional, configurable)
  - Runtime/Syntax error → 0 marks + error feedback
- FR-006: At least one code question must be included in the default question bank
- FR-007: Show clear feedback (passed/failed test cases + error message if any)
- FR-008: Execution must be sandboxed / have timeout protection

### Must Not Have (for this feature)
- Support for languages other than Python
- Full IDE features (debugging, multiple files, packages)
- Unlimited execution time
- Network access from user code
- File system access from user code

## 5. Question Examples (Minimum)
- Check if a string is a palindrome
- Check if two words are anagrams
- (Optional) Simple list/string manipulation related to data cleaning

## 6. Acceptance Criteria
1. User can receive a `code` type question during the assessment
2. User can submit Python code
3. System executes the code safely against test cases
4. Correct code receives full marks
5. Incorrect / broken code receives 0 (or partial) marks + clear feedback
6. At least one code question exists in the question bank
7. Execution has a timeout (e.g. 3–5 seconds)

## 7. Out of Scope
- Multi-language support
- Advanced coding environment
- Code plagiarism detection
- AI-assisted code completion inside the editor