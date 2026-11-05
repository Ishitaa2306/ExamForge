"""
LangGraph conditional edge functions for the examination workflow.
"""


def should_continue_or_complete(state: dict) -> str:
    """
    Edge condition: decide whether to continue questioning or complete the exam.
    Returns the name of the next node.
    """
    if state.get("is_complete"):
        return "complete"

    asked = state.get("questions_asked_count", 0)
    max_q = state.get("max_questions", 20)
    if asked >= max_q:
        return "complete"

    return "continue"


def has_answer_to_evaluate(state: dict) -> str:
    """
    Edge condition: skip evaluation if no answer was provided (first question turn).
    """
    if state.get("student_answer"):
        return "evaluate"
    return "skip_evaluate"
