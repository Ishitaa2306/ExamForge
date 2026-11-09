"""
Live IBM Granite client via watsonx.ai REST API.
Uses official IBM Cloud IAM authentication and watsonx.ai text generation endpoint.
Strict real inference — no mock responses.
"""
import json
import logging
import re
from typing import Any

import httpx

from app.llm.base_client import BaseLLMClient
from app.llm.exceptions import GraniteProviderError

logger = logging.getLogger(__name__)


class GraniteClient(BaseLLMClient):
    def __init__(
        self,
        api_key: str,
        project_id: str,
        model_id: str = "ibm/granite-4-h-small",
        url: str = "https://us-south.ml.cloud.ibm.com",
    ):
        if not api_key or not api_key.strip():
            raise GraniteProviderError(
                "WATSONX_API_KEY is not configured. Please configure WATSONX_API_KEY in .env"
            )
        if not project_id or not project_id.strip():
            raise GraniteProviderError(
                "WATSONX_PROJECT_ID is not configured. Please configure WATSONX_PROJECT_ID in .env"
            )
        self._api_key = api_key.strip()
        self._project_id = project_id.strip()
        self._model_id = model_id.strip() if model_id else "ibm/granite-4-h-small"
        self._base_url = (url.strip() if url else "https://us-south.ml.cloud.ibm.com").rstrip("/")
        self._iam_token: str | None = None

    def _get_iam_token(self) -> str:
        """Obtain an IBM Cloud IAM bearer token using the configured API key."""
        try:
            response = httpx.post(
                "https://iam.cloud.ibm.com/identity/token",
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self._api_key,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()
            token = response.json().get("access_token")
            if not token:
                raise GraniteProviderError("IAM token response did not contain an access_token.")
            self._iam_token = token
            return self._iam_token
        except httpx.HTTPStatusError as exc:
            logger.error("IBM IAM token exchange failed with HTTP %s: %s", exc.response.status_code, exc.response.text)
            raise GraniteProviderError(
                f"IBM IAM authentication failed (HTTP {exc.response.status_code}). Verify your WATSONX_API_KEY."
            ) from exc
        except Exception as exc:
            logger.exception("Failed to obtain IBM IAM token: %s", exc)
            raise GraniteProviderError(f"IBM IAM connection failed: {exc}") from exc

    @property
    def model_name(self) -> str:
        return self._model_id

    def generate(self, prompt: str, **kwargs: Any) -> str:
        token = self._iam_token or self._get_iam_token()
        endpoint = f"{self._base_url}/ml/v1/text/generation?version=2023-05-29"

        payload = {
            "model_id": self._model_id,
            "project_id": self._project_id,
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": kwargs.get("max_new_tokens", 768),
                "min_new_tokens": kwargs.get("min_new_tokens", 1),
                "stop_sequences": kwargs.get("stop_sequences", []),
                "repetition_penalty": kwargs.get("repetition_penalty", 1.05),
            },
        }

        request_timeout = httpx.Timeout(180.0, connect=30.0, read=180.0)

        try:
            response = httpx.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=request_timeout,
            )

            # Retry once on token expiration (401)
            if response.status_code == 401:
                token = self._get_iam_token()
                response = httpx.post(
                    endpoint,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    timeout=request_timeout,
                )

            response.raise_for_status()
            result = response.json()
            results_arr = result.get("results", [])
            if not results_arr or "generated_text" not in results_arr[0]:
                raise GraniteProviderError("watsonx.ai returned an unexpected response structure.")
            return results_arr[0]["generated_text"]

        except httpx.HTTPStatusError as exc:
            logger.error("Granite API HTTP error: %s — %s", exc.response.status_code, exc.response.text)
            raise GraniteProviderError(
                f"Granite API returned HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            ) from exc
        except GraniteProviderError:
            raise
        except Exception as exc:
            logger.exception("Granite API call failed: %s", exc)
            raise GraniteProviderError(f"Granite API inference failed: {exc}") from exc

    def generate_json(self, prompt: str, **kwargs: Any) -> dict:
        if "<|system|>" not in prompt and "<|user|>" not in prompt:
            formatted_prompt = (
                f"<|system|>\nYou are an AI assistant powered by IBM Granite. "
                f"Your task is to analyze the input and output ONLY a valid RFC-8259 JSON object. "
                f"Do not include markdown fences, comments, introductory text, or explanations outside the JSON.\n"
                f"<|user|>\n{prompt}\n<|assistant|>\n{{"
            )
            prefilled = True
        else:
            formatted_prompt = prompt
            prefilled = False

        raw = self.generate(formatted_prompt, **kwargs)
        text = raw.strip()

        if prefilled and not text.startswith("{"):
            text = "{" + text

        # Remove markdown fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Clean single-line and multi-line comments and trailing commas
        cleaned_text = re.sub(r'//[^\r\n]*', '', text)
        cleaned_text = re.sub(r'/\*.*?\*/', '', cleaned_text, flags=re.DOTALL)
        cleaned_text = re.sub(r',\s*([}\]])', r'\1', cleaned_text).strip()

        def _unwrap(obj: Any) -> Any:
            if isinstance(obj, list) and len(obj) == 1 and isinstance(obj[0], dict):
                return obj[0]
            return obj

        try:
            return _unwrap(json.loads(cleaned_text))
        except json.JSONDecodeError:
            # 1. Try finding outermost { ... }
            first_brace = cleaned_text.find("{")
            last_brace = cleaned_text.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                sub = cleaned_text[first_brace : last_brace + 1]
                try:
                    return _unwrap(json.loads(sub))
                except Exception:
                    pass

            # 2. Try raw_decode from every '{' or '[' index in cleaned_text
            bracket_indices = [i for i, c in enumerate(cleaned_text) if c in ("{", "[")]
            for idx in reversed(bracket_indices):
                try:
                    obj, _ = json.JSONDecoder().raw_decode(cleaned_text[idx:])
                    if isinstance(obj, (dict, list)):
                        return _unwrap(obj)
                except Exception:
                    continue

            # 3. Try regex extraction
            match = re.search(r"(\{.*\}|\[.*\])", cleaned_text, re.DOTALL)
            if match:
                try:
                    return _unwrap(json.loads(match.group()))
                except json.JSONDecodeError:
                    pass

            logger.error("Failed to parse Granite JSON response: %s", raw[:300])
            raise GraniteProviderError(
                "Granite returned an invalid JSON response structure.",
                details=raw[:500],
            )

    def test_connection(self) -> dict:
        """Verify IAM authentication, project access, and model inference."""
        test_prompt = "Return exactly this JSON: {\"status\": \"connected\", \"provider\": \"granite\"}"
        res = self.generate_json(test_prompt)
        return {
            "status": "connected",
            "provider": "granite",
            "model_id": self._model_id,
            "project_id": self._project_id,
            "response": res,
        }
