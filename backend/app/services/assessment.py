"""Session lifecycle: start, navigate, answer, submit, result and review."""

import asyncio
import random
from datetime import UTC

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Answer, AssessmentSession, Question, Result
from app.schemas.assessment import (
    AnswerSaved,
    QuestionOut,
    ResultOut,
    ReviewItem,
    ReviewOut,
    SessionState,
    StartIn,
    TopicScore,
)
from app.schemas.code import CodeResult
from app.services import code_execution, scoring
from app.services.adaptive import AdaptiveConfig, AdaptiveEngine, difficulty_weight
from app.services.errors import ConflictError, InvalidAnswerError, NotFoundError
from app.services.evaluation import EvaluationService
from app.services.selection import select_questions


class AssessmentService:
    """Business logic for assessment sessions (UI-agnostic)."""

    def __init__(self, db: Session, adaptive_config: AdaptiveConfig | None = None) -> None:
        self._db = db
        self._adaptive_config = adaptive_config or AdaptiveConfig.from_settings()

    # ---- helpers -------------------------------------------------------
    def _session(self, session_id: str) -> AssessmentSession:
        found = self._db.get(AssessmentSession, session_id)
        if found is None:
            raise NotFoundError("Assessment session not found")
        return found

    def _questions(self, assessment: AssessmentSession) -> list[Question]:
        rows = self._db.exec(
            select(Question).where(Question.id.in_(assessment.question_ids))  # type: ignore[attr-defined]
        ).all()
        by_id = {q.id: q for q in rows}
        return [by_id[qid] for qid in assessment.question_ids if qid in by_id]

    def _answers(self, session_id: str) -> dict[str, Answer]:
        rows = self._db.exec(select(Answer).where(Answer.session_id == session_id)).all()
        return {a.question_id: a for a in rows}

    @staticmethod
    def _question_out(question: Question, index: int) -> QuestionOut:
        return QuestionOut(
            id=question.id,
            index=index,
            type=question.type,  # type: ignore[arg-type]
            topic=question.topic,
            text=question.text,
            difficulty=question.difficulty,
            options=question.options,
            starter_code=question.starter_code,
        )

    @staticmethod
    def _is_adaptive(assessment: AssessmentSession) -> bool:
        return assessment.mode == "adaptive"

    def _engine(self) -> AdaptiveEngine:
        return AdaptiveEngine(self._adaptive_config, random.Random())

    def _bank(self) -> list[Question]:
        return list(self._db.exec(select(Question).order_by(Question.id)).all())

    # ---- use cases -----------------------------------------------------
    def start(self, options: StartIn | None = None) -> SessionState:
        """Create a session: a balanced fixed set, or just the first adaptive question."""
        bank = self._bank()
        if not bank:
            raise NotFoundError("No questions available")
        if options is not None and options.mode == "adaptive":
            return self._start_adaptive(bank)
        chosen = select_questions(bank, settings.questions_per_session)
        assessment = AssessmentSession(question_ids=[q.id for q in chosen])
        self._db.add(assessment)
        self._db.commit()
        return self.get_state(assessment.id)

    def _start_adaptive(self, bank: list[Question]) -> SessionState:
        engine = self._engine()
        target = self._adaptive_config.start_difficulty
        first = engine.select_next(bank, [], target, engine.effective_max(len(bank)))
        assert first is not None  # bank is non-empty
        assessment = AssessmentSession(
            question_ids=[first.id],
            mode="adaptive",
            current_difficulty=target,
            performance_history=[],
            adaptive_complete=False,
        )
        self._db.add(assessment)
        self._db.commit()
        return self.get_state(assessment.id)

    def get_state(self, session_id: str, index: int | None = None) -> SessionState:
        """Return session state and the question at `index` (default: current)."""
        assessment = self._session(session_id)
        questions = self._questions(assessment)
        position = assessment.current_question_index if index is None else index
        if not 0 <= position < len(questions):
            raise NotFoundError("Question index out of range")
        answers = self._answers(session_id)
        question = questions[position]
        saved = answers.get(question.id)
        return SessionState(
            session_id=assessment.id,
            status=assessment.status,  # type: ignore[arg-type]
            mode="adaptive" if self._is_adaptive(assessment) else "fixed",
            total_questions=len(questions),
            max_questions=self._max_questions(assessment),
            ready_to_submit=bool(assessment.adaptive_complete),
            current_question_index=assessment.current_question_index,
            answered_question_ids=[qid for qid in assessment.question_ids if qid in answers],
            question=self._question_out(question, position),
            saved_answer=saved.user_answer if saved else None,
            saved_code_result=CodeResult(**saved.code_result)
            if saved and saved.code_result
            else None,
        )

    def _max_questions(self, assessment: AssessmentSession) -> int | None:
        if not self._is_adaptive(assessment):
            return None
        return self._engine().effective_max(len(self._bank()))

    def _open_session(self, session_id: str, question_id: str) -> AssessmentSession:
        """Load a session that can still be answered and contains `question_id`."""
        assessment = self._session(session_id)
        if assessment.status != "in_progress":
            raise ConflictError("Assessment already submitted")
        if question_id not in assessment.question_ids:
            raise NotFoundError("Question is not part of this session")
        if self._is_adaptive(assessment) and (
            assessment.adaptive_complete or question_id != assessment.question_ids[-1]
        ):
            raise ConflictError("Earlier answers cannot be changed in an adaptive assessment")
        return assessment

    def _store_answer(self, assessment: AssessmentSession, question_id: str, text: str) -> None:
        """Insert or replace the answer, clearing any previous scoring."""
        question = self._db.get(Question, question_id)
        served = question.difficulty if question else None
        existing = self._answers(assessment.id).get(question_id)
        if existing:
            existing.user_answer = text
            existing.llm_score = None
            existing.llm_feedback = None
            existing.code_result = None
            existing.difficulty_served = served
            self._db.add(existing)
        else:
            self._db.add(
                Answer(
                    session_id=assessment.id,
                    question_id=question_id,
                    user_answer=text,
                    difficulty_served=served,
                )
            )
        assessment.current_question_index = assessment.question_ids.index(question_id)
        self._db.add(assessment)
        self._db.commit()

    def save_answer(self, session_id: str, question_id: str, answer: str) -> AnswerSaved:
        """Validate and upsert an answer; remembers the position for resuming."""
        assessment = self._open_session(session_id, question_id)
        question = self._db.get(Question, question_id)
        text = answer.strip("\n") if question and question.type == "code" else answer.strip()
        if not text.strip():
            raise InvalidAnswerError("Answer must not be blank")
        if question is not None and question.type == "mcq" and text not in (question.options or []):
            raise InvalidAnswerError("Answer must be one of the listed options")
        self._store_answer(assessment, question_id, text)
        return AnswerSaved(
            question_id=question_id,
            answered_count=len(self._answers(session_id)),
            total_questions=len(assessment.question_ids),
        )

    def evaluate_code(self, session_id: str, question_id: str, code: str) -> CodeResult:
        """Save a code answer and run it against the question's tests."""
        assessment = self._open_session(session_id, question_id)
        question = self._db.get(Question, question_id)
        if question is None or question.type != "code":
            raise InvalidAnswerError("This question is not a code question")
        text = code.strip("\n")
        if not text.strip():
            raise InvalidAnswerError("Answer must not be blank")
        self._store_answer(assessment, question_id, text)
        result = self._run_code(question, text)
        answer = self._answers(session_id)[question_id]
        answer.code_result = result.model_dump()
        self._db.add(answer)
        self._db.commit()
        return result

    @staticmethod
    def _run_code(question: Question, code: str) -> CodeResult:
        """Execute code in the sandbox (blocking; safe to call from a worker thread)."""
        return code_execution.run_submission(
            code,
            question.starter_code or "",
            question.test_cases or [],
            float(question.timeout_seconds or settings.code_timeout_seconds),
        )

    async def next_question(self, session_id: str, evaluator: EvaluationService) -> SessionState:
        """Adaptive mode: grade the latest answer, then serve the next question or finish."""
        assessment = self._session(session_id)
        if not self._is_adaptive(assessment):
            raise InvalidAnswerError("Only adaptive assessments serve questions on demand")
        if assessment.status != "in_progress":
            raise ConflictError("Assessment already submitted")
        history = list(assessment.performance_history or [])
        if assessment.adaptive_complete or len(history) == len(assessment.question_ids):
            return self.get_state(session_id)
        last = self._db.get(Question, assessment.question_ids[-1])
        answer = self._answers(session_id).get(assessment.question_ids[-1])
        if last is None or answer is None:
            raise InvalidAnswerError("Answer the current question first")
        credit = await self._grade(last, answer, evaluator)
        history.append(credit >= self._adaptive_config.correct_threshold)
        self._advance(assessment, history)
        return self.get_state(session_id, len(assessment.question_ids) - 1)

    async def _grade(
        self, question: Question, answer: Answer, evaluator: EvaluationService
    ) -> float:
        """Score one answer now (the result is kept so submit does not redo the work)."""
        if question.type == "mcq":
            answer.is_correct = scoring.score_mcq(answer.user_answer, question.correct_answer or "")
        elif question.type == "code" and answer.code_result is None:
            result = await asyncio.to_thread(self._run_code, question, answer.user_answer)
            answer.code_result = result.model_dump()
        elif question.type == "open" and answer.llm_score is None:
            answer.llm_score, answer.llm_feedback = await evaluator.evaluate_open_answer(
                question.text, question.evaluation_criteria, answer.user_answer
            )
        self._db.add(answer)
        self._db.commit()
        return scoring.question_points(
            question.type,
            is_correct=answer.is_correct,
            llm_score=answer.llm_score,
            code_score=(answer.code_result or {}).get("score"),
        )

    def _advance(self, assessment: AssessmentSession, history: list[bool]) -> None:
        """Record the outcome, move the target difficulty and append the next question."""
        engine = self._engine()
        bank = self._bank()
        target = engine.next_difficulty(
            assessment.current_difficulty or "intermediate", history[-1]
        )
        used = set(assessment.question_ids)
        candidates = [q for q in bank if q.id not in used]
        assessment.performance_history = history
        assessment.current_difficulty = target
        if engine.should_stop(history, target, len(bank), len(candidates)):
            assessment.adaptive_complete = True
        else:
            served = [q for q in bank if q.id in used]
            slots_left = engine.effective_max(len(bank)) - len(history)
            chosen = engine.select_next(candidates, served, target, slots_left)
            assert chosen is not None  # remaining > 0 was checked by should_stop
            assessment.question_ids = [*assessment.question_ids, chosen.id]
            assessment.current_question_index = len(assessment.question_ids) - 1
        self._db.add(assessment)
        self._db.commit()

    async def submit(self, session_id: str, evaluator: EvaluationService) -> ResultOut:
        """Score all answers, generate feedback and persist the result (idempotent)."""
        assessment = self._session(session_id)
        if assessment.status == "completed":
            return self.get_result(session_id)
        if self._is_adaptive(assessment) and not assessment.adaptive_complete:
            raise ConflictError("The adaptive assessment is not finished yet")
        questions = self._questions(assessment)
        answers = self._answers(session_id)
        self._score_mcq(questions, answers)
        await self._score_code(questions, answers)
        await self._score_open(questions, answers, evaluator)
        topic_scores = self._topic_scores(assessment, questions, answers)
        total = scoring.weighted_percent(
            self._points(questions, answers), self._weights(assessment, questions)
        )
        level = scoring.proficiency_level(total)
        feedback = await evaluator.generate_feedback(
            total, level, {t.topic: t.score_percent for t in topic_scores}
        )
        self._db.add(
            Result(
                session_id=session_id,
                total_score=total,
                proficiency_level=level,
                feedback_text=feedback,
                topic_scores=[t.model_dump() for t in topic_scores],
            )
        )
        assessment.status = "completed"
        self._db.add(assessment)
        try:
            self._db.commit()
        except IntegrityError:
            # A concurrent submit for this session finished first; reuse its result.
            self._db.rollback()
        return self.get_result(session_id)

    def _score_mcq(self, questions: list[Question], answers: dict[str, Answer]) -> None:
        for question in questions:
            answer = answers.get(question.id)
            if question.type == "mcq" and answer is not None:
                answer.is_correct = scoring.score_mcq(
                    answer.user_answer, question.correct_answer or ""
                )
                self._db.add(answer)

    async def _score_open(
        self, questions: list[Question], answers: dict[str, Answer], evaluator: EvaluationService
    ) -> None:
        pending = [
            (q, answers[q.id])
            for q in questions
            if q.type == "open" and q.id in answers and answers[q.id].llm_score is None
        ]
        results = await asyncio.gather(
            *(
                evaluator.evaluate_open_answer(q.text, q.evaluation_criteria, a.user_answer)
                for q, a in pending
            )
        )
        for (_, answer), (score, feedback) in zip(pending, results, strict=True):
            answer.llm_score, answer.llm_feedback = score, feedback
            self._db.add(answer)
        self._db.commit()

    async def _score_code(self, questions: list[Question], answers: dict[str, Answer]) -> None:
        """Run any code answers that have not been evaluated yet (in worker threads)."""
        pending = [
            (q, answers[q.id])
            for q in questions
            if q.type == "code" and q.id in answers and answers[q.id].code_result is None
        ]
        results = await asyncio.gather(
            *(asyncio.to_thread(self._run_code, q, a.user_answer) for q, a in pending)
        )
        for (_, answer), result in zip(pending, results, strict=True):
            answer.code_result = result.model_dump()
            self._db.add(answer)
        self._db.commit()

    @staticmethod
    def _points(questions: list[Question], answers: dict[str, Answer]) -> list[float]:
        points: list[float] = []
        for question in questions:
            answer = answers.get(question.id)
            points.append(
                scoring.question_points(
                    question.type,
                    is_correct=answer.is_correct if answer else None,
                    llm_score=answer.llm_score if answer else None,
                    code_score=(answer.code_result or {}).get("score") if answer else None,
                )
            )
        return points

    def _weights(self, assessment: AssessmentSession, questions: list[Question]) -> list[float]:
        """Fixed sessions weight all questions equally; adaptive ones weight by difficulty."""
        if self._is_adaptive(assessment):
            return [difficulty_weight(q.difficulty) for q in questions]
        return [1.0 for _ in questions]

    def _topic_scores(
        self, assessment: AssessmentSession, questions: list[Question], answers: dict[str, Answer]
    ) -> list[TopicScore]:
        points = self._points(questions, answers)
        weights = self._weights(assessment, questions)
        items = [
            (q.topic, credit, q.id in answers, weight)
            for q, credit, weight in zip(questions, points, weights, strict=True)
        ]
        return [TopicScore(**summary) for summary in scoring.topic_breakdown(items)]

    def _stored_topic_scores(
        self,
        assessment: AssessmentSession,
        result: Result,
        questions: list[Question],
        answers: dict[str, Answer],
    ) -> list[TopicScore]:
        """Use the saved breakdown; results from before it existed are recomputed."""
        if result.topic_scores:
            return [TopicScore(**entry) for entry in result.topic_scores]
        return self._topic_scores(assessment, questions, answers)

    def get_result(self, session_id: str) -> ResultOut:
        """Return the stored result for a completed session."""
        assessment = self._session(session_id)
        result = self._db.exec(select(Result).where(Result.session_id == session_id)).first()
        if result is None or assessment.status != "completed":
            raise ConflictError("Assessment has not been submitted yet")
        questions = self._questions(assessment)
        answers = self._answers(session_id)
        mcqs = [q for q in questions if q.type == "mcq"]
        open_scores = [
            a.llm_score
            for q in questions
            if q.type == "open" and (a := answers.get(q.id)) and a.llm_score is not None
        ]
        code_results = [
            a.code_result
            for q in questions
            if q.type == "code" and (a := answers.get(q.id)) and a.code_result
        ]
        return ResultOut(
            session_id=session_id,
            total_score=result.total_score,
            proficiency_level=result.proficiency_level,
            feedback_text=result.feedback_text,
            mcq_correct=sum(1 for q in mcqs if (a := answers.get(q.id)) and a.is_correct),
            mcq_total=len(mcqs),
            code_passed=sum(1 for r in code_results if r["score"] >= 1.0),
            code_total=sum(1 for q in questions if q.type == "code"),
            open_average=round(sum(open_scores) / len(open_scores), 1) if open_scores else None,
            mode="adaptive" if self._is_adaptive(assessment) else "fixed",
            questions_answered=len(answers),
            topic_scores=self._stored_topic_scores(assessment, result, questions, answers),
            completed_at=result.completed_at.replace(tzinfo=UTC)
            if result.completed_at.tzinfo is None
            else result.completed_at,
        )

    def get_review(self, session_id: str) -> ReviewOut:
        """Return every question with the user's answer and evaluation."""
        assessment = self._session(session_id)
        if assessment.status != "completed":
            raise ConflictError("Assessment has not been submitted yet")
        answers = self._answers(session_id)
        items: list[ReviewItem] = []
        for index, question in enumerate(self._questions(assessment)):
            answer = answers.get(question.id)
            items.append(
                ReviewItem(
                    index=index,
                    question_id=question.id,
                    type=question.type,  # type: ignore[arg-type]
                    topic=question.topic,
                    text=question.text,
                    options=question.options,
                    user_answer=answer.user_answer if answer else None,
                    correct_answer=question.correct_answer if question.type == "mcq" else None,
                    is_correct=self._review_correct(question, answer),
                    llm_score=answer.llm_score if answer else None,
                    llm_feedback=answer.llm_feedback if answer else None,
                    explanation=question.explanation,
                    code_result=CodeResult(**answer.code_result)
                    if answer and answer.code_result
                    else None,
                    difficulty_served=answer.difficulty_served if answer else None,
                )
            )
        return ReviewOut(session_id=session_id, items=items)

    @staticmethod
    def _review_correct(question: Question, answer: Answer | None) -> bool | None:
        if question.type == "mcq":
            return answer.is_correct if answer else False
        if question.type == "code":
            return bool(answer and answer.code_result and answer.code_result["score"] >= 1.0)
        return None
