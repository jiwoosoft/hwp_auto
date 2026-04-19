from __future__ import annotations

from adapters.rhwp_adapter import RHWPAdapter, RHWPAdapterError
from document_store import DOCUMENT_STORE, DocumentStoreError
from schemas.common import ToolResponseDict, build_tool_response


def extract_document_text_tool(
    path: str = "",
    document_id: str = "",
    include_tables: bool = True,
    max_chars: int = 50_000,
) -> ToolResponseDict:
    """Extract text by direct path or previously opened document_id."""
    adapter = RHWPAdapter()

    target_path = path.strip()
    resolved_document_id = document_id.strip()
    working_text: str | None = None
    source_format = ""

    if resolved_document_id:
        try:
            record = DOCUMENT_STORE.get(resolved_document_id)
        except DocumentStoreError as exc:
            return build_tool_response(
                ok=False,
                error_code="UNKNOWN_DOCUMENT_ID",
                message=str(exc),
                suggestion="Call open_document first or provide a direct path.",
            )
        target_path = record["path"]
        source_format = record["format"]
        working_text = DOCUMENT_STORE.get_working_text(resolved_document_id)

    if not target_path:
        return build_tool_response(
            ok=False,
            error_code="MISSING_DOCUMENT_TARGET",
            message="Provide either path or document_id.",
            suggestion="Use open_document for editor-style workflows, or pass a direct path for quick tests.",
        )

    if working_text is not None:
        normalized_text = working_text.strip()
        truncated = len(normalized_text) > max_chars
        final_text = normalized_text[:max_chars] if truncated else normalized_text
        return build_tool_response(
            ok=True,
            message="text extracted",
            data={
                "text": final_text,
                "char_count": len(normalized_text),
                "truncated": truncated,
                "source_format": source_format,
                "path": target_path,
                "document_id": resolved_document_id,
                "from_working_copy": True,
            },
        )

    try:
        extracted = adapter.extract_text(
            target_path,
            include_tables=include_tables,
            max_chars=max_chars,
        )
    except RHWPAdapterError as exc:
        return build_tool_response(
            ok=False,
            error_code="DOCUMENT_EXTRACTION_FAILED",
            message=str(exc),
            suggestion=(
                "Check the input path first. For .hwp/.hwpx files, configure RHWP_EXTRACT_COMMAND so the adapter can call a local extractor."
            ),
        )

    return build_tool_response(
        ok=True,
        message="text extracted",
        data={
            "text": extracted.text,
            "char_count": extracted.char_count,
            "truncated": extracted.truncated,
            "source_format": extracted.source_format,
            "path": target_path,
            "document_id": resolved_document_id,
            "from_working_copy": False,
        },
    )
