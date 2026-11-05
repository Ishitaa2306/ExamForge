"""
LangGraph examination workflow graph definition.

The graph models the examination state machine:
  START
  → select_question   (Gemini selects next question from bank with topic coverage logic)
  → [condition]       should_continue_or_complete
      ↓ continue
      → wait_for_answer   (state holds the question; caller submits answer via HTTP)
      → evaluate_answer   (Granite evaluates the submitted answer)
      → adjust_difficulty (adapt based on evaluation score)
      → select_question   (loop)
      ↓ complete
      → complete_examination
      → END

Because the examination runs across multiple HTTP requests, the graph is compiled
with a MemorySaver checkpointer so state is preserved between invocations.
"""
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class ExaminationGraph:
    @staticmethod
    @lru_cache(maxsize=1)
    def get_graph():
        """
        Build and return the compiled LangGraph StateGraph.
        Cached so the graph is only compiled once per process.
        The graph uses a MemorySaver checkpointer for cross-request state persistence.
        """
        try:
            from langgraph.graph import StateGraph, END  # type: ignore

            from app.workflows.graph_state import ExaminationGraphState
            from app.workflows.graph_nodes import (
                adjust_difficulty_node,
                complete_examination_node,
                evaluate_answer_node,
                select_question_node,
            )
            from app.workflows.graph_conditions import should_continue_or_complete
            from app.workflows.checkpoint_manager import CheckpointManager

            builder = StateGraph(ExaminationGraphState)

            # ── Register nodes ──────────────────────────────────────────────
            builder.add_node("select_question", select_question_node)
            builder.add_node("evaluate_answer", evaluate_answer_node)
            builder.add_node("adjust_difficulty", adjust_difficulty_node)
            builder.add_node("complete_examination", complete_examination_node)

            # ── Entry point ─────────────────────────────────────────────────
            builder.set_entry_point("select_question")

            # ── After select_question: check whether to continue or complete ─
            builder.add_conditional_edges(
                "select_question",
                should_continue_or_complete,
                {
                    "continue": END,          # Pause and wait for answer via HTTP
                    "complete": "complete_examination",
                },
            )

            # ── Answer submitted: evaluate → adjust → select next ───────────
            builder.add_edge("evaluate_answer", "adjust_difficulty")
            builder.add_edge("adjust_difficulty", "select_question")

            # ── Complete → END ───────────────────────────────────────────────
            builder.add_edge("complete_examination", END)

            checkpointer = CheckpointManager.get_checkpointer()
            if checkpointer:
                graph = builder.compile(checkpointer=checkpointer)
                logger.info("LangGraph examination graph compiled with MemorySaver checkpointer.")
            else:
                graph = builder.compile()
                logger.warning("LangGraph examination graph compiled WITHOUT checkpointer (stateless).")

            return graph

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to compile LangGraph examination graph: %s", exc)

            # Fallback: no-op callable so the app still runs if LangGraph is unavailable
            class _NoopGraph:
                def invoke(self, state: dict, **kwargs) -> dict:
                    logger.warning("Using no-op LangGraph fallback.")
                    return {**state, "is_complete": True}

            return _NoopGraph()

    @staticmethod
    def invoke_select_question(
        examination_id: int,
        document_id: int,
        thread_id: str,
        current_difficulty: str = "MEDIUM",
        questions_asked_count: int = 0,
        max_questions: int = 20,
    ) -> dict:
        """
        Invoke the graph to select the next question.
        Returns the updated state (includes current_question_text etc.).
        """
        from app.workflows.checkpoint_manager import CheckpointManager

        graph = ExaminationGraph.get_graph()
        initial_state = {
            "examination_id": examination_id,
            "document_id": document_id,
            "current_difficulty": current_difficulty,
            "questions_asked_count": questions_asked_count,
            "max_questions": max_questions,
            "is_complete": False,
            "student_answer": None,
        }
        config = CheckpointManager.get_thread_config(thread_id)
        result = graph.invoke(initial_state, config=config)
        return result

    @staticmethod
    def invoke_evaluate_answer(
        examination_id: int,
        document_id: int,
        thread_id: str,
        student_answer: str,
        current_question_text: str,
        current_difficulty: str = "MEDIUM",
        questions_asked_count: int = 0,
        max_questions: int = 20,
    ) -> dict:
        """
        Invoke the graph starting from the evaluate_answer node.
        Used after the student submits an answer.
        """
        from app.workflows.checkpoint_manager import CheckpointManager

        graph = ExaminationGraph.get_graph()
        state = {
            "examination_id": examination_id,
            "document_id": document_id,
            "student_answer": student_answer,
            "current_question_text": current_question_text,
            "current_difficulty": current_difficulty,
            "questions_asked_count": questions_asked_count,
            "max_questions": max_questions,
            "is_complete": False,
        }
        config = CheckpointManager.get_thread_config(thread_id)
        # Resume from evaluate_answer node
        result = graph.invoke(state, config=config)
        return result
