from __future__ import annotations

from typing import Iterable


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


def build_document_ai_prompt(
    *,
    task_type: str,
    instruction: str,
    paragraphs: Iterable[str],
) -> str:
    safe_instruction = instruction.strip() or "문서 전체를 더 명확하고 자연스럽게 다듬어줘."
    if task_type == "summarize":
        task_label = "summarize"
        task_hint = "문서 전체의 핵심을 반영하도록 필요한 문단을 요약·통합한다."
    elif task_type == "append":
        task_label = "append"
        task_hint = "기존 문단은 수정하지 않고, 문서 끝에 이어질 새 문단들을 추가한다 (append 항목에 포함)."
    else:
        task_label = "rewrite"
        task_hint = "문서의 톤과 맥락을 유지하며 문단들을 더 완성도 높은 한국어 문장으로 다시 쓴다."

    numbered_lines: list[str] = []
    for idx, text in enumerate(paragraphs):
        safe_text = (text or "").replace("\n", " ").strip()
        numbered_lines.append(f"[{idx}] {safe_text}")
    numbered_block = "\n".join(numbered_lines) if numbered_lines else "[0] (문서에 문단이 없습니다)"

    return f'''You are assisting a Korean HWP document-wide editing workflow.
Return ONLY valid JSON.

Required JSON shape:
{{
  "task_type": "{task_label}",
  "title": "short label (<=30 chars)",
  "preview": "one short Korean sentence summarizing the changes",
  "edits": [
    {{ "paragraph_index": <int>, "new_text": "수정된 문단 텍스트" }}
  ],
  "appends": [
    "문서 뒤에 새로 추가할 문단 1",
    "문서 뒤에 새로 추가할 문단 2"
  ]
}}

Rules:
- Output must be a single JSON object and nothing else.
- Keep all text in Korean.
- paragraph_index must be one of the indexes shown below (0-based).
- Include only the paragraphs you actually change inside "edits"; unchanged paragraphs must be omitted.
- new_text must be a non-empty single string (use \\n for line breaks if absolutely needed).
- Use "appends" only if the instruction asks to add new paragraphs; otherwise return an empty array.
- {task_hint}

User instruction:
{safe_instruction}

Document paragraphs (0-based index):
"""
{numbered_block}
"""
'''
