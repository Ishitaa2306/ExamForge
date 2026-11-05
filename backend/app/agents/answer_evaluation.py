"""
Answer Evaluation Agent — scores student answers against expected rubric using an LLM.
"""
import logging
import threading

from app.llm.model_router import get_granite_client
from app.prompts.evaluation_prompts import build_evaluation_prompt

logger = logging.getLogger(__name__)


class AnswerEvaluationAgent:
    @staticmethod
    def evaluate_async(student_answer_id: int) -> None:
        """Fire-and-forget: run evaluation in a daemon thread."""
        t = threading.Thread(
            target=AnswerEvaluationAgent._evaluate,
            args=(student_answer_id,),
            daemon=True,
        )
        t.start()

    @staticmethod
    def _evaluate(student_answer_id: int) -> None:
        """Evaluate a single student answer and persist the AnswerEvaluation row."""
        from app.database.connection import SessionLocal
        from app.database.models import (
            AnswerEvaluation,
            EvaluationLabel,
            QuestionAsked,
            StudentAnswer,
        )

        db = SessionLocal()
        try:
            answer = db.query(StudentAnswer).filter(StudentAnswer.id == student_answer_id).first()
            if not answer:
                return

            qa = db.query(QuestionAsked).filter(QuestionAsked.id == answer.question_asked_id).first()
            if not qa:
                return

            # Retrieve relevant context from vector store
            from app.services.embedding_service import EmbeddingService
            from app.database.models import Examination

            exam = db.query(Examination).filter(Examination.id == answer.examination_id).first()
            context_chunks: list[str] = []
            if exam:
                context_chunks = EmbeddingService.similarity_search(
                    query=qa.question_text,
                    document_id=exam.document_id,
                    n_results=3,
                )

            client = get_granite_client()
            prompt = build_evaluation_prompt(
                question_text=qa.question_text,
                expected_points=[],
                student_answer=answer.answer_text,
                context="\n\n".join(context_chunks),
            )

            try:
                result = client.generate_json(prompt)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Evaluation LLM call failed: %s", exc)
                result = {}

            from app.core.config import settings

            evaluation = AnswerEvaluation(
                student_answer_id=answer.id,
                examination_id=answer.examination_id,
                evaluation_label=_safe_label(result.get("evaluation_label")),
                correctness_score=result.get("correctness_score"),
                completeness_score=result.get("completeness_score"),
                conceptual_score=result.get("conceptual_score"),
                reasoning_score=result.get("reasoning_score"),
                application_score=result.get("application_score"),
                overall_score=result.get("overall_score", 0.0),
                missing_concepts=result.get("missing_concepts"),
                mistakes_identified=result.get("mistakes_identified"),
                evaluation_explanation=result.get("evaluation_explanation"),
                confidence=result.get("confidence"),
                evidence_used=context_chunks[:2] if context_chunks else None,
                provider_mode=settings.AI_PROVIDER_MODE,
            )
            db.add(evaluation)
            db.commit()
            logger.info("Evaluated student answer %d", student_answer_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Answer evaluation failed for answer %d: %s", student_answer_id, exc)
        finally:
            db.close()


def _safe_label(value: str | None):
    from app.database.models import EvaluationLabel

    try:
        return EvaluationLabel(value) if value else EvaluationLabel.UNCLEAR
    except ValueError:
        return EvaluationLabel.UNCLEAR
