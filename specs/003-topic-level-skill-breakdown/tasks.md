
---

### 3. `specs/003-topic-level-skill-breakdown/tasks.md`

```markdown
# Tasks – Topic-level Skill Breakdown

**Feature ID**: 003-topic-level-skill-breakdown

## Phase 1: Backend Logic
- [X] T001: Update Result model/schema to include `topic_scores` (JSON)
- [X] T002: Create helper function to calculate topic scores from answers + questions
- [X] T003: Integrate topic score calculation into the final result generation flow
- [X] T004: Ensure code questions and open-ended questions are correctly attributed to their topic
- [X] T005: Handle edge case when a topic has no questions

## Phase 2: API
- [X] T006: Update `/assessment/{session_id}/result` response to include `topic_scores`
- [X] T007: Verify backward compatibility with existing results

## Phase 3: Frontend (Streamlit)
- [X] T008: Add “Skill Breakdown” section on the Results page
- [X] T009: Display topic name, score, proficiency level, and progress bar
- [X] T010: Show number of questions per topic (optional but recommended)
- [X] T011: Apply consistent color coding for score levels
- [X] T012: Ensure the overall score remains the most prominent element

## Phase 4: Testing & Polish
- [X] T013: Test with uneven question distribution across topics
- [X] T014: Test with assessments that contain code questions
- [X] T015: Test with old assessment sessions (no topic_scores)
- [X] T016: Final UI review and copy improvements

## Definition of Done
- Result page shows clear topic-level breakdown
- Scores are calculated correctly
- Works with all existing question types
- Overall result remains the primary focus
- Code is clean and follows the project constitution