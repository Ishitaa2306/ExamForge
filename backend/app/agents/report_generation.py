"""
Report Generation Agent — builds comprehensive academic reports from persisted evidence.
Model Provider: Google Gemini.
"""
import logging
from sqlalchemy.orm import Session

from app.database.models import (
    AnswerEvaluation,
    Examination,
    ExaminationReport,
    QuestionAsked,
    StudentAnswer,
    TopicAssessment,
)
from app.llm.model_router import get_client_for_agent
from app.prompts.report_prompts import build_report_prompt

logger = logging.getLogger(__name__)


class ReportGenerationAgent:
    @staticmethod
    def generate(db: Session, examination: Examination) -> ExaminationReport:
        """
        Executes cumulative knowledge assessment across all topics using IBM Granite,
        then invokes Google Gemini to synthesize a deeply grounded, comprehensive academic report.
        Persists and returns the ExaminationReport row.
        """
        from app.agents.knowledge_assessment import KnowledgeAssessmentAgent

        # 1. Ensure all topic assessments and knowledge profile are finalized with Granite
        assessments = KnowledgeAssessmentAgent.assess_all(db=db, examination=examination)

        # 2. Gather all evaluations and question details
        eval_rows = (
            db.query(AnswerEvaluation, QuestionAsked, StudentAnswer)
            .join(StudentAnswer, AnswerEvaluation.student_answer_id == StudentAnswer.id)
            .join(QuestionAsked, StudentAnswer.question_asked_id == QuestionAsked.id)
            .filter(AnswerEvaluation.examination_id == examination.id)
            .order_by(QuestionAsked.order_index.asc())
            .all()
        )

        eval_summary_list = []
        scores = []
        for ev, qa, sa in eval_rows:
            scores.append(ev.overall_score)
            eval_summary_list.append({
                "question_text": qa.question_text,
                "category": qa.category.value if hasattr(qa.category, "value") else str(qa.category),
                "difficulty": qa.difficulty.value if hasattr(qa.difficulty, "value") else str(qa.difficulty),
                "overall_score": ev.overall_score,
                "evaluation_label": ev.evaluation_label.value if hasattr(ev.evaluation_label, "value") else str(ev.evaluation_label),
                "missing_concepts": ev.missing_concepts or [],
                "mistakes_identified": ev.mistakes_identified or [],
            })

        overall_score = sum(scores) / len(scores) if scores else 0.0

        topic_assessment_data = [
            {
                "topic_id": ta.topic_id,
                "topic_name": ta.topic.name if ta.topic else f"Topic {ta.topic_id}",
                "status": ta.status.value if hasattr(ta.status, "value") else str(ta.status),
                "questions_examined": ta.questions_examined,
                "strength_score": ta.strength_score or 0.0,
                "notes": ta.notes,
            }
            for ta in assessments
        ]

        exam_summary = {
            "examination_id": examination.id,
            "document_title": examination.document.original_filename if examination.document else "Academic Examination",
            "questions_answered": len(eval_rows),
            "max_questions": examination.max_questions,
            "overall_score": overall_score,
        }

        # 3. Invoke Google Gemini Report Generation Agent
        client = get_client_for_agent("report_generation")
        prompt = build_report_prompt(
            examination_summary=exam_summary,
            topic_assessments=topic_assessment_data,
            evaluations_summary=eval_summary_list,
        )

        report_data = client.generate_json(prompt)

        # 4. Extract structured fields
        strong_concepts = report_data.get("demonstrated_strengths") or []
        weak_concepts = report_data.get("critical_knowledge_gaps") or []
        partial_concepts = report_data.get("partially_understood_concepts") or []
        not_assessed = report_data.get("not_assessed_areas") or []
        recommendations = report_data.get("revision_priorities") or []

        # Per-topic scores map
        topic_scores = {
            str(ta.topic_id): ta.strength_score
            for ta in assessments
            if ta.strength_score is not None
        }

        # 5. Persist or update ExaminationReport
        existing_report = (
            db.query(ExaminationReport)
            .filter(ExaminationReport.examination_id == examination.id)
            .first()
        )

        if existing_report:
            report = existing_report
        else:
            report = ExaminationReport(
                examination_id=examination.id,
                user_id=examination.user_id,
                document_id=examination.document_id,
            )
            db.add(report)

        report.overall_score = overall_score
        report.topic_scores = topic_scores
        report.strong_concepts = strong_concepts
        report.weak_concepts = weak_concepts
        report.partial_concepts = partial_concepts
        report.not_assessed_concepts = not_assessed
        report.recommendations = recommendations
        report.provider_mode = "live"

        db.commit()
        db.refresh(report)
        logger.info(
            "Gemini generated report for examination %d: Overall Score=%.2f",
            examination.id,
            report.overall_score,
        )
        return report
