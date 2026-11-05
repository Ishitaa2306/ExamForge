"""
Document Understanding Agent — extracts topic/subtopic/concept structure from a PDF.
"""
import logging

from sqlalchemy.orm import Session

from app.database.models import Concept, ConceptType, DocumentTopic, Subtopic
from app.llm.model_router import get_default_client
from app.prompts.document_prompts import build_structure_prompt

logger = logging.getLogger(__name__)


class DocumentUnderstandingAgent:
    @staticmethod
    def analyse(document_id: int, text_pages: list[str], db: Session) -> dict:
        """
        Calls the LLM to extract document structure.
        Persists DocumentTopic, Subtopic, and Concept rows.
        Returns the raw structure dict for downstream use.
        """
        full_text = "\n\n".join(text_pages[:30])  # cap to first 30 pages
        client = get_default_client()
        prompt = build_structure_prompt(full_text)

        try:
            structure = client.generate_json(prompt)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Document understanding LLM call failed: %s", exc)
            structure = {}

        topics_data: list[dict] = structure.get("topics", [])

        for idx, topic_data in enumerate(topics_data):
            topic = DocumentTopic(
                document_id=document_id,
                name=topic_data.get("name", f"Topic {idx + 1}"),
                description=topic_data.get("description"),
                order_index=topic_data.get("order_index", idx),
                page_start=topic_data.get("page_start"),
                page_end=topic_data.get("page_end"),
            )
            db.add(topic)
            db.flush()  # get topic.id

            for sub_idx, sub_data in enumerate(topic_data.get("subtopics", [])):
                subtopic = Subtopic(
                    topic_id=topic.id,
                    document_id=document_id,
                    name=sub_data.get("name", f"Subtopic {sub_idx + 1}"),
                    description=sub_data.get("description"),
                    order_index=sub_data.get("order_index", sub_idx),
                )
                db.add(subtopic)
                db.flush()

                for concept_data in sub_data.get("concepts", []):
                    concept = Concept(
                        subtopic_id=subtopic.id,
                        topic_id=topic.id,
                        document_id=document_id,
                        type=_safe_concept_type(concept_data.get("type")),
                        name=concept_data.get("name", "Unnamed Concept"),
                        content=concept_data.get("content", ""),
                        page_references=concept_data.get("page_references"),
                    )
                    db.add(concept)

        db.commit()
        logger.info(
            "Document %d: extracted %d topics.", document_id, len(topics_data)
        )
        return structure


def _safe_concept_type(value: str | None) -> ConceptType:
    try:
        return ConceptType(value) if value else ConceptType.CONCEPT
    except ValueError:
        return ConceptType.CONCEPT
