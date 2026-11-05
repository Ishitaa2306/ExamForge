"""
Mock Gemini client — returns realistic content-aware responses for offline dev/test.
All responses are clearly labelled as MOCK mode.
"""
import json
import random
from typing import Any

from app.llm.base_client import BaseLLMClient


def _make_topic_structure(text_hint: str = "") -> dict:
    """Generate a plausible topic structure based on text hints."""
    topics = [
        {
            "name": "Introduction and Foundations",
            "description": "Core concepts, definitions and historical background of the subject.",
            "order_index": 0,
            "page_start": 1,
            "page_end": 8,
            "subtopics": [
                {
                    "name": "Definition and Scope",
                    "description": "What the subject covers and its boundaries.",
                    "order_index": 0,
                    "concepts": [
                        {
                            "type": "DEFINITION",
                            "name": "Core Definition",
                            "content": "The formal definition of the primary subject of study.",
                            "page_references": [1, 2]
                        },
                        {
                            "type": "CONCEPT",
                            "name": "Fundamental Principles",
                            "content": "The guiding principles that underpin the entire subject area.",
                            "page_references": [3]
                        }
                    ]
                },
                {
                    "name": "Historical Development",
                    "description": "How the field evolved over time.",
                    "order_index": 1,
                    "concepts": [
                        {
                            "type": "CONCEPT",
                            "name": "Key Milestones",
                            "content": "Significant developments that shaped the modern understanding of the subject.",
                            "page_references": [4, 5]
                        }
                    ]
                }
            ]
        },
        {
            "name": "Core Concepts and Mechanisms",
            "description": "The primary theoretical constructs and how they operate.",
            "order_index": 1,
            "page_start": 9,
            "page_end": 25,
            "subtopics": [
                {
                    "name": "Primary Mechanisms",
                    "description": "How the core processes work.",
                    "order_index": 0,
                    "concepts": [
                        {
                            "type": "CONCEPT",
                            "name": "Process Model",
                            "content": "The step-by-step mechanism by which the primary process operates.",
                            "page_references": [10, 11]
                        },
                        {
                            "type": "ALGORITHM",
                            "name": "Core Algorithm",
                            "content": "The algorithmic steps underlying the primary computational or analytical process.",
                            "page_references": [12]
                        }
                    ]
                },
                {
                    "name": "Key Relationships",
                    "description": "How different components interact.",
                    "order_index": 1,
                    "concepts": [
                        {
                            "type": "FORMULA",
                            "name": "Primary Formula",
                            "content": "The mathematical relationship expressing the core quantitative behaviour.",
                            "page_references": [15]
                        }
                    ]
                }
            ]
        },
        {
            "name": "Applications and Use Cases",
            "description": "Real-world applications and practical implementations.",
            "order_index": 2,
            "page_start": 26,
            "page_end": 40,
            "subtopics": [
                {
                    "name": "Practical Applications",
                    "description": "How theory applies in practice.",
                    "order_index": 0,
                    "concepts": [
                        {
                            "type": "CONCEPT",
                            "name": "Application Domain",
                            "content": "The primary domains where the subject is applied.",
                            "page_references": [27, 28]
                        }
                    ]
                }
            ]
        },
        {
            "name": "Advanced Topics and Current Research",
            "description": "Contemporary developments and open problems.",
            "order_index": 3,
            "page_start": 41,
            "page_end": 55,
            "subtopics": [
                {
                    "name": "Recent Developments",
                    "description": "State-of-the-art advances.",
                    "order_index": 0,
                    "concepts": [
                        {
                            "type": "CONCEPT",
                            "name": "Emerging Approaches",
                            "content": "New methodologies and paradigms currently being explored.",
                            "page_references": [42, 43]
                        }
                    ]
                },
                {
                    "name": "Limitations and Open Problems",
                    "description": "Known constraints and unsolved challenges.",
                    "order_index": 1,
                    "concepts": [
                        {
                            "type": "CONCEPT",
                            "name": "Key Limitations",
                            "content": "Fundamental constraints that limit the applicability or performance of current approaches.",
                            "page_references": [50]
                        }
                    ]
                }
            ]
        }
    ]
    return {"topics": topics}


def _make_questions(topic_name: str = "General Topic") -> dict:
    """Generate a realistic set of questions for a topic."""
    questions = [
        {
            "question_text": f"Define the concept of '{topic_name}' and explain its significance in the broader field.",
            "category": "DEFINITION",
            "difficulty": "EASY",
            "expected_answer_points": [
                f"Precise definition of {topic_name}",
                "Context within the broader field",
                "Why it is significant"
            ],
            "evaluation_rubric": {
                "key_concepts": ["definition", "significance", "context"],
                "partial_credit": True,
                "minimum_points_for_correct": 2
            },
            "source_pages": [1, 2]
        },
        {
            "question_text": f"Explain the fundamental principles underlying {topic_name}. What are the core assumptions it relies on?",
            "category": "CONCEPTUAL",
            "difficulty": "MEDIUM",
            "expected_answer_points": [
                "At least two core principles identified",
                "Explanation of each principle",
                "Description of underlying assumptions",
                "Relationship between principles"
            ],
            "evaluation_rubric": {
                "key_concepts": ["principles", "assumptions", "relationships"],
                "partial_credit": True,
                "minimum_points_for_correct": 3
            },
            "source_pages": [3, 4, 5]
        },
        {
            "question_text": f"Compare and contrast the two primary approaches discussed in {topic_name}. What are the trade-offs between them?",
            "category": "DIFFERENCE",
            "difficulty": "MEDIUM",
            "expected_answer_points": [
                "Both approaches clearly identified",
                "Key similarities noted",
                "Key differences explained",
                "Trade-offs analysed with justification"
            ],
            "evaluation_rubric": {
                "key_concepts": ["comparison", "contrast", "trade-offs"],
                "partial_credit": True,
                "minimum_points_for_correct": 3
            },
            "source_pages": [6, 7]
        },
        {
            "question_text": f"Given a real-world scenario where {topic_name} is applied, describe how you would implement the core methodology step by step.",
            "category": "APPLICATION",
            "difficulty": "HARD",
            "expected_answer_points": [
                "Scenario correctly interpreted",
                "Methodology steps clearly described",
                "Steps are in correct order",
                "Edge cases or limitations acknowledged"
            ],
            "evaluation_rubric": {
                "key_concepts": ["implementation", "methodology", "steps"],
                "partial_credit": True,
                "minimum_points_for_correct": 3
            },
            "source_pages": [10, 11, 12]
        },
        {
            "question_text": f"Analyse the limitations of the current approaches in {topic_name}. What conditions would cause them to fail, and how might these limitations be addressed?",
            "category": "ANALYTICAL",
            "difficulty": "HARD",
            "expected_answer_points": [
                "At least two limitations identified",
                "Failure conditions described precisely",
                "Potential solutions or workarounds proposed",
                "Analysis is grounded in theoretical understanding"
            ],
            "evaluation_rubric": {
                "key_concepts": ["limitations", "failure conditions", "solutions"],
                "partial_credit": True,
                "minimum_points_for_correct": 3
            },
            "source_pages": [15, 16]
        },
        {
            "question_text": f"A common misconception about {topic_name} is that it always produces optimal results. Explain why this is incorrect and identify the conditions under which suboptimal outcomes arise.",
            "category": "TRICKY",
            "difficulty": "HARD",
            "expected_answer_points": [
                "Misconception clearly refuted",
                "Conditions for suboptimal outcomes identified",
                "Specific examples provided",
                "Theoretical justification given"
            ],
            "evaluation_rubric": {
                "key_concepts": ["misconception", "suboptimal conditions", "justification"],
                "partial_credit": True,
                "minimum_points_for_correct": 2
            },
            "source_pages": [20, 21]
        },
        {
            "question_text": f"Consider a scenario in which an organisation is deciding whether to adopt {topic_name} for a critical system. What factors should they evaluate, and what recommendation would you make?",
            "category": "SCENARIO",
            "difficulty": "HARD",
            "expected_answer_points": [
                "Key evaluation factors identified",
                "Benefits and risks assessed",
                "Recommendation clearly stated with justification",
                "Alternative approaches considered"
            ],
            "evaluation_rubric": {
                "key_concepts": ["evaluation factors", "recommendation", "justification"],
                "partial_credit": True,
                "minimum_points_for_correct": 3
            },
            "source_pages": [25, 26]
        },
        {
            "question_text": f"What is the relationship between {topic_name} and adjacent concepts in this domain? How do they interact or depend on one another?",
            "category": "CONCEPTUAL",
            "difficulty": "MEDIUM",
            "expected_answer_points": [
                "Adjacent concepts correctly identified",
                "Relationships described accurately",
                "Dependencies or interactions explained",
                "Practical implications noted"
            ],
            "evaluation_rubric": {
                "key_concepts": ["relationships", "dependencies", "interactions"],
                "partial_credit": True,
                "minimum_points_for_correct": 2
            },
            "source_pages": [8, 9]
        }
    ]
    return {"questions": questions}


def _make_evaluation(answer: str) -> dict:
    """Generate a realistic evaluation based on answer length and content."""
    word_count = len(answer.split()) if answer else 0

    if word_count == 0:
        return {
            "evaluation_label": "UNCLEAR",
            "correctness_score": 0.0,
            "completeness_score": 0.0,
            "conceptual_score": 0.0,
            "reasoning_score": 0.0,
            "application_score": 0.0,
            "overall_score": 0.0,
            "missing_concepts": ["No answer provided"],
            "mistakes_identified": [],
            "evaluation_explanation": "[MOCK] No answer was submitted.",
            "confidence": 1.0,
            "provider_mode": "mock"
        }
    elif word_count < 10:
        return {
            "evaluation_label": "INCOMPLETE",
            "correctness_score": 0.2,
            "completeness_score": 0.1,
            "conceptual_score": 0.2,
            "reasoning_score": 0.1,
            "application_score": 0.1,
            "overall_score": 0.15,
            "missing_concepts": ["Detailed explanation", "Supporting evidence", "Examples"],
            "mistakes_identified": ["Answer is too brief to demonstrate understanding"],
            "evaluation_explanation": "[MOCK] The answer is far too brief to demonstrate meaningful understanding. A complete answer should explain the concept, provide supporting details, and where applicable, give examples.",
            "confidence": 0.9,
            "provider_mode": "mock"
        }
    elif word_count < 30:
        score = random.uniform(0.35, 0.55)
        return {
            "evaluation_label": "PARTIALLY_CORRECT",
            "correctness_score": round(score + 0.1, 2),
            "completeness_score": round(score - 0.1, 2),
            "conceptual_score": round(score, 2),
            "reasoning_score": round(score - 0.05, 2),
            "application_score": round(score - 0.1, 2),
            "overall_score": round(score, 2),
            "missing_concepts": ["Further elaboration needed", "Supporting examples"],
            "mistakes_identified": [],
            "evaluation_explanation": f"[MOCK] The answer demonstrates partial understanding. You have identified some key points but the response lacks sufficient depth and detail. A stronger answer would elaborate on the mechanisms, provide concrete examples, and address potential edge cases.",
            "confidence": 0.85,
            "provider_mode": "mock"
        }
    elif word_count < 80:
        score = random.uniform(0.55, 0.80)
        return {
            "evaluation_label": "PARTIALLY_CORRECT",
            "correctness_score": round(score + 0.05, 2),
            "completeness_score": round(score, 2),
            "conceptual_score": round(score + 0.05, 2),
            "reasoning_score": round(score - 0.05, 2),
            "application_score": round(score - 0.1, 2),
            "overall_score": round(score, 2),
            "missing_concepts": ["Deeper theoretical grounding", "Critical analysis"],
            "mistakes_identified": [],
            "evaluation_explanation": f"[MOCK] Good attempt. The answer covers the main ideas and shows reasonable understanding. To achieve full marks, you should provide stronger theoretical grounding, more precise terminology, and deeper critical analysis of the concepts involved.",
            "confidence": 0.82,
            "provider_mode": "mock"
        }
    else:
        score = random.uniform(0.80, 0.95)
        return {
            "evaluation_label": "CORRECT",
            "correctness_score": round(score, 2),
            "completeness_score": round(score - 0.05, 2),
            "conceptual_score": round(score + 0.02, 2),
            "reasoning_score": round(score - 0.03, 2),
            "application_score": round(score - 0.05, 2),
            "overall_score": round(score, 2),
            "missing_concepts": [],
            "mistakes_identified": [],
            "evaluation_explanation": f"[MOCK] Excellent answer. The response demonstrates strong conceptual understanding, accurate use of terminology, and well-structured reasoning. The answer addresses the key aspects of the question thoroughly.",
            "confidence": 0.88,
            "provider_mode": "mock"
        }


def _make_next_question(topic_name: str = "General Topic", difficulty: str = "MEDIUM") -> dict:
    """Generate an examination agent response with next question selection."""
    return {
        "next_question_strategy": "cross_question",
        "selected_difficulty": difficulty,
        "reasoning": f"[MOCK] Based on the student's performance on the previous answer, we will continue examining {topic_name} at {difficulty} difficulty.",
        "should_continue": True
    }


def _make_report(overall_score: float = 0.65) -> dict:
    """Generate a mock final report."""
    return {
        "summary": f"[MOCK] This examination assessed understanding across the uploaded document. The student demonstrated {_score_to_label(overall_score)} overall performance.",
        "overall_assessment": _score_to_label(overall_score),
        "key_strengths": [
            "Demonstrated foundational understanding",
            "Able to recall key definitions",
            "Showed capability with conceptual questions"
        ],
        "areas_for_improvement": [
            "Application of concepts to novel scenarios",
            "Analytical depth in complex questions",
            "Precision of technical terminology"
        ],
        "revision_priorities": [
            "Review topics where performance was below 50%",
            "Practice application-based questions",
            "Focus on areas marked as WEAK or NOT_ASSESSED"
        ]
    }


def _score_to_label(score: float) -> str:
    if score >= 0.85:
        return "Excellent"
    elif score >= 0.70:
        return "Good"
    elif score >= 0.55:
        return "Satisfactory"
    elif score >= 0.40:
        return "Needs Improvement"
    else:
        return "Poor"


class MockGeminiClient(BaseLLMClient):
    @property
    def model_name(self) -> str:
        return "mock-gemini"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        prompt_lower = prompt.lower()

        # Answer evaluation — must check specifically for evaluation context, not just "evaluat" keyword
        # since question prompts also contain "evaluation_rubric"
        if (("student's answer" in prompt_lower or "student answer" in prompt_lower) and
                "evaluat" in prompt_lower):
            answer = ""
            for line in prompt.split("\n"):
                if "student" in line.lower() and "answer" in line.lower() and ":" in line:
                    answer = line.split(":", 1)[1].strip()
                    break
            return json.dumps(_make_evaluation(answer))

        # Question generation — "exam question writer" or "generate...question" together
        # Must be checked before document structure (both use "topic")
        if ("exam question writer" in prompt_lower or
                "generate a diverse set" in prompt_lower or
                ("generate" in prompt_lower and "question" in prompt_lower and "topic" in prompt_lower)):
            topic_name = "Core Topic"
            for line in prompt.split("\n"):
                line_stripped = line.strip()
                if line_stripped.startswith("Topic:"):
                    topic_name = line_stripped.split(":", 1)[1].strip()
                    break
            return json.dumps(_make_questions(topic_name))

        # Document structure extraction
        if any(k in prompt_lower for k in ["analyse the following document", "hierarchical", "topic structure", "extract its hierarchical"]):
            return json.dumps(_make_topic_structure(prompt[:200]))

        # Next question / examination agent
        if any(k in prompt_lower for k in ["next question", "examination agent", "cross-question"]):
            return json.dumps(_make_next_question())

        # Report generation
        if any(k in prompt_lower for k in ["assessment report", "final report", "revision priorities"]):
            return json.dumps(_make_report())

        return json.dumps({"result": "[MOCK] Mock response from Gemini client.", "provider_mode": "mock"})

    def generate_json(self, prompt: str, **kwargs: Any) -> dict:
        raw = self.generate(prompt, **kwargs)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"result": raw}
