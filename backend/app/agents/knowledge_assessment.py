"""
Knowledge Assessment Agent — analyzes topic and concept mastery using IBM Granite via watsonx.ai.
Model Provider: IBM Granite.
"""
import logging
from sqlalchemy.orm import Session

from app.database.models import (
    AnswerEvaluation,
    DocumentTopic,
    Examination,
    KnowledgeProfile,
    QuestionAsked,
    StudentAnswer,
    TopicAssessment,
    TopicAssessmentStatus,
)
from app.llm.model_router import get_client_for_agent
from app.prompts.assessment_prompts import build_assessment_prompt

logger = logging.getLogger(__name__)


class KnowledgeAssessmentAgent:
    @staticmethod
    def assess_topic(
        db: Session,
        examination: Examination,
        topic_id: int,
    ) -> TopicAssessment:
        """
        Assess a single topic using IBM Granite inference on all answers submitted for it so far.
        """
        topic = db.query(DocumentTopic).filter(DocumentTopic.id == topic_id).first()
        topic_name = topic.name if topic else f"Topic {topic_id}"
        topic_desc = topic.description if topic else ""

        # Gather evaluations for this topic in this examination
        evaluations_query = (
            db.query(AnswerEvaluation, QuestionAsked)
            .join(StudentAnswer, AnswerEvaluation.student_answer_id == StudentAnswer.id)
            .join(QuestionAsked, StudentAnswer.question_asked_id == QuestionAsked.id)
            .filter(
                AnswerEvaluation.examination_id == examination.id,
                QuestionAsked.topic_id == topic_id,
            )
            .order_by(QuestionAsked.order_index.asc())
            .all()
        )

        eval_data_list = []
        correct_count = 0
        partial_count = 0
        incorrect_count = 0

        for ev, qa in evaluations_query:
            eval_data_list.append({
                "question_text": qa.question_text,
                "overall_score": ev.overall_score,
                "evaluation_label": ev.evaluation_label.value if hasattr(ev.evaluation_label, "value") else str(ev.evaluation_label),
                "missing_concepts": ev.missing_concepts or [],
                "mistakes_identified": ev.mistakes_identified or [],
            })
            lbl = ev.evaluation_label.value if hasattr(ev.evaluation_label, "value") else str(ev.evaluation_label)
            if lbl == "CORRECT":
                correct_count += 1
            elif lbl == "PARTIALLY_CORRECT":
                partial_count += 1
            else:
                incorrect_count += 1

        count = len(eval_data_list)

        # Existing assessment if any
        existing_ta = (
            db.query(TopicAssessment)
            .filter(
                TopicAssessment.examination_id == examination.id,
                TopicAssessment.topic_id == topic_id,
            )
            .first()
        )

        prev_dict = None
        if existing_ta:
            prev_dict = {
                "status": existing_ta.status.value if hasattr(existing_ta.status, "value") else str(existing_ta.status),
                "strength_score": existing_ta.strength_score,
            }

        # If unexplored or 0 evaluations, never mark as WEAK
        if count == 0:
            status = TopicAssessmentStatus.NOT_ASSESSED
            strength_score = None
            evidence_sufficient = False
            notes = "No questions have been answered on this topic yet."
        else:
            client = get_client_for_agent("knowledge_assessment")
            prompt = build_assessment_prompt(
                topic_name=topic_name,
                topic_description=topic_desc,
                evaluations=eval_data_list,
                previous_assessment=prev_dict,
            )
            try:
                assessment_res = client.generate_json(prompt)
                status_raw = assessment_res.get("status", "PARTIALLY_UNDERSTOOD")
                status = _safe_assessment_status(status_raw)
                strength_score = float(assessment_res.get("strength_score", 0.5))
                evidence_sufficient = bool(assessment_res.get("evidence_sufficient", count >= 2))
                notes = assessment_res.get("qualitative_assessment", "")
            except Exception as exc:
                logger.error("Granite topic assessment inference failed: %s", exc)
                # Re-raise to ensure no silent mock fallback
                raise

        if existing_ta:
            ta = existing_ta
        else:
            ta = TopicAssessment(
                examination_id=examination.id,
                topic_id=topic_id,
            )
            db.add(ta)

        ta.status = status
        ta.questions_examined = count
        ta.correct_count = correct_count
        ta.partial_count = partial_count
        ta.incorrect_count = incorrect_count
        ta.evidence_sufficient = evidence_sufficient
        ta.strength_score = strength_score
        ta.notes = notes

        db.commit()
        db.refresh(ta)
        return ta

    @staticmethod
    def assess_all(db: Session, examination: Examination) -> list[TopicAssessment]:
        """
        Assess all topics for this examination's document, and update the student's cumulative KnowledgeProfile.
        """
        all_topics = (
            db.query(DocumentTopic)
            .filter(DocumentTopic.document_id == examination.document_id)
            .all()
        )

        assessments = []
        for topic in all_topics:
            ta = KnowledgeAssessmentAgent.assess_topic(
                db=db,
                examination=examination,
                topic_id=topic.id,
            )
            assessments.append(ta)

        # Update cumulative KnowledgeProfile for user + document
        KnowledgeAssessmentAgent.update_knowledge_profile(db=db, examination=examination, assessments=assessments)
        return assessments

    @staticmethod
    def update_knowledge_profile(
        db: Session,
        examination: Examination,
        assessments: list[TopicAssessment],
    ) -> KnowledgeProfile:
        """Update or create the cumulative KnowledgeProfile based on current assessments."""
        strong = [ta.topic_id for ta in assessments if ta.status == TopicAssessmentStatus.STRONG]
        partial = [ta.topic_id for ta in assessments if ta.status == TopicAssessmentStatus.PARTIALLY_UNDERSTOOD]
        weak = [ta.topic_id for ta in assessments if ta.status == TopicAssessmentStatus.WEAK]
        not_assessed = [ta.topic_id for ta in assessments if ta.status == TopicAssessmentStatus.NOT_ASSESSED]

        assessed_scores = [ta.strength_score for ta in assessments if ta.strength_score is not None]
        overall = sum(assessed_scores) / len(assessed_scores) if assessed_scores else None

        profile = (
            db.query(KnowledgeProfile)
            .filter(
                KnowledgeProfile.user_id == examination.user_id,
                KnowledgeProfile.document_id == examination.document_id,
            )
            .first()
        )

        if not profile:
            profile = KnowledgeProfile(
                user_id=examination.user_id,
                document_id=examination.document_id,
                total_examinations=1,
            )
            db.add(profile)
        else:
            profile.total_examinations += 1

        profile.strong_topics = strong
        profile.partial_topics = partial
        profile.weak_topics = weak
        profile.not_assessed_topics = not_assessed
        profile.overall_score = overall
        profile.last_examination_id = examination.id

        db.commit()
        db.refresh(profile)
        return profile


def _safe_assessment_status(value: str | None) -> TopicAssessmentStatus:
    if not value:
        return TopicAssessmentStatus.NOT_ASSESSED
    val_upper = str(value).upper().strip()
    try:
        return TopicAssessmentStatus(val_upper)
    except ValueError:
        return TopicAssessmentStatus.PARTIALLY_UNDERSTOOD
