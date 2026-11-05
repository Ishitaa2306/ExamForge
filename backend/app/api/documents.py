import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.database.models import Document, DocumentStatus, DocumentTopic, QuestionBank, Subtopic, User
from app.schemas.documents import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStructureResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF document for analysis."""
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB} MB limit",
        )
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    # Validate PDF magic bytes
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File does not appear to be a valid PDF",
        )

    # Persist file to disk
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    document = Document(
        user_id=current_user.id,
        filename=safe_name,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        status=DocumentStatus.UPLOADED,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Kick off async analysis automatically
    background_tasks.add_task(
        DocumentService.analyze_document_background, document.id
    )

    return document


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents belonging to the current user."""
    query = db.query(Document).filter(Document.user_id == current_user.id)
    total = query.count()
    docs = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    return DocumentListResponse(documents=docs, total=total)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single document by ID."""
    doc = _get_own_doc(db, document_id, current_user.id)
    return doc


@router.get("/{document_id}/status")
def get_document_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll the processing status of a document."""
    doc = _get_own_doc(db, document_id, current_user.id)
    topic_count = db.query(DocumentTopic).filter(DocumentTopic.document_id == document_id).count()
    question_count = db.query(QuestionBank).filter(QuestionBank.document_id == document_id).count()
    return {
        "id": doc.id,
        "status": doc.status.value,
        "page_count": doc.page_count,
        "word_count": doc.word_count,
        "topic_count": topic_count,
        "question_count": question_count,
        "analyzed_at": doc.analyzed_at,
    }


@router.post("/{document_id}/analyze")
def trigger_analysis(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger (re-)analysis of a document."""
    doc = _get_own_doc(db, document_id, current_user.id)
    if doc.status == DocumentStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis is already in progress",
        )
    doc.status = DocumentStatus.UPLOADED
    db.commit()
    background_tasks.add_task(DocumentService.analyze_document_background, document_id)
    return {"message": "Analysis triggered", "document_id": document_id}


@router.get("/{document_id}/knowledge-map")
def get_knowledge_map(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the full knowledge map (topics, subtopics, concepts) for a document."""
    doc = _get_own_doc(db, document_id, current_user.id)
    if doc.status != DocumentStatus.ANALYZED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not yet analyzed (current status: {doc.status.value})",
        )

    from app.database.models import Concept
    topics = db.query(DocumentTopic).filter(DocumentTopic.document_id == document_id).order_by(DocumentTopic.order_index).all()
    subtopics = db.query(Subtopic).filter(Subtopic.document_id == document_id).order_by(Subtopic.order_index).all()
    concepts = db.query(Concept).filter(Concept.document_id == document_id).all()
    questions = db.query(QuestionBank).filter(QuestionBank.document_id == document_id).all()

    # Build nested structure
    subtopic_map: dict = {}
    for st in subtopics:
        subtopic_map.setdefault(st.topic_id, []).append({
            "id": st.id,
            "name": st.name,
            "description": st.description,
            "concepts": [
                {
                    "id": c.id,
                    "type": c.type.value,
                    "name": c.name,
                    "content": c.content,
                    "page_references": c.page_references,
                }
                for c in concepts if c.subtopic_id == st.id
            ],
        })

    topics_out = []
    for t in topics:
        topic_concepts = [
            {
                "id": c.id,
                "type": c.type.value,
                "name": c.name,
                "content": c.content,
                "page_references": c.page_references,
            }
            for c in concepts if c.topic_id == t.id and c.subtopic_id is None
        ]
        topics_out.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "order_index": t.order_index,
            "page_start": t.page_start,
            "page_end": t.page_end,
            "subtopics": subtopic_map.get(t.id, []),
            "direct_concepts": topic_concepts,
            "question_count": sum(1 for q in questions if q.topic_id == t.id),
        })

    return {
        "document_id": document_id,
        "document_name": doc.original_filename,
        "total_topics": len(topics),
        "total_subtopics": len(subtopics),
        "total_concepts": len(concepts),
        "total_questions": len(questions),
        "topics": topics_out,
    }


@router.get("/{document_id}/questions")
def get_document_questions(
    document_id: int,
    category: str | None = None,
    difficulty: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the question bank for a document."""
    _get_own_doc(db, document_id, current_user.id)
    query = db.query(QuestionBank).filter(QuestionBank.document_id == document_id)
    if category:
        from app.database.models import QuestionCategory
        try:
            query = query.filter(QuestionBank.category == QuestionCategory(category.upper()))
        except ValueError:
            pass
    if difficulty:
        from app.database.models import DifficultyLevel
        try:
            query = query.filter(QuestionBank.difficulty == DifficultyLevel(difficulty.upper()))
        except ValueError:
            pass
    total = query.count()
    questions = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "questions": [
            {
                "id": q.id,
                "topic_id": q.topic_id,
                "question_text": q.question_text,
                "category": q.category.value,
                "difficulty": q.difficulty.value,
                "source_pages": q.source_pages,
            }
            for q in questions
        ],
    }


@router.get("/{document_id}/structure", response_model=DocumentStructureResponse)
def get_document_structure(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full topic/subtopic/concept structure of a document."""
    from app.database.models import Concept

    doc = _get_own_doc(db, document_id, current_user.id)
    topics = db.query(DocumentTopic).filter(DocumentTopic.document_id == document_id).all()
    subtopics = db.query(Subtopic).filter(Subtopic.document_id == document_id).all()
    concepts = db.query(Concept).filter(Concept.document_id == document_id).all()

    return DocumentStructureResponse(
        document=doc, topics=topics, subtopics=subtopics, concepts=concepts
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document and all associated data."""
    doc = _get_own_doc(db, document_id, current_user.id)
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()


def _get_own_doc(db: Session, document_id: int, user_id: int) -> Document:
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc
