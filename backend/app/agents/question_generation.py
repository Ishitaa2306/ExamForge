"""
Question Generation Agent — generates a multi-category question bank from document structure.
"""
import logging

from sqlalchemy.orm import Session

from app.database.models import (
    DifficultyLevel,
    DocumentTopic,
    QuestionBank,
    QuestionCategory,
    Subtopic,
)
from app.llm.model_router import get_default_client
from app.prompts.question_prompts import build_question_prompt

logger = logging.getLogger(__name__)

CATEGORIES = [c.value for c in QuestionCategory]
DIFFICULTIES = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]


class QuestionGenerationAgent:
    @staticmethod
    def generate(document_id: int, structure: dict, db: Session) -> int:
        """
        Generate questions for every topic extracted from the document.
        Returns the total count of questions created.
        """
        topics = (
            db.query(DocumentTopic)
            .filter(DocumentTopic.document_id == document_id)
            .all()
        )
        client = get_default_client()
        total = 0

        for topic in topics:
            prompt = build_question_prompt(
                topic_name=topic.name,
                topic_description=topic.description or "",
                document_id=document_id,
            )
            try:
                response = client.generate_json(prompt)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Question gen failed for topic %s: %s", topic.name, exc)
                continue

            for q in response.get("questions", []):
                question = QuestionBank(
                    document_id=document_id,
                    topic_id=topic.id,
                    question_text=q.get("question_text", ""),
                    category=_safe_category(q.get("category")),
                    difficulty=_safe_difficulty(q.get("difficulty")),
                    expected_answer_points=q.get("expected_answer_points"),
                    evaluation_rubric=q.get("evaluation_rubric"),
                    source_pages=q.get("source_pages"),
                )
                db.add(question)
                total += 1

        db.commit()
        logger.info("Generated %d questions for document %d", total, document_id)
        return total


def _safe_category(value: str | None) -> QuestionCategory:
    try:
        return QuestionCategory(value) if value else QuestionCategory.CONCEPTUAL
    except ValueError:
        return QuestionCategory.CONCEPTUAL


def _safe_difficulty(value: str | None) -> DifficultyLevel:
    try:
        return DifficultyLevel(value) if value else DifficultyLevel.MEDIUM
    except ValueError:
        return DifficultyLevel.MEDIUM
