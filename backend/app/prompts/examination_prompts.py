"""
Prompts for examination orchestration.
"""


def build_next_question_prompt(
    previous_question: str,
    previous_answer: str,
    topic_name: str,
    difficulty: str,
) -> str:
    return f"""You are conducting an academic oral examination.

Previous question: {previous_question}
Student answer: {previous_answer}
Current topic: {topic_name}
Required difficulty: {difficulty}

Based on the student's answer, generate one follow-up question that:
1. Probes deeper if the answer was strong
2. Revisits fundamentals if the answer was weak
3. Maintains the specified difficulty level

Return ONLY valid JSON:
{{
  "question_text": "Your follow-up question here",
  "category": "CONCEPTUAL|DEFINITION|DIFFERENCE|APPLICATION|ANALYTICAL",
  "difficulty": "{difficulty}",
  "rationale": "Why this follow-up is appropriate"
}}
"""
