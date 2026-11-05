"""
Question Generation Agent — creates multi-category, grounded questions from extracted academic material.
Model Provider: Google Gemini.
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
from app.llm.model_router import get_client_for_agent
from app.prompts.question_prompts import build_question_prompt
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class QuestionGenerationAgent:
    @staticmethod
    def generate(document_id: int, structure: dict, db: Session) -> int:
        """
        Generates comprehensive examination questions for every topic using Google Gemini.
        Returns the total count of questions created and persisted.
        """
        topics = (
            db.query(DocumentTopic)
            .filter(DocumentTopic.document_id == document_id)
            .all()
        )
        if not topics:
            logger.warning("No topics found for document %d to generate questions.", document_id)
            return 0

        client = get_client_for_agent("question_generation")
        total = 0

        for topic in topics:
            subtopics = (
                db.query(Subtopic)
                .filter(Subtopic.topic_id == topic.id)
                .all()
            )
            subtopic_names = [st.name for st in subtopics]

            # Fetch grounding context chunks from ChromaDB for this topic
            context_chunks = EmbeddingService.similarity_search(
                query=f"{topic.name} {topic.description or ''}",
                document_id=document_id,
                n_results=4,
            )
            context_text = "\n\n".join(context_chunks)

            prompt = build_question_prompt(
                topic_name=topic.name,
                topic_description=topic.description or "",
                document_context=context_text,
                subtopics=subtopic_names,
            )

            try:
                response = client.generate_json(prompt)
                questions_data = response.get("questions", [])
            except Exception as exc:
                logger.warning("Question generation failed for topic '%s': %s", topic.name, exc)
                continue

            subtopic_by_name = {st.name.lower(): st.id for st in subtopics}

            for q in questions_data:
                q_text = q.get("question_text", "").strip()
                if not q_text:
                    continue

                subtopic_name = q.get("subtopic_name", "")
                subtopic_id = subtopic_by_name.get(subtopic_name.lower()) if subtopic_name else None

                question = QuestionBank(
                    document_id=document_id,
                    topic_id=topic.id,
                    subtopic_id=subtopic_id,
                    question_text=q_text,
                    category=_safe_category(q.get("category")),
                    difficulty=_safe_difficulty(q.get("difficulty")),
                    expected_answer_points=q.get("expected_answer_points"),
                    evaluation_rubric=q.get("evaluation_rubric"),
                    source_pages=q.get("source_pages"),
                )
                db.add(question)
                total += 1

        db.commit()
        logger.info("Gemini generated %d questions for document %d.", total, document_id)
        return total


def _safe_category(value: str | None) -> QuestionCategory:
    if not value:
        return QuestionCategory.CONCEPTUAL
    val_upper = str(value).upper()
    try:
        return QuestionCategory(val_upper)
    except ValueError:
        return QuestionCategory.CONCEPTUAL


def _safe_difficulty(value: str | None) -> DifficultyLevel:
    if not value:
        return DifficultyLevel.MEDIUM
    val_upper = str(value).upper()
    try:
        return DifficultyLevel(val_upper)
    except ValueError:
        return DifficultyLevel.MEDIUM
