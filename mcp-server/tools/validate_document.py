from __future__ import annotations

from adapters.rhwp_adapter import RHWPAdapter, RHWPAdapterError
from schemas.common import ToolResponseDict, build_tool_response


def validate_document_tool(path: str) -> ToolResponseDict:
    adapter = RHWPAdapter()
    try:
        resolved = adapter.resolve_path(path)
        extracted = adapter.extract_text(str(resolved))
    except RHWPAdapterError as exc:
        return build_tool_response(
            ok=False,
            error_code="VALIDATION_FAILED",
            message=str(exc),
            suggestion="Check the file path and ensure the file can still be read after saving.",
        )

    return build_tool_response(
        ok=True,
        message="document validated",
        data={
            "path": str(resolved),
            "readable": True,
            "text_extractable": bool(extracted.text),
            "char_count": extracted.char_count,
            "source_format": extracted.source_format,
        },
    )
