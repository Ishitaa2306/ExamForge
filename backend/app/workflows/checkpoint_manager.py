"""
Checkpoint Manager — coordinates state persistence between LangGraph and PostgreSQL.
PostgreSQL serves as the authoritative, durable source of truth.
"""
import logging
from typing import Any, Optional

from app.database.connection import SessionLocal
from app.database.models import (
    AnswerEvaluation,
    Examination,
    ExaminationStatus,
    QuestionAsked,
    StudentAnswer,
    TopicAssessment,
)

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Coordinates examination state persistence and thread recovery.
    Guarantees cross-request durability, browser refresh survival, and process restart recovery.
    """

    _checkpointer = None

    @classmethod
    def get_checkpointer(cls):
        """Lazy-initialize checkpointer."""
        if cls._checkpointer is None:
            try:
                from langgraph.checkpoint.memory import MemorySaver  # type: ignore
                cls._checkpointer = MemorySaver()
                logger.info("LangGraph checkpointer initialized.")
            except Exception as exc:
                logger.warning("LangGraph in-memory checkpointer init failed: %s", exc)
                cls._checkpointer = None
        return cls._checkpointer

    @classmethod
    def get_thread_config(cls, thread_id: str) -> dict[str, Any]:
        """Return a LangGraph config dict for the given examination thread."""
        return {"configurable": {"thread_id": thread_id}}

    @classmethod
    def load_authoritative_state(cls, examination_id: int) -> dict[str, Any]:
        """
        Reconstructs the complete, authoritative examination state directly from PostgreSQL.
        Guarantees that examinations can always resume across server restarts and browser refreshes.
        """
        db = SessionLocal()
        try:
            exam = db.query(Examination).filter(Examination.id == examination_id).first()
            if not exam:
                raise ValueError(f"Examination {examination_id} not found in database.")

            # Latest question asked
            last_qa = (
                db.query(QuestionAsked)
                .filter(QuestionAsked.examination_id == exam.id)
                .order_by(QuestionAsked.order_index.desc())
                .first()
            )

            # Check if answered
            last_answer = None
            last_eval = None
            if last_qa:
                last_answer = (
                    db.query(StudentAnswer)
                    .filter(StudentAnswer.question_asked_id == last_qa.id)
                    .first()
                )
                if last_answer:
                    last_eval_row = (
                        db.query(AnswerEvaluation)
                        .filter(AnswerEvaluation.student_answer_id == last_answer.id)
                        .first()
                    )
                    if last_eval_row:
                        last_eval = {
                            "evaluation_label": last_eval_row.evaluation_label.value,
                            "overall_score": last_eval_row.overall_score,
                            "missing_concepts": last_eval_row.missing_concepts,
                            "mistakes_identified": last_eval_row.mistakes_identified,
                        }

            topic_name = last_qa.topic.name if (last_qa and last_qa.topic) else "General"
            progress_pct = round(
                (exam.questions_asked_count / exam.max_questions) * 100
                if exam.max_questions > 0
                else 0.0,
                1,
            )

            is_complete = exam.status == ExaminationStatus.COMPLETED

            state: dict[str, Any] = {
                "user_id": exam.user_id,
                "document_id": exam.document_id,
                "examination_id": exam.id,
                "thread_id": exam.langgraph_thread_id or f"exam_{exam.id}",
                "questions_asked_count": exam.questions_asked_count,
                "max_questions": exam.max_questions,
                "current_difficulty": exam.current_difficulty.value if hasattr(exam.current_difficulty, "value") else str(exam.current_difficulty),
                "current_topic_id": exam.current_topic_id,
                "current_topic_name": topic_name,
                "progress_pct": progress_pct,
                "is_complete": is_complete,
                "question_asked_id": last_qa.id if last_qa else None,
                "current_question_text": last_qa.question_text if last_qa else None,
                "current_category": (last_qa.category.value if hasattr(last_qa.category, "value") else str(last_qa.category)) if last_qa else "CONCEPTUAL",
                "student_answer_id": last_answer.id if last_answer else None,
                "student_answer": last_answer.answer_text if last_answer else None,
                "last_evaluation": last_eval,
                "last_successful_stage": "STATE_HYDRATED_FROM_POSTGRES",
            }
            return state
        finally:
            db.close()

    @classmethod
    def clear_thread(cls, thread_id: str) -> None:
        """Remove thread state cache on exam completion."""
        checkpointer = cls.get_checkpointer()
        if checkpointer and hasattr(checkpointer, "storage"):
            try:
                keys_to_remove = [k for k in checkpointer.storage if thread_id in str(k)]
                for k in keys_to_remove:
                    del checkpointer.storage[k]
            except Exception as exc:
                logger.debug("Failed to clear checkpointer thread %s: %s", thread_id, exc)
