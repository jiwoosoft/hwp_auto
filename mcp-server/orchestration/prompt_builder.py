from __future__ import annotations


def build_paragraph_ai_prompt(*, task_type: str, instruction: str, paragraph_text: str) -> str:
    safe_instruction = instruction.strip() or "문단을 더 명확하고 자연스럽게 다듬어줘."
    if task_type == "summarize":
        task_label = "summarize"
        format_hint = "핵심을 3~5문장으로 요약한다."
    elif task_type == "insert":
        task_label = "insert"
        format_hint = "현재 문단 뒤에 들어갈 새 문단 하나를 작성한다."
    else:
        task_label = "rewrite"
        format_hint = "현재 문단을 같은 의미로 더 좋은 문장으로 다시 쓴다."

    return f'''You are assisting a Korean HWP document editing workflow.
Return ONLY valid JSON.

Required JSON shape:
{{
  "task_type": "{task_label}",
  "title": "very short label",
  "preview": "human-readable short explanation",
  "content": "final Korean text only"
}}

Rules:
- Output must be a single JSON object and nothing else.
- Keep the response in Korean.
- content must not be empty.
- title must be under 30 characters.
- preview must be one short sentence.
- {format_hint}

User instruction:
{safe_instruction}

Current paragraph:
"""
{paragraph_text}
"""
'''
