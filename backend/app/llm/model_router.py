"""
Model router — returns the correct LLM client based on AI_PROVIDER_MODE.
"""
from functools import lru_cache

from app.core.config import settings
from app.llm.base_client import BaseLLMClient


@lru_cache(maxsize=2)
def get_gemini_client() -> BaseLLMClient:
    """Return a Gemini client (live or mock) based on settings."""
    if settings.AI_PROVIDER_MODE == "live":
        from app.llm.gemini_client import GeminiClient

        return GeminiClient(api_key=settings.GEMINI_API_KEY)
    from app.llm.mock_gemini_client import MockGeminiClient

    return MockGeminiClient()


@lru_cache(maxsize=2)
def get_granite_client() -> BaseLLMClient:
    """Return a Granite client (live or mock) based on settings."""
    if settings.AI_PROVIDER_MODE == "live":
        from app.llm.granite_client import GraniteClient

        return GraniteClient(
            api_key=settings.WATSONX_API_KEY,
            project_id=settings.WATSONX_PROJECT_ID,
            model_id=settings.GRANITE_MODEL_ID,
            url=settings.WATSONX_URL,
        )
    from app.llm.mock_granite_client import MockGraniteClient

    return MockGraniteClient()


def get_default_client() -> BaseLLMClient:
    """Return the primary client (Gemini) for general tasks."""
    return get_gemini_client()
