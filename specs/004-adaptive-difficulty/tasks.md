
---

### 3. `specs/004-adaptive-difficulty/tasks.md`

```markdown
# Tasks – Adaptive Difficulty

**Feature ID**: 004-adaptive-difficulty

## Phase 1: Foundation
- [X] T001: Add `mode` field to AssessmentSession (`fixed` | `adaptive`)
- [X] T002: Add tracking fields (`current_difficulty`, `performance_history`, etc.)
- [X] T003: Create Adaptive configuration settings
- [X] T004: Ensure all questions have a valid `difficulty` value

## Phase 2: Core Engine
- [X] T005: Create `AdaptiveEngine` class/service
- [X] T006: Implement logic to determine next difficulty level
- [X] T007: Implement question selection logic (difficulty + topic balance)
- [X] T008: Implement stopping conditions (min/max questions)
- [X] T009: Add fallback when no question exists at target difficulty

## Phase 3: Integration
- [X] T010: Update `/assessment/start` to support adaptive mode
- [X] T011: Update answer submission flow to call AdaptiveEngine
- [X] T012: Store the difficulty served with each answer
- [X] T013: Ensure final scoring & topic breakdown still work correctly

## Phase 4: Frontend
- [X] T014: Allow user to choose “Classic” or “Adaptive” assessment
- [X] T015: Show progress (e.g. Question X of max Y) in adaptive mode
- [X] T016: Optional: Display current difficulty level
- [X] T017: Clear messaging when the test ends early due to adaptive logic

## Phase 5: Testing & Tuning
- [X] T018: Test rapid correct answers → difficulty increases properly
- [X] T019: Test rapid incorrect answers → difficulty decreases properly
- [X] T020: Test edge cases (not enough questions in a difficulty band)
- [X] T021: Validate topic coverage remains acceptable
- [X] T022: Final review of user experience

## Definition of Done
- User can start an Adaptive assessment
- Difficulty adjusts based on performance
- Min/max question limits are respected
- Final score and topic breakdown remain accurate
- System behaves predictably and safely