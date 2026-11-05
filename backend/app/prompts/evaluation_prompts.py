"""
Prompts for answer evaluation.
"""


def build_evaluation_prompt(
    question_text: str,
    expected_points: list[str],
    student_answer: str,
    context: str = "",
) -> str:
    expected_str = "\n".join(f"- {p}" for p in expected_points) if expected_points else "Not specified"
    context_section = f"\nReference context from document:\n\"\"\"\n{context[:3000]}\n\"\"\"" if context else ""

    return f"""You are an expert academic examiner evaluating a student's answer.

Question: {question_text}

Expected answer points:
{expected_str}
{context_section}

Student's answer: {student_answer}

Evaluate the student's answer strictly and fairly.

Evaluate the answer strictly and fairly. Return ONLY valid JSON:
{{
  "evaluation_label": "CORRECT|PARTIALLY_CORRECT|INCORRECT|INCOMPLETE|UNCLEAR",
  "correctness_score": 0.0,
  "completeness_score": 0.0,
  "conceptual_score": 0.0,
  "reasoning_score": 0.0,
  "application_score": 0.0,
  "overall_score": 0.0,
  "missing_concepts": ["concept that was missed"],
  "mistakes_identified": ["specific error"],
  "evaluation_explanation": "Detailed feedback for the student",
  "confidence": 0.9
}}

Scoring guide (0.0 – 1.0):
- CORRECT: overall_score >= 0.85
- PARTIALLY_CORRECT: 0.5 <= overall_score < 0.85
- INCORRECT: overall_score < 0.35
- INCOMPLETE: answer attempts but omits critical points (0.35–0.5)
- UNCLEAR: answer is incoherent or off-topic
"""
