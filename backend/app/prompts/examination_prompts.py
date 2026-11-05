"""
Prompts for Autonomous Examination Agent (Google Gemini).
Central intelligent examiner that adapts dynamically based on student responses and Granite evaluations.
"""
from typing import Any


def build_examiner_turn_prompt(
    examination_context: dict[str, Any],
    turn_history: list[dict[str, Any]],
    candidate_questions: list[dict[str, Any]],
    topic_coverage: dict[str, Any],
    current_difficulty: str,
) -> str:
    # Format recent turns with previous answers and Granite evaluation evidence
    history_blocks = []
    for idx, turn in enumerate(turn_history, 1):
        history_blocks.append(
            f"--- Turn {idx} ---\n"
            f"Question Asked: {turn.get('question_text')}\n"
            f"Topic: {turn.get('topic_name')} | Difficulty: {turn.get('difficulty')} | Category: {turn.get('category')}\n"
            f"Student Answer: {turn.get('answer_text', 'No answer submitted')}\n"
            f"Granite Evaluation Result: Label={turn.get('evaluation_label')}, Score={turn.get('overall_score')}\n"
            f"Granite Identified Missing Concepts: {turn.get('missing_concepts', [])}\n"
            f"Granite Identified Misconceptions: {turn.get('mistakes_identified', [])}\n"
            f"Granite Topic Assessment: {turn.get('topic_status', 'N/A')}"
        )

    history_str = "\n\n".join(history_blocks) if history_blocks else "This is the very first question of the examination."

    candidates_str = "\n".join(
        f"- [ID:{q.get('id')}] [{q.get('category')} - {q.get('difficulty')}] (Topic: {q.get('topic_name')}): {q.get('question_text')}"
        for q in candidate_questions[:8]
    ) if candidate_questions else "No pre-generated candidates available. You may generate an original contextual question."

    coverage_str = "\n".join(
        f"- Topic '{name}': {count} questions asked"
        for name, count in topic_coverage.items()
    ) if topic_coverage else "No topics examined yet."

    return f"""You are Google Gemini, acting as the Autonomous Academic Examiner in an oral/interactive academic examination.

EXAMINATION ROLE:
You behave like an astute, perceptive university professor conducting an oral defense or rigorous examination.
You closely review what the student has previously stated and the semantic evaluation provided by IBM Granite.

DECISION PROTOCOL:
1. Review the student's most recent answer and Granite's evaluation:
   - If the student was PARTIALLY_CORRECT or INCOMPLETE, and critical missing concepts were flagged by Granite, you should decide whether to ask a targeted FOLLOW_UP question to probe their reasoning deeper or clarify the gap.
   - If the student was INCORRECT, decide whether to test foundational understanding of the concept or shift to another topic.
   - If the student was CORRECT with high confidence, reward them by progressing to a more challenging question or exploring another unexamined topic for balanced coverage.
2. Ensure broad curriculum coverage across topics according to current coverage statistics.
3. Dynamically modulate difficulty: EASY, MEDIUM, or HARD.
4. You may either select the best candidate question from the repository OR generate a tailored follow-up question specifically probing the student's previous misunderstanding.

EXAMINATION CONTEXT:
Document / Subject: {examination_context.get('document_title', 'Academic Subject')}
Current Target Difficulty: {current_difficulty}
Questions Asked So Far: {len(turn_history)} of {examination_context.get('max_questions', 20)}

TOPIC COVERAGE SO FAR:
{coverage_str}

CANDIDATE QUESTIONS FROM QUESTION BANK:
{candidates_str}

TURN & EVALUATION HISTORY:
{history_str}

Return ONLY valid RFC-8259 JSON with this exact structure:
{{
  "decision_action": "FOLLOW_UP",
  "selected_question_id": null,
  "question_text": "Precise formulation of the question to ask the student next.",
  "category": "CONCEPTUAL",
  "difficulty": "{current_difficulty}",
  "topic_id": {examination_context.get('current_topic_id', 'null')},
  "expected_answer_points": [
    "Key expected point 1",
    "Key expected point 2"
  ],
  "examiner_reasoning": "Clear pedagogical explanation of why this question was chosen or generated based on the student's previous response and Granite's evaluation evidence."
}}
"""
