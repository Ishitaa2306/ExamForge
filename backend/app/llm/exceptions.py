"""
Provider exception definitions for ExamForge real AI integrations.
Never exposes private credentials in error strings.
"""


class AIProviderError(Exception):
    """Base exception for all AI provider errors."""
    def __init__(self, provider: str, message: str, details: str | None = None):
        super().__init__(f"[{provider.upper()} PROVIDER ERROR] {message}")
        self.provider = provider
        self.message = message
        self.details = details


class GeminiProviderError(AIProviderError):
    """Raised when Google Gemini operations fail or credentials are missing."""
    def __init__(self, message: str, details: str | None = None):
        super().__init__("Gemini", message, details)


class GraniteProviderError(AIProviderError):
    """Raised when IBM Granite / watsonx operations fail or credentials are missing."""
    def __init__(self, message: str, details: str | None = None):
        super().__init__("Granite", message, details)

