"""
LangGraph Node Implementations for the ExamForge Autonomous Examination Workflow.
Directly orchestrates real Gemini and Granite agents with PostgreSQL persistence.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from app.database.connection import SessionLocal
from app.database.models import (
    DifficultyLevel,
    Examination,
    ExaminationStatus,
    QuestionAsked,
    QuestionCategory,
    StudentAnswer,
)

logger = logging.getLogger(__name__)


def initial_question_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Initial examination node: Gemini Autonomous Examiner selects/formulates Question 1.
    Persists QuestionAsked into PostgreSQL.
    """
    db = SessionLocal()
    try:
        exam = db.query(Examination).filter(Examination.id == state["examination_id"]).first()
        if not exam:
            return {**state, "error": "Examination not found", "is_complete": True}

        if exam.status == ExaminationStatus.CREATED:
            exam.status = ExaminationStatus.IN_PROGRESS
            exam.started_at = datetime.now(timezone.utc)
            db.commit()

        # Check if question 1 was already asked (e.g. on resume)
        existing_qa = (
            db.query(QuestionAsked)
            .filter(QuestionAsked.examination_id == exam.id, QuestionAsked.order_index == 1)
            .first()
        )

        if existing_qa:
            qa = existing_qa
        else:
            from app.agents.examination_agent import AutonomousExaminerAgent
            decision = AutonomousExaminerAgent.decide_next_question(db=db, examination=exam)

            qa = QuestionAsked(
                examination_id=exam.id,
                question_id=decision.get("question_bank_id"),
                question_text=decision["question_text"],
                category=decision["category"],
                difficulty=decision["difficulty"],
                topic_id=decision["topic_id"],
                order_index=1,
            )
            db.add(qa)
            exam.questions_asked_count = 1
            exam.current_topic_id = decision["topic_id"]
            exam.current_difficulty = decision["difficulty"]
            db.commit()
            db.refresh(qa)

        topic_name = qa.topic.name if qa.topic else "General"
        progress_pct = round((1 / exam.max_questions) * 100 if exam.max_questions > 0 else 0.0, 1)

        return {
            **state,
            "question_asked_id": qa.id,
            "current_question_text": qa.question_text,
            "current_category": qa.category.value if hasattr(qa.category, "value") else str(qa.category),
            "current_difficulty": qa.difficulty.value if hasattr(qa.difficulty, "value") else str(qa.difficulty),
            "current_topic_id": qa.topic_id,
            "current_topic_name": topic_name,
            "questions_asked_count": 1,
            "max_questions": exam.max_questions,
            "progress_pct": progress_pct,
            "is_follow_up": False,
            "last_successful_stage": "INITIAL_QUESTION_GENERATED",
            "is_complete": False,
        }
    finally:
        db.close()


def persist_answer_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Persists student's submitted answer into PostgreSQL.
    Prevents duplicate submissions for the same question.
    """
    db = SessionLocal()
    try:
        qa_id = state.get("question_asked_id")
        answer_text = state.get("student_answer", "").strip()
        time_taken = state.get("time_taken_seconds", 0)

        if not qa_id or not answer_text:
            return {**state, "error": "Invalid answer submission: missing question or answer text"}

        # Prevent duplicate submissions
        existing_answer = (
            db.query(StudentAnswer)
            .filter(StudentAnswer.question_asked_id == qa_id)
            .first()
        )

        if existing_answer:
            answer = existing_answer
        else:
            answer = StudentAnswer(
                examination_id=state["examination_id"],
                question_asked_id=qa_id,
                answer_text=answer_text,
                time_taken_seconds=time_taken,
            )
            db.add(answer)
            db.commit()
            db.refresh(answer)

        return {
            **state,
            "student_answer_id": answer.id,
            "last_successful_stage": "ANSWER_PERSISTED",
        }
    finally:
        db.close()


def evaluate_answer_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Synchronously evaluates student's answer using real IBM Granite inference via watsonx.ai.
    Persists AnswerEvaluation row.
    """
    db = SessionLocal()
    try:
        from app.agents.answer_evaluation import AnswerEvaluationAgent

        answer_id = state["student_answer_id"]
        evaluation = AnswerEvaluationAgent.evaluate(db=db, student_answer_id=answer_id)

        eval_data = {
            "evaluation_label": evaluation.evaluation_label.value,
            "overall_score": evaluation.overall_score,
            "correctness_score": evaluation.correctness_score,
            "completeness_score": evaluation.completeness_score,
            "conceptual_score": evaluation.conceptual_score,
            "reasoning_score": evaluation.reasoning_score,
            "application_score": evaluation.application_score,
            "missing_concepts": evaluation.missing_concepts,
            "mistakes_identified": evaluation.mistakes_identified,
            "explanation": evaluation.evaluation_explanation,
            "confidence": evaluation.confidence,
        }

        return {
            **state,
            "last_evaluation": eval_data,
            "last_successful_stage": "GRANITE_ANSWER_EVALUATED",
        }
    finally:
        db.close()


def assess_knowledge_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Synchronously assesses topic mastery using real IBM Granite inference.
    Persists TopicAssessment and updates cumulative KnowledgeProfile.
    """
    db = SessionLocal()
    try:
        from app.agents.knowledge_assessment import KnowledgeAssessmentAgent

        exam = db.query(Examination).filter(Examination.id == state["examination_id"]).first()
        topic_id = state.get("current_topic_id")

        ta_data = None
        if exam and topic_id:
            ta = KnowledgeAssessmentAgent.assess_topic(
                db=db,
                examination=exam,
                topic_id=topic_id,
            )
            ta_data = {
                "topic_id": ta.topic_id,
                "status": ta.status.value,
                "strength_score": ta.strength_score,
                "questions_examined": ta.questions_examined,
            }

        return {
            **state,
            "topic_assessment": ta_data,
            "last_successful_stage": "GRANITE_KNOWLEDGE_ASSESSED",
        }
    finally:
        db.close()


def examiner_decision_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Google Gemini Autonomous Examiner receives Granite evaluation evidence,
    determines next pedagogical move (Follow-up vs New Question),
    and adapts difficulty.
    """
    db = SessionLocal()
    try:
        exam = db.query(Examination).filter(Examination.id == state["examination_id"]).first()
        if not exam:
            return {**state, "is_complete": True}

        # Check completion rules
        if exam.questions_asked_count >= exam.max_questions:
            return {**state, "is_complete": True, "last_successful_stage": "COMPLETION_CONDITIONS_MET"}

        from app.agents.examination_agent import AutonomousExaminerAgent
        decision = AutonomousExaminerAgent.decide_next_question(db=db, examination=exam)

        # Application-level validation & record next question
        new_order = exam.questions_asked_count + 1
        qa = QuestionAsked(
            examination_id=exam.id,
            question_id=decision.get("question_bank_id"),
            question_text=decision["question_text"],
            category=decision["category"],
            difficulty=decision["difficulty"],
            topic_id=decision["topic_id"],
            order_index=new_order,
        )
        db.add(qa)
        exam.questions_asked_count = new_order
        exam.current_topic_id = decision["topic_id"]
        exam.current_difficulty = decision["difficulty"]
        db.commit()
        db.refresh(qa)

        topic_name = qa.topic.name if qa.topic else "General"
        progress_pct = round((new_order / exam.max_questions) * 100 if exam.max_questions > 0 else 0.0, 1)
        is_last = new_order >= exam.max_questions

        return {
            **state,
            "question_asked_id": qa.id,
            "current_question_text": qa.question_text,
            "current_category": qa.category.value if hasattr(qa.category, "value") else str(qa.category),
            "current_difficulty": qa.difficulty.value if hasattr(qa.difficulty, "value") else str(qa.difficulty),
            "current_topic_id": qa.topic_id,
            "current_topic_name": topic_name,
            "is_follow_up": decision.get("is_follow_up", False),
            "examiner_reasoning": decision.get("examiner_reasoning"),
            "questions_asked_count": new_order,
            "progress_pct": progress_pct,
            "is_complete": is_last,
            "student_answer": None,
            "student_answer_id": None,
            "last_successful_stage": "NEXT_QUESTION_PREPARED",
        }
    finally:
        db.close()


def complete_examination_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Finalizes examination in PostgreSQL and invokes Google Gemini Report Generation Agent.
    """
    db = SessionLocal()
    try:
        from app.agents.report_generation import ReportGenerationAgent

        exam = db.query(Examination).filter(Examination.id == state["examination_id"]).first()
        if exam:
            exam.status = ExaminationStatus.COMPLETED
            exam.completed_at = datetime.now(timezone.utc)
            db.commit()

            # Generate and persist final report using Google Gemini
            ReportGenerationAgent.generate(db=db, examination=exam)

        return {
            **state,
            "is_complete": True,
            "last_successful_stage": "EXAMINATION_REPORT_FINALIZED",
        }
    finally:
        db.close()
