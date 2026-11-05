"""
Knowledge Assessment Agent — determines per-topic mastery from answer evaluations.
"""
import logging

from sqlalchemy.orm import Session

from app.database.models import (
    AnswerEvaluation,
    EvaluationLabel,
    Examination,
    QuestionAsked,
    StudentAnswer,
    TopicAssessment,
    TopicAssessmentStatus,
)

logger = logging.getLogger(__name__)

# Minimum number of questions per topic to consider evidence sufficient
MIN_QUESTIONS_FOR_EVIDENCE = 2
STRONG_THRESHOLD = 0.75
WEAK_THRESHOLD = 0.40


class KnowledgeAssessmentAgent:
    @staticmethod
    def assess(db: Session, examination: Examination) -> list[TopicAssessment]:
        """
        Compute per-topic assessments from evaluation scores and persist them.
        Returns all TopicAssessment rows for the examination.
        """
        # Gather evaluations grouped by topic
        evaluations = (
            db.query(AnswerEvaluation, QuestionAsked)
            .join(StudentAnswer, AnswerEvaluation.student_answer_id == StudentAnswer.id)
            .join(QuestionAsked, StudentAnswer.question_asked_id == QuestionAsked.id)
            .filter(AnswerEvaluation.examination_id == examination.id)
            .all()
        )

        topic_data: dict[int, list[AnswerEvaluation]] = {}
        for ev, qa in evaluations:
            if qa.topic_id:
                topic_data.setdefault(qa.topic_id, []).append(ev)

        assessments: list[TopicAssessment] = []
        for topic_id, evs in topic_data.items():
            count = len(evs)
            correct = sum(
                1
                for e in evs
                if e.evaluation_label in (EvaluationLabel.CORRECT,)
            )
            partial = sum(
                1
                for e in evs
                if e.evaluation_label == EvaluationLabel.PARTIALLY_CORRECT
            )
            incorrect = sum(
                1
                for e in evs
                if e.evaluation_label in (
                    EvaluationLabel.INCORRECT,
                    EvaluationLabel.INCOMPLETE,
                    EvaluationLabel.UNCLEAR,
                )
            )

            if count > 0:
                strength_score = (correct + 0.5 * partial) / count
            else:
                strength_score = 0.0

            sufficient = count >= MIN_QUESTIONS_FOR_EVIDENCE
            if not sufficient:
                status = TopicAssessmentStatus.NOT_ASSESSED
            elif strength_score >= STRONG_THRESHOLD:
                status = TopicAssessmentStatus.STRONG
            elif strength_score >= WEAK_THRESHOLD:
                status = TopicAssessmentStatus.PARTIALLY_UNDERSTOOD
            else:
                status = TopicAssessmentStatus.WEAK

            # Upsert
            existing = (
                db.query(TopicAssessment)
                .filter(
                    TopicAssessment.examination_id == examination.id,
                    TopicAssessment.topic_id == topic_id,
                )
                .first()
            )
            if existing:
                ta = existing
            else:
                ta = TopicAssessment(
                    examination_id=examination.id,
                    topic_id=topic_id,
                )
                db.add(ta)

            ta.status = status
            ta.questions_examined = count
            ta.correct_count = correct
            ta.partial_count = partial
            ta.incorrect_count = incorrect
            ta.evidence_sufficient = sufficient
            ta.strength_score = strength_score
            assessments.append(ta)

        db.commit()
        return assessments
