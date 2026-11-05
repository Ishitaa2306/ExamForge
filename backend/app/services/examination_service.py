"""
Examination Service — orchestrates the examination lifecycle, question selection,
and answer submission using the LangGraph examination engine.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.database.models import (
    DifficultyLevel,
    DocumentTopic,
    Examination,
    ExaminationStatus,
    QuestionAsked,
    StudentAnswer,
    TopicAssessment,
)
from app.schemas.examinations import (
    ExaminationProgressResponse,
    NextQuestionResponse,
    SubmitAnswerRequest,
    TopicProgressItem,
)
from app.workflows.examination_graph import ExaminationGraph

logger = logging.getLogger(__name__)


class ExaminationService:
    @staticmethod
    def create_examination(
        db: Session,
        user_id: int,
        document_id: int,
        max_questions: int = 20,
    ) -> Examination:
        """Create a new Examination session row with unique thread ID."""
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
    def start_or_resume_examination(
        db: Session,
        examination: Examination,
    ) -> NextQuestionResponse:
        """
        Starts an examination or resumes an in-progress session.
        Returns the active question without duplicates.
        """
        result_state = ExaminationGraph.execute_start(examination.id)
        db.refresh(examination)

        is_last = (
            examination.questions_asked_count >= examination.max_questions
            or result_state.get("is_complete", False)
        )

        qa_id = result_state.get("question_asked_id", -1)
        q_text = result_state.get("current_question_text", "No question available.")
        category = result_state.get("current_category", "CONCEPTUAL")
        diff = result_state.get("current_difficulty", "MEDIUM")
        topic_id = result_state.get("current_topic_id")
        topic_name = result_state.get("current_topic_name")
        progress_pct = result_state.get("progress_pct", 0.0)

        return NextQuestionResponse(
            examination_id=examination.id,
            question_asked_id=qa_id,
            question_text=q_text,
            category=category,
            difficulty=diff,
            topic_id=topic_id,
            topic_name=topic_name,
            order_index=examination.questions_asked_count,
            is_follow_up=result_state.get("is_follow_up", False),
            is_last=is_last,
            progress_pct=progress_pct,
        )

    @staticmethod
    def submit_answer_and_advance(
        db: Session,
        examination: Examination,
        payload: SubmitAnswerRequest,
    ) -> NextQuestionResponse:
        """
        Executes the mandatory strict sequential examination workflow:
        1. Persist answer
        2. Real IBM Granite Answer Evaluation
        3. Real IBM Granite Knowledge Assessment
        4. Real Google Gemini Examiner Decision (Follow-up vs New Question)
        5. Validate and return next question or completion signal.
        """
        # Guard against duplicate answer submissions on the same question
        existing_answer = (
            db.query(StudentAnswer)
            .filter(StudentAnswer.question_asked_id == payload.question_asked_id)
            .first()
        )
        if existing_answer:
            logger.info("Answer already submitted for question_asked_id %d", payload.question_asked_id)

        result_state = ExaminationGraph.execute_submission(
            examination_id=examination.id,
            question_asked_id=payload.question_asked_id,
            student_answer=payload.answer_text,
            time_taken_seconds=payload.time_taken_seconds or 0,
        )
        db.refresh(examination)

        if result_state.get("is_complete") or examination.status == ExaminationStatus.COMPLETED:
            return NextQuestionResponse(
                examination_id=examination.id,
                question_asked_id=-1,
                question_text="Examination completed. Your academic performance report has been generated.",
                category="CONCEPTUAL",
                difficulty=examination.current_difficulty.value if hasattr(examination.current_difficulty, "value") else str(examination.current_difficulty),
                topic_id=None,
                topic_name=None,
                order_index=examination.questions_asked_count,
                is_last=True,
                progress_pct=100.0,
            )

        qa_id = result_state.get("question_asked_id", -1)
        q_text = result_state.get("current_question_text", "Next question.")
        category = result_state.get("current_category", "CONCEPTUAL")
        diff = result_state.get("current_difficulty", "MEDIUM")
        topic_id = result_state.get("current_topic_id")
        topic_name = result_state.get("current_topic_name")
        progress_pct = result_state.get("progress_pct", 0.0)
        is_last = examination.questions_asked_count >= examination.max_questions

        return NextQuestionResponse(
            examination_id=examination.id,
            question_asked_id=qa_id,
            question_text=q_text,
            category=category,
            difficulty=diff,
            topic_id=topic_id,
            topic_name=topic_name,
            order_index=examination.questions_asked_count,
            is_follow_up=result_state.get("is_follow_up", False),
            is_last=is_last,
            progress_pct=progress_pct,
        )

    @staticmethod
    def get_progress(
        db: Session,
        examination: Examination,
    ) -> ExaminationProgressResponse:
        """Returns structured progress, topic assessments, and mastery metrics."""
        assessments = (
            db.query(TopicAssessment)
            .filter(TopicAssessment.examination_id == examination.id)
            .all()
        )

        all_topics = (
            db.query(DocumentTopic)
            .filter(DocumentTopic.document_id == examination.document_id)
            .all()
        )
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
            if examination.max_questions > 0
            else 0.0,
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
    def manual_complete(db: Session, examination: Examination) -> None:
        """Manually trigger examination finalization and report generation."""
        from app.agents.report_generation import ReportGenerationAgent

        examination.status = ExaminationStatus.COMPLETED
        examination.completed_at = datetime.now(timezone.utc)
        db.commit()

        ReportGenerationAgent.generate(db=db, examination=examination)
