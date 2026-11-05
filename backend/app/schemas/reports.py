from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TopicScoreItem(BaseModel):
    topic_id: int
    topic_name: str
    score: float
    status: str
    questions_examined: int


class ExaminationReportResponse(BaseModel):
    id: int
    examination_id: int
    user_id: int
    document_id: int
    overall_score: Optional[float]
    topic_scores: Optional[dict]
    strong_concepts: Optional[list[str]]
    weak_concepts: Optional[list[str]]
    partial_concepts: Optional[list[str]]
    not_assessed_concepts: Optional[list[str]]
    recommendations: Optional[list[str]]
    provider_mode: Optional[str]
    generated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeProfileResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    strong_topics: Optional[list[int]]
    weak_topics: Optional[list[int]]
    partial_topics: Optional[list[int]]
    not_assessed_topics: Optional[list[int]]
    overall_score: Optional[float]
    total_examinations: int
    last_examination_id: Optional[int]
    updated_at: datetime

    model_config = {"from_attributes": True}
