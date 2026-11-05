"""
Examination service — creates exams, orchestrates question selection and answer flow.
"""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database.models import (
    DifficultyLevel,
    DocumentTopic,
    Examination,
    ExaminationStatus,
    QuestionAsked,
    QuestionBank,
    StudentAnswer,
    TopicAssessment,
    TopicAssessmentStatus,
)
from app.schemas.examinations import (
    ExaminationProgressResponse,
    NextQuestionResponse,
    SubmitAnswerRequest,
    TopicProgressItem,
)

logger = logging.getLogger(__name__)

# Minimum questions answered before considering raising/lowering difficulty
DIFFICULTY_ADAPT_AFTER = 3


class ExaminationService:
    @staticmethod
    def create_examination(
        db: Session,
        user_id: int,
        document_id: int,
        max_questions: int = 20,
    ) -> Examination:
        """Instantiate a new Examination row."""
        thread_id = str(uuid.uuid4())
        exam = Examination(
            user_id=user_id,
            document_id=document_id,
            max_questions=max_questions,
            status=ExaminationStatus.CREATED,
            langgraph_thread_id=thread_id,
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)
        return exam

    @staticmethod
    def get_next_question(
        db: Session,
        examination: Examination,
    ) -> NextQuestionResponse:
        """Select the next question and record it in questions_asked."""
        if examination.status == ExaminationStatus.CREATED:
            examination.status = ExaminationStatus.IN_PROGRESS
            examination.started_at = datetime.now(timezone.utc)
            db.commit()

        # Determine which questions have already been asked
        asked_ids = [
            qa.question_id
            for qa in db.query(QuestionAsked)
            .filter(QuestionAsked.examination_id == examination.id)
            .all()
            if qa.question_id is not None
        ]

        # Topics already covered and their question counts
        topic_question_counts: dict[int, int] = {}
        for qa in db.query(QuestionAsked).filter(
            QuestionAsked.examination_id == examination.id
        ).all():
            if qa.topic_id:
                topic_question_counts[qa.topic_id] = topic_question_counts.get(qa.topic_id, 0) + 1

        # Find a topic with fewer questions asked (for coverage balance)
        # Get all topics for this document
        all_topics = db.query(DocumentTopic).filter(
            DocumentTopic.document_id == examination.document_id
        ).all()
        topic_ids = [t.id for t in all_topics]

        # Prefer topics with fewer questions
        least_examined_topic_id = None
        min_count = float("inf")
        for tid in topic_ids:
            count = topic_question_counts.get(tid, 0)
            if count < min_count:
                min_count = count
                least_examined_topic_id = tid

        # Select question: prefer least-examined topic + current difficulty
        question: QuestionBank | None = None

        if least_examined_topic_id and asked_ids:
            question = (
                db.query(QuestionBank)
                .filter(
                    QuestionBank.document_id == examination.document_id,
                    QuestionBank.difficulty == examination.current_difficulty,
                    QuestionBank.topic_id == least_examined_topic_id,
                    QuestionBank.id.notin_(asked_ids),
                )
                .first()
            )

        # Fallback: any question matching current difficulty not yet asked
        if not question:
            filter_args = [
                QuestionBank.document_id == examination.document_id,
                QuestionBank.difficulty == examination.current_difficulty,
            ]
            if asked_ids:
                filter_args.append(QuestionBank.id.notin_(asked_ids))
            question = db.query(QuestionBank).filter(*filter_args).first()

        # Final fallback: any unused question regardless of difficulty
        if not question:
            filter_args = [QuestionBank.document_id == examination.document_id]
            if asked_ids:
                filter_args.append(QuestionBank.id.notin_(asked_ids))
            question = db.query(QuestionBank).filter(*filter_args).first()

        progress_pct = round(
            (examination.questions_asked_count / examination.max_questions) * 100
            if examination.max_questions > 0
            else 0.0,
            1,
        )

        is_last = (
            examination.questions_asked_count + 1 >= examination.max_questions
            or question is None
        )

        if question is None:
            # No more questions — complete
            ExaminationService._complete_examination(db, examination)
            return NextQuestionResponse(
                examination_id=examination.id,
                question_asked_id=-1,
                question_text="No more questions available.",
                category="CONCEPTUAL",
                difficulty=examination.current_difficulty,
                topic_id=None,
                topic_name=None,
                order_index=examination.questions_asked_count,
                is_last=True,
                progress_pct=100.0,
            )

        order_index = examination.questions_asked_count + 1
        qa = QuestionAsked(
            examination_id=examination.id,
            question_id=question.id,
            question_text=question.question_text,
            category=question.category,
            difficulty=question.difficulty,
            topic_id=question.topic_id,
            order_index=order_index,
        )
        db.add(qa)

        examination.questions_asked_count = order_index
        examination.current_topic_id = question.topic_id
        db.commit()
        db.refresh(qa)

        topic_name: str | None = None
        if qa.topic_id:
            topic = db.query(DocumentTopic).filter(DocumentTopic.id == qa.topic_id).first()
            topic_name = topic.name if topic else None

        return NextQuestionResponse(
            examination_id=examination.id,
            question_asked_id=qa.id,
            question_text=qa.question_text,
            category=qa.category.value,
            difficulty=qa.difficulty,
            topic_id=qa.topic_id,
            topic_name=topic_name,
            order_index=qa.order_index,
            is_last=is_last,
            progress_pct=progress_pct,
        )

    @staticmethod
    def submit_answer_and_advance(
        db: Session,
        examination: Examination,
        payload: SubmitAnswerRequest,
    ) -> NextQuestionResponse:
        """Save the student's answer, trigger async evaluation, then return the next question."""
        answer = StudentAnswer(
            examination_id=examination.id,
            question_asked_id=payload.question_asked_id,
            answer_text=payload.answer_text,
            time_taken_seconds=payload.time_taken_seconds,
        )
        db.add(answer)
        db.commit()
        db.refresh(answer)

        # Fire-and-forget evaluation in background
        try:
            from app.agents.answer_evaluation import AnswerEvaluationAgent
            AnswerEvaluationAgent.evaluate_async(student_answer_id=answer.id)
        except Exception as exc:
            logger.warning("Answer evaluation agent failed to start: %s", exc)

        # Adapt difficulty based on recent performance
        ExaminationService._adapt_difficulty(db, examination)

        if examination.questions_asked_count >= examination.max_questions:
            ExaminationService._complete_examination(db, examination)
            return NextQuestionResponse(
                examination_id=examination.id,
                question_asked_id=-1,
                question_text="Examination complete.",
                category="CONCEPTUAL",
                difficulty=examination.current_difficulty,
                topic_id=None,
                topic_name=None,
                order_index=examination.questions_asked_count,
                is_last=True,
                progress_pct=100.0,
            )

        next_q = ExaminationService.get_next_question(db, examination)
        # If the next question itself signals last, check if we've hit the limit
        if next_q.is_last and next_q.question_asked_id == -1:
            # Already completed via get_next_question
            pass
        return next_q

    @staticmethod
    def get_progress(
        db: Session,
        examination: Examination,
    ) -> ExaminationProgressResponse:
        """Return structured progress info for an examination."""
        from app.database.models import TopicAssessment

        assessments = (
            db.query(TopicAssessment)
            .filter(TopicAssessment.examination_id == examination.id)
            .all()
        )

        all_topics = db.query(DocumentTopic).filter(
            DocumentTopic.document_id == examination.document_id
        ).all()
        topic_name_map = {t.id: t.name for t in all_topics}

        topics_covered = [
            TopicProgressItem(
                topic_id=ta.topic_id,
                topic_name=topic_name_map.get(ta.topic_id, f"Topic {ta.topic_id}"),
                questions_examined=ta.questions_examined,
                status=ta.status.value,
                strength_score=ta.strength_score,
            )
            for ta in assessments
        ]

        progress_pct = round(
            (examination.questions_asked_count / examination.max_questions) * 100
            if examination.max_questions > 0 else 0.0,
            1,
        )

        return ExaminationProgressResponse(
            examination_id=examination.id,
            status=examination.status,
            questions_asked=examination.questions_asked_count,
            max_questions=examination.max_questions,
            progress_pct=progress_pct,
            current_difficulty=examination.current_difficulty,
            topics_covered=topics_covered,
            total_topics=len(all_topics),
        )

    @staticmethod
    def _adapt_difficulty(db: Session, examination: Examination) -> None:
        """
        Adjust examination difficulty based on recent answer evaluations.
        """
        from app.database.models import AnswerEvaluation, EvaluationLabel

        # Only adapt after enough data
        if examination.questions_asked_count < DIFFICULTY_ADAPT_AFTER:
            return

        # Get last 3 evaluations
        recent_evals = (
            db.query(AnswerEvaluation)
            .filter(AnswerEvaluation.examination_id == examination.id)
            .order_by(AnswerEvaluation.created_at.desc())
            .limit(3)
            .all()
        )

        if len(recent_evals) < 2:
            return

        correct_count = sum(
            1 for e in recent_evals
            if e.evaluation_label == EvaluationLabel.CORRECT
        )
        incorrect_count = sum(
            1 for e in recent_evals
            if e.evaluation_label in (EvaluationLabel.INCORRECT, EvaluationLabel.INCOMPLETE)
        )

        current = examination.current_difficulty
        if correct_count >= 3 and current != DifficultyLevel.HARD:
            # All correct — increase difficulty
            if current == DifficultyLevel.EASY:
                examination.current_difficulty = DifficultyLevel.MEDIUM
            elif current == DifficultyLevel.MEDIUM:
                examination.current_difficulty = DifficultyLevel.HARD
            db.commit()
        elif incorrect_count >= 2 and current != DifficultyLevel.EASY:
            # Mostly wrong — decrease difficulty
            if current == DifficultyLevel.HARD:
                examination.current_difficulty = DifficultyLevel.MEDIUM
            elif current == DifficultyLevel.MEDIUM:
                examination.current_difficulty = DifficultyLevel.EASY
            db.commit()

    @staticmethod
    def _complete_examination(db: Session, examination: Examination) -> None:
        """Mark examination as complete and trigger report generation."""
        examination.status = ExaminationStatus.COMPLETED
        examination.completed_at = datetime.now(timezone.utc)
        db.commit()

        # Trigger knowledge assessment + report generation asynchronously
        import threading
        t = threading.Thread(
            target=ExaminationService._finalize_examination,
            args=(examination.id,),
            daemon=True,
        )
        t.start()

    @staticmethod
    def _finalize_examination(examination_id: int) -> None:
        """Run knowledge assessment and generate report after examination ends."""
        from app.database.connection import SessionLocal
        db = SessionLocal()
        try:
            exam = db.query(Examination).filter(Examination.id == examination_id).first()
            if not exam:
                return

            # Run knowledge assessment
            from app.agents.knowledge_assessment import KnowledgeAssessmentAgent
            KnowledgeAssessmentAgent.assess(db=db, examination=exam)

            # Generate report
            from app.services.report_service import ReportService
            ReportService.generate_report(db=db, examination=exam)

            logger.info("Finalized examination %d", examination_id)
        except Exception as exc:
            logger.exception("Examination finalization failed for %d: %s", examination_id, exc)
        finally:
            db.close()
