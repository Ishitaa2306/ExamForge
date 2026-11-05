"""
LangGraph Examination Workflow Engine.
Coordinates the strict autonomous examination lifecycle across Google Gemini and IBM Granite.
"""
import logging
from typing import Any

from app.workflows.checkpoint_manager import CheckpointManager
from app.workflows.graph_conditions import should_continue_or_complete
from app.workflows.graph_nodes import (
    assess_knowledge_node,
    complete_examination_node,
    evaluate_answer_node,
    examiner_decision_node,
    initial_question_node,
    persist_answer_node,
)
from app.workflows.graph_state import ExaminationGraphState

logger = logging.getLogger(__name__)


class ExaminationGraph:
    """
    Compiles and executes the autonomous examination workflow graph.
    PostgreSQL maintains durable persistence across execution steps.
    """

    _compiled_graph = None

    @classmethod
    def get_graph(cls):
        """Build and compile the LangGraph StateGraph."""
        if cls._compiled_graph is not None:
            return cls._compiled_graph

        try:
            from langgraph.graph import StateGraph, END  # type: ignore

            builder = StateGraph(ExaminationGraphState)

            # Register Nodes
            builder.add_node("initial_question", initial_question_node)
            builder.add_node("persist_answer", persist_answer_node)
            builder.add_node("evaluate_answer", evaluate_answer_node)
            builder.add_node("assess_knowledge", assess_knowledge_node)
            builder.add_node("examiner_decision", examiner_decision_node)
            builder.add_node("complete_examination", complete_examination_node)

            # Edges
            builder.set_entry_point("initial_question")
            builder.add_edge("initial_question", END)  # Pause to wait for student answer

            # Submission turn flow
            builder.add_edge("persist_answer", "evaluate_answer")
            builder.add_edge("evaluate_answer", "assess_knowledge")

            builder.add_conditional_edges(
                "assess_knowledge",
                should_continue_or_complete,
                {
                    "continue": "examiner_decision",
                    "complete": "complete_examination",
                },
            )

            builder.add_edge("examiner_decision", END)  # Pause with new question for student
            builder.add_edge("complete_examination", END)

            checkpointer = CheckpointManager.get_checkpointer()
            if checkpointer:
                cls._compiled_graph = builder.compile(checkpointer=checkpointer)
            else:
                cls._compiled_graph = builder.compile()

            logger.info("LangGraph examination workflow graph successfully compiled.")
            return cls._compiled_graph

        except Exception as exc:
            logger.warning("LangGraph graph compilation deferred: %s", exc)
            return None

    @classmethod
    def execute_start(cls, examination_id: int) -> dict[str, Any]:
        """
        Executes the initial question generation turn for an examination.
        Reconciles with PostgreSQL to support seamless resumption.
        """
        state = CheckpointManager.load_authoritative_state(examination_id)

        # If already in progress and last question is unanswered, return it directly
        if state.get("question_asked_id") and not state.get("student_answer_id"):
            logger.info("Resuming examination %d on unanswered question %s", examination_id, state["question_asked_id"])
            return state

        # If questions haven't been asked yet
        if state.get("questions_asked_count", 0) == 0:
            result_state = initial_question_node(state)
            return result_state

        return state

    @classmethod
    def execute_submission(
        cls,
        examination_id: int,
        question_asked_id: int,
        student_answer: str,
        time_taken_seconds: int = 0,
    ) -> dict[str, Any]:
        """
        Executes the mandatory strict sequential examination loop:
        1. Persist student answer
        2. IBM Granite answer evaluation
        3. IBM Granite knowledge assessment
        4. Check completion rules
        5. Google Gemini autonomous examiner decision (follow-up vs new question)
        """
        state = CheckpointManager.load_authoritative_state(examination_id)
        state["question_asked_id"] = question_asked_id
        state["student_answer"] = student_answer
        state["time_taken_seconds"] = time_taken_seconds

        # 1. Persist Answer
        state = persist_answer_node(state)

        # 2. Granite Answer Evaluation
        state = evaluate_answer_node(state)

        # 3. Granite Knowledge Assessment
        state = assess_knowledge_node(state)

        # 4. Check completion
        condition = should_continue_or_complete(state)
        if condition == "complete":
            state = complete_examination_node(state)
            return state

        # 5. Gemini Examiner Next Action Decision
        state = examiner_decision_node(state)
        return state
