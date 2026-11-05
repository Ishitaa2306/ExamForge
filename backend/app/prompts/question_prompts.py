"""
Prompts for question generation.
"""


def build_question_prompt(
    topic_name: str,
    topic_description: str,
    document_id: int,
) -> str:
    return f"""You are an expert exam question writer.

Generate a diverse set of examination questions for the following academic topic.
Create at least 3 questions covering different cognitive levels and categories.

Topic: {topic_name}
Description: {topic_description}

Return ONLY valid JSON with this exact schema:
{{
  "questions": [
    {{
      "question_text": "Full question text",
      "category": "DEFINITION|CONCEPTUAL|DIFFERENCE|APPLICATION|NUMERICAL|ANALYTICAL|SCENARIO|TRICKY",
      "difficulty": "EASY|MEDIUM|HARD",
      "expected_answer_points": ["Key point 1", "Key point 2"],
      "evaluation_rubric": {{"key_concepts": ["concept1"], "partial_credit": true}},
      "source_pages": [1, 2]
    }}
  ]
}}

Guidelines:
- DEFINITION: Ask for precise definitions of key terms
- CONCEPTUAL: Test understanding of core ideas
- DIFFERENCE: Compare and contrast related concepts
- APPLICATION: Apply theory to scenarios
- NUMERICAL: Calculation-based questions (if applicable)
- ANALYTICAL: Analyse trade-offs or implications
- SCENARIO: Real-world problem solving
- TRICKY: Common misconceptions or edge cases
"""
