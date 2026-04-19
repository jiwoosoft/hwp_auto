from __future__ import annotations

from adapters.rhwp_adapter import RHWPAdapter, RHWPAdapterError
from document_store import DOCUMENT_STORE
from schemas.common import ToolResponseDict, build_tool_response


def open_document_tool(path: str, readonly: bool = True) -> ToolResponseDict:
    adapter = RHWPAdapter()
    try:
        resolved_path = adapter.resolve_path(path)
    except RHWPAdapterError as exc:
        return build_tool_response(
            ok=False,
            error_code="DOCUMENT_OPEN_FAILED",
            message=str(exc),
            suggestion="Provide a valid local document path inside the project workspace.",
        )

    record = DOCUMENT_STORE.open_document(resolved_path, readonly=readonly)
    return build_tool_response(
        ok=True,
        message="document opened",
        data=dict(record),
    )
