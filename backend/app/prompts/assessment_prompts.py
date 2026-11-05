"""
Prompts for knowledge assessment.
"""


def build_assessment_prompt(
    topic_name: str,
    evaluations: list[dict],
) -> str:
    eval_summary = "\n".join(
        f"- Q{i+1}: score={e.get('overall_score', 0):.2f}, label={e.get('evaluation_label', 'N/A')}"
        for i, e in enumerate(evaluations)
    )
    return f"""You are an academic knowledge assessment specialist.

Topic: {topic_name}
Evaluation summary for this topic:
{eval_summary}

Based on these evaluation results, assess the student's mastery of this topic.
Return ONLY valid JSON:
{{
  "status": "STRONG|PARTIALLY_UNDERSTOOD|WEAK|NOT_ASSESSED",
  "strength_score": 0.0,
  "evidence_sufficient": true,
  "notes": "Qualitative assessment note"
}}
"""
