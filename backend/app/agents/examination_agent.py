"""
Examination Agent — high-level orchestrator that wraps the LangGraph workflow.
"""
import logging

from sqlalchemy.orm import Session

from app.database.models import Examination

logger = logging.getLogger(__name__)


class ExaminationAgent:
    @staticmethod
    def run_turn(
        db: Session,
        examination: Examination,
        student_answer: str | None = None,
    ) -> dict:
        """
        Execute one turn of the examination workflow via the LangGraph graph.
        Returns a dict with at minimum: {"question_text": str, "is_complete": bool}.
        """
        try:
            from app.workflows.examination_graph import ExaminationGraph

            graph = ExaminationGraph.get_graph()
            result = graph.invoke(
                {
                    "examination_id": examination.id,
                    "document_id": examination.document_id,
                    "student_answer": student_answer,
                },
                config={"configurable": {"thread_id": examination.langgraph_thread_id}},
            )
            return result
        except Exception as exc:  # noqa: BLE001
            logger.exception("ExaminationAgent run_turn failed: %s", exc)
            return {"question_text": "Unable to generate question at this time.", "is_complete": False}
