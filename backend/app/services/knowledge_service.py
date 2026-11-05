"""
Knowledge service — retrieval helpers for the knowledge assessment agent.
"""
import logging

from sqlalchemy.orm import Session

from app.database.models import DocumentTopic, KnowledgeProfile, TopicAssessment
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class KnowledgeService:
    @staticmethod
    def retrieve_context(document_id: int, query: str, n_results: int = 5) -> list[str]:
        """Return relevant chunks from ChromaDB for a given query."""
        return EmbeddingService.similarity_search(
            query=query,
            document_id=document_id,
            n_results=n_results,
        )

    @staticmethod
    def get_topic_assessment_summary(db: Session, examination_id: int) -> dict:
        """Return a dict of topic_id -> assessment status for an examination."""
        assessments = (
            db.query(TopicAssessment)
            .filter(TopicAssessment.examination_id == examination_id)
            .all()
        )
        return {str(ta.topic_id): ta.status.value for ta in assessments}

    @staticmethod
    def get_knowledge_gaps(db: Session, user_id: int, document_id: int) -> list[str]:
        """Return topic names that the user has historically struggled with."""
        profile = (
            db.query(KnowledgeProfile)
            .filter(
                KnowledgeProfile.user_id == user_id,
                KnowledgeProfile.document_id == document_id,
            )
            .first()
        )
        if not profile or not profile.weak_topics:
            return []

        weak_ids: list[int] = profile.weak_topics
        topics = (
            db.query(DocumentTopic)
            .filter(DocumentTopic.id.in_(weak_ids))
            .all()
        )
        return [t.name for t in topics]
