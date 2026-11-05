"""
Live IBM Granite client via watsonx.ai REST API.
Uses the official IBM watsonx.ai text generation endpoint.
"""
import json
import logging
from typing import Any

import httpx

from app.llm.base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class GraniteClient(BaseLLMClient):
    def __init__(
        self,
        api_key: str,
        project_id: str,
        model_id: str = "ibm/granite-13b-instruct-v2",
        url: str = "https://us-south.ml.cloud.ibm.com",
    ):
        if not api_key:
            raise ValueError("WATSONX_API_KEY is required for live mode")
        if not project_id:
            raise ValueError("WATSONX_PROJECT_ID is required for live mode")
        self._api_key = api_key
        self._project_id = project_id
        self._model_id = model_id
        self._base_url = url.rstrip("/")
        self._iam_token: str | None = None

    def _get_iam_token(self) -> str:
        """Obtain an IBM IAM access token."""
        response = httpx.post(
            "https://iam.cloud.ibm.com/identity/token",
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self._api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        response.raise_for_status()
        self._iam_token = response.json()["access_token"]
        return self._iam_token

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
                "max_new_tokens": 2048,
                "min_new_tokens": 10,
                "stop_sequences": [],
                "repetition_penalty": 1.05,
            },
        }

        try:
            response = httpx.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=60,
            )
            if response.status_code == 401:
                # Token may have expired — refresh and retry
                token = self._get_iam_token()
                response = httpx.post(
                    endpoint,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    timeout=60,
                )
            response.raise_for_status()
            result = response.json()
            return result["results"][0]["generated_text"]
        except httpx.HTTPStatusError as exc:
            logger.exception("Granite API HTTP error: %s — %s", exc.response.status_code, exc.response.text)
            raise
        except Exception as exc:
            logger.exception("Granite API call failed: %s", exc)
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
            logger.warning("Failed to parse Granite JSON response: %s", raw[:200])
            return {"raw_response": raw, "parse_error": True}
