"""
Model Router — strictly maps the six logical AI responsibilities to their designated live models.
No mock clients or silent fallbacks.

Mapping:
- document_understanding  -> Google Gemini
- question_generation     -> Google Gemini
- examination             -> Google Gemini
- answer_evaluation       -> IBM Granite (watsonx.ai)
- knowledge_assessment    -> IBM Granite (watsonx.ai)
- report_generation       -> Google Gemini
"""
from functools import lru_cache

from app.core.config import settings
from app.llm.base_client import BaseLLMClient
from app.llm.exceptions import AIProviderError, GeminiProviderError, GraniteProviderError
from app.llm.gemini_client import GeminiClient
from app.llm.granite_client import GraniteClient

AGENT_MODEL_MAPPING = {
    "document_understanding": "gemini",
    "question_generation": "gemini",
    "examination": "gemini",
    "answer_evaluation": "granite",
    "knowledge_assessment": "granite",
    "report_generation": "gemini",
}


@lru_cache(maxsize=1)
def get_gemini_client() -> GeminiClient:
    """Return configured live Google Gemini client. Raises GeminiProviderError if unconfigured."""
    if not settings.GEMINI_API_KEY:
        raise GeminiProviderError(
            "GEMINI_API_KEY is not configured in environment. Google Gemini operations require valid credentials."
        )
    return GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model_id=settings.GEMINI_MODEL_ID,
    )


@lru_cache(maxsize=1)
def get_granite_client() -> GraniteClient:
    """Return configured live IBM Granite client. Raises GraniteProviderError if unconfigured."""
    if not settings.WATSONX_API_KEY:
        raise GraniteProviderError(
            "WATSONX_API_KEY is not configured in environment. IBM Granite operations require valid watsonx credentials."
        )
    if not settings.WATSONX_PROJECT_ID:
        raise GraniteProviderError(
            "WATSONX_PROJECT_ID is not configured in environment. IBM Granite operations require a watsonx Project ID."
        )
    return GraniteClient(
        api_key=settings.WATSONX_API_KEY,
        project_id=settings.WATSONX_PROJECT_ID,
        model_id=settings.GRANITE_MODEL_ID,
        url=settings.WATSONX_URL,
    )


def get_client_for_agent(agent_name: str) -> BaseLLMClient:
    """
    Route an agent to its designated AI provider according to AGENT_MODEL_MAPPING.
    Strictly enforces responsibility mapping.
    """
    provider = AGENT_MODEL_MAPPING.get(agent_name)
    if not provider:
        raise AIProviderError(
            provider="router",
            message=f"Unknown agent responsibility '{agent_name}'. Supported: {list(AGENT_MODEL_MAPPING.keys())}",
        )

    if provider == "gemini":
        return get_gemini_client()
    elif provider == "granite":
        return get_granite_client()
    else:
        raise AIProviderError(
            provider=provider,
            message=f"Unsupported provider '{provider}' mapped for agent '{agent_name}'.",
        )


def get_default_client() -> BaseLLMClient:
    """Default general-purpose client mapped to Gemini."""
    return get_gemini_client()
