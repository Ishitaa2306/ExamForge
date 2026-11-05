"""
LangGraph state definition for the examination workflow.
"""
from typing import Any, Optional
from typing_extensions import TypedDict


class ExaminationGraphState(TypedDict, total=False):
    """Shared mutable state passed between LangGraph nodes."""

    # Identity
    examination_id: int
    document_id: int

    # Current turn
    student_answer: Optional[str]
    current_question_id: Optional[int]
    current_question_text: Optional[str]
    current_topic_id: Optional[int]
    current_difficulty: str

    # Progress counters
    questions_asked_count: int
    max_questions: int

    # Evaluation result from last turn
    last_evaluation: Optional[dict]

    # Control
    is_complete: bool
    error: Optional[str]
