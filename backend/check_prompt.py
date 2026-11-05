from app.prompts.question_prompts import build_question_prompt
prompt = build_question_prompt("Test Topic", "description", 1)
p_lower = prompt.lower()
print("Contains 'evaluat':", "evaluat" in p_lower)
print("Contains 'scoring guide':", "scoring guide" in p_lower)
print("Contains 'exam question writer':", "exam question writer" in p_lower)
print("Contains 'generate a diverse set':", "generate a diverse set" in p_lower)
# Show lines containing evaluat
for i, line in enumerate(p_lower.split("\n")):
    if "evaluat" in line:
        print(f"Line {i} EVALUAT: {repr(line[:100])}")
