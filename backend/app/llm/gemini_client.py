"""
Live Gemini client using the google-generativeai SDK.
"""
import json
import logging
from typing import Any

from app.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for live mode")
        self._api_key = api_key
        self._model = None

    def _get_model(self):
        if self._model is None:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                }
            )
        return self._model

    @property
    def model_name(self) -> str:
        return "gemini-1.5-flash"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            return response.text
        except Exception as exc:
            logger.exception("Gemini API call failed: %s", exc)
            raise

    def generate_json(self, prompt: str, **kwargs: Any) -> dict:
        raw = self.generate(prompt, **kwargs)
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            inner = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            text = inner.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning("Failed to parse Gemini JSON response: %s", raw[:200])
            return {"raw_response": raw, "parse_error": True}
