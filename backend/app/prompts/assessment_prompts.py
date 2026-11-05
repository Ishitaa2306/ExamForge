"""
Prompts for Knowledge Assessment Agent (IBM Granite via watsonx.ai).
Determines topic and concept mastery from cumulative examination evidence.
"""
from typing import Any


def build_assessment_prompt(
    topic_name: str,
    topic_description: str,
    evaluations: list[dict[str, Any]],
    previous_assessment: dict[str, Any] | None = None,
) -> str:
    eval_lines = []
    for idx, ev in enumerate(evaluations, 1):
        q_text = ev.get("question_text", "N/A")
        label = ev.get("evaluation_label", "UNCLEAR")
        score = ev.get("overall_score", 0.0)
        missing = ev.get("missing_concepts", [])
        mistakes = ev.get("mistakes_identified", [])
        eval_lines.append(
            f"Question {idx}: \"{q_text}\"\n"
            f"  Result: {label} (Score: {score:.2f})\n"
            f"  Missing: {', '.join(missing) if missing else 'None'}\n"
            f"  Mistakes: {', '.join(mistakes) if mistakes else 'None'}"
        )

    eval_summary = "\n\n".join(eval_lines) if eval_lines else "No questions asked yet for this topic."
    prev_str = (
        f"Previous Status: {previous_assessment.get('status')}, Strength: {previous_assessment.get('strength_score')}"
        if previous_assessment
        else "No previous assessment on record."
    )

    return f"""You are IBM Granite, acting as an Academic Knowledge Assessment Specialist.

Your task is to analyze the student's cumulative examination performance on a specific academic topic and synthesize an authoritative knowledge profile.

TOPIC DETAILS:
Topic: {topic_name}
Description: {topic_description or 'Academic syllabus topic'}
Previous Assessment: {prev_str}

CUMULATIVE EXAMINATION EVIDENCE FOR THIS TOPIC:
{eval_summary}

ASSESSMENT RULES:
1. Status Definitions:
   - STRONG: Demonstrates consistent, deep understanding across questions with sound conceptual reasoning.
   - PARTIALLY_UNDERSTOOD: Shows grasp of basics but exhibits recurring gaps, missing mechanisms, or incomplete application.
   - WEAK: Demonstrates significant misconceptions or persistent failure to address fundamental concepts despite evidence.
   - NOT_ASSESSED: Insufficient questions answered (e.g. fewer than 2 questions, or zero questions) to reach a reliable academic conclusion. NEVER mark an unexplored or lightly probed topic as WEAK.
2. Track repeated misconceptions and identify if understanding improved over successive questions.
3. Base your judgment on semantic depth and qualitative evidence, not a simplistic average of numerical scores.

Return ONLY valid RFC-8259 JSON matching this exact structure:
{{
  "status": "STRONG",
  "strength_score": 0.85,
  "evidence_sufficient": true,
  "mastered_concepts": ["concept 1", "concept 2"],
  "knowledge_gaps": ["gap 1"],
  "repeated_mistakes": ["repeated error if any"],
  "learning_trajectory": "IMPROVING | STABLE | DECLINING | INSUFFICIENT_DATA",
  "qualitative_assessment": "Clear explanation of the student's actual level of understanding on this topic.",
  "recommended_revision_priority": "HIGH | MEDIUM | LOW"
}}
"""
