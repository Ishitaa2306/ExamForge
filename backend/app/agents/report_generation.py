"""
Report Generation Agent — builds a narrative ExaminationReport using an LLM.
"""
import logging

from sqlalchemy.orm import Session

from app.database.models import Examination
from app.llm.model_router import get_default_client
from app.prompts.report_prompts import build_report_prompt
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)


class ReportGenerationAgent:
    @staticmethod
    def generate(db: Session, examination: Examination):
        """
        Run knowledge assessment, then build a full report.
        Returns the ExaminationReport ORM instance.
        """
        from app.agents.knowledge_assessment import KnowledgeAssessmentAgent

        # Ensure topic assessments are up to date
        KnowledgeAssessmentAgent.assess(db=db, examination=examination)

        # Generate LLM narrative (optional — enriches recommendations)
        try:
            from app.database.models import TopicAssessment

            assessments = (
                db.query(TopicAssessment)
                .filter(TopicAssessment.examination_id == examination.id)
                .all()
            )
            prompt = build_report_prompt(
                examination_id=examination.id,
                assessments=[
                    {
                        "topic_id": a.topic_id,
                        "status": a.status.value,
                        "strength_score": a.strength_score,
                        "questions_examined": a.questions_examined,
                    }
                    for a in assessments
                ],
            )
            client = get_default_client()
            llm_response = client.generate_json(prompt)
            extra_recommendations: list[str] = llm_response.get("recommendations", [])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Report LLM call failed: %s", exc)
            extra_recommendations = []

        report = ReportService.generate_report(db=db, examination=examination)

        if extra_recommendations:
            existing = report.recommendations or []
            report.recommendations = existing + extra_recommendations
            db.commit()

        return report
