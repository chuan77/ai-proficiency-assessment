# Spec – Adaptive Difficulty

**Feature ID**: 004-adaptive-difficulty  
**Status**: Draft  
**Depends on**: 001-ai-proficiency-assessment, 003-topic-level-skill-breakdown  
**Priority**: High

## 1. Overview

Implement Adaptive Difficulty so the assessment dynamically adjusts the difficulty of upcoming questions based on the user’s performance so far.  

This makes the test shorter, more accurate, and more engaging by avoiding questions that are too easy or too hard for the individual.

## 2. Goals

- Improve assessment accuracy with fewer questions
- Create a better user experience (less boredom / less frustration)
- Maintain fairness and transparency
- Keep the system understandable and controllable

## 3. User Stories

- As a user, I want the test to adapt to my level so I don’t waste time on questions that are too easy or extremely hard.
- As a user, I want the assessment to feel fair and not randomly jump in difficulty.
- As a user, I still want to receive a reliable overall score and topic breakdown at the end.

## 4. Functional Requirements

### Must Have
- FR-001: Support adaptive question selection during an assessment session.
- FR-002: Start with a medium difficulty question (or a short fixed calibration set).
- FR-003: After each answer (or after a small batch), adjust the difficulty of the next question based on recent performance.
- FR-004: Difficulty levels supported: `beginner`, `intermediate`, `advanced`, `expert`.
- FR-005: Rules (simple version):
  - Correct answer → increase difficulty (when possible)
  - Incorrect answer → decrease difficulty (when possible)
- FR-006: Allow configuration of:
  - Minimum number of questions
  - Maximum number of questions
  - Target confidence / stopping condition (optional for MVP)
- FR-007: Ensure topic coverage remains reasonable (do not sacrifice topic balance completely for difficulty).
- FR-008: Final scoring must still work correctly with the adaptive sequence.
- FR-009: Record the difficulty of each question served for auditability.

### Should Have
- FR-010: Support a simple “calibration” phase (first 2–3 questions fixed or milder adaptation).
- FR-011: Prefer questions from weaker topics when performance is strong overall (light personalization).
- FR-012: Show current difficulty level to the user (optional, can be hidden).

### Must Not Have
- Full Item Response Theory (IRT) or complex psychometric models in MVP
- Changing difficulty of already answered questions
- Allowing users to manually choose difficulty mid-test
- Making the test endlessly long

## 5. Adaptation Logic (MVP)

**Simple Rule-Based Approach** (recommended for first version):

- Start at `intermediate`
- Track recent performance (e.g. last 2–3 questions)
- If user answers correctly → move one level up (if available)
- If user answers incorrectly → move one level down (if available)
- Never jump more than one level at a time
- Respect maximum and minimum number of questions

**Stopping Conditions** (configurable):
- Reached maximum questions, or
- Reached minimum questions **and** performance has stabilized

## 6. Acceptance Criteria

1. Assessment can run in Adaptive mode.
2. Difficulty of next question changes based on previous answers.
3. Difficulty never jumps more than one level at a time.
4. Assessment respects min/max question limits.
5. Final score and topic breakdown still calculate correctly.
6. Each served question records the difficulty level used at the time.
7. System falls back gracefully if not enough questions exist at the desired difficulty.

## 7. Out of Scope

- True psychometric IRT / CAT engine
- Multi-dimensional adaptive testing (adapting per topic simultaneously in a complex way)
- User-selectable difficulty mode mid-assessment
- Machine-learning based difficulty prediction

## 8. Success Metrics

- Average number of questions per assessment decreases while maintaining result reliability
- Users report the test feels more appropriately challenging
- Strong correlation between adaptive results and full fixed-length test results (future validation)