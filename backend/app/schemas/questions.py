from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.database.models import DifficultyLevel, EvaluationLabel, QuestionCategory


class QuestionBankItemResponse(BaseModel):
    id: int
    document_id: int
    topic_id: Optional[int]
    subtopic_id: Optional[int]
    question_text: str
    category: QuestionCategory
    difficulty: DifficultyLevel
    expected_answer_points: Optional[list[str]]
    source_pages: Optional[list[int]]
    is_used: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionBankListResponse(BaseModel):
    questions: list[QuestionBankItemResponse]
    total: int


class QuestionAskedResponse(BaseModel):
    id: int
    examination_id: int
    question_text: str
    category: QuestionCategory
    difficulty: DifficultyLevel
    topic_id: Optional[int]
    asked_at: datetime
    order_index: int

    model_config = {"from_attributes": True}


class AnswerEvaluationResponse(BaseModel):
    id: int
    student_answer_id: int
    examination_id: int
    evaluation_label: EvaluationLabel
    correctness_score: Optional[float]
    completeness_score: Optional[float]
    conceptual_score: Optional[float]
    reasoning_score: Optional[float]
    application_score: Optional[float]
    overall_score: float
    missing_concepts: Optional[list[str]]
    mistakes_identified: Optional[list[str]]
    evaluation_explanation: Optional[str]
    confidence: Optional[float]
    provider_mode: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
