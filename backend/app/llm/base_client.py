"""
Abstract base class for all LLM provider clients.
"""
import json
from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier string for this model/provider."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a text response from a prompt string."""

    def generate_json(self, prompt: str, **kwargs: Any) -> dict:
        """Generate and parse a JSON response. Override for streaming/structured output."""
        raw = self.generate(prompt, **kwargs)
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```) and last line (```)
            inner = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            text = inner.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from the text
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {"raw_response": raw, "parse_error": True}
