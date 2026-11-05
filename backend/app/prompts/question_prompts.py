"""
Prompts for Question Generation Agent (Google Gemini).
Generates comprehensive question banks covering all 8 cognitive categories and 3 difficulty tiers.
"""


def build_question_prompt(
    topic_name: str,
    topic_description: str,
    document_context: str = "",
    subtopics: list[str] | None = None,
) -> str:
    subtopics_str = ", ".join(subtopics) if subtopics else "General topic concepts"
    context_str = f"\nGROUNDING DOCUMENT EXCERPTS:\n\"\"\"\n{document_context[:4000]}\n\"\"\"\n" if document_context else ""

    return f"""You are Google Gemini, acting as an elite Academic Examination Committee Author.

Your task is to author a comprehensive, multi-dimensional question bank for the academic topic below, grounded strictly in the provided syllabus and document material.

TOPIC: {topic_name}
DESCRIPTION: {topic_description or 'Academic topic overview'}
SUBTOPICS: {subtopics_str}
{context_str}
REQUIREMENTS:
1. Generate between 4 and 8 rigorous questions spanning multiple cognitive categories:
   - DEFINITION: Precise technical definitions and exact terminology.
   - CONCEPTUAL: Core foundational principles, mechanisms, and theories.
   - DIFFERENCE: Comparative analysis between contrasting concepts or methods.
   - APPLICATION: Problem-solving in realistic engineering/scientific scenarios.
   - NUMERICAL: Quantitative calculations or algorithmic derivations where appropriate.
   - ANALYTICAL: Trade-offs, edge cases, complexity, or structural properties.
   - SCENARIO: Applied troubleshooting, diagnosis, or design cases.
   - TRICKY: Counter-intuitive concepts, common student misconceptions, or boundary conditions.
2. Provide a balanced distribution of difficulties: EASY, MEDIUM, and HARD.
3. For EVERY question, define explicit expected answer points and an evaluation rubric for scoring semantic answers.
4. Avoid duplicate or trivial questions.

Return ONLY valid RFC-8259 JSON matching this exact structure:
{{
  "questions": [
    {{
      "question_text": "Complete and clear question formulation",
      "category": "CONCEPTUAL",
      "difficulty": "MEDIUM",
      "subtopic_name": "Associated subtopic if known",
      "expected_answer_points": [
        "Primary concept that must be stated",
        "Supporting mechanism or causal explanation"
      ],
      "evaluation_rubric": {{
        "core_criteria": ["Factual accuracy", "Conceptual reasoning"],
        "partial_credit_guidelines": "Award 50% if the student states the definition but omits the boundary conditions.",
        "common_misconceptions": ["Confusing X with Y"]
      }},
      "source_pages": [1, 2],
      "expected_reasoning": "Detailed technical explanation of what a stellar answer should contain."
    }}
  ]
}}
"""
