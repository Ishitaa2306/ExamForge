"""
Tests for AI agent components (mock mode).
"""
import pytest

from app.llm.mock_gemini_client import MockGeminiClient
from app.llm.mock_granite_client import MockGraniteClient
from app.llm.model_router import get_gemini_client, get_granite_client


def test_mock_gemini_generate_returns_string():
    client = MockGeminiClient()
    result = client.generate("Tell me about topics in this document.")
    assert isinstance(result, str)
    assert len(result) > 0


def test_mock_gemini_generate_json_topics():
    client = MockGeminiClient()
    result = client.generate_json("Extract the topic structure from this document.")
    assert isinstance(result, dict)
    assert "topics" in result


def test_mock_gemini_generate_json_questions():
    client = MockGeminiClient()
    result = client.generate_json("Generate questions for this topic.")
    assert isinstance(result, dict)
    assert "questions" in result


def test_mock_gemini_generate_json_evaluation():
    client = MockGeminiClient()
    result = client.generate_json("Evaluate this student answer.")
    assert isinstance(result, dict)
    assert "overall_score" in result


def test_mock_granite_client():
    client = MockGraniteClient()
    assert client.model_name == "mock-granite"
    result = client.generate_json("Extract topics.")
    assert isinstance(result, dict)


def test_model_router_returns_mock_in_mock_mode(monkeypatch):
    # Clear cache so our override takes effect
    get_gemini_client.cache_clear()
    get_granite_client.cache_clear()

    monkeypatch.setattr("app.llm.model_router.settings.AI_PROVIDER_MODE", "mock")
    client = get_gemini_client()
    assert client.model_name == "mock-gemini"

    get_gemini_client.cache_clear()
    get_granite_client.cache_clear()


def test_evaluation_prompt_builds():
    from app.prompts.evaluation_prompts import build_evaluation_prompt

    prompt = build_evaluation_prompt(
        question_text="What is recursion?",
        expected_points=["A function calling itself", "Base case required"],
        student_answer="Recursion is when a function calls itself.",
        context="Recursion is a programming technique...",
    )
    assert "recursion" in prompt.lower()
    assert "student" in prompt.lower()


def test_question_prompt_builds():
    from app.prompts.question_prompts import build_question_prompt

    prompt = build_question_prompt(
        topic_name="Data Structures",
        topic_description="Arrays, linked lists, trees, graphs.",
        document_id=1,
    )
    assert "Data Structures" in prompt
    assert "DEFINITION" in prompt
