from __future__ import annotations

from adapters.rhwp_adapter import RHWPAdapter, RHWPAdapterError
from document_store import DOCUMENT_STORE, DocumentStoreError
from schemas.common import ToolResponseDict, build_tool_response


def extract_document_structure_tool(
    path: str = "",
    document_id: str = "",
    include_tables: bool = True,
    max_chars: int = 50_000,
) -> ToolResponseDict:
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

    try:
        if working_text is not None:
            structure = adapter.structure_from_text(
                text=working_text,
                source_format=source_format,
                path=target_path,
                max_chars=max_chars,
            )
        else:
            structure = adapter.extract_structure(
                target_path,
                include_tables=include_tables,
                max_chars=max_chars,
            )
    except RHWPAdapterError as exc:
        return build_tool_response(
            ok=False,
            error_code="DOCUMENT_STRUCTURE_FAILED",
            message=str(exc),
            suggestion=(
                "Check the input path first. For .hwp/.hwpx files, configure RHWP_EXTRACT_COMMAND so the adapter can call a local extractor."
            ),
        )

    structure["document_id"] = resolved_document_id
    structure["from_working_copy"] = working_text is not None
    return build_tool_response(
        ok=True,
        message="structure extracted",
        data=structure,
    )
