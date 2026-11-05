"""
Prompts for document structure extraction.
"""


def build_structure_prompt(document_text: str) -> str:
    return f"""You are an expert academic content analyser.

Analyse the following document text and extract its hierarchical topic structure.
Please extract its hierarchical organisation completely.

Return ONLY valid JSON with this exact schema:
{{
  "topics": [
    {{
      "name": "Topic name",
      "description": "Brief description",
      "order_index": 0,
      "page_start": 1,
      "page_end": 5,
      "subtopics": [
        {{
          "name": "Subtopic name",
          "description": "Brief description",
          "order_index": 0,
          "concepts": [
            {{
              "type": "DEFINITION|FORMULA|ALGORITHM|CONCEPT",
              "name": "Concept name",
              "content": "Concept content or definition",
              "page_references": [1, 2]
            }}
          ]
        }}
      ]
    }}
  ]
}}

Document text:
\"\"\"
{document_text[:8000]}
\"\"\"
"""
