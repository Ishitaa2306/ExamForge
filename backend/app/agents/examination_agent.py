"""
Autonomous Examination Agent — central examiner powered by Google Gemini.
Directs examination flow, adapts difficulty, and creates/selects follow-up or new questions.
"""
import logging
from typing import Any
from sqlalchemy.orm import Session

from app.database.models import (
    DifficultyLevel,
    DocumentTopic,
    Examination,
    QuestionAsked,
    QuestionBank,
    QuestionCategory,
    StudentAnswer,
    TopicAssessment,
)
from app.llm.model_router import get_client_for_agent
from app.prompts.examination_prompts import build_examiner_turn_prompt

logger = logging.getLogger(__name__)


class AutonomousExaminerAgent:
    @staticmethod
    def decide_next_question(
        db: Session,
        examination: Examination,
    ) -> dict[str, Any]:
        """
        Gemini analyzes recent turn history and Granite evaluation results,
        then decides the next pedagogical move (Follow-up vs New Question).
        Returns a dict:
        {
            "question_text": str,
            "category": QuestionCategory,
            "difficulty": DifficultyLevel,
            "topic_id": int | None,
            "is_follow_up": bool,
            "question_bank_id": int | None,
            "expected_answer_points": list[str],
            "examiner_reasoning": str
        }
        """
        # 1. Fetch questions already asked
        questions_asked = (
            db.query(QuestionAsked)
            .filter(QuestionAsked.examination_id == examination.id)
            .order_by(QuestionAsked.order_index.asc())
            .all()
        )
        asked_bank_ids = [q.question_id for q in questions_asked if q.question_id is not None]

        # 2. Gather turn history with student answers and Granite evaluations
        turn_history = []
        topic_counts: dict[str, int] = {}

        for qa in questions_asked:
            topic_name = qa.topic.name if qa.topic else "General"
            topic_counts[topic_name] = topic_counts.get(topic_name, 0) + 1

            turn_item: dict[str, Any] = {
                "question_text": qa.question_text,
                "topic_name": topic_name,
                "difficulty": qa.difficulty.value if hasattr(qa.difficulty, "value") else str(qa.difficulty),
                "category": qa.category.value if hasattr(qa.category, "value") else str(qa.category),
            }

            if qa.student_answer:
                turn_item["answer_text"] = qa.student_answer.answer_text
                ev = qa.student_answer.evaluation
                if ev:
                    turn_item["evaluation_label"] = ev.evaluation_label.value if hasattr(ev.evaluation_label, "value") else str(ev.evaluation_label)
                    turn_item["overall_score"] = ev.overall_score
                    turn_item["missing_concepts"] = ev.missing_concepts or []
                    turn_item["mistakes_identified"] = ev.mistakes_identified or []

            # Check if there is a topic assessment
            if qa.topic_id:
                ta = (
                    db.query(TopicAssessment)
                    .filter(
                        TopicAssessment.examination_id == examination.id,
                        TopicAssessment.topic_id == qa.topic_id,
                    )
                    .first()
                )
                if ta:
                    turn_item["topic_status"] = ta.status.value if hasattr(ta.status, "value") else str(ta.status)

            turn_history.append(turn_item)

        # 3. Candidate questions from the repository
        candidate_query = (
            db.query(QuestionBank)
            .filter(QuestionBank.document_id == examination.document_id)
        )
        if asked_bank_ids:
            candidate_query = candidate_query.filter(QuestionBank.id.notin_(asked_bank_ids))

        candidate_questions = candidate_query.limit(10).all()
        candidates_data = [
            {
                "id": q.id,
                "question_text": q.question_text,
                "category": q.category.value if hasattr(q.category, "value") else str(q.category),
                "difficulty": q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
                "topic_id": q.topic_id,
                "topic_name": q.topic.name if q.topic else "General",
                "expected_answer_points": q.expected_answer_points,
            }
            for q in candidate_questions
        ]

        # 4. Invoke Google Gemini Autonomous Examiner
        client = get_client_for_agent("examination")
        exam_context = {
            "document_title": examination.document.original_filename if examination.document else "Academic Exam",
            "max_questions": examination.max_questions,
            "current_topic_id": examination.current_topic_id,
        }

        diff_str = examination.current_difficulty.value if hasattr(examination.current_difficulty, "value") else str(examination.current_difficulty)

        prompt = build_examiner_turn_prompt(
            examination_context=exam_context,
            turn_history=turn_history,
            candidate_questions=candidates_data,
            topic_coverage=topic_counts,
            current_difficulty=diff_str,
        )

        decision = client.generate_json(prompt)
        if isinstance(decision, list) and len(decision) > 0 and isinstance(decision[0], dict):
            decision = decision[0]
        elif not isinstance(decision, dict):
            decision = {}

        action = str(decision.get("decision_action", "NEW_QUESTION")).upper()
        q_text = decision.get("question_text", "").strip()
        category = _safe_category(decision.get("category"))
        difficulty = _safe_difficulty(decision.get("difficulty"))
        topic_id = decision.get("topic_id")
        reasoning = decision.get("examiner_reasoning", "Pedagogical decision by examiner.")
        expected_points = decision.get("expected_answer_points", [])

        # Check if Gemini selected an existing candidate question
        selected_id = decision.get("selected_question_id")
        selected_qb = None
        if selected_id:
            selected_qb = db.query(QuestionBank).filter(QuestionBank.id == selected_id).first()
            if selected_qb and selected_qb.id not in asked_bank_ids:
                q_text = selected_qb.question_text
                category = selected_qb.category
                difficulty = selected_qb.difficulty
                topic_id = selected_qb.topic_id
                expected_points = selected_qb.expected_answer_points or expected_points

        # Application-level validation fallback if q_text was empty
        if not q_text and candidates_data:
            fallback_c = candidates_data[0]
            q_text = fallback_c["question_text"]
            category = _safe_category(fallback_c["category"])
            difficulty = _safe_difficulty(fallback_c["difficulty"])
            topic_id = fallback_c["topic_id"]
            selected_id = fallback_c["id"]
            action = "NEW_QUESTION"

        is_follow_up = action == "FOLLOW_UP" and len(turn_history) > 0

        # Update difficulty on exam if adapted
        examination.current_difficulty = difficulty
        if topic_id:
            examination.current_topic_id = topic_id
        db.commit()

        return {
            "question_text": q_text,
            "category": category,
            "difficulty": difficulty,
            "topic_id": topic_id,
            "is_follow_up": is_follow_up,
            "question_bank_id": selected_id if selected_qb else None,
            "expected_answer_points": expected_points,
            "examiner_reasoning": reasoning,
        }


def _safe_category(value: str | None) -> QuestionCategory:
    if not value:
        return QuestionCategory.CONCEPTUAL
    val_upper = str(value).upper().strip()
    try:
        return QuestionCategory(val_upper)
    except ValueError:
        return QuestionCategory.CONCEPTUAL


def _safe_difficulty(value: str | None) -> DifficultyLevel:
    if not value:
        return DifficultyLevel.MEDIUM
    val_upper = str(value).upper().strip()
    try:
        return DifficultyLevel(val_upper)
    except ValueError:
        return DifficultyLevel.MEDIUM
