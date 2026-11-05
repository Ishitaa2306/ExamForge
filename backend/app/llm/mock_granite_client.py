"""
Mock Granite client — realistic content-aware evaluation responses for offline dev/test.
Delegates to mock_gemini_client helper functions but identifies itself as Granite.
"""
import json
from typing import Any

from app.llm.base_client import BaseLLMClient
from app.llm.mock_gemini_client import _make_evaluation, _make_questions


class MockGraniteClient(BaseLLMClient):
    @property
    def model_name(self) -> str:
        return "mock-granite"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        prompt_lower = prompt.lower()

        # Answer evaluation — must check specifically for evaluation context
        if (("student's answer" in prompt_lower or "student answer" in prompt_lower) and
                "evaluat" in prompt_lower):
            answer = ""
            for line in prompt.split("\n"):
                if "student" in line.lower() and ":" in line:
                    answer = line.split(":", 1)[1].strip()
                    break
            result = _make_evaluation(answer)
            # Mark this as Granite evaluation
            result["evaluation_explanation"] = result["evaluation_explanation"].replace("[MOCK]", "[MOCK-GRANITE]")
            result["provider_mode"] = "mock"
            result["model"] = "mock-granite"
            return json.dumps(result)

        # Knowledge assessment — second Granite responsibility
        if any(k in prompt_lower for k in ["knowledge assessment", "topic mastery", "assess", "performance"]):
            return json.dumps({
                "topic_assessments": [
                    {
                        "status": "PARTIALLY_UNDERSTOOD",
                        "strength_score": 0.62,
                        "notes": "[MOCK-GRANITE] Assessment based on available evidence.",
                        "evidence_sufficient": True
                    }
                ],
                "overall_observation": "[MOCK-GRANITE] The student has demonstrated partial mastery of the examined topics.",
                "provider_mode": "mock"
            })

        return json.dumps({"result": "[MOCK-GRANITE] Mock response from Granite client.", "provider_mode": "mock"})

    def generate_json(self, prompt: str, **kwargs: Any) -> dict:
        raw = self.generate(prompt, **kwargs)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"result": raw}
