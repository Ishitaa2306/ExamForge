from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.database.models import Document, KnowledgeProfile, User
from app.schemas.reports import KnowledgeProfileResponse

router = APIRouter()


@router.get("/profile/{document_id}", response_model=KnowledgeProfileResponse)
def get_knowledge_profile(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the user's cumulative knowledge profile for a document."""
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    profile = (
        db.query(KnowledgeProfile)
        .filter(
            KnowledgeProfile.user_id == current_user.id,
            KnowledgeProfile.document_id == document_id,
        )
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No knowledge profile yet — complete an examination first",
        )
    return profile


@router.get("/profiles", response_model=list[KnowledgeProfileResponse])
def list_knowledge_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all knowledge profiles for the current user."""
    return (
        db.query(KnowledgeProfile)
        .filter(KnowledgeProfile.user_id == current_user.id)
        .order_by(KnowledgeProfile.updated_at.desc())
        .all()
    )
