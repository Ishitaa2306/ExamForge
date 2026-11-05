"""
Prompts for Final Report Generation Agent (Google Gemini).
Synthesizes comprehensive academic reports strictly from persisted examination evidence.
"""
from typing import Any


def build_report_prompt(
    examination_summary: dict[str, Any],
    topic_assessments: list[dict[str, Any]],
    evaluations_summary: list[dict[str, Any]],
) -> str:
    topic_lines = []
    for ta in topic_assessments:
        topic_lines.append(
            f"- Topic '{ta.get('topic_name')}': Status={ta.get('status')}, "
            f"Questions Examined={ta.get('questions_examined', 0)}, "
            f"Strength Score={ta.get('strength_score', 0):.2f}, "
            f"Mastered={ta.get('mastered_concepts', [])}, "
            f"Gaps={ta.get('knowledge_gaps', [])}"
        )
    topic_str = "\n".join(topic_lines) if topic_lines else "No topic assessments available."

    eval_lines = []
    for ev in evaluations_summary[:15]:
        eval_lines.append(
            f"- Q: \"{ev.get('question_text')}\" (Difficulty: {ev.get('difficulty')}, Category: {ev.get('category')})\n"
            f"  Score: {ev.get('overall_score', 0):.2f} | Label: {ev.get('evaluation_label')}\n"
            f"  Missing: {ev.get('missing_concepts', [])} | Mistakes: {ev.get('mistakes_identified', [])}"
        )
    eval_str = "\n\n".join(eval_lines) if eval_lines else "No individual evaluations recorded."

    return f"""You are Google Gemini, acting as the Senior Academic Dean & Examination Review Committee Chair.

Your task is to synthesize an authoritative, deeply constructive Examination Performance Report for a student who has completed their examination.

IMPORTANT:
- Every score, observation, strength, and weakness must be derived SOLELY from the actual recorded examination evidence below.
- Do NOT fabricate scores, answers, or nonexistent exam items.
- Acknowledge areas where data is insufficient (NOT_ASSESSED topics).

EXAMINATION OVERVIEW:
Document / Subject: {examination_summary.get('document_title')}
Total Questions Answered: {examination_summary.get('questions_answered', 0)} of {examination_summary.get('max_questions', 20)}
Overall Numerical Average: {examination_summary.get('overall_score', 0):.2f}

PER-TOPIC EVIDENCE & MASTERY:
{topic_str}

DETAILED EVALUATIONS OF STUDENT RESPONSES:
{eval_str}

Return ONLY valid RFC-8259 JSON matching this exact structure:
{{
  "overall_summary": "Comprehensive 2-3 paragraph academic synthesis of the student's mastery, cognitive agility, and demonstrated understanding.",
  "academic_standing": "Distinction | Commended | Satisfactory | Needs Intensive Review",
  "demonstrated_strengths": [
    "Specific concept or topic mastered with clear evidence"
  ],
  "critical_knowledge_gaps": [
    "Specific concept or mechanism missed during examination"
  ],
  "partially_understood_concepts": [
    "Concepts where student exhibited incomplete explanations"
  ],
  "not_assessed_areas": [
    "Syllabus topics not probed due to examination constraints"
  ],
  "repeated_misconceptions": [
    "Specific recurring mistakes or misunderstandings identified"
  ],
  "difficulty_performance_analysis": "Assessment of how student handled EASY vs MEDIUM vs HARD questions.",
  "examination_coverage_analysis": "Summary of breadth and depth across the syllabus.",
  "revision_priorities": [
    {{
      "priority": "HIGH | MEDIUM | LOW",
      "topic": "Topic Name",
      "focus_area": "Exact conceptual area to revise",
      "concrete_action": "Specific study exercise or reading recommendation"
    }}
  ]
}}
"""
