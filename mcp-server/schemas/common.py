from __future__ import annotations

from typing import TypedDict


class ToolResponseDict(TypedDict, total=False):
    ok: bool
    message: str
    data: dict[str, object]
    error_code: str
    suggestion: str


def build_tool_response(
    *,
    ok: bool,
    message: str,
    data: dict[str, object] | None = None,
    error_code: str | None = None,
    suggestion: str | None = None,
) -> ToolResponseDict:
    payload: ToolResponseDict = {
        "ok": ok,
        "message": message,
    }
    if data is not None:
        payload["data"] = data
    if error_code is not None:
        payload["error_code"] = error_code
    if suggestion is not None:
        payload["suggestion"] = suggestion
    return payload
