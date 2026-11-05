"""
LangGraph state definition for the Autonomous Examination Workflow.
Reflects persistent examination execution state.
"""
from typing import Any, Optional
from typing_extensions import TypedDict


class ExaminationGraphState(TypedDict, total=False):
    """Shared state coordinated across LangGraph examination turns."""

    # Identity
    user_id: int
    document_id: int
    examination_id: int
    thread_id: str

    # Current Turn Details
    question_asked_id: Optional[int]
    current_question_text: Optional[str]
    current_category: Optional[str]
    current_difficulty: str
    current_topic_id: Optional[int]
    current_topic_name: Optional[str]
    is_follow_up: bool
    expected_answer_points: Optional[list[str]]

    # Student Submission
    student_answer_id: Optional[int]
    student_answer: Optional[str]
    time_taken_seconds: Optional[int]

    # Evaluation Evidence (Granite)
    last_evaluation: Optional[dict[str, Any]]

    # Knowledge Assessment (Granite)
    topic_assessment: Optional[dict[str, Any]]

    # Progress & Metrics
    questions_asked_count: int
    max_questions: int
    progress_pct: float

    # Next Action Decision (Gemini)
    decision_action: Optional[str]  # "FOLLOW_UP" | "NEW_QUESTION"
    examiner_reasoning: Optional[str]

    # Workflow Control & Fault Tolerance
    last_successful_stage: str
    is_complete: bool
    error: Optional[str]
