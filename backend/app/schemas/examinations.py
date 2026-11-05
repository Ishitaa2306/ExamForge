from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.database.models import DifficultyLevel, ExaminationStatus


class ExaminationCreateRequest(BaseModel):
    document_id: int
    max_questions: int = 20


class ExaminationResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    status: ExaminationStatus
    current_topic_id: Optional[int] = None
    questions_asked_count: int
    max_questions: int
    current_difficulty: DifficultyLevel
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    langgraph_thread_id: Optional[str] = None

    model_config = {"from_attributes": True}


class ExaminationListResponse(BaseModel):
    examinations: list[ExaminationResponse]
    total: int


class SubmitAnswerRequest(BaseModel):
    question_asked_id: int
    answer_text: str
    time_taken_seconds: Optional[int] = None


class NextQuestionResponse(BaseModel):
    examination_id: int
    question_asked_id: int
    question_text: str
    category: str
    difficulty: DifficultyLevel
    topic_id: Optional[int] = None
    topic_name: Optional[str] = None
    order_index: int
    is_last: bool = False
    progress_pct: float = 0.0


class ExaminationCompleteResponse(BaseModel):
    examination_id: int
    status: ExaminationStatus
    message: str


class TopicProgressItem(BaseModel):
    topic_id: int
    topic_name: str
    questions_examined: int
    status: str
    strength_score: Optional[float] = None


class ExaminationProgressResponse(BaseModel):
    examination_id: int
    status: ExaminationStatus
    questions_asked: int
    max_questions: int
    progress_pct: float
    current_difficulty: DifficultyLevel
    topics_covered: list[TopicProgressItem]
    total_topics: int
