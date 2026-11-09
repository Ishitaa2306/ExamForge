import sys
import time

sys.path.insert(0, r"D:\ibm sample\ExamForge\backend")
from app.core.config import settings
from app.llm.granite_client import GraniteClient
from app.prompts.evaluation_prompts import build_evaluation_prompt

client = GraniteClient(
    api_key=settings.WATSONX_API_KEY,
    project_id="824a19a1-dc4a-4cb9-aec6-b007a2455c77",
    model_id="ibm/granite-4-h-small",
    url=settings.WATSONX_URL,
)

sample_answer = """
State space tree is a tree representation of the state space.
It organizes the search space into smaller choices or decisions.
Every node represents a problem state, and each branch represents a decision or choice.
Root node represents the initial state of the problem before making any choices.
Branch nodes represent intermediate partial solutions.
Leaf nodes represent final states which can be either valid solutions or dead ends.
Backtracking searches through this tree using depth first search, pruning branches that violate constraints using bounding functions.
"""

prompt = build_evaluation_prompt(
    question_text="Differentiate between State Space and State Space Tree in Backtracking. Elaborate on what the root, branch, and leaf nodes specifically represent.",
    expected_points=["State space is the set of all possible configurations", "State space tree is the tree organization of choices", "Root is initial state", "Branch nodes are partial states", "Leaf nodes are goal states or dead ends"],
    student_answer=sample_answer,
    context="In backtracking, the state space is the set of all valid and invalid configurations. A state space tree represents this space hierarchically. The root represents the initial problem state with no choices made. Intermediate nodes represent partial solutions where some variables are assigned. Leaves represent complete candidate solutions which may be valid or dead ends pruned by constraints.",
    difficulty="MEDIUM",
    category="CONCEPTUAL",
)

t0 = time.time()
res = client.generate_json(prompt, max_new_tokens=768)
elapsed = time.time() - t0
print(f"Type: {type(res)}, Elapsed: {elapsed:.2f}s")
print("Content:", res)
