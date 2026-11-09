# Spec – AI Proficiency Assessment App

**Feature ID**: 001-ai-proficiency-assessment  
**Status**: Draft  
**Created**: 2026-11-06

## 1. Overview

Build a fully local AI Proficiency Assessment application that evaluates a user’s practical understanding and ability to work with AI systems. The app must run offline using open-weight models served by LM Studio.

## 2. User Stories

### US-01 – Start Assessment
As a user, I want to start a new assessment so that I can test my AI proficiency.

### US-02 – Answer Questions
As a user, I want to answer a series of multiple-choice and open-ended questions so that my knowledge can be evaluated.

### US-03 – See Progress
As a user, I want to see my progress during the assessment so that I know how much is left.

### US-04 – Submit Assessment
As a user, I want to submit the assessment and receive a clear proficiency result.

### US-05 – Receive Feedback
As a user, I want personalized feedback on my strengths and weaknesses.

### US-06 – Review Answers
As a user, I want to review my answers after completing the assessment.

## 3. Functional Requirements

### Must Have
- FR-001: User can start a new assessment session
- FR-002: Assessment contains a mix of Multiple Choice Questions (MCQ) and Open-ended questions
- FR-003: Questions are organized by topic (Fundamentals, Prompt Engineering, Limitations & Risks, Practical Usage)
- FR-004: User can navigate between questions (Next / Previous)
- FR-005: Progress indicator is shown (e.g. Question 5 of 12)
- FR-006: MCQ answers are scored deterministically
- FR-007: Open-ended answers are evaluated using the local LLM (LM Studio)
- FR-008: Final score (0-100) and proficiency level are calculated:
  - Beginner (0-39)
  - Intermediate (40-64)
  - Advanced (65-84)
  - Expert (85-100)
- FR-009: Personalized feedback is generated based on performance
- FR-010: User can review all answers and correct/incorrect status after submission
- FR-011: Assessment session and results are persisted (SQLite)

### Must Not Have (MVP)
- User accounts / login
- Public sharing of results
- Payment features
- Adaptive difficulty engine
- Admin question management UI
- Multi-language support

## 4. Non-Functional Requirements
- Must run fully offline once models are loaded in LM Studio
- Streamlit frontend + FastAPI backend
- Clear loading states when waiting for LLM responses
- Assessment should be completable in under 20 minutes
- Clean and simple user interface

## 5. Acceptance Criteria
1. User can complete a full assessment flow without errors
2. MCQ scoring is 100% accurate
3. Open-ended answers receive reasonable LLM evaluation
4. Final result page shows score, proficiency level, and feedback
5. User can review previous answers after submission
6. Data is saved in SQLite and can be retrieved by session ID
7. Application works with LM Studio running locally on port 1234

## 6. Out of Scope
- Authentication
- PDF export / certificates
- Organizational analytics
- Cloud deployment version
- Mobile app