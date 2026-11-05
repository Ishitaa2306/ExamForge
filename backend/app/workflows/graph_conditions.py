"""
LangGraph Conditional Edge Functions for the ExamForge Examination Workflow.
Enforces strict application-level examination rules and completion criteria.
"""
from typing import Any


def should_continue_or_complete(state: dict[str, Any]) -> str:
    """
    Evaluates whether the examination should transition to final completion or continue.
    Returns: 'complete' | 'continue'
    """
    if state.get("is_complete"):
        return "complete"

    asked_count = state.get("questions_asked_count", 0)
    max_questions = state.get("max_questions", 20)

    if asked_count >= max_questions:
        return "complete"

    return "continue"
