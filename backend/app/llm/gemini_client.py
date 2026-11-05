"""
Live Google Gemini client using the google-generativeai SDK.
Strict real inference — no mock responses, no hardcoded models, no silent fallbacks.
"""
import json
import logging
import re
from typing import Any

from app.llm.base_client import BaseLLMClient
from app.llm.exceptions import GeminiProviderError

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model_id: str = ""):
        if not api_key or not api_key.strip():
            raise GeminiProviderError(
                "GEMINI_API_KEY is not configured. Please configure a valid Google Gemini API key in .env"
            )
        if not model_id or not model_id.strip():
            raise GeminiProviderError(
                "GEMINI_MODEL_ID is not configured. Please configure a valid Gemini model ID in .env (e.g. GEMINI_MODEL_ID=gemini-3.8-flash)."
            )
        self._api_key = api_key.strip()
        self._model_id = model_id.strip()
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                import google.generativeai as genai
                from google.api_core.exceptions import NotFound, PermissionDenied
                
                genai.configure(api_key=self._api_key)

                # Pre-verify the model existence and supported methods
                formatted_name = (
                    self._model_id
                    if self._model_id.startswith("models/")
                    else f"models/{self._model_id}"
                )
                try:
                    model_info = genai.get_model(formatted_name)
                    if (
                        hasattr(model_info, "supported_generation_methods")
                        and "generateContent" not in model_info.supported_generation_methods
                    ):
                        raise GeminiProviderError(
                            f"Configured Gemini model '{self._model_id}' does not support 'generateContent'. "
                            f"Supported methods: {model_info.supported_generation_methods}."
                        )
                except NotFound as not_found_exc:
                    raise GeminiProviderError(
                        f"Configured Gemini model '{self._model_id}' was not found for API version v1beta, "
                        f"or is not accessible with the provided GEMINI_API_KEY. "
                        f"Please set a supported model in your root .env file (e.g. GEMINI_MODEL_ID=gemini-3.8-flash)."
                    ) from not_found_exc
                except PermissionDenied as perm_exc:
                    raise GeminiProviderError(
                        f"Access denied for configured Gemini model '{self._model_id}': {perm_exc}. "
                        f"Please check your GEMINI_API_KEY permissions."
                    ) from perm_exc
                except GeminiProviderError:
                    raise
                except Exception as verify_err:
                    # Non-fatal warning if network inspection fails (e.g. permission or rate limit on list)
                    logger.warning("Could not pre-verify model info for '%s': %s", self._model_id, verify_err)

                self._model = genai.GenerativeModel(
                    model_name=self._model_id,
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 8192,
                    },
                )
            except GeminiProviderError:
                raise
            except Exception as exc:
                logger.error("Failed to initialize Google Generative AI model '%s': %s", self._model_id, exc)
                raise GeminiProviderError(
                    f"Failed to initialize Gemini model '{self._model_id}': {exc}"
                ) from exc
        return self._model

    @property
    def model_name(self) -> str:
        return self._model_id

    def generate(self, prompt: str, **kwargs: Any) -> str:
        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            if not response or not response.text:
                raise GeminiProviderError("Gemini returned an empty response.")
            return response.text
        except GeminiProviderError:
            raise
        except Exception as exc:
            logger.exception("Gemini API call failed: %s", exc)
            err_str = str(exc)
            if "404" in err_str or "not found" in err_str.lower() or "no longer available" in err_str.lower():
                raise GeminiProviderError(
                    f"Gemini API inference failed for configured model '{self._model_id}': {exc}. "
                    f"Please update GEMINI_MODEL_ID in .env to a supported model (e.g. gemini-3.8-flash)."
                ) from exc
            raise GeminiProviderError(f"Gemini API inference failed: {exc}") from exc

    def generate_json(self, prompt: str, **kwargs: Any) -> dict:
        json_instruction_prompt = (
            prompt
            + "\n\nCRITICAL: Return ONLY valid, RFC 8259 compliant JSON. Do NOT include markdown code blocks, prefixes, or explanations outside the JSON object."
        )
        raw = self.generate(json_instruction_prompt, **kwargs)
        text = raw.strip()

        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Extract outermost JSON object or array
            match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            logger.error("Failed to parse Gemini JSON response: %s", raw[:300])
            raise GeminiProviderError(
                "Gemini returned an invalid JSON response structure.",
                details=raw[:500],
            )

    def test_connection(self) -> dict:
        """Verify API key authentication and model inference."""
        test_prompt = "Return exactly this JSON: {\"status\": \"connected\", \"provider\": \"gemini\"}"
        res = self.generate_json(test_prompt)
        return {
            "status": "connected",
            "provider": "gemini",
            "model_id": self._model_id,
            "response": res,
        }
