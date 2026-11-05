"""
Unit tests for the Six AI Agent responsibilities, prompt builders, and model router.
Tests application mechanics, error handling, and structured output parsing.
"""
import pytest

from app.llm.exceptions import GeminiProviderError, GraniteProviderError
from app.llm.gemini_client import GeminiClient
from app.llm.granite_client import GraniteClient
from app.llm.model_router import AGENT_MODEL_MAPPING, get_client_for_agent
from app.prompts.assessment_prompts import build_assessment_prompt
from app.prompts.document_prompts import build_structure_prompt
from app.prompts.evaluation_prompts import build_evaluation_prompt
from app.prompts.examination_prompts import build_examiner_turn_prompt
from app.prompts.question_prompts import build_question_prompt
from app.prompts.report_prompts import build_report_prompt


def test_agent_model_mapping_exact():
    """Verify exact six-agent responsibility allocation."""
    assert AGENT_MODEL_MAPPING["document_understanding"] == "gemini"
    assert AGENT_MODEL_MAPPING["question_generation"] == "gemini"
    assert AGENT_MODEL_MAPPING["examination"] == "gemini"
    assert AGENT_MODEL_MAPPING["answer_evaluation"] == "granite"
    assert AGENT_MODEL_MAPPING["knowledge_assessment"] == "granite"
    assert AGENT_MODEL_MAPPING["report_generation"] == "gemini"


def test_gemini_client_requires_key():
    """GeminiClient must raise GeminiProviderError when API key is empty."""
    with pytest.raises(GeminiProviderError) as exc_info:
        GeminiClient(api_key="", model_id="gemini-3.8-flash")
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)


def test_gemini_client_requires_model_id():
    """GeminiClient must raise GeminiProviderError when model_id is empty."""
    with pytest.raises(GeminiProviderError) as exc_info:
        GeminiClient(api_key="valid-key", model_id="")
    assert "GEMINI_MODEL_ID is not configured" in str(exc_info.value)


def test_granite_client_requires_credentials():
    """GraniteClient must raise GraniteProviderError when credentials are missing."""
    with pytest.raises(GraniteProviderError) as exc_info:
        GraniteClient(api_key="", project_id="proj-123")
    assert "WATSONX_API_KEY is not configured" in str(exc_info.value)

    with pytest.raises(GraniteProviderError) as exc_info:
        GraniteClient(api_key="valid-key", project_id="")
    assert "WATSONX_PROJECT_ID is not configured" in str(exc_info.value)


def test_document_prompt_builder():
    """Prompt 1: Document Understanding."""
    prompt = build_structure_prompt("Sample lecture notes on Operating Systems: processes, threads, scheduling.")
    assert "Operating Systems" in prompt
    assert "DEFINITION" in prompt
    assert "FORMULA" in prompt
    assert "ALGORITHM" in prompt


def test_question_prompt_builder():
    """Prompt 2: Question Generation."""
    prompt = build_question_prompt(
        topic_name="Memory Management",
        topic_description="Virtual memory, paging, segmentation",
        subtopics=["Paging", "Page Faults"],
    )
    assert "Memory Management" in prompt
    assert "Paging" in prompt
    assert "TRICKY" in prompt
    assert "expected_answer_points" in prompt


def test_examiner_prompt_builder():
    """Prompt 3: Autonomous Examiner."""
    prompt = build_examiner_turn_prompt(
        examination_context={"document_title": "Distributed Systems", "max_questions": 10},
        turn_history=[{
            "question_text": "What is the CAP theorem?",
            "topic_name": "Consensus",
            "difficulty": "MEDIUM",
            "category": "CONCEPTUAL",
            "answer_text": "You can only pick two of Consistency, Availability, Partition tolerance.",
            "evaluation_label": "PARTIALLY_CORRECT",
            "overall_score": 0.65,
            "missing_concepts": ["Network partitions are inevitable in real networks"],
            "mistakes_identified": [],
        }],
        candidate_questions=[],
        topic_coverage={"Consensus": 1},
        current_difficulty="MEDIUM",
    )
    assert "CAP theorem" in prompt
    assert "PARTIALLY_CORRECT" in prompt
    assert "FOLLOW_UP" in prompt


def test_evaluation_prompt_builder():
    """Prompt 5: Answer Evaluation (IBM Granite)."""
    prompt = build_evaluation_prompt(
        question_text="Explain gradient descent.",
        expected_points=["First-order optimization", "Computes loss gradient", "Updates parameters iteratively"],
        student_answer="It moves in the direction of the negative gradient to minimize the loss.",
        context="Gradient descent is an optimization algorithm...",
        difficulty="MEDIUM",
    )
    assert "Correctness (30%)" in prompt
    assert "Completeness (25%)" in prompt
    assert "gradient descent" in prompt.lower()
    assert "negative gradient" in prompt.lower()


def test_assessment_prompt_builder():
    """Prompt 6: Knowledge Assessment (IBM Granite)."""
    prompt = build_assessment_prompt(
        topic_name="Convolutional Neural Networks",
        topic_description="Convolutions, pooling, feature maps",
        evaluations=[{
            "question_text": "What is pooling?",
            "overall_score": 0.90,
            "evaluation_label": "CORRECT",
            "missing_concepts": [],
            "mistakes_identified": [],
        }],
    )
    assert "Convolutional Neural Networks" in prompt
    assert "STRONG" in prompt
    assert "NOT_ASSESSED" in prompt


def test_report_prompt_builder():
    """Prompt 4: Final Report Generation (Google Gemini)."""
    prompt = build_report_prompt(
        examination_summary={"document_title": "Machine Learning", "questions_answered": 5, "max_questions": 5, "overall_score": 0.82},
        topic_assessments=[{"topic_id": 1, "topic_name": "Supervised Learning", "status": "STRONG", "strength_score": 0.9}],
        evaluations_summary=[],
    )
    assert "Supervised Learning" in prompt
    assert "revision_priorities" in prompt
