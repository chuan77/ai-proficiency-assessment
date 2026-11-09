# Spec – Topic-level Skill Breakdown

**Feature ID**: 003-topic-level-skill-breakdown  
**Status**: Draft  
**Depends on**: 001-ai-proficiency-assessment, 002-python-code-snippet-testing  
**Priority**: High

## 1. Overview

After a user completes an assessment, the system should provide a clear breakdown of performance across different skill topics (e.g. Fundamentals, Prompt Engineering, Limitations & Risks, Practical Application / Coding).  

This helps users understand their strengths and weaknesses instead of only receiving a single overall score.

## 2. Goals

- Give users meaningful, actionable insight into their AI proficiency
- Show performance per topic both as a score and visual indicator
- Maintain consistency with the existing proficiency levels (Beginner → Expert)
- Support future features (adaptive testing, personalized learning recommendations)

## 3. User Stories

- As a user, I want to see how I performed in each skill area so I know what I’m good at and what I need to improve.
- As a user, I want a clear visual summary (not just numbers) of my topic performance.
- As a user, I want the overall proficiency level to still be shown prominently, with the topic breakdown as supporting detail.

## 4. Functional Requirements

### Must Have
- FR-001: Calculate a separate score (0–100) for each topic used in the assessment.
- FR-002: Support at least these standard topics:
  - Fundamentals
  - Prompt Engineering
  - Limitations & Risks
  - Practical Application (includes coding questions)
- FR-003: Display topic-level results on the final Result page.
- FR-004: For each topic show:
  - Topic name
  - Score (0–100)
  - Proficiency label (Beginner / Intermediate / Advanced / Expert)
  - Visual indicator (progress bar or equivalent)
- FR-005: Calculate topic score only from questions that belong to that topic.
- FR-006: Handle cases where a topic has zero questions gracefully (do not show the topic or show “N/A”).
- FR-007: Overall score and overall proficiency level remain the primary result.
- FR-008: Topic breakdown must work with both MCQ, Open-ended, and Code question types.

### Should Have
- FR-009: Show number of questions answered per topic (e.g. 4/5 questions).
- FR-010: Sort topics by score (weakest to strongest or strongest to weakest) — configurable.
- FR-011: Use consistent color coding (e.g. red → yellow → green) across topic bars.

### Must Not Have
- Do not make topic scores the main focus over the overall result.
- Do not require users to complete a minimum number of questions per topic to see results.
- Do not introduce new complex analytics (trends over time, peer comparison, etc.) in this feature.

## 5. Scoring Rules

- Topic Score = (Points earned in topic / Maximum possible points in topic) × 100
- Use the same proficiency thresholds as the overall score:
  - 0–39 → Beginner
  - 40–64 → Intermediate
  - 65–84 → Advanced
  - 85–100 → Expert
- Code questions and open-ended questions contribute to the topic score using their existing point values.

## 6. Acceptance Criteria

1. After submitting an assessment, the Result page shows a Topic Breakdown section.
2. Each topic that had at least one question displays:
   - Name
   - Numeric score
   - Proficiency label
   - Visual progress bar
3. Topics with no questions are not shown (or clearly marked as N/A).
4. Overall score and proficiency level remain clearly visible and primary.
5. Scores are calculated correctly across MCQ, open-ended, and code questions.
6. The breakdown works even if the question distribution across topics is uneven.

## 7. Out of Scope

- Historical comparison (progress over multiple assessments)
- Personalized learning recommendations / resources
- Peer comparison or leaderboard
- Editable topic weights
- Admin UI to manage topics

## 8. Success Metrics

- Users can clearly identify their weakest and strongest areas
- Topic breakdown increases perceived value of the assessment result
- No significant performance impact on result generation