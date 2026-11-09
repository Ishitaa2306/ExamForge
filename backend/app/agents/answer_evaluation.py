"""
Answer Evaluation Agent — semantically evaluates student answers using IBM Granite via watsonx.ai.
Model Provider: IBM Granite.
"""
import logging
from sqlalchemy.orm import Session

from app.database.models import (
    AnswerEvaluation,
    EvaluationLabel,
    Examination,
    QuestionAsked,
    StudentAnswer,
)
from app.llm.model_router import get_client_for_agent
from app.prompts.evaluation_prompts import build_evaluation_prompt
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class AnswerEvaluationAgent:
    @staticmethod
    def evaluate(db: Session, student_answer_id: int) -> AnswerEvaluation:
        """
        Evaluates a single student answer using real IBM Granite inference.
        Returns and commits the persisted AnswerEvaluation row.
        """
        answer = db.query(StudentAnswer).filter(StudentAnswer.id == student_answer_id).first()
        if not answer:
            raise ValueError(f"StudentAnswer with ID {student_answer_id} not found.")

        qa = db.query(QuestionAsked).filter(QuestionAsked.id == answer.question_asked_id).first()
        if not qa:
            raise ValueError(f"QuestionAsked with ID {answer.question_asked_id} not found.")

        exam = db.query(Examination).filter(Examination.id == answer.examination_id).first()
        if not exam:
            raise ValueError(f"Examination with ID {answer.examination_id} not found.")

        # Ground answer evaluation in relevant document chunks via vector similarity
        context_chunks: list[str] = []
        try:
            context_chunks = EmbeddingService.similarity_search(
                query=f"{qa.question_text} {answer.answer_text}",
                document_id=exam.document_id,
                n_results=3,
            )
        except Exception as exc:
            logger.warning("Vector search for evaluation context failed: %s", exc)

        expected_points = []
        rubric = None
        if qa.question:
            expected_points = qa.question.expected_answer_points or []
            rubric = qa.question.evaluation_rubric

        client = get_client_for_agent("answer_evaluation")
        prompt = build_evaluation_prompt(
            question_text=qa.question_text,
            expected_points=expected_points,
            student_answer=answer.answer_text,
            context="\n\n".join(context_chunks),
            rubric=rubric,
            difficulty=qa.difficulty.value if hasattr(qa.difficulty, "value") else str(qa.difficulty),
            category=qa.category.value if hasattr(qa.category, "value") else str(qa.category),
        )

        result = client.generate_json(prompt, max_new_tokens=768)
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            result = result[0]
        elif not isinstance(result, dict):
            result = {}

        # Parse and sanitize scores
        overall_score = float(result.get("overall_score", 0.0))
        overall_score = max(0.0, min(1.0, overall_score))

        label_raw = result.get("evaluation_label", "UNCLEAR")
        label = _safe_label(label_raw)

        # Upsert AnswerEvaluation
        existing_eval = (
            db.query(AnswerEvaluation)
            .filter(AnswerEvaluation.student_answer_id == answer.id)
            .first()
        )

        if existing_eval:
            evaluation = existing_eval
        else:
            evaluation = AnswerEvaluation(
                student_answer_id=answer.id,
                examination_id=answer.examination_id,
                evaluation_label=label,
                overall_score=overall_score,
            )
            db.add(evaluation)

        evaluation.evaluation_label = label
        evaluation.overall_score = overall_score
        evaluation.correctness_score = result.get("correctness_score")
        evaluation.completeness_score = result.get("completeness_score")
        evaluation.conceptual_score = result.get("conceptual_score")
        evaluation.reasoning_score = result.get("reasoning_score")
        evaluation.application_score = result.get("application_score")
        evaluation.missing_concepts = result.get("missing_concepts") or []
        evaluation.mistakes_identified = result.get("mistakes_identified") or []
        evaluation.evaluation_explanation = result.get("evaluation_explanation")
        evaluation.confidence = float(result.get("confidence", 0.9))
        evaluation.evidence_used = context_chunks[:2] if context_chunks else None
        evaluation.provider_mode = "live"

        db.commit()
        db.refresh(evaluation)
        logger.info(
            "IBM Granite evaluated answer %d: Label=%s, Score=%.2f",
            answer.id,
            evaluation.evaluation_label.value,
            evaluation.overall_score,
        )
        return evaluation


def _safe_label(value: str | None) -> EvaluationLabel:
    if not value:
        return EvaluationLabel.UNCLEAR
    val_upper = str(value).upper().strip()
    try:
        return EvaluationLabel(val_upper)
    except ValueError:
        return EvaluationLabel.UNCLEAR
