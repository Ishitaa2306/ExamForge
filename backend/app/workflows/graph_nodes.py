"""
LangGraph node implementations for the examination workflow.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def select_question_node(state: dict) -> dict:
    """
    Choose the next question from the question bank.
    Updates state with current_question_text and current_question_id.
    """
    from app.database.connection import SessionLocal
    from app.database.models import (
        DifficultyLevel,
        Examination,
        QuestionAsked,
        QuestionBank,
    )

    db = SessionLocal()
    try:
        exam = db.query(Examination).filter(
            Examination.id == state["examination_id"]
        ).first()
        if not exam:
            return {**state, "error": "Examination not found", "is_complete": True}

        asked_ids = [
            qa.question_id
            for qa in db.query(QuestionAsked)
            .filter(QuestionAsked.examination_id == exam.id)
            .all()
            if qa.question_id is not None
        ]

        difficulty = state.get("current_difficulty", "MEDIUM")
        question = (
            db.query(QuestionBank)
            .filter(
                QuestionBank.document_id == exam.document_id,
                QuestionBank.difficulty == difficulty,
                QuestionBank.id.notin_(asked_ids) if asked_ids else True,
            )
            .first()
        )
        if not question:
            question = (
                db.query(QuestionBank)
                .filter(
                    QuestionBank.document_id == exam.document_id,
                    QuestionBank.id.notin_(asked_ids) if asked_ids else True,
                )
                .first()
            )

        if not question:
            return {**state, "is_complete": True}

        return {
            **state,
            "current_question_id": question.id,
            "current_question_text": question.question_text,
            "current_topic_id": question.topic_id,
        }
    finally:
        db.close()


def evaluate_answer_node(state: dict) -> dict:
    """
    Evaluate the student's answer to the last question.
    Updates state with last_evaluation.
    """
    from app.llm.model_router import get_granite_client
    from app.prompts.evaluation_prompts import build_evaluation_prompt
    from app.services.embedding_service import EmbeddingService

    student_answer = state.get("student_answer", "")
    question_text = state.get("current_question_text", "")
    document_id = state.get("document_id", 0)

    context_chunks = EmbeddingService.similarity_search(
        query=question_text, document_id=document_id, n_results=3
    )

    client = get_granite_client()
    prompt = build_evaluation_prompt(
        question_text=question_text,
        expected_points=[],
        student_answer=student_answer,
        context="\n\n".join(context_chunks),
    )

    try:
        evaluation = client.generate_json(prompt)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Evaluation node LLM call failed: %s", exc)
        evaluation = {"overall_score": 0.0, "evaluation_label": "UNCLEAR"}

    return {**state, "last_evaluation": evaluation}


def adjust_difficulty_node(state: dict) -> dict:
    """
    Adapt the difficulty level based on the last evaluation score.
    """
    evaluation = state.get("last_evaluation") or {}
    score = evaluation.get("overall_score", 0.5)
    current = state.get("current_difficulty", "MEDIUM")

    if score >= 0.8 and current != "HARD":
        new_difficulty = "HARD" if current == "MEDIUM" else "MEDIUM"
    elif score < 0.4 and current != "EASY":
        new_difficulty = "EASY" if current == "MEDIUM" else "MEDIUM"
    else:
        new_difficulty = current

    return {**state, "current_difficulty": new_difficulty}


def complete_examination_node(state: dict) -> dict:
    """Mark the examination as complete in the database."""
    from datetime import datetime, timezone

    from app.database.connection import SessionLocal
    from app.database.models import Examination, ExaminationStatus

    db = SessionLocal()
    try:
        exam = db.query(Examination).filter(
            Examination.id == state["examination_id"]
        ).first()
        if exam:
            exam.status = ExaminationStatus.COMPLETED
            exam.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()

    return {**state, "is_complete": True}
