# Plan – Adaptive Difficulty

**Feature ID**: 004-adaptive-difficulty

## 1. Approach

We will implement a **simple rule-based adaptive engine** first (not full IRT).  
This gives most of the user benefit with much lower complexity.

### High-Level Flow

1. User starts assessment → mode = `adaptive` (or keep classic mode as option)
2. System selects first question (medium difficulty)
3. User answers
4. Engine evaluates result and decides next difficulty
5. Engine selects next best question (difficulty + topic balance)
6. Repeat until stopping condition is met
7. Generate normal result + topic breakdown

## 2. Key Components

### New Service: `AdaptiveEngine`
Responsibilities:
- Decide next difficulty level
- Select the next question
- Track performance window
- Enforce min/max questions
- Maintain light topic coverage

### Data Changes
- `AssessmentSession`: add fields such as:
  - `mode` (`fixed` | `adaptive`)
  - `current_difficulty`
  - `questions_served`
  - `performance_history` (recent correct/incorrect)
- `Answer` or tracking table: store the difficulty that was served

### Question Selection Priority
When choosing the next question:
1. Match target difficulty
2. Prefer under-represented topics
3. Avoid already asked questions
4. Fallback to nearest difficulty if needed

## 3. Configuration (can live in config or database)

```python
ADAPTIVE_CONFIG = {
    "min_questions": 8,
    "max_questions": 15,
    "start_difficulty": "intermediate",
    "performance_window": 2,          # last N answers
    "allow_topic_balancing": True
}
```

### 4 Implementation Phases
Data model changes
AdaptiveEngine (core logic)
Integration into assessment flow
Frontend support (start Adaptive vs Classic test)
Testing & tuning of rules

### 5 Risk,Mitigation
Not enough questions at certain difficulty,Fallback to nearest difficulty + logging
Topic coverage becomes skewed,Add light topic balancing logic
Users find it unpredictable,Keep rules simple and optional display of difficulty
Over-complexity,Strictly stay with rule-based MVP