"""
Document Understanding Agent — extracts subject, modules, topics, subtopics, and concepts from academic PDFs.
Model Provider: Google Gemini.
"""
import logging
from sqlalchemy.orm import Session

from app.database.models import Concept, ConceptType, DocumentTopic, Subtopic
from app.llm.model_router import get_client_for_agent
from app.prompts.document_prompts import build_structure_prompt

logger = logging.getLogger(__name__)


class DocumentUnderstandingAgent:
    @staticmethod
    def analyse(document_id: int, text_pages: list[str], db: Session) -> dict:
        """
        Calls Google Gemini to extract complete academic document structure.
        Persists DocumentTopic, Subtopic, and Concept rows.
        Returns the structure dict for downstream question generation and knowledge mapping.
        """
        # Process complete extracted document text
        page_texts = []
        for p_idx, page in enumerate(text_pages, 1):
            if page.strip():
                page_texts.append(f"--- Page {p_idx} ---\n{page.strip()}")

        full_text = "\n\n".join(page_texts)
        if not full_text.strip():
            logger.warning("Document %d has no extractable text.", document_id)
            return {"topics": []}

        client = get_client_for_agent("document_understanding")
        prompt = build_structure_prompt(full_text)

        structure = client.generate_json(prompt)
        topics_data: list[dict] = structure.get("topics", [])

        if not topics_data:
            logger.warning("Gemini returned 0 topics for document %d.", document_id)
            return structure

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
            db.flush()  # Obtain topic.id

            subtopics_data = topic_data.get("subtopics", [])
            for sub_idx, sub_data in enumerate(subtopics_data):
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
                        name=concept_data.get("name", "Core Concept"),
                        content=concept_data.get("content", ""),
                        page_references=concept_data.get("page_references"),
                    )
                    db.add(concept)

            # If topic has direct concepts without subtopics
            for direct_concept in topic_data.get("concepts", []):
                concept = Concept(
                    subtopic_id=None,
                    topic_id=topic.id,
                    document_id=document_id,
                    type=_safe_concept_type(direct_concept.get("type")),
                    name=direct_concept.get("name", "Core Concept"),
                    content=direct_concept.get("content", ""),
                    page_references=direct_concept.get("page_references"),
                )
                db.add(concept)

        db.commit()
        logger.info(
            "Document %d: successfully extracted and persisted %d topics with Gemini.",
            document_id,
            len(topics_data),
        )
        return structure


def _safe_concept_type(value: str | None) -> ConceptType:
    if not value:
        return ConceptType.CONCEPT
    val_upper = str(value).upper()
    try:
        return ConceptType(val_upper)
    except ValueError:
        return ConceptType.CONCEPT
