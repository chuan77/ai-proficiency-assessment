# Plan – Topic-level Skill Breakdown

**Feature ID**: 003-topic-level-skill-breakdown

## 1. Architecture Impact

This is primarily a **backend calculation + frontend display** feature.  
No major architectural changes are required.

### Backend
- Extend the Result model / response schema to include `topic_scores`
- Add calculation logic inside the scoring / result generation service
- Group answers by `question.topic`

### Frontend (Streamlit)
- Add a new “Skill Breakdown” section on the Results page
- Display clean progress bars + labels

## 2. Data Shape

Example of what the API should return:

```json
{
  "overall_score": 78,
  "proficiency_level": "Advanced",
  "topic_scores": [
    {
      "topic": "Fundamentals",
      "score": 90,
      "level": "Expert",
      "questions_answered": 5,
      "max_points": 25,
      "earned_points": 22.5
    },
    {
      "topic": "Prompt Engineering",
      "score": 70,
      "level": "Advanced",
      "questions_answered": 4,
      "max_points": 20,
      "earned_points": 14
    },
    {
      "topic": "Limitations & Risks",
      "score": 55,
      "level": "Intermediate",
      "questions_answered": 3,
      "max_points": 15,
      "earned_points": 8.25
    },
    {
      "topic": "Practical Application",
      "score": 82,
      "level": "Advanced",
      "questions_answered": 4,
      "max_points": 30,
      "earned_points": 24.6
    }
  ]
}

Implementation Approach
Scoring Service
After all answers are evaluated, group by topic
Calculate earned vs max points per topic
Map score to proficiency level

Result Model
Store topic_scores as JSON in the Result table (simple and flexible)

API
Enrich the existing /assessment/{session_id}/result endpoint

Frontend
Add a clear section titled “Skill Breakdown” or “Performance by Topic”
Use st.progress + text, or custom HTML/CSS for nicer bars

4. Edge Cases
Topic has zero questions → exclude from list
All questions in one topic → still show breakdown (only one item)
Partial points from open-ended/code questions → must be supported
Old assessments (before this feature) → gracefully handle missing topic_scores
5. Tech Decisions
Keep topic list flexible (driven by questions, not hard-coded)
Store calculated topic scores in the Result record (avoid recalculating every time)
Use the same proficiency thresholds for consistency