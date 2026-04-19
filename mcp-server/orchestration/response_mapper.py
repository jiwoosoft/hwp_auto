from __future__ import annotations

from schemas.common import ToolResponseDict, build_tool_response


def map_ai_preview(*, task_type: str, paragraph_index: int, response: dict[str, object]) -> ToolResponseDict:
    content = str(response.get("content", "")).strip()
    if not content:
        return build_tool_response(
            ok=False,
            error_code="AI_EMPTY_CONTENT",
            message="AI response did not include usable content.",
            suggestion="Try a simpler instruction or shorter paragraph.",
        )

    return build_tool_response(
        ok=True,
        message="ai preview ready",
        data={
            "task_type": task_type,
            "paragraph_index": paragraph_index,
            "title": str(response.get("title", "AI 결과")).strip() or "AI 결과",
            "preview": str(response.get("preview", "")).strip(),
            "content": content,
        },
    )
