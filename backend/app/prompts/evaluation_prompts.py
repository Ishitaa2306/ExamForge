"""
Prompts for Answer Evaluation Agent (IBM Granite via watsonx.ai).
Evaluates student answers semantically against rubrics and academic context.
"""
from typing import Any


def build_evaluation_prompt(
    question_text: str,
    expected_points: list[str],
    student_answer: str,
    context: str = "",
    rubric: dict[str, Any] | None = None,
    difficulty: str = "MEDIUM",
    category: str = "CONCEPTUAL",
) -> str:
    points_str = "\n".join(f"- {p}" for p in expected_points) if expected_points else "Infer from academic question & context."
    rubric_str = str(rubric) if rubric else "Standard 5-criterion academic evaluation."
    context_str = f"\nDOCUMENT GROUNDING CONTEXT:\n\"\"\"\n{context}\n\"\"\"\n" if context else ""

    return f"""You are IBM Granite, acting as a rigorous, fair Academic Answer Evaluation Specialist.

Your task is to evaluate the student's submitted answer against the examination question, expected concepts, and grounded document context.

EVALUATION CRITERIA & WEIGHTING:
1. Correctness (30%): Factual and theoretical accuracy of statements made.
2. Completeness (25%): Coverage of essential expected points and core dimensions.
3. Conceptual Understanding (20%): Depth of comprehension vs superficial keyword dropping.
4. Reasoning & Logic (15%): Logical coherence, cause-and-effect clarity, justifications.
5. Application (10%): Ability to connect theory to scenarios, examples, or practical context.

SEMANTIC EVALUATION RULES:
- Recognize semantic equivalence: Alternative phrasing or student's own words expressing the correct concept must be awarded full credit.
- Penalize keyword stuffing: Memorized terminology without sound reasoning or explanation must NOT receive full marks.
- Pinpoint misconceptions: Identify exactly what misconceptions or gaps are evident in the student's reasoning.

QUESTION DETAILS:
Question: {question_text}
Question Type: {category}
Difficulty: {difficulty}

EXPECTED CONCEPTS & RUBRIC:
Expected Points:
{points_str}

Rubric Details:
{rubric_str}
{context_str}
STUDENT SUBMISSION:
\"\"\"
{student_answer}
\"\"\"

CLASSIFICATION SYSTEM:
- CORRECT: Demonstrates sound understanding, satisfies all core criteria (overall_score >= 0.85).
- PARTIALLY_CORRECT: Contains valid elements but has omissions or minor flaws (0.50 <= overall_score < 0.85).
- INCORRECT: Fundamentally flawed, erroneous reasoning, or major misconceptions (overall_score < 0.35).
- INCOMPLETE: Answer begins correctly but omits indispensable components (0.35 <= overall_score < 0.50).
- UNCLEAR: Incoherent, irrelevant, evasive, or unparseable.

Return ONLY valid RFC-8259 JSON matching this exact structure:
{{
  "evaluation_label": "CORRECT",
  "overall_score": 0.85,
  "correctness_score": 0.90,
  "completeness_score": 0.80,
  "conceptual_score": 0.85,
  "reasoning_score": 0.85,
  "application_score": 0.80,
  "correct_concepts": [
    "Identified correct concept explanation"
  ],
  "missing_concepts": [
    "Specific concept or detail omitted by student"
  ],
  "mistakes_identified": [
    "Specific misconception or factual inaccuracy"
  ],
  "evaluation_explanation": "Detailed objective feedback explaining the scoring breakdown and suggestions.",
  "confidence": 0.95,
  "reasoning_quality": "High | Moderate | Low | None",
  "evidence_sufficiency": "SUFFICIENT"
}}
"""
