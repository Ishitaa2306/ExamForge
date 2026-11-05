"""
SQLAlchemy ORM models for ExamForge.

Tables (14):
  users, documents, document_topics, subtopics, concepts,
  document_chunks, question_bank, examinations, questions_asked,
  student_answers, answer_evaluations, topic_assessments,
  knowledge_profiles, examination_reports
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


# ─── Enums ────────────────────────────────────────────────────────────────────


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


class ConceptType(str, enum.Enum):
    DEFINITION = "DEFINITION"
    FORMULA = "FORMULA"
    ALGORITHM = "ALGORITHM"
    CONCEPT = "CONCEPT"


class QuestionCategory(str, enum.Enum):
    DEFINITION = "DEFINITION"
    CONCEPTUAL = "CONCEPTUAL"
    DIFFERENCE = "DIFFERENCE"
    APPLICATION = "APPLICATION"
    NUMERICAL = "NUMERICAL"
    ANALYTICAL = "ANALYTICAL"
    SCENARIO = "SCENARIO"
    TRICKY = "TRICKY"


class DifficultyLevel(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class ExaminationStatus(str, enum.Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class EvaluationLabel(str, enum.Enum):
    CORRECT = "CORRECT"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    INCORRECT = "INCORRECT"
    INCOMPLETE = "INCOMPLETE"
    UNCLEAR = "UNCLEAR"


class TopicAssessmentStatus(str, enum.Enum):
    STRONG = "STRONG"
    PARTIALLY_UNDERSTOOD = "PARTIALLY_UNDERSTOOD"
    WEAK = "WEAK"
    NOT_ASSESSED = "NOT_ASSESSED"


# ─── Helper ───────────────────────────────────────────────────────────────────


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── Models ───────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    examinations = relationship("Examination", back_populates="user", cascade="all, delete-orphan")
    knowledge_profiles = relationship("KnowledgeProfile", back_populates="user", cascade="all, delete-orphan")
    examination_reports = relationship("ExaminationReport", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="documents")
    topics = relationship("DocumentTopic", back_populates="document", cascade="all, delete-orphan")
    subtopics = relationship("Subtopic", back_populates="document", cascade="all, delete-orphan")
    concepts = relationship("Concept", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    question_bank = relationship("QuestionBank", back_populates="document", cascade="all, delete-orphan")
    examinations = relationship("Examination", back_populates="document", cascade="all, delete-orphan")
    knowledge_profiles = relationship("KnowledgeProfile", back_populates="document", cascade="all, delete-orphan")
    examination_reports = relationship("ExaminationReport", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_documents_user_status", "user_id", "status"),)


class DocumentTopic(Base):
    __tablename__ = "document_topics"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="topics")
    subtopics = relationship("Subtopic", back_populates="topic", cascade="all, delete-orphan")
    concepts = relationship("Concept", back_populates="topic", cascade="all, delete-orphan")
    question_bank = relationship("QuestionBank", back_populates="topic")
    examinations = relationship("Examination", foreign_keys="Examination.current_topic_id", back_populates="current_topic")
    questions_asked = relationship("QuestionAsked", back_populates="topic")
    topic_assessments = relationship("TopicAssessment", back_populates="topic", cascade="all, delete-orphan")


class Subtopic(Base):
    __tablename__ = "subtopics"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("document_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    topic = relationship("DocumentTopic", back_populates="subtopics")
    document = relationship("Document", back_populates="subtopics")
    concepts = relationship("Concept", back_populates="subtopic", cascade="all, delete-orphan")
    question_bank = relationship("QuestionBank", back_populates="subtopic")


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    subtopic_id = Column(Integer, ForeignKey("subtopics.id", ondelete="SET NULL"), nullable=True, index=True)
    topic_id = Column(Integer, ForeignKey("document_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(ConceptType), nullable=False)
    name = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    page_references = Column(JSON, nullable=True)  # list of page numbers
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    subtopic = relationship("Subtopic", back_populates="concepts")
    topic = relationship("DocumentTopic", back_populates="concepts")
    document = relationship("Document", back_populates="concepts")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    chroma_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (Index("ix_document_chunks_doc_idx", "document_id", "chunk_index"),)


class QuestionBank(Base):
    __tablename__ = "question_bank"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("document_topics.id", ondelete="SET NULL"), nullable=True, index=True)
    subtopic_id = Column(Integer, ForeignKey("subtopics.id", ondelete="SET NULL"), nullable=True, index=True)
    question_text = Column(Text, nullable=False)
    category = Column(Enum(QuestionCategory), nullable=False)
    difficulty = Column(Enum(DifficultyLevel), nullable=False)
    expected_answer_points = Column(JSON, nullable=True)  # list of strings
    evaluation_rubric = Column(JSON, nullable=True)       # dict
    source_pages = Column(JSON, nullable=True)            # list of page numbers
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="question_bank")
    topic = relationship("DocumentTopic", back_populates="question_bank")
    subtopic = relationship("Subtopic", back_populates="question_bank")
    questions_asked = relationship("QuestionAsked", back_populates="question")

    __table_args__ = (
        Index("ix_question_bank_doc_category_difficulty", "document_id", "category", "difficulty"),
        Index("ix_question_bank_is_used", "is_used"),
    )


class Examination(Base):
    __tablename__ = "examinations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(ExaminationStatus), default=ExaminationStatus.CREATED, nullable=False)
    current_topic_id = Column(Integer, ForeignKey("document_topics.id", ondelete="SET NULL"), nullable=True)
    questions_asked_count = Column(Integer, default=0, nullable=False)
    max_questions = Column(Integer, default=20, nullable=False)
    current_difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    langgraph_thread_id = Column(String(255), nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="examinations")
    document = relationship("Document", back_populates="examinations")
    current_topic = relationship(
        "DocumentTopic",
        foreign_keys=[current_topic_id],
        back_populates="examinations",
    )
    questions_asked = relationship("QuestionAsked", back_populates="examination", cascade="all, delete-orphan")
    student_answers = relationship("StudentAnswer", back_populates="examination", cascade="all, delete-orphan")
    answer_evaluations = relationship("AnswerEvaluation", back_populates="examination", cascade="all, delete-orphan")
    topic_assessments = relationship("TopicAssessment", back_populates="examination", cascade="all, delete-orphan")
    report = relationship("ExaminationReport", back_populates="examination", uselist=False, cascade="all, delete-orphan")
    knowledge_profiles = relationship("KnowledgeProfile", foreign_keys="KnowledgeProfile.last_examination_id", back_populates="last_examination")

    __table_args__ = (Index("ix_examinations_user_status", "user_id", "status"),)


class QuestionAsked(Base):
    __tablename__ = "questions_asked"

    id = Column(Integer, primary_key=True, index=True)
    examination_id = Column(Integer, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("question_bank.id", ondelete="SET NULL"), nullable=True)
    question_text = Column(Text, nullable=False)
    category = Column(Enum(QuestionCategory), nullable=False)
    difficulty = Column(Enum(DifficultyLevel), nullable=False)
    topic_id = Column(Integer, ForeignKey("document_topics.id", ondelete="SET NULL"), nullable=True)
    asked_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)

    # Relationships
    examination = relationship("Examination", back_populates="questions_asked")
    question = relationship("QuestionBank", back_populates="questions_asked")
    topic = relationship("DocumentTopic", back_populates="questions_asked")
    student_answer = relationship("StudentAnswer", back_populates="question_asked", uselist=False, cascade="all, delete-orphan")


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True)
    examination_id = Column(Integer, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    question_asked_id = Column(Integer, ForeignKey("questions_asked.id", ondelete="CASCADE"), nullable=False, unique=True)
    answer_text = Column(Text, nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    time_taken_seconds = Column(Integer, nullable=True)

    # Relationships
    examination = relationship("Examination", back_populates="student_answers")
    question_asked = relationship("QuestionAsked", back_populates="student_answer")
    evaluation = relationship("AnswerEvaluation", back_populates="student_answer", uselist=False, cascade="all, delete-orphan")


class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    student_answer_id = Column(Integer, ForeignKey("student_answers.id", ondelete="CASCADE"), nullable=False, unique=True)
    examination_id = Column(Integer, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluation_label = Column(Enum(EvaluationLabel), nullable=False)

    # Score breakdown (0.0 – 1.0)
    correctness_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    conceptual_score = Column(Float, nullable=True)
    reasoning_score = Column(Float, nullable=True)
    application_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=False)

    missing_concepts = Column(JSON, nullable=True)       # list of strings
    mistakes_identified = Column(JSON, nullable=True)    # list of strings
    evaluation_explanation = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)            # 0.0 – 1.0
    evidence_used = Column(JSON, nullable=True)          # list of chunk/page refs
    provider_mode = Column(String(50), nullable=True)    # "mock" | "live"
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    student_answer = relationship("StudentAnswer", back_populates="evaluation")
    examination = relationship("Examination", back_populates="answer_evaluations")


class TopicAssessment(Base):
    __tablename__ = "topic_assessments"

    id = Column(Integer, primary_key=True, index=True)
    examination_id = Column(Integer, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("document_topics.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(TopicAssessmentStatus), default=TopicAssessmentStatus.NOT_ASSESSED, nullable=False)
    questions_examined = Column(Integer, default=0, nullable=False)
    correct_count = Column(Integer, default=0, nullable=False)
    partial_count = Column(Integer, default=0, nullable=False)
    incorrect_count = Column(Integer, default=0, nullable=False)
    evidence_sufficient = Column(Boolean, default=False, nullable=False)
    strength_score = Column(Float, nullable=True)   # 0.0 – 1.0
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    examination = relationship("Examination", back_populates="topic_assessments")
    topic = relationship("DocumentTopic", back_populates="topic_assessments")

    __table_args__ = (
        Index("ix_topic_assessments_exam_topic", "examination_id", "topic_id", unique=True),
    )


class KnowledgeProfile(Base):
    __tablename__ = "knowledge_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    strong_topics = Column(JSON, nullable=True)        # list of topic ids
    weak_topics = Column(JSON, nullable=True)          # list of topic ids
    partial_topics = Column(JSON, nullable=True)       # list of topic ids
    not_assessed_topics = Column(JSON, nullable=True)  # list of topic ids
    overall_score = Column(Float, nullable=True)
    total_examinations = Column(Integer, default=0, nullable=False)
    last_examination_id = Column(Integer, ForeignKey("examinations.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="knowledge_profiles")
    document = relationship("Document", back_populates="knowledge_profiles")
    last_examination = relationship(
        "Examination",
        foreign_keys=[last_examination_id],
        back_populates="knowledge_profiles",
    )

    __table_args__ = (
        Index("ix_knowledge_profiles_user_doc", "user_id", "document_id", unique=True),
    )


class ExaminationReport(Base):
    __tablename__ = "examination_reports"

    id = Column(Integer, primary_key=True, index=True)
    examination_id = Column(Integer, ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_score = Column(Float, nullable=True)
    topic_scores = Column(JSON, nullable=True)           # dict topic_id -> score
    strong_concepts = Column(JSON, nullable=True)        # list of concept names
    weak_concepts = Column(JSON, nullable=True)          # list of concept names
    partial_concepts = Column(JSON, nullable=True)       # list of concept names
    not_assessed_concepts = Column(JSON, nullable=True)  # list of concept names
    recommendations = Column(JSON, nullable=True)        # list of strings
    provider_mode = Column(String(50), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    examination = relationship("Examination", back_populates="report")
    user = relationship("User", back_populates="examination_reports")
    document = relationship("Document", back_populates="examination_reports")
