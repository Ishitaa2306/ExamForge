from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.database.models import Document, QuestionBank, User
from app.schemas.questions import (
    AnswerEvaluationResponse,
    QuestionBankListResponse,
    QuestionBankItemResponse,
)

router = APIRouter()


@router.get("/bank/{document_id}", response_model=QuestionBankListResponse)
def get_question_bank(
    document_id: int,
    category: str | None = None,
    difficulty: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List questions from the bank for a document (with optional filters)."""
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    query = db.query(QuestionBank).filter(QuestionBank.document_id == document_id)
    if category:
        query = query.filter(QuestionBank.category == category)
    if difficulty:
        query = query.filter(QuestionBank.difficulty == difficulty)

    total = query.count()
    questions = query.offset(skip).limit(limit).all()
    return QuestionBankListResponse(questions=questions, total=total)


@router.get("/evaluation/{answer_id}", response_model=AnswerEvaluationResponse)
def get_answer_evaluation(
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the AI evaluation for a specific student answer."""
    from app.database.models import AnswerEvaluation, StudentAnswer, QuestionAsked, Examination

    evaluation = (
        db.query(AnswerEvaluation)
        .join(StudentAnswer, AnswerEvaluation.student_answer_id == StudentAnswer.id)
        .join(Examination, AnswerEvaluation.examination_id == Examination.id)
        .filter(
            AnswerEvaluation.student_answer_id == answer_id,
            Examination.user_id == current_user.id,
        )
        .first()
    )
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return evaluation
