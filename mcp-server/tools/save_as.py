from __future__ import annotations

import json
from pathlib import Path
import tempfile

from adapters.rhwp_adapter import RHWPAdapter, RHWPAdapterError
from document_store import DOCUMENT_STORE, DocumentStoreError
from schemas.common import ToolResponseDict, build_tool_response


TEXT_SAVE_FORMATS = {"txt", "md"}
RHWP_SAVE_FORMATS = {"hwp", "hwpx"}


def save_as_tool(document_id: str, output_path: str) -> ToolResponseDict:
    resolved_document_id = document_id.strip()
    if not resolved_document_id:
        return build_tool_response(
            ok=False,
            error_code="MISSING_DOCUMENT_ID",
            message="document_id is required.",
            suggestion="Call open_document first and reuse its document_id.",
        )

    try:
        record = DOCUMENT_STORE.get(resolved_document_id)
    except DocumentStoreError as exc:
        return build_tool_response(
            ok=False,
            error_code="UNKNOWN_DOCUMENT_ID",
            message=str(exc),
            suggestion="Call open_document first.",
        )

    source_format = record["format"]
    output_format = Path(output_path).suffix.lower().lstrip(".")
    adapter = RHWPAdapter()
    working_text = DOCUMENT_STORE.get_working_text(resolved_document_id)
    if working_text is None:
        try:
            working_text = adapter.extract_text(record["path"]).text
        except RHWPAdapterError as exc:
            return build_tool_response(
                ok=False,
                error_code="DOCUMENT_EXTRACTION_FAILED",
                message=str(exc),
                suggestion="Make sure the source document can be read before saving.",
            )

    if output_format in TEXT_SAVE_FORMATS:
        try:
            saved_path = adapter.write_text_file(output_path, working_text)
        except RHWPAdapterError as exc:
            return build_tool_response(
                ok=False,
                error_code="SAVE_FAILED",
                message=str(exc),
                suggestion="Check the output path and make sure it stays inside the allowed workspace.",
            )
        return build_tool_response(
            ok=True,
            message="document saved",
            data={
                "document_id": resolved_document_id,
                "output_path": str(saved_path),
                "dirty": record["dirty"],
                "mode": "text-write",
            },
        )

    if output_format in RHWP_SAVE_FORMATS:
        try:
            if source_format in RHWP_SAVE_FORMATS and record["operations"]:
                with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as tmp:
                    json.dump(record["operations"], tmp, ensure_ascii=False)
                    ops_path = tmp.name
                payload = adapter.write_hwp_roundtrip_file(
                    source_path=record["path"],
                    output_path=output_path,
                    operations_path=ops_path,
                )
                Path(ops_path).unlink(missing_ok=True)
            else:
                payload = adapter.write_hwp_like_file(output_path, working_text)
        except RHWPAdapterError as exc:
            return build_tool_response(
                ok=False,
                error_code="SAVE_FAILED",
                message=str(exc),
                suggestion=(
                    "Check the output path and verify the rhwp save bridge is implemented. The current HWP/HWPX save mode preserves text content, and roundtrip replay works for recorded paragraph edits."
                ),
            )
        return build_tool_response(
            ok=True,
            message="document saved",
            data={
                "document_id": resolved_document_id,
                "output_path": str(payload.get("output_path", output_path)),
                "dirty": record["dirty"],
                "mode": str(payload.get("mode", "blank-document-text-export")),
                "source_format": source_format,
                "output_format": output_format,
                "note": str(payload.get("note", "")),
            },
        )

    return build_tool_response(
        ok=False,
        error_code="SAVE_FORMAT_NOT_SUPPORTED",
        message=f"Unsupported save format: {output_format or 'unknown'}.",
        suggestion="Use .txt, .md, .hwp, or .hwpx as the output extension.",
    )
