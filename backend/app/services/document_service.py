"""
Document service — orchestrates the async document analysis pipeline.
"""
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import SessionLocal
from app.database.models import Document, DocumentStatus

logger = logging.getLogger(__name__)


class DocumentService:
    @staticmethod
    def analyze_document_background(document_id: int) -> None:
        """
        Background task: extract text, create embeddings, extract topics/concepts,
        and generate question bank.  Runs in a separate thread (FastAPI BackgroundTasks).
        """
        db: Session = SessionLocal()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return

            document.status = DocumentStatus.PROCESSING
            db.commit()

            # 1. Extract text (pdf_service)
            from app.services.pdf_service import PDFService

            text_pages = PDFService.extract_text(document.file_path)
            page_count = len(text_pages)
            word_count = sum(len(p.split()) for p in text_pages)

            # 2. Chunk + embed document
            from app.services.embedding_service import EmbeddingService

            EmbeddingService.embed_document(
                db=db,
                document=document,
                text_pages=text_pages,
            )

            # 3. Analyse document with AI agent
            from app.agents.document_understanding import DocumentUnderstandingAgent

            structure = DocumentUnderstandingAgent.analyse(
                document_id=document_id,
                text_pages=text_pages,
                db=db,
            )

            # 4. Generate question bank
            from app.agents.question_generation import QuestionGenerationAgent

            QuestionGenerationAgent.generate(
                document_id=document_id,
                structure=structure,
                db=db,
            )

            # 5. Mark complete
            document.page_count = page_count
            document.word_count = word_count
            document.status = DocumentStatus.ANALYZED
            from datetime import datetime, timezone

            document.analyzed_at = datetime.now(timezone.utc)
            db.commit()
            logger.info("Document %s analysed successfully.", document_id)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Document %s analysis failed: %s", document_id, exc)
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.status = DocumentStatus.FAILED
                    db.commit()
            except Exception:  # noqa: BLE001
                pass
        finally:
            db.close()
