from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.database.models import DocumentStatus


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    status: DocumentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    original_filename: str
    file_size: int
    status: DocumentStatus
    page_count: Optional[int]
    word_count: Optional[int]
    created_at: datetime
    updated_at: datetime
    analyzed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class TopicResponse(BaseModel):
    id: int
    document_id: int
    name: str
    description: Optional[str]
    order_index: int
    page_start: Optional[int]
    page_end: Optional[int]

    model_config = {"from_attributes": True}


class SubtopicResponse(BaseModel):
    id: int
    topic_id: int
    name: str
    description: Optional[str]
    order_index: int

    model_config = {"from_attributes": True}


class ConceptResponse(BaseModel):
    id: int
    topic_id: int
    subtopic_id: Optional[int]
    type: str
    name: str
    content: str
    page_references: Optional[list[int]]

    model_config = {"from_attributes": True}


class DocumentStructureResponse(BaseModel):
    document: DocumentResponse
    topics: list[TopicResponse]
    subtopics: list[SubtopicResponse]
    concepts: list[ConceptResponse]
