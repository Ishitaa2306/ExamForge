"""
FastAPI Examination Session Endpoints.
Manages examination creation, turn submissions, live progress, and manual completion.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.database.models import Document, Examination, ExaminationStatus, QuestionAsked, User
from app.schemas.examinations import (
    ExaminationCompleteResponse,
    ExaminationCreateRequest,
    ExaminationListResponse,
    ExaminationProgressResponse,
    ExaminationResponse,
    NextQuestionResponse,
    SubmitAnswerRequest,
)
from app.services.examination_service import ExaminationService

router = APIRouter()


@router.post("/", response_model=ExaminationResponse, status_code=status.HTTP_201_CREATED)
def create_examination(
    payload: ExaminationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new examination session for a document."""
    doc = (
        db.query(Document)
        .filter(Document.id == payload.document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.status.value != "ANALYZED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be fully analyzed before starting an examination",
        )

    examination = ExaminationService.create_examination(
        db=db,
        user_id=current_user.id,
        document_id=payload.document_id,
        max_questions=payload.max_questions,
    )
    return examination


@router.get("/", response_model=ExaminationListResponse)
def list_examinations(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all examinations for the current user."""
    query = db.query(Examination).filter(Examination.user_id == current_user.id)
    total = query.count()
    exams = query.order_by(Examination.created_at.desc()).offset(skip).limit(limit).all()
    return ExaminationListResponse(examinations=exams, total=total)


@router.get("/{examination_id}", response_model=ExaminationResponse)
def get_examination(
    examination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single examination by ID."""
    exam = _get_own_exam(db, examination_id, current_user.id)
    return exam


@router.post("/{examination_id}/start", response_model=NextQuestionResponse)
def start_examination(
    examination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start an examination or resume an active session.
    Retrieves the first question or returns the active unanswered question.
    """
    exam = _get_own_exam(db, examination_id, current_user.id)
    if exam.status not in (ExaminationStatus.CREATED, ExaminationStatus.IN_PROGRESS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Examination is already {exam.status.value}",
        )

    return ExaminationService.start_or_resume_examination(db=db, examination=exam)


@router.post("/{examination_id}/answer", response_model=NextQuestionResponse)
def submit_answer(
    examination_id: int,
    payload: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit an answer to the current question.
    Executes real Granite evaluation & assessment and Gemini next-action decision.
    """
    exam = _get_own_exam(db, examination_id, current_user.id)
    if exam.status != ExaminationStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit answers — examination is {exam.status.value}",
        )

    # Ensure question_asked belongs to this examination
    qa = (
        db.query(QuestionAsked)
        .filter(
            QuestionAsked.id == payload.question_asked_id,
            QuestionAsked.examination_id == examination_id,
        )
        .first()
    )
    if not qa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in this examination session",
        )

    return ExaminationService.submit_answer_and_advance(db=db, examination=exam, payload=payload)


@router.get("/{examination_id}/progress", response_model=ExaminationProgressResponse)
def get_progress(
    examination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get examination progress summary and topic mastery states."""
    exam = _get_own_exam(db, examination_id, current_user.id)
    return ExaminationService.get_progress(db=db, examination=exam)


@router.post("/{examination_id}/complete", response_model=ExaminationCompleteResponse)
def complete_examination(
    examination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually complete an examination and finalize the report."""
    exam = _get_own_exam(db, examination_id, current_user.id)
    if exam.status == ExaminationStatus.COMPLETED:
        return ExaminationCompleteResponse(
            examination_id=exam.id,
            status=exam.status,
            message="Examination already completed",
        )

    ExaminationService.manual_complete(db=db, examination=exam)
    return ExaminationCompleteResponse(
        examination_id=exam.id,
        status=exam.status,
        message="Examination completed and report finalized",
    )


@router.post("/{examination_id}/abandon", response_model=ExaminationCompleteResponse)
def abandon_examination(
    examination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Abandon an in-progress examination."""
    exam = _get_own_exam(db, examination_id, current_user.id)
    exam.status = ExaminationStatus.ABANDONED
    db.commit()
    return ExaminationCompleteResponse(
        examination_id=exam.id,
        status=exam.status,
        message="Examination abandoned",
    )


def _get_own_exam(db: Session, examination_id: int, user_id: int) -> Examination:
    exam = (
        db.query(Examination)
        .filter(Examination.id == examination_id, Examination.user_id == user_id)
        .first()
    )
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examination not found")
    return exam
