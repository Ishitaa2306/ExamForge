"""
Prompts for report generation.
"""


def build_report_prompt(examination_id: int, assessments: list[dict]) -> str:
    assessment_summary = "\n".join(
        f"- Topic {a['topic_id']}: status={a['status']}, score={a.get('strength_score', 0):.2f}, "
        f"questions={a.get('questions_examined', 0)}"
        for a in assessments
    )
    return f"""You are an academic performance coach generating a personalised study report.

Examination ID: {examination_id}

Topic assessment results:
{assessment_summary}

Generate actionable, encouraging, and specific study recommendations.
Return ONLY valid JSON:
{{
  "recommendations": [
    "Specific recommendation 1",
    "Specific recommendation 2",
    "Specific recommendation 3"
  ],
  "overall_summary": "1-2 sentence summary of the student's performance"
}}

Guidelines:
- Be specific (name topics, not just 'study more')
- Be encouraging but honest
- Prioritise weak topics
- Suggest concrete revision strategies
"""
